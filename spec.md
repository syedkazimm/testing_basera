# Basera — Complete Project Specification

**Audience:** Claude Code (an AI coding agent).
**Purpose:** One self-contained brief that describes the whole product so that the full application can be built from it without further questions.
**Team:** Basera — Software Engineering, Fall 2026, Section 102112.

---

## 0. How to use this document (instructions for Claude Code)

1. Build the **entire** application described here (all features in Section 7), in **two phases**: first finish every **Sprint 1** story completely (Section 12), and only then start the **Sprint 2** stories. Do not begin a Sprint 2 story until all Sprint 1 stories work end to end.
2. Do not invent features, pages, models or packages that are not described. If something is unspecified, choose the simplest option consistent with this document and record the choice in `docs/DECISIONS.md`.
3. Work **story by story** in the order given in Section 12. Commit directly to `main` with **one commit per user story**, whose message starts with the story ID, for example `US-06: create a grow profile`. Do not use feature branches, pull requests or CI.
4. Put the story ID in a comment or docstring on every view. This lets every view be traced back to its backlog card.
5. **Do not write automated tests.** Verify each story by running it: after each story, run `python manage.py check` and try the feature (for example with the Django test client or by running the server) before moving on.
6. The code must be simple, readable and commented, so that anyone can read and maintain it. Prefer Django built-ins (class-based views, ModelForms, `auth`, `admin`, `messages`, `paginator`) over custom code. No JavaScript frameworks; interactivity comes from **HTMX** (Section 8.1), so pages update in place instead of reloading on every click.
7. Finish with a `README.md` that lets a stranger run the app locally in under five minutes and explains how it is deployed (Section 11).

---

## 1. Product overview

**Basera** is a web application that helps people in Pakistan choose and buy **native plants** that suit their own growing conditions.

**Problem.** Home growers, schools and housing societies often buy plants that are not suited to their region or that are invasive, and they have no easy way to know which native species will thrive in their sunlight, soil and water conditions. Local nurseries also lack a simple way to reach these buyers.

**Solution.** A customer describes their growing space once (a *grow profile*). Basera then recommends a ranked shortlist of native species that suit it, explains why each fits, hides invasive species, and lets the customer order the plants (Cash on Delivery). Sellers (nurseries) list their species and fulfil orders. An admin keeps reference data and listings clean.

**Two linked halves of the product:**

- **Research and matching:** grow profile → ranked, explained native-species shortlist.
- **E-commerce:** browse catalogue → cart → delivery details → order → fulfilment.

---

## 2. Actors and roles

| Actor | Logged in? | What they can do |
|---|---|---|
| **Guest** | No | Sign up, log in, browse the catalogue, view species details. |
| **Customer** | Yes (role CUSTOMER) | Everything a guest can, plus manage profile and password, manage grow profiles, run matching, use cart, place/view/cancel orders. |
| **Seller** | Yes (role SELLER) | Manage profile and password; create/edit/remove own listings; manage stock; see and update orders that contain their listings. Sellers cannot place orders or use grow profiles. |
| **Admin** | Yes (Django staff/superuser) | Manage regions, moderate listings (deactivate, remove, flag invasive), manage user accounts. Done through the customised Django admin site. |

There is no "Registered User" actor. "Guest" simply means "not logged in". The four actors never inherit from or point at each other.

---

## 3. Technology stack and constraints

| Area | Choice |
|---|---|
| Language | Python 3.12 |
| Framework | Django 5.x, a single monolith, one Django app per feature area |
| Front end | Django templates + Bootstrap 5 (CDN) + a little plain CSS + **HTMX** (CDN, pinned version) for in-page updates. No SPA, no npm build. |
| Database | **PostgreSQL in production** (via the `DATABASE_URL` environment variable, parsed with `dj-database-url`). **SQLite locally** when `DATABASE_URL` is unset, so setup is one command. |
| Images | Pillow + Django `ImageField`, stored under `MEDIA_ROOT` |
| Static files | WhiteNoise |
| App server | gunicorn |
| Email | Django console backend locally (`EMAIL_BACKEND` env var can switch to SMTP) |
| Source control | Git (single branch `main`, one commit per user story) |
| Project management | Trello (outside the repo) |

**Hard constraints (from the course brief):**

- No no-code or low-code tools. AI-generated code is allowed.
- A relational database with the team's **own backend**. Managed backends such as Firebase are not allowed.
- **The backend must be deployed online**; running only on a laptop is not enough.
- Payments are **Cash on Delivery only**. No real payment integration.
- Currency is Pakistani Rupees, displayed as `Rs 1,250`.

---

## 4. Repository layout

