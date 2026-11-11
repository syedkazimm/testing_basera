# Decisions where the spec was silent

Each entry records a judgement call made while building Basera.

## EN-01
- **Repo root:** `manage.py` and the `basera/` project package live directly in the repository root (the folder that holds `SPEC.md`), rather than in a nested `basera/` folder.
- **Spec file name:** the spec is committed as `spec.md` (the name it was supplied with).
- **App templates:** each app keeps its templates in `<app>/templates/<app>/`; the project-level `templates/` folder holds only shared pages (`base.html`, navbar, home, error pages).
- **Python version:** developed on Python 3.12 in a local `.venv` (git-ignored). Dependencies are pinned in `requirements.txt`.
- **Static assets:** Bootstrap 5.3.3 from jsDelivr and HTMX 2.0.4 from unpkg, both pinned.
- **Home buttons:** the two home buttons are placeholders until the catalogue and grow profile pages exist; they are wired in later stories.

## US-01
- **Shared form helper:** `basera/forms.py` holds `BootstrapFormMixin` (adds Bootstrap CSS classes to widgets) and `templates/_form_fields.html` renders any form with inline errors. Every form in the project reuses them.
- **Phone validator:** `accounts/validators.py` holds the Pakistani phone regex so checkout can reuse it later.
- **Sign-up form:** first and last name are required on sign-up (the model allows blank so admin-created accounts need not have them). Role choices are only Customer and Seller; `is_staff` is not on the form.
- **Sign-up with HTMX:** the form is a partial; errors swap in place and success uses `HX-Redirect` to the login page.
- **Login link:** until US-02 adds the named `login` URL, templates link to `/accounts/login/` directly.

## US-02
- **Role landing pages:** customer goes to `/profiles/`, seller to `/seller/listings/`, admin to `/admin/`. The customer and seller pages are built in later stories, so those two paths show a 404 until their stories land (the seller page arrives in Sprint 2).
- **Login form:** the generic error text is "Incorrect email or password." for wrong password, unknown email and inactive accounts alike. Email is lower-cased before checking.
- **Logout:** a POST button in the navbar (Django 5's `LogoutView` rejects GET); it lands on home.
- **Logged-in visitors** who open the login or sign-up page are sent on (login → their landing page, sign-up → home).

## EN-02
- **Where things live:** `Region` and the shared choice lists (sunlight, soil, water, purpose, space type) are in `growprofiles/models.py`; `Species` and `SpeciesRegion` are in `catalog/models.py`. The seed command is `catalog/management/commands/seed_demo.py` and its data table is `catalog/seed_data.py`.
- **Sample grow profile deferred:** the `GrowProfile` model is built in US-06 (a story creates only the models it needs), so the seed command gains the demo customer's sample profile in that story.
- **Species count:** the spec's table has 35 rows; all 35 are seeded (4 flagged invasive).
- **Prices and stock:** derived deterministically from each species' position in the list (Rs 188 - 2,418; stock 5 - 50), so repeated runs give the same data.
- **Idempotent seeding:** a species is matched by seller + scientific name and only created if absent, so a seller's later edits are never overwritten. Regions are matched by name; accounts by email.
- **Demo password:** a single demo password (`Basera-demo-2026`) is used for all three demo accounts, printed only when an account is created. Setting the `DEMO_PASSWORD` environment variable overrides it, which production should do because `build.sh` runs the seed.
- **Demo admin:** `admin@basera.test` is a superuser; its `role` stays CUSTOMER (role is irrelevant for admins).
- **Naturalised plants:** Aloe vera and Marigold are kept, with a note in their ecological benefit that they are widely naturalised rather than strictly native (as the spec allows).
- **Species images:** seeded species have no uploaded image and show `static/img/placeholder.png` (a generated leaf graphic), which the spec allows ("images may be placeholders"). `static/img/species/` is left empty.
- **Admin:** species can be edited in the admin with regions as an inline; `is_invasive` is editable there (and nowhere else).

## US-18 (with the invasive warning from US-10)
- **HTMX timing:** the catalogue already splits its results into `catalog/_species_results.html`, and the view returns only that partial for HTMX requests. The `hx-*` attributes on the search box are added in the Sprint 1 wrap-up, as the build order says.
- **Ordering and search:** results are sorted by common name; search matches common or scientific name, case-insensitively, and keeps the search text when paging.
- **Catalogue cards** show the badge "Invasive — not sold" for invasive species, "Out of stock" at zero stock and "In stock" otherwise. Add-to-cart buttons arrive in Sprint 2 (US-19), so cards have only "View details" for now.

## US-12
- **Add to cart on the detail page:** the button is added with US-19 in Sprint 2. Until then the page shows stock state only (it already shows "Invasive — not sold" and "Out of stock" badges).
- **Price format:** prices show as whole rupees with thousands separators (`Rs 1,250`); the stored value keeps two decimals.

## US-06
- **Permissions:** `accounts/mixins.py` defines `CustomerRequiredMixin` and `SellerRequiredMixin`. Logged-out visitors are redirected to login (with `?next=`); the wrong role gets a 403. Admins (staff) are not treated as customers or sellers.
- **HTMX helpers:** `basera/htmx.py` has `is_htmx()` and `redirect_to()` (normal redirect, or `HX-Redirect` for HTMX). The sign-up view now uses them too.
- **Sample grow profile:** the seed command creates "Backyard" (Punjab Plains, outdoor, full sun, loam, medium water, shade and cooling) for the demo customer only if they have no profile yet.
- **List page:** shows name, region and purpose. The "Find plants", Edit and Delete buttons arrive with US-08 and US-07.
- **Navigation:** the "Find plants for my space" home button goes to My Profiles, where a profile is chosen or created.

## US-08
- **Rounding:** the score is rounded half up (62.5 → 63) rather than with Python's `round()` (banker's rounding), so it behaves the way people expect.
- **One calculation:** `matching/services.py` scores and builds the reason lines in the same loop (`score_species`), so the two can never disagree. US-09 only adds how the reasons are displayed.
- **Hard filters in one query:** `Species.objects.visible().filter(regions=profile.region, is_invasive=False)`; scoring happens in Python (about 20 ms for the 21 matches in the demo data).
- **Access:** another customer's profile gives a 404; sellers get a 403; guests go to login.
- **Add to cart** buttons and storing the profile in the session arrive with the cart (US-19, US-22).

