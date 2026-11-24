# Project context

## Product vision

- Read `AppFlow.md` before planning or implementing app behavior. The user supplied this flow on November 24, 2026 to clarify their intended My Kitchen experience. Preserve their original prose.
- Use `AppFlow.md` as the current product reference, with `README.md` supplying complementary requirements. Where the older `INITIAL_DESIGN.md` conflicts with the flow, follow the flow and identify the design as needing revision. Later explicit user instructions take precedence.
- `colors.jpg` is the referenced palette. The visual direction is beginner-friendly, image-led, Pinterest-inspired browsing with smooth onboarding transitions.
- Sign-in uses Firebase with Google accounts. Onboarding collects name, address/phone, up to three preferred stores, cuisine preferences, appliance inventory, and optional spice inventory. Preferences guide recommendations unless the user explicitly enables exclusive filtering.
- Appliance onboarding uses illustrated cards, common tools first, swipe left for owned and right for not owned, undo, and early finish. The user intends to supply `kitchenAppliances.csv` later; it is not yet supplied. Recipe swipe meanings remain to be specified.
- Four main areas: Find Recipes, Calendar, Your Recipes, and Profile.
- Recipe discovery combines chat-assisted internet search with kitchen inventory, time, preferences, source ratings, and novelty. Present candidates sequentially for swiping. Keep the source recipe's requirements intact while making the presentation easy to follow; offer appropriate unit conversions, available instructional images, ingredient-have/need checks, saving, and later ratings. Ingredient status must be understandable without color alone.
- The calendar covers roughly four weeks of dinners, allows browsing past months, and supports choosing/replacing recipes through the same discovery flow. Breakfast and lunch are explicitly for later development.
- Meal Prep jointly considers recipes, existing ingredients/spices, selected-store prices and inventory, budget, and planning duration. Do not silently replace this goal with unrelated recipe suggestions or assume pricing data is available.
- Your Recipes distinguishes loved/favorited recipes (including 10/10 satisfaction) from saved recipes to try. Profile allows editing contact details, stores, kitchen/spice inventories, and preference history.
- Open details include exact inactivity timeout, map/store data provider, recipe data sources, rating scale beyond the 10/10 reference, unit-conversion rules, budget/servings/package-cost rules, and calendar month versus rolling-four-week behavior. Label assumptions rather than treating them as settled requirements.
- Agree on behavior and feasibility before revising implementation scope.