```
basera/
├── manage.py
├── requirements.txt            # pinned versions
├── build.sh                    # deployment build script (Section 11)
├── Procfile / render.yaml      # deployment process definition
├── .env.example                # documented environment variables
├── README.md
├── docs/
│   ├── DECISIONS.md            # any choices made where this spec was silent
│   ├── architecture.png        # (provided separately by the team)
│   └── ...
├── basera/                     # project package
│   ├── settings.py             # reads env vars; DEBUG, SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL
│   ├── urls.py                 # routes to the five apps
│   └── wsgi.py
├── accounts/                   # users, signup, login, password, profile
├── growprofiles/               # Region + GrowProfile
├── catalog/                    # Species (listings), browse, seller dashboard
├── matching/                   # scoring service, results page
├── orders/                     # cart, checkout, orders, fulfilment
├── templates/                  # base.html + one folder per app
├── static/                     # css, img/placeholder.png, img/species/*.jpg
└── media/                      # uploaded images (git-ignored)
```

Each app contains: `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`, and `templates/<app>/`.

The `matching` app has **no models**. It holds `services.py` (pure scoring functions kept separate from the view) and a view that calls it.

---

## 5. Data model

Eight entities. Use Django ORM models. All tables get an auto `id`. `created_at` is `DateTimeField(auto_now_add=True)`.

### 5.1 `accounts.User` (custom user model, set `AUTH_USER_MODEL`)

- Subclass `AbstractUser`; **login with email** (`USERNAME_FIELD = "email"`, `username` removed or unused), email unique and stored lower-case.
- `first_name`, `last_name` (from AbstractUser) — shown together as "full name".
- `role`: choices `CUSTOMER`, `SELLER` (default `CUSTOMER`). Admins are users with `is_staff=True`; their `role` is irrelevant.
- `phone`: CharField(20, blank) — Pakistani format, validated by regex `^(\+92|0)3\d{9}$` or empty.
- `default_address` (TextField, blank), `default_city` (CharField(60), blank) — used to prefill checkout.
- Create the custom manager (`create_user`, `create_superuser`) with email as identifier.

### 5.2 `growprofiles.Region`

- `name` CharField(80, unique), `description` TextField(blank).
- Deleting a region that is referenced must be blocked (`on_delete=PROTECT` on all references).

### 5.3 `growprofiles.GrowProfile`

- `customer` FK → User (CASCADE), `name` CharField(80) (for example "Balcony", "Backyard")
- `region` FK → Region (PROTECT)
- `space_type`: `INDOOR` / `OUTDOOR`
- `sunlight`: `FULL_SUN` / `PARTIAL_SHADE` / `SHADE`
- `soil`: `SANDY` / `LOAM` / `CLAY` / `ROCKY`
- `water`: `LOW` / `MEDIUM` / `HIGH` (water the customer can provide)
- `purpose`: `SHADE_COOLING` / `FOOD` / `POLLINATOR` / `EROSION_CONTROL` / `ORNAMENTAL` / `MEDICINAL`
- `created_at`, `updated_at`

### 5.4 `catalog.Species` (a seller's plant listing)

- `seller` FK → User (CASCADE)
- `common_name` CharField(100), `scientific_name` CharField(150), `description` TextField
- `image` ImageField(upload_to="species/", blank, null) — JPG/PNG, max 2 MB (validated in the form); show `static/img/placeholder.png` when empty
- `price` Decimal(10,2) > 0, `stock` PositiveIntegerField (≥ 0)
- Suitability attributes, using the same choice codes as the grow profile:
  - `sunlight` (FULL_SUN / PARTIAL_SHADE / SHADE) — the light the species prefers
  - `water` (LOW / MEDIUM / HIGH) — the water it needs
  - `soil` (SANDY / LOAM / CLAY / ROCKY) — preferred soil (LOAM means adaptable)
  - `setting`: `INDOOR` / `OUTDOOR` / `BOTH`
  - `plant_type`: `TREE` / `SHRUB` / `HERB` / `CLIMBER` / `GRASS`
  - `purposes`: comma-separated purpose codes (same codes as `GrowProfile.purpose`); expose a `purposes_list` property and use a `MultipleChoiceField` in the form.
  - `ecological_benefit` TextField — plain-language benefit (for example "Flowers feed bees and butterflies.").
- `regions` ManyToMany → Region through `SpeciesRegion` (`species`, `region`, unique together, both CASCADE for species / PROTECT for region).
- `is_invasive` Boolean (default False) — **only an admin can set this** (not on the seller form).
- `status`: `ACTIVE` / `INACTIVE` (seller toggles availability)
- `is_deleted` Boolean (default False) — soft delete used by "remove listing".
- A manager method `Species.objects.visible()` returns `status=ACTIVE, is_deleted=False`. All public pages and matching use it.

### 5.5 `orders.CartItem`

- `customer` FK → User, `species` FK → Species, `quantity` PositiveIntegerField ≥ 1
- Unique together (`customer`, `species`). Quantity may never exceed the species' stock.

### 5.6 `orders.Order`

- `customer` FK → User (PROTECT)
- `grow_profile` FK → GrowProfile (`SET_NULL`, null, blank) — the profile that led to this purchase, if any
- Delivery snapshot: `delivery_name`, `delivery_address` (TextField), `delivery_city`, `delivery_phone`
- `payment_method`: only `COD`
- `status`: `PENDING` → `CONFIRMED` → `SHIPPED` → `DELIVERED`, or `CANCELLED`
- `total` Decimal(12,2), `created_at`
- Display order number as `BSR-000123` (derive from `id`).

