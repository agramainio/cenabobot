from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.settings.config import settings


class OpenAIRecipeDraftError(RuntimeError):
    pass


RECIPE_DRAFT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {
            "type": "string",
            "description": "Short French recipe title.",
        },
        "short_description": {
            "type": "string",
            "description": (
                "Compact French preparation summary. This should be useful as the recipe card notes. "
                "Do not write a generic import sentence."
            ),
        },
        "servings": {
            "type": "integer",
            "description": "Number of servings. Use 2 if absent, and add a warning.",
        },
        "prep_minutes": {
            "type": ["integer", "null"],
            "description": "Preparation time in minutes, or null if unknown.",
        },
        "cook_minutes": {
            "type": ["integer", "null"],
            "description": "Cooking time in minutes, or null if unknown.",
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
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
                ],
            },
            "description": "Diet/filter tags for the recipe.",
        },
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Ingredient name only. Do not include metadata such as '2 personnes' or '25 min'.",
                    },
                    "quantity": {
                        "type": ["number", "null"],
                        "description": "Numeric quantity if explicitly present; otherwise null.",
                    },
                    "unit": {
                        "type": ["string", "null"],
                        "description": "Unit such as g, ml, pièce, c. à soupe; otherwise null.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Useful shopping category in French.",
                    },
                    "optional": {
                        "type": "boolean",
                        "description": "True only if the ingredient is explicitly optional.",
                    },
                    "display_order": {
                        "type": "integer",
                        "description": "0-based display order.",
                    },
                },
                "required": [
                    "name",
                    "quantity",
                    "unit",
                    "category",
                    "optional",
                    "display_order",
                ],
            },
        },
        "notes": {
            "type": "string",
            "description": "Concise French preparation instructions extracted or rewritten from the pasted text.",
        },
        "warnings": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Uncertainties or fields to verify before approval.",
        },
    },
    "required": [
        "title",
        "short_description",
        "servings",
        "prep_minutes",
        "cook_minutes",
        "tags",
        "ingredients",
        "notes",
        "warnings",
    ],
}


SYSTEM_PROMPT = """
Tu transformes une recette fournie par un utilisateur autorisé en brouillon structuré pour cenabobot.

Règles produit :
- cenabobot est un catalogue privé de recettes approuvées.
- Tu ne dois pas inventer une recette différente.
- Si le texte vient d’une page web, ignore la navigation, les publicités, les commentaires, les articles liés et tout contenu non-recette.
- Tu dois extraire et structurer uniquement ce qui est présent ou clairement implicite.
- Si une information manque, mets null ou une valeur par défaut prudente, puis ajoute un warning.
- Ne traite jamais les lignes de métadonnées comme ingrédients.
  Exemples de métadonnées à exclure des ingrédients : "2 personnes", "25 min", "30 minutes".
- Les ingrédients doivent contenir seulement de vrais ingrédients.
- Les instructions/préparation doivent aller dans notes et short_description.
- La sortie doit être en français.
- Les tags doivent respecter exactement l'enum du schéma.
- no_meat signifie pas de viande, mais peut contenir poisson/œufs/lait.
- vegetarian exclut viande et poisson, mais peut contenir œufs/lait.
- vegan exclut viande, poisson, œufs et lait.
- lactose_free n'est pas forcément dairy_free.
- En cas de doute alimentaire, ajoute un warning au lieu d'affirmer.
"""


async def generate_recipe_draft_data(raw_text: str, source_url: str | None = None) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        raise OpenAIRecipeDraftError(
            "OPENAI_API_KEY n’est pas configuré dans .env.production."
        )

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        response = await client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT.strip(),
                },
                {
                    "role": "user",
                    "content": (
                        f"Source URL: {source_url}\n\n" if source_url else ""
                    ) + raw_text.strip(),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "cenabobot_recipe_draft",
                    "strict": True,
                    "schema": RECIPE_DRAFT_SCHEMA,
                }
            },
            max_output_tokens=2500,
        )
    except Exception as exc:
        raise OpenAIRecipeDraftError(f"Erreur OpenAI : {exc}") from exc

    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise OpenAIRecipeDraftError("OpenAI n’a pas renvoyé de texte structuré.")

    try:
        data = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise OpenAIRecipeDraftError(f"Réponse OpenAI JSON invalide : {exc}") from exc

    if not isinstance(data, dict):
        raise OpenAIRecipeDraftError("Réponse OpenAI invalide : objet JSON attendu.")

    return data
