from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECIPE_DIR = ROOT / "data" / "recipes"

ID_PATTERN = re.compile(r"^[a-z0-9_]+$")

KNOWN_TAGS = {
    "vegetarian",
    "vegan",
    "no_meat",
    "no_fish",
    "lactose_free",
    "dairy_free",
    "contains_egg",
    "contains_dairy",
    "contains_fish",
    "contains_meat",
    "fast",
    "cheap",
    "common_paris_ingredients",
    "fish",
    "meat",
    "soup",
    "salad",
    "cold",
    "pantry",
    "no_cook",
}

DAIRY_KEYWORDS = {
    "lait",
    "crème",
    "creme",
    "beurre",
    "fromage",
    "yaourt",
    "yogourt",
    "feta",
    "mozzarella",
    "parmesan",
    "ricotta",
    "chèvre",
    "chevre",
    "emmental",
    "comté",
    "comte",
    "gruyère",
    "gruyere",
    "mascarpone",
    "pecorino",
    "halloumi",
}

EGG_KEYWORDS = {
    "œuf",
    "oeuf",
    "œufs",
    "oeufs",
    "egg",
    "eggs",
}

FISH_KEYWORDS = {
    "thon",
    "saumon",
    "sardine",
    "maquereau",
    "cabillaud",
    "poisson",
    "crevette",
    "crevettes",
    "anchois",
    "truite",
    "colin",
    "lieu noir",
    "merlu",
    "moules",
}

MEAT_KEYWORDS = {
    "poulet",
    "jambon",
    "lard",
    "boeuf",
    "bœuf",
    "porc",
    "saucisse",
    "chorizo",
    "dinde",
    "veau",
    "agneau",
    "canard",
    "bacon",
}


@dataclass(frozen=True)
class Finding:
    level: str
    recipe_id: str
    message: str


def add_error(findings: list[Finding], recipe_id: str, message: str) -> None:
    findings.append(Finding("ERROR", recipe_id, message))


def add_warning(findings: list[Finding], recipe_id: str, message: str) -> None:
    findings.append(Finding("WARNING", recipe_id, message))


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def contains_any_keyword(text: str, keywords: set[str]) -> bool:
    normalized = normalize_text(text)
    return any(keyword in normalized for keyword in keywords)