### 5.7 `orders.OrderItem`

- `order` FK → Order (CASCADE), `species` FK → Species (PROTECT)
- **Snapshots:** `species_name` CharField, `unit_price` Decimal(10,2), `quantity` PositiveIntegerField
- `line_total` property = `unit_price * quantity`.

### 5.8 Relationships summary (for the ERD)

User 1—N GrowProfile; User 1—N Species (as seller); User 1—N CartItem; User 1—N Order; Region N—M Species (via SpeciesRegion); Region 1—N GrowProfile; Species 1—N CartItem; Species 1—N OrderItem; Order 1—N OrderItem; GrowProfile 0..1—N Order.

---

## 6. Business rules

### 6.1 Matching algorithm (`matching/services.py`)

Input: a `GrowProfile`. Output: a list of result objects (`species`, `score`, `reasons`, `in_stock`).

**Step 1 — hard filters** (a species failing any of these is never returned):

1. `Species.objects.visible()` (active, not deleted)
2. The species is native to the profile's region (a `SpeciesRegion` row exists)
3. `is_invasive = False`

Species that pass but have `stock = 0` are **kept and marked "Out of stock"** (no add-to-cart button).

**Step 2 — weighted score (0–100):**

| Criterion | Weight | Rule |
|---|---|---|
| Sunlight | 30 | Ordinal FULL_SUN=2, PARTIAL_SHADE=1, SHADE=0. Score = `1 − |difference| / 2` → exact 1.0, one step 0.5, opposite 0. |
| Soil | 25 | Exact match 1.0; species soil is LOAM (adaptable) but profile differs 0.5; otherwise 0. |
| Water | 20 | Ordinal LOW=0, MEDIUM=1, HIGH=2, same formula as sunlight. |
| Indoor/outdoor | 15 | 1.0 if species setting equals profile space type or species is BOTH; else 0. |
| Purpose | 10 | 1.0 if the profile purpose is in the species' purposes; else 0. |

`score = round(30*s_sun + 25*s_soil + 20*s_water + 15*s_set + 10*s_purpose)`.
Sort by `score` descending, ties broken by `common_name`. Scores under 40 get a "Low fit" badge.

**Step 3 — reasons (generated from the same numbers as the score, so they can never contradict it):** for each criterion produce one plain-language line with a state of `match`, `partial` or `no match`, for example:

- ✔ "Prefers full sun — your space gets full sun."
- ◐ "Prefers loam soil — adaptable, but your soil is sandy."
- ✘ "Needs high water — you can only provide low water."

Also show the species' `ecological_benefit` on each result card.

**Empty result:** show "No native species match this profile" and suggest relaxing one criterion (list which of sunlight, soil, water, indoor/outdoor, purpose would add the most species — a simple count is enough; a static message is acceptable if this is too heavy).

**Filters and sorting on the results page (US-11):** GET parameters `purpose`, `setting`, `max_price`, `sort` (`score` default, `price_asc`, `price_desc`). Filter the already-scored list; show the active filters as removable chips; a "Clear filters" link restores the full list.

**Performance:** scoring is done in Python over at most a few hundred species with a single query using `prefetch_related("regions")`/`filter(regions=...)`. Target: under 2 seconds for 500 species.

### 6.2 Cart and checkout

- Add to cart: customer role only; guests are redirected to login and returned to the species after logging in. Adding an existing item increases quantity up to `stock`. Invasive, inactive, deleted or out-of-stock species cannot be added.
- Cart page lists name, unit price, quantity, line total and grand total; quantity change and remove update totals immediately (a normal form post is acceptable). An empty cart links to the catalogue.
- Delivery form: `name`, `address`, `city`, `phone`, prefilled from the user profile; phone validated with the Pakistani regex. Payment shows "Cash on Delivery". Next step is an order summary page.
- **Placing an order (US-22) runs inside one `transaction.atomic()` block:**
  1. Lock the species rows with `select_for_update()`.
  2. If any cart quantity exceeds current stock → roll back, create nothing, and show which item to fix.
  3. Create the `Order` (status PENDING) and `OrderItem`s with **price and name copied** in.
  4. Decrease each species' stock.
  5. Delete the cart items.
  6. After commit: print a confirmation email to the console (`send_mail`) and redirect to the confirmation page with the order number and summary.
- Cancel (US-24): only while `PENDING`. Within one atomic block, set status CANCELLED and add the quantities back to stock.

### 6.3 Seller fulfilment

- A seller sees only orders that contain at least one of **their** species (filter via `items__species__seller`).
- Status moves strictly `PENDING → CONFIRMED → SHIPPED → DELIVERED`; no skipping and no going back; `CANCELLED` orders cannot be advanced.
- Because `status` lives on the order, if an order contains items from several sellers, any involved seller may advance it. Record this simplification in `docs/DECISIONS.md`.

### 6.4 Soft delete and history

