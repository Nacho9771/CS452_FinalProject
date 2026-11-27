# Project context

## Product vision

- Read `AppFlow.md` before planning or implementing app behavior. The user supplied this flow on November 24, 2026 to clarify their intended My Kitchen experience. Preserve their original prose.
- Use `AppFlow.md` as the current product reference, with `README.md` supplying complementary requirements. Where the older `INITIAL_DESIGN.md` conflicts with the flow, follow the flow and identify the design as needing revision. Later explicit user instructions take precedence.
- `colors.jpg` is the referenced palette. The visual direction is beginner-friendly, image-led, Pinterest-inspired browsing with smooth onboarding transitions.
- Sign-in uses Firebase with Google accounts. Onboarding collects name, address/phone, up to three preferred stores, cuisine preferences, appliance inventory, and optional spice inventory. Preferences guide recommendations unless the user explicitly enables exclusive filtering.
- Appliance onboarding uses illustrated cards, common tools first, swipe left for owned and right for not owned, undo, and early finish. The user intends to supply `kitchenAppliances.csv` later; it is not yet supplied. The November 26 flow defines recipe swipe directions, separate bookmarks/likes, and disabling tab swipes inside card selection.
- Four main areas: Find Recipes, Calendar, Your Recipes, and Profile.
- Recipe discovery combines chat-assisted internet search with kitchen inventory, time, preferences, source ratings, and novelty. Present candidates sequentially for swiping. Keep the source recipe's requirements intact while making the presentation easy to follow; offer appropriate unit conversions, available instructional images, ingredient-have/need checks, saving, and later ratings. Ingredient status must be understandable without color alone.
- The calendar covers roughly four weeks of dinners, allows browsing past months, and supports choosing/replacing recipes through the same discovery flow. Breakfast and lunch are explicitly for later development.
- Meal Prep jointly considers recipes, existing ingredients/spices, selected-store prices and inventory, budget, and planning duration. Do not silently replace this goal with unrelated recipe suggestions or assume pricing data is available.
- Your Recipes distinguishes loved/favorited recipes (including 10/10 satisfaction) from saved recipes to try. Profile allows editing contact details, stores, kitchen/spice inventories, and preference history.
- The November 26 flow adds household defaults/per-meal servings, source-preserving scaling, ingredient-specific weight/volume conversion, household budgeting with combined-list pricing before approval, shopping days, private recipes with optional publishing, dietary-filter choice, cooked/skipped/moved calendar actions, logout/deletion, and unavailable-feature behavior. Read the file for the exact rules.
- Remaining decisions include exact inactivity timeout, external data providers, rating scale beyond the 10/10 reference, pantry quantities/package-cost details, and calendar month versus rolling-four-week behavior. Label assumptions rather than treating them as settled requirements.
- Agree on behavior and feasibility before revising implementation scope.

## Development and learning

- The user wants to understand and independently debug, personalize, and extend every part. Build in understandable increments; explain each request path and service boundary. Keep `docs/DEVELOPMENT.md` accurate, distinguish implemented features from planned integrations, and give runnable examples and relevant verification results.
- Preserve the original prose in `AppFlow.md` and the original goals in `README.md`. Track implementation notes separately. Do not invent completed hours or overwrite the user's project log.