def load_yaml(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        return None, f"YAML parse error: {exc}"
    except OSError as exc:
        return None, f"Could not read file: {exc}"

    if not isinstance(data, dict):
        return None, "expected YAML object at top level"

    return data, None


def validate_minutes(
    data: dict[str, Any],
    key: str,
    recipe_id: str,
    findings: list[Finding],
) -> None:
    value = data.get(key)
    if value is None:
        return

    if not isinstance(value, int):
        add_error(findings, recipe_id, f"{key} must be an integer if present")
        return

    if value < 0:
        add_error(findings, recipe_id, f"{key} must not be negative")


def validate_servings(
    data: dict[str, Any],
    recipe_id: str,
    findings: list[Finding],
) -> None:
    value = data.get("servings")

    if value is None:
        add_warning(findings, recipe_id, "servings missing; importer will default to 2")
        return

    if not isinstance(value, int):
        add_error(findings, recipe_id, "servings must be an integer")
        return

    if value <= 0:
        add_error(findings, recipe_id, "servings must be greater than 0")


def validate_tags(
    data: dict[str, Any],
    recipe_id: str,
    findings: list[Finding],
) -> set[str]:
    raw_tags = data.get("tags")

    if raw_tags is None:
        add_warning(findings, recipe_id, "tags missing; recipe will be hard to filter")
        return set()

    if not isinstance(raw_tags, list):
        add_error(findings, recipe_id, "tags must be a list")
        return set()

    tags: list[str] = []

    for index, raw_tag in enumerate(raw_tags, start=1):
        if not is_non_empty_string(raw_tag):
            add_error(findings, recipe_id, f"tag #{index} must be a non-empty string")
            continue

        tag = raw_tag.strip()
        tags.append(tag)

        if tag not in KNOWN_TAGS:
            add_warning(findings, recipe_id, f"unknown tag: {tag}")

    duplicates = sorted(tag for tag, count in Counter(tags).items() if count > 1)
    for tag in duplicates:
        add_warning(findings, recipe_id, f"duplicate tag: {tag}")

    return set(tags)


def validate_ingredients(
    data: dict[str, Any],
    recipe_id: str,
    findings: list[Finding],
) -> list[dict[str, Any]]:
    raw_ingredients = data.get("ingredients")

    if not isinstance(raw_ingredients, list) or not raw_ingredients:
        add_error(findings, recipe_id, "ingredients must be a non-empty list")
        return []

    clean_ingredients: list[dict[str, Any]] = []
    seen_names: Counter[str] = Counter()
    seen_display_orders: Counter[int] = Counter()

    for index, raw_ingredient in enumerate(raw_ingredients, start=1):
        if not isinstance(raw_ingredient, dict):
            add_error(findings, recipe_id, f"ingredient #{index} must be an object")
            continue

        name = raw_ingredient.get("name")
        if not is_non_empty_string(name):
            add_error(findings, recipe_id, f"ingredient #{index} missing non-empty name")
            continue

        normalized_name = normalize_text(name)
        seen_names[normalized_name] += 1

        quantity = raw_ingredient.get("quantity")
        if quantity is not None and not isinstance(quantity, (int, float)):
            add_warning(
                findings,
                recipe_id,
                f"ingredient '{name}' quantity should usually be numeric if present",
            )

        unit = raw_ingredient.get("unit")
        if unit is not None and not isinstance(unit, str):
            add_warning(findings, recipe_id, f"ingredient '{name}' unit should be text")

        category = raw_ingredient.get("category")
        if category is not None and not isinstance(category, str):
            add_warning(findings, recipe_id, f"ingredient '{name}' category should be text")

        optional = raw_ingredient.get("optional", False)
        if not isinstance(optional, bool):
            add_error(
                findings,
                recipe_id,
                f"ingredient '{name}' optional must be true/false, not text",
            )

        display_order = raw_ingredient.get("display_order")
        if display_order is not None:
            if not isinstance(display_order, int):
                add_warning(
                    findings,
                    recipe_id,
                    f"ingredient '{name}' display_order should be an integer",
                )
            else:
                seen_display_orders[display_order] += 1

        clean_ingredients.append(raw_ingredient)

    duplicate_names = sorted(name for name, count in seen_names.items() if count > 1)
    for name in duplicate_names:
        add_warning(findings, recipe_id, f"duplicate ingredient name: {name}")

    duplicate_orders = sorted(order for order, count in seen_display_orders.items() if count > 1)
    for order in duplicate_orders:
        add_warning(findings, recipe_id, f"duplicate ingredient display_order: {order}")

    return clean_ingredients


def ingredient_names(ingredients: list[dict[str, Any]]) -> list[tuple[str, bool]]:
    names: list[tuple[str, bool]] = []

    for ingredient in ingredients:
        name = str(ingredient.get("name") or "")
        optional = ingredient.get("optional", False)
        names.append((name, bool(optional) if isinstance(optional, bool) else False))

    return names


def validate_tag_logic(
    recipe_id: str,
    tags: set[str],
    ingredients: list[dict[str, Any]],
    findings: list[Finding],
) -> None:
    hard_contradictions = [
        ("vegan", "contains_egg"),
        ("vegan", "contains_dairy"),
        ("vegan", "contains_fish"),
        ("vegan", "contains_meat"),
        ("vegetarian", "contains_fish"),
        ("vegetarian", "contains_meat"),
        ("dairy_free", "contains_dairy"),
        ("no_fish", "contains_fish"),
        ("no_meat", "contains_meat"),
    ]

    for left, right in hard_contradictions:
        if left in tags and right in tags:
            add_error(findings, recipe_id, f"contradictory tags: {left} + {right}")

    if "vegetarian" in tags and "no_meat" not in tags:
        add_warning(findings, recipe_id, "vegetarian recipe should usually also have no_meat")

    if "vegan" in tags:
        expected_vegan_tags = {
            "vegetarian",
            "no_meat",
            "no_fish",
            "dairy_free",
            "lactose_free",
        }
        missing = sorted(expected_vegan_tags - tags)
        if missing:
            add_warning(findings, recipe_id, f"vegan recipe missing implied tags: {', '.join(missing)}")

    if "dairy_free" in tags and "lactose_free" not in tags:
        add_warning(findings, recipe_id, "dairy_free recipe should usually also have lactose_free")

    names = ingredient_names(ingredients)

    has_egg_ingredient = False
    has_optional_egg = False
    has_dairy_ingredient = False
    has_fish_ingredient = False
    has_meat_ingredient = False

    for name, optional in names:
        if contains_any_keyword(name, EGG_KEYWORDS):
            has_egg_ingredient = True
            if optional:
                has_optional_egg = True

        if contains_any_keyword(name, DAIRY_KEYWORDS):
            has_dairy_ingredient = True

        if contains_any_keyword(name, FISH_KEYWORDS):
            has_fish_ingredient = True

        if contains_any_keyword(name, MEAT_KEYWORDS):
            has_meat_ingredient = True

    if has_egg_ingredient and "contains_egg" not in tags:
        add_warning(findings, recipe_id, "egg-like ingredient found but contains_egg tag is missing")

    if has_optional_egg:
        add_warning(
            findings,
            recipe_id,
            "optional egg ingredient found; contains_egg may be ambiguous",
        )

    if has_dairy_ingredient and "contains_dairy" not in tags and "dairy_free" not in tags:
        add_warning(findings, recipe_id, "dairy-like ingredient found but contains_dairy tag is missing")

    if has_dairy_ingredient and "dairy_free" in tags:
        add_warning(findings, recipe_id, "dairy_free tag may conflict with dairy-like ingredient")

    if has_dairy_ingredient and "lactose_free" in tags and "dairy_free" not in tags:
        add_warning(
            findings,
            recipe_id,
            "lactose_free tag with dairy-like ingredient; verify lactose strictness",
        )

    if has_fish_ingredient and "contains_fish" not in tags:
        add_warning(findings, recipe_id, "fish-like ingredient found but contains_fish tag is missing")

    if has_fish_ingredient and "no_fish" in tags:
        add_warning(findings, recipe_id, "no_fish tag may conflict with fish-like ingredient")

    if has_meat_ingredient and "contains_meat" not in tags:
        add_warning(findings, recipe_id, "meat-like ingredient found but contains_meat tag is missing")

    if has_meat_ingredient and "no_meat" in tags:
        add_warning(findings, recipe_id, "no_meat tag may conflict with meat-like ingredient")


def validate_recipe(
    path: Path,
    seen_ids: set[str],
    tag_counts: Counter[str],
    concerns: list[tuple[str, str]],
) -> list[Finding]:
    findings: list[Finding] = []

    data, load_error = load_yaml(path)
    if load_error is not None:
        return [Finding("ERROR", path.name, load_error)]

    assert data is not None

    raw_id = data.get("id")
    recipe_id = str(raw_id).strip() if raw_id is not None else path.stem

    if not is_non_empty_string(raw_id):
        add_error(findings, path.name, "missing required field: id")
        recipe_id = path.stem
    else:
        if recipe_id in seen_ids:
            add_error(findings, recipe_id, "duplicate recipe id")
        seen_ids.add(recipe_id)

        if not ID_PATTERN.match(recipe_id):
            add_warning(
                findings,
                recipe_id,
                "id should use lowercase letters, numbers, and underscores only",
            )

        if path.stem != recipe_id:
            add_warning(
                findings,
                recipe_id,
                f"filename does not match id: {path.name}",
            )

    if not is_non_empty_string(data.get("title")):
        add_error(findings, recipe_id, "missing required field: title")

    if not is_non_empty_string(data.get("short_description")):
        add_warning(findings, recipe_id, "short_description missing or empty")

    if not is_non_empty_string(data.get("notes")):
        add_warning(findings, recipe_id, "notes missing or empty; recipe steps may be weak")

    validate_servings(data, recipe_id, findings)
    validate_minutes(data, "prep_minutes", recipe_id, findings)
    validate_minutes(data, "cook_minutes", recipe_id, findings)

    is_active = data.get("is_active")
    if is_active is not None and not isinstance(is_active, bool):
        add_error(findings, recipe_id, "is_active must be true/false if present")

    tags = validate_tags(data, recipe_id, findings)
    tag_counts.update(tags)

    ingredients = validate_ingredients(data, recipe_id, findings)
    validate_tag_logic(recipe_id, tags, ingredients, findings)

    concern = data.get("concerns_or_tag_ambiguity")
    if is_non_empty_string(concern):
        concerns.append((recipe_id, str(concern).strip()))

    return findings


def print_summary(
    recipe_count: int,
    findings: list[Finding],
    tag_counts: Counter[str],
    concerns: list[tuple[str, str]],
) -> None:
    error_count = sum(1 for finding in findings if finding.level == "ERROR")
    warning_count = sum(1 for finding in findings if finding.level == "WARNING")

    print(f"Recipes checked: {recipe_count}")
    print(f"Errors: {error_count}")
    print(f"Warnings: {warning_count}")

    if tag_counts:
        print()
        print("Tag counts:")
        for tag, count in sorted(tag_counts.items()):
            print(f"- {tag}: {count}")

    if concerns:
        print()
        print("Recipes with concerns_or_tag_ambiguity:")
        for recipe_id, concern in concerns:
            first_line = " ".join(concern.split())
            print(f"- {recipe_id}: {first_line}")

    if findings:
        print()
        print("Findings:")
        for finding in findings:
            print(f"- {finding.level}: {finding.recipe_id}: {finding.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate cenabobot recipe YAML files.")
    parser.add_argument(
        "--recipes-dir",
        type=Path,
        default=DEFAULT_RECIPE_DIR,
        help="Directory containing recipe .yaml files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    args = parser.parse_args()

    recipe_dir = args.recipes_dir

    if not recipe_dir.exists():
        print(f"Recipe directory does not exist: {recipe_dir}", file=sys.stderr)
        return 1

    paths = sorted(recipe_dir.glob("*.yaml"))

    if not paths:
        print(f"No recipe YAML files found in {recipe_dir}", file=sys.stderr)
        return 1

    seen_ids: set[str] = set()
    tag_counts: Counter[str] = Counter()
    concerns: list[tuple[str, str]] = []
    findings: list[Finding] = []

    for path in paths:
        findings.extend(validate_recipe(path, seen_ids, tag_counts, concerns))

    print_summary(
        recipe_count=len(paths),
        findings=findings,
        tag_counts=tag_counts,
        concerns=concerns,
    )

    has_errors = any(finding.level == "ERROR" for finding in findings)
    has_warnings = any(finding.level == "WARNING" for finding in findings)

    if has_errors:
        return 1

    if args.strict and has_warnings:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