- "Removing" a listing sets `is_deleted=True`; past orders keep the snapshot name and price and still link to the species row.
- Deleting a grow profile sets `Order.grow_profile` to NULL; orders survive.
- A region referenced by any profile or species cannot be deleted (admin shows a friendly error).

### 6.5 Permissions and error codes

| Situation | Response |
|---|---|
| Not logged in on a protected page | Redirect to login with `?next=` and return afterwards |
| Customer opens another customer's grow profile or order | **404** |
| Seller edits or deletes another seller's listing | **403** page |
| Customer opens a seller page, or a seller opens a customer page | **403** |
| Inactive or deleted species opened by URL | **404** |

Use small mixins (`CustomerRequiredMixin`, `SellerRequiredMixin`) and always filter querysets by owner (`get_queryset` / `get_object_or_404(..., customer=request.user)`).

---

## 7. Features and acceptance criteria

All 27 backlog cards. Five epics (colour labels on the Trello board): **E1 Account and Profile**, **E2 Research and Matching**, **E3 Plant Directory**, **E4 Browse, Cart and Checkout**, plus **Enabler** (technical cards). Priority: Must / Should. Every item below must be implemented.

### Enablers

**EN-01 Project scaffold** (Must). A Django project with the five apps, a `base.html` with navbar, flash messages and footer, settings driven by environment variables, and `requirements.txt`.
- Cloning the repo and following the README starts the app with `python manage.py runserver`.

**EN-02 Seed data** (Must). A management command `python manage.py seed_demo` that is **idempotent** and creates: the regions and species of Section 9, one admin, one seller and one customer demo account (credentials printed by the command and listed in the README — demo/test values only), plus one sample grow profile for the demo customer.
- Creates at least 4 regions and at least 30 species; every species has regions, light, water, soil, setting, purposes and ecological benefit.
- At least 3 species are flagged `is_invasive`.

### E1 — Account and Profile

**US-01 Sign up** (Must). Form: first name, last name, email, phone (optional), role (Customer or Seller), password and confirmation.
- Unique email + valid password (8+ characters, not entirely numeric, not a common password) → account created with a hashed password, redirect to login with a success message.
- Email already used → error and no account.
- Seller role gives seller permissions and cannot reach admin pages. Admin accounts cannot be created from this form.

**US-02 Log in and log out** (Must).
- Valid credentials → redirected to the role's landing page (customer: "My Grow Profiles"; seller: "My Listings"; admin: admin site).
- Invalid credentials → one generic error that does not reveal which field was wrong.
- Protected page when logged out → login, then back to that page.
- Log out (POST) ends the session, lands on home; protected pages redirect to login.

**US-03 Forgot password** (Should). Use Django's built-in password-reset views and templates.
- Registered email → single-use, time-limited link (console email).
- Unknown email → same confirmation message (no enumeration).
- Valid link + a new password meeting the rules → can log in; the link no longer works.

**US-04 Change password** (Must). Django `PasswordChangeView`.
- Correct current + valid new → updated and the user stays logged in (`update_session_auth_hash`).
- Wrong current password → rejected with an error. Same password rules as signup.

**US-05 View and edit profile** (Should). Page "My Profile" with first name, last name, phone, default address, default city.
- Shows current details; valid changes save and show immediately.
- Email and role are shown read-only.

### E2 — Research and Matching

**US-06 Create a grow profile** (Must). ModelForm with name, region, space type, sunlight, soil, water, purpose.
- Valid → stored under the customer's account and listed.
- Missing required field → field-level errors, nothing saved.
- Region options come from the Region table; the others use the fixed choices of Section 5.3.

**US-07 Manage my grow profiles** (Must). List (name, region, purpose, buttons: Find plants, Edit, Delete), edit form, delete confirmation page.
- With profiles → list; with none → prompt to create one.
- Edit saves; previously placed orders are unaffected.
- Confirmed delete removes the profile; orders keep existing with the link cleared.
- Another user's profile → 404.

**US-08 Ranked shortlist** (Must). "Find plants" on a profile opens `/match/<profile_id>/`.
- Only species native to the profile's region and not invasive are returned.
- Sorted by score 0–100 % descending; each card shows photo, names, price, score badge, stock state and a link to the details.
- Out-of-stock or inactive species are excluded or clearly marked (this spec: inactive excluded, out-of-stock marked).
- Fast: 500 species in under 2 seconds.

**US-09 Reasons for each match** (Must). Each card has the criterion-by-criterion reasons and the ecological benefit exactly as in Section 6.1; they come from the same calculation as the score.

**US-10 Invasive and unsuitable species** (Must).
- Invasive species never appear in matches.
- In the catalogue and on detail pages, invasive species show a visible warning banner and **no add-to-cart button**.
- No matches → helpful message with a suggestion to relax a criterion.

**US-11 Filter and sort matches** (Should). As in Section 6.1.

**US-12 View species details** (Must). `/species/<id>/` shows image, common and scientific names, description, type, sunlight/water/soil/setting, purposes, ecological benefit, native regions, price, stock state, the seller's name, and an "Add to cart" button (hidden for invasive/out-of-stock). Inactive or removed species → 404.

