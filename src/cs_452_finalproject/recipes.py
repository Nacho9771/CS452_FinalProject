"""Recipe arithmetic, independent of HTTP, databases, and AI.

Use Decimal for reproducible quantities. Formatting/rounding for kitchen-friendly
fractions belongs in the display layer; preserve calculation precision here.
"""

from decimal import Decimal

from .models import PreviewIngredient, PreviewRequest, RecipePreview, Unit

# US customary volume is an explicit first-version convention, not a universal cup.
# Base units are grams for mass and milliliters for volume.
MASS = {
    Unit.GRAM: Decimal(1),
    Unit.KILOGRAM: Decimal(1000),
    Unit.OUNCE: Decimal("28.349523125"),
    Unit.POUND: Decimal("453.59237"),
}
VOLUME = {
    Unit.MILLILITER: Decimal(1),
    Unit.LITER: Decimal(1000),
    Unit.US_TEASPOON: Decimal("4.92892159375"),
    Unit.US_TABLESPOON: Decimal("14.78676478125"),
    Unit.US_CUP: Decimal("236.5882365"),
}


def convert(
    quantity: Decimal, source: Unit, target: Unit, density: Decimal | None
) -> Decimal | None:
    """Return None for unsupported conversions; the caller retains source units."""
    if source == target:
        return quantity
    for factors in (MASS, VOLUME):
        if source in factors and target in factors:
            return quantity * factors[source] / factors[target]
    if density is not None:
        if source in MASS and target in VOLUME:
            return quantity * MASS[source] / density / VOLUME[target]
        if source in VOLUME and target in MASS:
            return quantity * VOLUME[source] * density / MASS[target]
    return None


def preview_recipe(request: PreviewRequest) -> RecipePreview:
    """Scale quantities without rewriting recipe steps or cooking times."""
    recipe = request.recipe
    if any(index < 0 or index >= len(recipe.ingredients) for index in request.target_units):
        raise ValueError("Target unit indexes must refer to an existing ingredient.")

    scale = Decimal(request.target_servings) / Decimal(recipe.servings)
    ingredients = []
    for index, ingredient in enumerate(recipe.ingredients):
        quantity = ingredient.quantity
        warning = None
        unit = ingredient.unit
        target = request.target_units.get(index, unit)
        if quantity is not None:
            quantity *= scale
        elif scale != 1:
            warning = "No numeric quantity supplied; follow the original ingredient text."

        if target != unit:
            converted = (
                convert(quantity, unit, target, ingredient.density_g_per_ml)
                if quantity is not None and unit is not None
                else None
            )
            if converted is None:
                warning = (
                    "Conversion unavailable; kept the scaled quantity in its source unit. "
                    "Weight/volume conversion requires ingredient-specific density; "
                    "count conversions require additional information."
                )
            else:
                quantity, unit = converted, target
        ingredients.append(
            PreviewIngredient(
                name=ingredient.name,
                original_text=ingredient.original_text,
                quantity=quantity,
                unit=unit,
                warning=warning,
            )
        )
    return RecipePreview(
        title=recipe.title,
        original_servings=recipe.servings,
        servings=request.target_servings,
        ingredients=ingredients,
        steps=recipe.steps.copy(),
        prep_minutes=recipe.prep_minutes,
        cook_minutes=recipe.cook_minutes,
        source_url=recipe.source_url,
    )