## US-09
- **Reason display:** each match card lists five lines (sunlight, soil, water, indoor/outdoor, purpose) with a symbol and colour (✔ match, ◐ partial, ✘ no match). Screen readers also get the words "match", "partial" or "no match". The species' ecological benefit appears on every card.

## US-10
- **Invasive species** are excluded by the matching hard filter and show a warning banner and badge (no add-to-cart) in the catalogue and on detail pages (done in US-18 and US-12).
- **No-match suggestion:** the only hard filters are region, visibility and non-invasive, and the five criteria only change the score, so an empty shortlist means no native species are listed for that region. The message therefore suggests choosing a profile for a nearby region or browsing the catalogue. The "which criterion to relax" count applies to the US-11 filters and is added there.

## Sprint 1 wrap-up
- **HTMX on the catalogue:** the search box uses `hx-trigger="keyup changed delay:300ms"` with `hx-push-url`, and the pagination links swap only the `#results` block; with JavaScript off, the form and links still work as normal pages.
- **HTMX history restore:** when the Back button restores a page, HTMX sends `HX-Request` and `HX-History-Restore-Request` together; `is_htmx()` treats that as a full-page request so Back never shows a bare partial.
- **HTMX on match results:** the match page has no filter or sort controls until US-11, so the spinner and in-place updates are added with those controls in Sprint 2. The shortlist is already a partial (`matching/_results.html`).
- **Error pages:** `templates/403.html`, `404.html` (extend the base layout) and `500.html` (standalone, so it cannot fail). They show when `DEBUG=False`.
- **Deployment files:** `build.sh`, `Procfile` and `render.yaml` (web service plus free PostgreSQL). The blueprint generates `SECRET_KEY` and `DEMO_PASSWORD`. The live URL is not known until the user deploys, so the README leaves a placeholder.
- **Not done in Sprint 1:** the optional stretch story US-07 is built in Sprint 2 (step 9), as the build order lists it there too.