### E3 — Plant Directory (seller side)

**US-13 Create a species listing** (Must). Seller form with all species fields (not `is_invasive`, `status` defaults to ACTIVE).
- Valid → created under the seller and visible in the catalogue.
- Regions (at least one), sunlight, water, soil, setting, purposes and ecological benefit are required.
- Price > 0, stock ≥ 0.
- JPG/PNG up to 2 MB accepted; other files rejected with an error; placeholder shown when no image.

**US-14 Edit or remove a listing** (Must).
- Owner edits → changes are visible at once in the catalogue and matching.
- Confirmed removal → soft delete; past orders still show the name and price paid.
- Someone else's listing → 403.

**US-15 Manage stock and availability** (Should).
- Stock 0 → "Out of stock" badge, cannot be added to a cart.
- Seller can mark a listing INACTIVE/ACTIVE.
- Stock decreases automatically on order placement (Section 6.2) and increases on cancellation.

**US-16 My listings dashboard** (Should). Table of **only the seller's own** listings: thumbnail, name, price, stock, status, edit/remove links. Search by name; filter by Active/Inactive; paginate by 10.

**US-17 Manage regions** (Should; admin). Through Django admin: add and edit regions (new regions appear immediately in profile and listing forms); a region used by profiles or species cannot be deleted (catch `ProtectedError` and show a message).

### E4 — Browse, Cart and Checkout

**US-18 Browse and search the catalogue** (Must). `/catalogue/` lists `visible()` species 12 per page with a search box (common or scientific name, case-insensitive). Inactive or deleted species never appear. Invasive species appear with a warning badge.

**US-19 Add to cart** (Must). From a match card, the catalogue or the detail page: in stock → cart item quantity 1; same species again → quantity + 1 (never above stock); guests are redirected to login first.

**US-20 Review and edit cart** (Must). Table with name, unit price, quantity, line total, grand total; change quantity (1 – stock) and remove; empty cart shows a link to the catalogue.

**US-21 Enter delivery details** (Must). Name, address, city, phone (prefilled from the profile), payment method displayed as Cash on Delivery. Invalid or missing fields show errors and block continuing; valid fields lead to the order summary.

**US-22 Confirm and place order** (Must). As in Section 6.2: atomic; stock re-check; snapshot prices; cart emptied; confirmation page with the order number and summary; console email. The grow profile is attached when the customer arrived through matching (store the profile id in the session when adding from results).

**US-23 View my orders** (Must). "My Orders" newest first with number, date, status, total; the order page shows items, delivery details and the grow profile used (if any). Another user's order → 404.

**US-24 Cancel a pending order** (Should). Button only on PENDING orders; confirm page; status → CANCELLED and stock returned in one transaction.

**US-25 Fulfil orders** (Should). Seller page "Orders" shows orders containing their listings (only their lines are highlighted); a button advances the status exactly one step (Section 6.3); customers see the new status on their order page.

---

## 8. Screens and URLs

| URL | Page | Who |
|---|---|---|
| `/` | Home: pitch, "Find plants for my space" and "Browse catalogue" buttons | All |
| `/accounts/signup/` | Sign up | Guest |
| `/accounts/login/`, `/accounts/logout/` | Login / logout | All |
| `/accounts/password-reset/…` | Forgot password flow (4 built-in pages) | Guest |
| `/accounts/password-change/` | Change password | Logged in |
| `/accounts/profile/` | View and edit profile | Logged in |
| `/profiles/` | My grow profiles (list) | Customer |
| `/profiles/new/`, `/profiles/<id>/edit/`, `/profiles/<id>/delete/` | Create, edit, delete a profile | Customer |
| `/match/<profile_id>/` | Ranked shortlist with filters | Customer |
| `/catalogue/` | Catalogue with search and pagination | All |
| `/species/<id>/` | Species details | All |
| `/seller/listings/` | My listings dashboard | Seller |
| `/seller/listings/new/`, `/seller/listings/<id>/edit/`, `/seller/listings/<id>/delete/` | Create, edit, remove | Seller |
| `/seller/orders/`, `/seller/orders/<id>/advance/` | Fulfilment (POST to advance) | Seller |
| `/cart/`, `/cart/add/<species_id>/`, `/cart/update/<item_id>/`, `/cart/remove/<item_id>/` | Cart | Customer |
| `/checkout/`, `/checkout/summary/`, `/checkout/place/` | Delivery details, summary, confirm | Customer |
| `/orders/`, `/orders/<id>/`, `/orders/<id>/cancel/` | My orders | Customer |
| `/admin/` | Customised Django admin | Admin |
| 403, 404, 500 | Friendly error pages | All |

**Navbar by role:** Guest — Home, Catalogue, Log in, Sign up. Customer — Find plants, My profiles, Catalogue, Cart (item count), My orders, Profile, Log out. Seller — My listings, Orders, Profile, Log out. Show the logged-in user's name.

