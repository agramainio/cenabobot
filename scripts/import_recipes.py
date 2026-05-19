from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.db.models import Recipe, RecipeIngredient
from app.db.session import AsyncSessionLocal
from app.services.recipes import replace_recipe_details

RECIPE_DIR = ROOT / "data" / "recipes"


class RecipeImportError(Exception):
    pass


def require(data: dict[str, Any], key: str) -> Any:
    value = data.get(key)
    if value is None or value == "":
        raise RecipeImportError(f"Missing required field: {key}")
    return value


def load_recipe_file(path: Path) -> tuple[Recipe, list[str], list[RecipeIngredient]]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise RecipeImportError(f"{path.name}: expected YAML object")

    recipe_id = str(require(data, "id"))

    tags_raw = data.get("tags", [])
    if not isinstance(tags_raw, list):
        raise RecipeImportError(f"{recipe_id}: tags must be a list")

    ingredients_raw = data.get("ingredients", [])
    if not isinstance(ingredients_raw, list) or not ingredients_raw:
        raise RecipeImportError(f"{recipe_id}: ingredients must be a non-empty list")

    recipe = Recipe(
        id=recipe_id,
        title=str(require(data, "title")),
        short_description=str(data.get("short_description") or data.get("notes") or ""),
        source_name=data.get("source_name"),
        source_url=data.get("source_url"),
        servings=int(data.get("servings") or 2),
        prep_minutes=data.get("prep_minutes"),
        cook_minutes=data.get("cook_minutes"),
        is_active=bool(data.get("is_active", True)),
    )

    tags = [str(tag).strip() for tag in tags_raw if str(tag).strip()]

    ingredients: list[RecipeIngredient] = []
    for index, raw in enumerate(ingredients_raw):
        if not isinstance(raw, dict):
            raise RecipeImportError(f"{recipe_id}: ingredient #{index + 1} must be an object")

        name = str(require(raw, "name"))

        ingredients.append(
            RecipeIngredient(
                recipe_id=recipe_id,
                name=name,
                quantity=raw.get("quantity"),
                unit=raw.get("unit"),
                category=raw.get("category"),
                optional=bool(raw.get("optional", False)),
                display_order=int(raw.get("display_order", index)),
            )
        )

    return recipe, tags, ingredients


async def main() -> None:
    if not RECIPE_DIR.exists():
        raise SystemExit(f"Recipe directory does not exist: {RECIPE_DIR}")

    paths = sorted(RECIPE_DIR.glob("*.yaml"))

    if not paths:
        raise SystemExit(f"No recipe YAML files found in {RECIPE_DIR}")

    imported = 0

    async with AsyncSessionLocal() as session:
        for path in paths:
            try:
                recipe, tags, ingredients = load_recipe_file(path)
                await replace_recipe_details(
                    session,
                    recipe=recipe,
                    tags=tags,
                    ingredients=ingredients,
                )
                imported += 1
                print(f"Imported {recipe.id}: {recipe.title}")
            except Exception as exc:
                raise SystemExit(f"Failed to import {path}: {exc}") from exc

    print(f"Imported {imported} recipe(s).")


if __name__ == "__main__":
    asyncio.run(main())