## US-03
- **Built-in views:** forgot-password uses Django's own reset views with subclassed forms and our templates (`accounts/password_reset_*.html`). Unknown emails get the same "check your email" page and no email is sent.
- **Link lifetime:** `PASSWORD_RESET_TIMEOUT` is one hour. A link stops working once the password changes because Django's token includes the password hash.
- **Email text:** plain-text email printed on the console; subject "Reset your Basera password".

## US-04
- **After a successful change** the user stays on the change-password page with a green "Your password has been updated." message (the profile page arrives in US-05). The page is linked from My Profile.

## US-05
- **Any logged-in user** (customer, seller or admin) can open `/accounts/profile/`; it always edits the current user, so there is no way to open another user's profile. First and last name are required, phone is optional and validated, and email and role are shown read-only (the form does not contain them, so a forged POST cannot change them).
- **Navbar:** a "Profile (full name)" link replaces the plain name label.

## US-07
- **Delete flow:** without JavaScript the Delete link opens a confirmation page (POST to delete). With HTMX the same link asks with `hx-confirm`, posts, and the server answers with an empty body so the row disappears in place.
- **Orders:** the `Order.grow_profile` link (set to NULL when a profile is deleted) is created with the Order model in Sprint 2, so the "orders keep existing" rule is enforced there by `on_delete=SET_NULL`.
- **Ownership:** edit and delete use the same owner-filtered queryset as the list, so another customer's profile is a 404 for both viewing and posting.

## US-11
- **Filters:** `purpose` (species lists it), `setting` (Indoor or Outdoor; a species that grows BOTH matches either), `max_price` (price at or below) and `sort` (`score`, `price_asc`, `price_desc`). Invalid values are ignored rather than shown as errors. Scoring runs once; filters and sorting only work on the scored list.
- **HTMX targets:** changing a control swaps only `#results` (so keyboard focus stays in the controls); clicking a chip or "Clear filters" swaps the whole `#shortlist` block (controls and results) so the controls reset too. The view tells them apart with the `HX-Target` header. A spinner shows while scoring.
- **No result with filters:** the page lists, for each active filter, how many plants removing just that filter would bring back (the "relax one criterion" suggestion), most helpful first. This is the version of the US-10 suggestion that matters, since the five criteria only change the score and never hide a species.
- **Price sort ties** fall back to best score, then name.

## US-17
- **Protected regions:** Django's admin delete page already lists the protected profiles/species and refuses the delete (the POST does nothing). As a safety net `RegionAdmin.delete_model` and `delete_queryset` also catch `ProtectedError` and show an error message instead of a 500 page.
- **Admin list:** the region list shows how many grow profiles and species use each region.
- Adding a region needs no other code: the profile and listing forms read the Region table on every request.

## US-13
- **Form fields:** all species fields except `seller`, `is_invasive` and `status`. Purposes and regions are checkbox groups (at least one of each is required). `status` is added to the form in US-15; new listings start ACTIVE through the model default.
- **Image checks:** the picture must be a real JPEG or PNG (checked with Pillow, not just the file name) and at most 2 MB. Without a picture the placeholder is shown.
- **Where a seller lands:** after saving, the seller goes back to `/seller/listings/` ("My Listings"). It is a plain table for now; US-16 adds thumbnails, search, filters and paging.
- **Seller URLs** live in `catalog/urls.py` beside the public ones (`/seller/listings/…`).

## US-14
- **403 vs 404:** a seller opening another seller's existing listing gets a 403; a removed listing (even their own) or a missing id is a 404. Customers get a 403 on every seller page.
- **Remove = soft delete** (`is_deleted=True`). The row stays so past orders keep working; removed listings disappear from the catalogue, matching, details pages and the seller's own list. There is no "undo" page (the admin can clear the flag).
- **Remove flow** mirrors profile deletion: a confirmation page without JavaScript, or `hx-confirm` and an in-place row removal with HTMX.