**UI guidance:** a clean green-and-white Bootstrap look; cards for species; badges for score, "Out of stock", "Invasive — not sold", "Low fit"; every form shows field errors inline; success/error feedback uses Django messages. The pages must work on a phone-width screen (360 px).

### 8.1 Interactivity with HTMX (required)

Basera must not reload the whole page for every click. Use **HTMX** (a single `<script>` tag in `base.html`, loaded from a CDN with a pinned 2.x version) with Django templates. Do not add React, Vue, jQuery or any build step; at most a few lines of plain JavaScript if HTMX cannot do something.

**Pattern (use it everywhere below):**

1. Every HTMX interaction targets a URL that **also works as a normal page** (progressive enhancement). The view checks `request.headers.get("HX-Request")`: if true it renders only a small partial template (named `_something.html`, for example `catalog/_species_results.html`); if false it renders the full page that includes the same partial.
2. Send the CSRF token on every HTMX request: put `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'` on the `<body>` tag.
3. Form validation errors: re-render the form partial with status 200 so HTMX swaps in the errors inline. Success on a create/edit/delete form redirects normally (use the `HX-Redirect` response header when the request came from HTMX).
4. Use `hx-push-url="true"` on filters and search so the address bar stays shareable and the Back button works.
5. Show a small loading spinner with Bootstrap's spinner and the `htmx-indicator` class on requests that may take a moment (matching results).
6. Keep the navbar cart count in sync: after add/update/remove, respond with the updated cart badge as an out-of-band swap (`hx-swap-oob="true"`).
7. Destructive actions (delete, cancel) keep a confirmation step (`hx-confirm` or a confirmation page).

**Where to use it:**

| Screen | Behaviour |
|---|---|
| Catalogue (US-18) | Search box filters results as you type (`hx-trigger="keyup changed delay:300ms"`); pagination swaps only the results block. |
| Matching results (US-08, US-11) | Filter and sort controls update only the shortlist; "Clear filters" resets in place; spinner while scoring. |
| Add to cart (US-19) | "Add to cart" button on cards and detail pages adds without leaving the page; the button changes to "Added ✔" and the navbar badge updates. |
| Cart (US-20) | Quantity change and remove update the row and totals in place. |
| Seller dashboard (US-16) | Search and Active/Inactive filter update the table in place. |
| Seller orders (US-25) | The "advance status" button updates that order's row and badge in place. |
| Forms (signup, grow profile, listing, delivery) | Inline validation errors without a page reload. |
| Grow profiles list (US-07) | Delete confirmation then the row disappears without a reload. |

Full-page loads are fine for: login/logout, the checkout steps, order confirmation, and anything that changes the whole screen.

---

## 9. Seed data

> The botanical attributes below are a reasonable **illustrative starting set**. The team should check them against a reliable source (for example a forestry department or Flora of Pakistan) before presenting. Prices are invented (Rs 150 – 2,500) and stock is 5 – 50; images may be placeholders.

**Regions (suggested, at least 4):** Punjab Plains · Potohar Plateau · Sindh Indus Plains · Northern Highlands · Balochistan Uplands.
Region codes below: **PP** Punjab Plains, **PO** Potohar, **SI** Sindh, **NH** Northern Highlands, **BU** Balochistan.

Columns: Sun (F full, P partial, S shade) · Water (L/M/H) · Soil (Sa sandy, Lo loam, Cl clay, Ro rocky) · Setting (O outdoor, B both) · Purposes.

