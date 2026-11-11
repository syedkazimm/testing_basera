"""Matching service (US-08, US-09, US-10).

Pure scoring functions, kept apart from the view. Given a GrowProfile it returns a ranked list of
MatchResult objects. The score and the reasons come from the SAME per-criterion numbers, so the
reasons can never contradict the score.
"""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from catalog.models import Species
from growprofiles.models import Purpose, Soil, Sunlight, Water

# Weights add up to 100 (SPEC 6.1).
WEIGHTS = {"sunlight": 30, "soil": 25, "water": 20, "setting": 15, "purpose": 10}
LOW_FIT_BELOW = 40

# Ordinal positions used for "how many steps apart are these two?".
SUN_ORDER = {Sunlight.FULL_SUN: 2, Sunlight.PARTIAL_SHADE: 1, Sunlight.SHADE: 0}
WATER_ORDER = {Water.LOW: 0, Water.MEDIUM: 1, Water.HIGH: 2}

MATCH, PARTIAL, NO_MATCH = "match", "partial", "no match"


@dataclass
class Reason:
    """One plain-language line explaining one criterion."""

    criterion: str
    state: str  # "match", "partial" or "no match"
    text: str

    @property
    def symbol(self):
        return {MATCH: "✔", PARTIAL: "◐", NO_MATCH: "✘"}[self.state]


@dataclass
class MatchResult:
    species: Species
    score: int
    reasons: list = field(default_factory=list)

    @property
    def in_stock(self):
        return self.species.stock > 0

    @property
    def low_fit(self):
        return self.score < LOW_FIT_BELOW


def _state(fraction):
    """Turn a 0 / 0.5 / 1 criterion score into its state name."""
    return MATCH if fraction == 1 else PARTIAL if fraction == 0.5 else NO_MATCH


def _ordinal_fraction(a, b, order):
    """1 - |difference| / 2: exact 1.0, one step 0.5, opposite 0."""
    return 1 - abs(order[a] - order[b]) / 2


def _label(choice_class, value):
    """Lower-case label for a choice code, e.g. FULL_SUN -> 'full sun'."""
    return choice_class(value).label.lower()


def _sunlight(species, profile):
    fraction = _ordinal_fraction(species.sunlight, profile.sunlight, SUN_ORDER)
    wants, has = _label(Sunlight, species.sunlight), _label(Sunlight, profile.sunlight)
    if fraction == 1:
        text = f"Prefers {wants} — your space gets {has}."
    elif fraction == 0.5:
        text = f"Prefers {wants} — your space gets {has}, which is close."
    else:
        text = f"Prefers {wants} — your space gets {has}."
    return fraction, text


def _soil(species, profile):
    wants, has = _label(Soil, species.soil), _label(Soil, profile.soil)
    if species.soil == profile.soil:
        return 1, f"Prefers {wants} soil — your soil is {has}."
    if species.soil == Soil.LOAM:
        return 0.5, f"Prefers loam soil — adaptable, but your soil is {has}."
    return 0, f"Prefers {wants} soil — your soil is {has}."


def _water(species, profile):
    fraction = _ordinal_fraction(species.water, profile.water, WATER_ORDER)
    needs, gives = _label(Water, species.water), _label(Water, profile.water)
    if fraction == 1:
        return fraction, f"Needs {needs} water — you can provide {gives} water."
    needs_more = WATER_ORDER[species.water] > WATER_ORDER[profile.water]
    if needs_more:
        return fraction, f"Needs {needs} water — you can only provide {gives} water."
    return fraction, f"Needs only {needs} water — you would provide {gives} water."


def _setting(species, profile):
    space = profile.get_space_type_display().lower()  # "indoor" / "outdoor"
    yours = space + "s"  # "indoors" / "outdoors"
    if species.setting == "BOTH":
        return 1, f"Grows indoors or outdoors — suits your {space} space."
    grows = "indoors" if species.setting == "INDOOR" else "outdoors"
    if species.setting == profile.space_type:
        return 1, f"Grows {grows} — your space is {yours}."
    return 0, f"Grows {grows} only — your space is {yours}."


def _purpose(species, profile):
    goal = profile.get_purpose_display().lower()
    if profile.purpose in species.purposes_list:
        return 1, f"Useful for {goal} — matches your goal."
    return 0, f"Not listed for {goal}, your goal."


# The criteria in the order they are shown to the customer.
CRITERIA = [
    ("sunlight", _sunlight),
    ("soil", _soil),
    ("water", _water),
    ("setting", _setting),
    ("purpose", _purpose),
]


def score_species(species, profile):
    """Return a MatchResult: the 0-100 score and one reason per criterion."""
    total = 0
    reasons = []
    for name, judge in CRITERIA:
        fraction, text = judge(species, profile)
        total += WEIGHTS[name] * fraction
        reasons.append(Reason(name, _state(fraction), text))
    # Round half up, so 62.5 becomes 63 (Python's round() would give 62).
    return MatchResult(species=species, score=int(total + 0.5), reasons=reasons)


def candidate_species(profile):
    """Step 1, the hard filters: visible, native to the profile's region, not invasive. One query."""
    return Species.objects.visible().filter(regions=profile.region, is_invasive=False)


def find_matches(profile):
    """Score every candidate and return them best first (ties broken by common name)."""
    results = [score_species(species, profile) for species in candidate_species(profile)]
    results.sort(key=lambda result: (-result.score, result.species.common_name))
    return results


# --- Filters and sorting for the results page (US-11) ----------------------------------------
SORTS = {
    "score": lambda r: (-r.score, r.species.common_name),
    "price_asc": lambda r: (r.species.price, -r.score, r.species.common_name),
    "price_desc": lambda r: (-r.species.price, -r.score, r.species.common_name),
}
FILTER_LABELS = {"purpose": "Purpose", "setting": "Indoor/outdoor", "max_price": "Max price"}


def parse_filters(params):
    """Read the filters from GET parameters. Unknown or invalid values are simply ignored."""
    filters = {}
    purpose = params.get("purpose", "")
    if purpose in Purpose.values:
        filters["purpose"] = purpose
    setting = params.get("setting", "")
    if setting in ("INDOOR", "OUTDOOR"):
        filters["setting"] = setting
    try:
        max_price = Decimal(params.get("max_price", "").strip())
        if max_price > 0:
            filters["max_price"] = max_price
    except (InvalidOperation, AttributeError):
        pass
    return filters


def _passes(species, filters):
    """True if one species satisfies every active filter."""
    if "purpose" in filters and filters["purpose"] not in species.purposes_list:
        return False
    # A species that grows BOTH indoors and outdoors fits either choice.
    if "setting" in filters and species.setting not in (filters["setting"], "BOTH"):
        return False
    if "max_price" in filters and species.price > filters["max_price"]:
        return False
    return True


def apply_filters(results, filters, sort="score"):
    """Filter the already-scored list, then sort it (default: best score first)."""
    kept = [result for result in results if _passes(result.species, filters)]
    kept.sort(key=SORTS.get(sort, SORTS["score"]))
    return kept


def relax_suggestions(results, filters):
    """When filters leave nothing: for each active filter, how many species it alone is hiding.

    Returns [{"key", "label", "count"}, ...] with the most helpful first; filters that would
    not bring back anything are left out.
    """
    suggestions = []
    for key in filters:
        remaining = {k: v for k, v in filters.items() if k != key}
        count = sum(1 for result in results if _passes(result.species, remaining))
        if count:
            suggestions.append({"key": key, "label": FILTER_LABELS[key], "count": count})
    return sorted(suggestions, key=lambda item: -item["count"])