| Common name | Scientific name | Regions | Sun | Water | Soil | Set. | Type | Purposes | Invasive |
|---|---|---|---|---|---|---|---|---|---|
| Neem | Azadirachta indica | PP, PO, SI | F | L | Lo | O | Tree | SHADE_COOLING, MEDICINAL | No |
| Shisham | Dalbergia sissoo | PP, PO, SI | F | M | Lo | O | Tree | SHADE_COOLING, EROSION_CONTROL | No |
| Kikar (Babul) | Vachellia nilotica | PP, SI, BU | F | L | Cl | O | Tree | EROSION_CONTROL, POLLINATOR | No |
| Ber | Ziziphus mauritiana | PP, PO, SI, BU | F | L | Sa | O | Tree | FOOD, POLLINATOR | No |
| Jand | Prosopis cineraria | SI, BU, PP | F | L | Sa | O | Tree | SHADE_COOLING, EROSION_CONTROL | No |
| Peepal | Ficus religiosa | PP, PO, SI | P | M | Lo | O | Tree | SHADE_COOLING, ORNAMENTAL | No |
| Amaltas (Golden Shower) | Cassia fistula | PP, PO, SI | F | M | Lo | O | Tree | ORNAMENTAL, POLLINATOR | No |
| Arjun | Terminalia arjuna | PP, PO, SI | F | H | Cl | O | Tree | SHADE_COOLING, MEDICINAL | No |
| Jamun | Syzygium cumini | PP, PO, SI | F | M | Lo | O | Tree | FOOD, SHADE_COOLING | No |
| Phulai | Senegalia modesta | PO, NH, BU | F | L | Ro | O | Tree | EROSION_CONTROL, POLLINATOR | No |
| Kachnar | Bauhinia variegata | PO, PP, NH | F | M | Lo | O | Tree | ORNAMENTAL, FOOD | No |
| Deodar | Cedrus deodara | NH | P | M | Lo | O | Tree | SHADE_COOLING, EROSION_CONTROL | No |
| Chir Pine | Pinus roxburghii | NH, PO | F | L | Ro | O | Tree | EROSION_CONTROL, SHADE_COOLING | No |
| Blue Pine | Pinus wallichiana | NH | P | M | Lo | O | Tree | EROSION_CONTROL | No |
| Himalayan Walnut | Juglans regia | NH | P | M | Lo | O | Tree | FOOD, SHADE_COOLING | No |
| Sea Buckthorn | Hippophae rhamnoides | NH, BU | F | L | Sa | O | Shrub | EROSION_CONTROL, FOOD, MEDICINAL | No |
| Wild Rose | Rosa brunonii | NH, PO | P | M | Lo | O | Shrub | POLLINATOR, ORNAMENTAL | No |
| Sanatha (Hopbush) | Dodonaea viscosa | PO, NH, BU, PP | F | L | Ro | B | Shrub | EROSION_CONTROL, POLLINATOR | No |
| Ak (Calotropis) | Calotropis procera | SI, BU, PP | F | L | Sa | O | Shrub | POLLINATOR, MEDICINAL | No |
| Karir | Capparis decidua | SI, BU, PP | F | L | Sa | O | Shrub | FOOD, EROSION_CONTROL | No |
| Pilu (Salvadora) | Salvadora oleoides | SI, BU | F | L | Sa | O | Tree | SHADE_COOLING, FOOD | No |
| Farash (Tamarisk) | Tamarix aphylla | SI, BU, PP | F | L | Sa | O | Tree | EROSION_CONTROL, SHADE_COOLING | No |
| Bakain (Adhatoda) | Justicia adhatoda | PO, PP, NH | P | M | Lo | B | Shrub | MEDICINAL, POLLINATOR | No |
| Ashwagandha | Withania somnifera | PP, SI, BU | F | L | Sa | B | Herb | MEDICINAL | No |
| Tulsi (Holy Basil) | Ocimum tenuiflorum | PP, PO, SI | F | M | Lo | B | Herb | MEDICINAL, POLLINATOR | No |
| Mint (Pudina) | Mentha arvensis | PP, PO, NH | P | H | Lo | B | Herb | FOOD, MEDICINAL | No |
| Aloe (Kunwar Gandal) | Aloe vera ‡ | SI, BU | F | L | Sa | B | Herb | MEDICINAL, ORNAMENTAL | No |
| Sarkanda | Saccharum munja | PP, PO, SI | F | M | Sa | O | Grass | EROSION_CONTROL | No |
| Vetiver (Khus) | Chrysopogon zizanioides | PP, SI | F | M | Cl | O | Grass | EROSION_CONTROL | No |
| Himalayan Jasmine | Jasminum humile | PO, NH | P | M | Lo | B | Shrub | ORNAMENTAL, POLLINATOR | No |
| Marigold (Genda) | Tagetes erecta ‡ | PP, PO, SI | F | M | Lo | B | Herb | ORNAMENTAL, POLLINATOR | No |
| Mesquite | Prosopis juliflora | SI, BU, PP | F | L | Sa | O | Tree | SHADE_COOLING | **Yes** |
| Lantana | Lantana camara | PP, PO, SI | F | L | Lo | B | Shrub | ORNAMENTAL, POLLINATOR | **Yes** |
| Paper Mulberry | Broussonetia papyrifera | PO, PP | F | M | Lo | O | Tree | SHADE_COOLING | **Yes** |
| Conocarpus | Conocarpus erectus | SI, PP | F | M | Lo | O | Tree | ORNAMENTAL, SHADE_COOLING | **Yes** |

‡ Aloe vera and Tagetes erecta are widely grown and naturalised rather than strictly native — either replace them with true natives or keep them with a note in `docs/DECISIONS.md`; the matching logic does not depend on it.

Write a one-sentence `ecological_benefit` and a two-sentence description for each (for example Neem: "Provides dense shade and its flowers support bees."). Assign all seeded species to the one demo seller account, which is enough for the demo.

**Demo accounts** (test values only, documented in the README): `admin@basera.test`, `seller@basera.test`, `customer@basera.test`; the seed command prints their passwords and creates them only if absent.

---

## 10. Non-functional requirements (testable)

| Category | Requirement |
|---|---|
| Performance | Catalogue, profile and cart pages load in under 3 seconds for 95 % of requests on a standard laptop with seeded data. Matching returns in under 2 seconds against 500 species. |
| Scalability | The demo handles 20 concurrent users browsing and ordering without errors. |
| Security | Passwords stored only as salted hashes (Django default). Users view and change only their own profiles, carts and orders (403/404 otherwise). Every form carries a CSRF token. No raw SQL; ORM only. `SECRET_KEY` and database credentials come from environment variables, never from the repository. In production `DEBUG=False`. |
| Data integrity | Checkout is one atomic transaction: if any item is out of stock no order is created and stock never falls below zero. |
| Usability | A first-time customer can create a grow profile and see matches within 2 minutes without training. |
| Compatibility | Latest two versions of Chrome, Edge, Firefox and Safari; works at 360 px width. |
| Accessibility basics | Labels on all inputs, sufficient contrast, keyboard-reachable buttons, alt text on images. |
| Maintainability | One app per feature, readable code, no function longer than ~40 lines where avoidable. |

---

## 11. Deployment (required by the course)

Deploy the Django app and PostgreSQL database on a free host (Render is the default suggestion; PythonAnywhere is an acceptable alternative).

- `requirements.txt` includes `Django`, `gunicorn`, `whitenoise`, `dj-database-url`, `psycopg[binary]`, `Pillow`, `python-dotenv` (optional).
- `settings.py`: `DATABASES = {"default": dj_database_url.config(default="sqlite:///db.sqlite3")}`; `STATIC_ROOT`, WhiteNoise middleware and `CompressedManifestStaticFilesStorage`; `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SECRET_KEY`, `DEBUG` read from environment variables; `SECURE_PROXY_SSL_HEADER` set for HTTPS behind the host's proxy.
- `build.sh`: `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python manage.py seed_demo`.
- Start command: `gunicorn basera.wsgi`.
- **Uploaded images:** free hosts have an ephemeral disk, so images uploaded in production may vanish on redeploy. Species images that ship with the seed data live in `static/img/species/` so the demo always looks complete. Note this limitation in the README.
- Document in the README the live URL, the environment variables (also in `.env.example`) and the steps to redeploy.

---

## 12. Build order: Sprint 1 first, then Sprint 2

The backlog is split into two sprints. Build **Sprint 1 completely, run through its demo script, and commit it** before touching Sprint 2. Within a sprint, follow the numbered order, because later items depend on earlier ones.

### Sprint 1 — "A customer finds native plants for their space" (10 stories, 39 points)

Demo script: sign up → log in → create a grow profile → click "Find plants" → see a ranked list with a score and reasons for each species (invasive species never shown) → open a species page → search the catalogue.

1. **EN-01** Project scaffold: settings, base template (Bootstrap + HTMX loaded), README skeleton.
2. **US-01** Sign up and **US-02** Log in/log out (custom user model first, before any migration is shared).
3. **EN-02** Seed data: `Region` and `Species` models, seed command, admin registration (so data can be inspected). Sellers do not create species in Sprint 1; the demo seller owns the seeded species.
4. **US-18** Browse and search the catalogue (with the invasive warning from **US-10**) and **US-12** Species details.
5. **US-06** Create a grow profile (including the basic "my profiles" list that its acceptance criteria require).
6. **US-08** Ranked shortlist, **US-09** Reasons for each match, and the rest of **US-10** (no-match message and relax-a-criterion suggestion).
7. Sprint 1 wrap-up: HTMX behaviour for catalogue search and matching results (Section 8.1), error pages, deployment files, README with the demo script.

Stretch for Sprint 1 (only if everything above is done): **US-07** edit/delete grow profiles.

### Sprint 2 — "Sellers list plants, customers buy them" (everything else)

8. **US-03** Forgot password, **US-04** Change password, **US-05** View and edit profile.
9. **US-07** Manage my grow profiles (if not already done) and **US-11** Filter and sort matches.
10. **US-17** Manage regions (admin) and the seller listing stories **US-13, US-14, US-15, US-16**.
11. **US-19, US-20, US-21, US-22** Cart and checkout (create the `CartItem`, `Order` and `OrderItem` models here).
12. **US-23, US-24, US-25** My orders, cancellation, seller fulfilment.
13. Final polish: HTMX on cart, seller dashboard and order screens (Section 8.1), admin tidy-up, README final pass.

For each story, create only the models and screens that story needs (the full data model in Section 5 is the target, not something to build up front), except that the custom `User` model must exist before the first migration.

---

## 13. Definition of Done (applies to every story)

1. Acceptance criteria in Section 7 are met.
2. The story is committed to `main` as a single commit starting with its story ID.
3. Permissions and validation are in place (Section 6.5).
4. The page works at 360 px and shows clear error and success messages.
5. The feature has been tried by hand and `python manage.py check` passes.
6. No secrets in the repository.
7. The README or `docs/DECISIONS.md` is updated if behaviour or setup changed.

---

## 14. Out of scope

Online payments, delivery tracking, reviews and ratings, wishlists, plant-care reminders, chat, mobile app, multi-language, multi-seller split shipments, analytics dashboards, third-party sign-in, REST API. Do not build these.

---

## 15. Scope of this build

Produce the working application, its seed data, its deployment files and the README. Do not generate Scrum logs, wireframes, a Trello board, a test plan or automated tests; those are separate deliverables handled outside this build. Keep `docs/DECISIONS.md` up to date with every judgement call you make where this specification was silent.
