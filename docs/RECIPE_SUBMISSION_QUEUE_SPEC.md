# V2.5 trusted recipe submission queue

This document defines the future V2.5 recipe submission feature for cenabobot.

This is a planning/specification document only.

Do not implement this before the V2 group acceptance flow and migration cleanup are stable.

## Product boundary

cenabobot remains a private trusted-catalogue meal suggestion bot.

Core rule:

    No approved saved recipe_id = no suggestion.

AI may help transform submitted recipe material into a structured draft, but AI must not invent live meal suggestions at runtime.

The normal suggestion flow must continue to use only recipes saved in the database/catalogue.

## Milestone definition

V2.5 trusted recipe submission queue includes:

1. Add button-first import menu
2. Allow trusted users to submit URL
3. Allow trusted users to submit pasted recipe text
4. AI creates structured draft
5. Validator checks draft
6. Safe correction pass
7. Preview with warnings
8. Approve/reject buttons
9. Approved recipe inserted into DB
10. Add Menu button everywhere
11. Improve button labels and emojis
12. Keep slash commands as shortcuts, not primary UX

## Trusted user rule

This feature is not admin-only.

Because cenabobot is private, all trusted users may submit and approve recipes.

Trusted user should mean:

    user_id is in ALLOWED_USER_IDS

Do not rely only on ALLOWED_CHAT_IDS for recipe submission or approval.

Reason:

- ALLOWED_CHAT_IDS authorizes a chat context.
- ALLOWED_USER_IDS authorizes a real Telegram user.
- Recipe import changes the trusted catalogue, so it should be tied to trusted user IDs.

Self-approval is allowed.

This is acceptable because the bot is private and the catalogue is owner/trusted-user curated, not public.

## Supported submission inputs

### 1. Recipe URL

A trusted user can submit a URL.

Possible command shortcut:

    /import https://example.com/recipe

Button-first flow:

    📝 Ajouter une recette
    → 🔗 Depuis un lien
    → user pastes URL

The bot should fetch the page, extract recipe-like content, and create a draft.

### 2. Pasted recipe text

A trusted user can submit free text.

Possible command shortcut:

    /import

Then bot asks the user to paste the recipe.

Button-first flow:

    📝 Ajouter une recette
    → 📋 Depuis un texte
    → user pastes recipe text or notes

The pasted text may be messy. Examples:

- ingredients only
- rough notes
- copied recipe text
- quantities without categories
- steps without precise timing
- personal recipe notes

AI should transform this into a structured draft, but uncertain fields must be flagged.

## Submission pipeline

The expected pipeline is:

    trusted user submits URL or text
    → bot creates import draft record
    → AI creates structured recipe draft
    → validator checks draft
    → safe correction pass
    → validator checks again
    → bot shows Telegram preview with warnings
    → trusted user approves or rejects
    → approved draft is inserted into recipes / recipe_ingredients / recipe_tags
    → approved recipe becomes available for normal suggestions

A submitted draft must not be suggestible until approved.

## AI role

AI is a formatting and extraction assistant.

Allowed AI tasks:

- extract title
- infer concise short_description
- extract ingredients
- normalize ingredient names
- normalize quantities where clearly present
- infer servings when clearly present
- infer prep_minutes and cook_minutes when clearly present
- propose tags
- rewrite compact internal notes
- identify warnings and ambiguity
- convert draft into cenabobot recipe schema

AI must not:

- invent a recipe for immediate suggestion
- silently invent missing quantities
- silently invent cooking times
- silently mark lactose_free / dairy_free / vegetarian / vegan when uncertain
- copy long recipe instructions verbatim from a website
- bypass validation
- insert directly into active recipes without approval

## Safe correction pass

The validator or AI may perform one safe correction pass.

Safe corrections:

- normalize recipe id to lowercase snake_case
- fix obvious tag spelling
- remove duplicate tags
- add no_meat when vegetarian is present
- add vegetarian/no_meat/no_fish/dairy_free/lactose_free when vegan is present
- add lactose_free when dairy_free is present
- convert clear numeric strings such as "30 minutes" to 30
- move uncertain assumptions to concerns_or_tag_ambiguity
- normalize empty source_url to null/empty string according to current schema

Unsafe corrections:

- invent missing ingredients
- invent missing quantities
- invent missing timing
- infer dietary safety without evidence
- delete warnings just to make validation pass
- rewrite a website recipe as a full copied instruction set

If the draft remains uncertain, it can still be previewed with warnings.

Approval should be blocked only on hard schema errors.

## Validator behavior

The validator should check:

- YAML/structured data parses
- required fields exist
- proposed recipe id is unique
- title exists
- short_description exists or warning is shown
- servings is valid
- prep_minutes/cook_minutes are valid if present
- tags are valid
- ingredients are non-empty
- ingredient names are non-empty
- optional is true/false
- contradictions are flagged

Hard errors should block approval.

Warnings should appear in the preview.

Examples of hard errors:

- missing id
- duplicate id
- missing title
- no ingredients
- vegan + contains_egg
- vegetarian + contains_fish
- dairy_free + contains_dairy

Examples of warnings:

- optional egg creates contains_egg ambiguity
- lactose_free with dairy-like ingredient
- missing cook time
- missing quantities
- unknown category
- source page incomplete
- AI confidence low

## Draft preview in Telegram

The bot should show a compact preview, not a huge YAML dump by default.

Example:

    📝 Brouillon de recette

    🍽️ Riz sauté aux œufs et courgettes
    ⏱️ 25 min · 👥 2 personnes

    Tags proposés :
    🥚 contient œuf · 🚫 sans viande · ⚡ rapide

    Ingrédients :
    - riz
    - œufs
    - courgette
    - sauce soja

    ⚠️ À vérifier :
    - quantité de sauce soja non précisée
    - tag sans lactose supposé, à confirmer

    Proposé par : Dani

Buttons:

    ✅ Approuver
    👀 Voir YAML
    🗑️ Refuser
    ⬅️ Menu

If approved:

    ✅ Recette ajoutée au catalogue.
    Elle peut maintenant apparaître dans les idées repas.

Buttons:

    🍽️ Proposer cette recette
    📝 Ajouter une autre recette
    ⬅️ Menu

If rejected:

    Recette refusée.

Buttons:

    📝 Ajouter une autre recette
    📚 Recettes en attente
    ⬅️ Menu

## Data model idea

Add a table similar to:

    recipe_import_drafts
    - id
    - source_type: url / text
    - source_url
    - raw_text
    - submitted_by_user_id
    - submitted_by_name
    - status: pending / approved / rejected / failed
    - proposed_recipe_id
    - proposed_title
    - proposed_yaml
    - warnings
    - validation_errors
    - approved_by_user_id
    - created_at
    - approved_at

Approved drafts should insert into:

    recipes
    recipe_ingredients
    recipe_tags

The draft record should remain as history.

## Source of truth

For V2.5, approved recipe drafts may initially be inserted into the database only.

Do not attempt automatic Git commits from the running Docker container in the first version.

Later, add an export tool:

    /export-recipes

or a script that exports database recipes back to YAML files.

This avoids making the production bot mutate the Git working tree.

## Commands and buttons

Slash commands should remain available as shortcuts and debugging aids.

Keep:

    /start
    /help
    /whoami
    /setup
    /import

But normal users should not need to type commands for everyday use.

Main menu should expose recipe submission through buttons.

Suggested main menu:

    🍽️ Proposer un repas
    🥬 Végétarien
    ⚡ Rapide
    🚫 Sans viande
    🥛 Sans lactose
    ⭐ Favoris
    📝 Ajouter une recette
    📚 Recettes en attente
    ⚙️ Aide / configuration

Import menu:

    🔗 Depuis un lien
    📋 Depuis un texte
    📚 Recettes en attente
    ⬅️ Menu

## Menu button rule

Every non-final screen should include:

    ⬅️ Menu

Examples:

Recipe card:

    ✅ Ça me va
    🙅 Pas ce soir
    👀 Recette
    🛒 Courses
    🔁 Autre idée
    ⬅️ Menu

Shopping list:

    👥 1
    👥 2
    👥 4
    👀 Recette
    ⬅️ Menu

Import preview:

    ✅ Approuver
    👀 Voir YAML
    🗑️ Refuser
    ⬅️ Menu

## Button label direction

Use emojis as small anchors, not decoration everywhere.

Preferred labels:

    🍽️ Proposer un repas
    🔁 Autre idée
    👀 Recette
    🛒 Courses
    ⭐ Garder
    ✅ Ça me va
    🙅 Pas ce soir
    📝 Ajouter une recette
    🔗 Depuis un lien
    📋 Depuis un texte
    📚 En attente
    ✅ Approuver
    🗑️ Refuser
    ⬅️ Menu

Avoid excessive emoji tone such as:

    🔥😍🤤✨🚀🥳

The bot should feel useful, calm, and readable.

## Copyright and source handling

For URL imports:

- keep source_url
- keep source_name/domain when available
- do not copy long recipe instructions verbatim
- rewrite compact notes for private catalogue use
- keep warnings when extraction is uncertain

The goal is a practical private meal catalogue, not a recipe scraper dump.

## Out of scope for first V2.5 pass

Do not include in the first implementation:

- full recipe editing UI in Telegram
- automatic Git commits
- public web admin panel
- multi-step ingredient editor
- nutrition scoring
- user ratings
- AI live meal invention
- import from images/PDFs
- scheduled meal planning
- full grocery app behavior

## Success criteria

V2.5 is successful when:

- a trusted user can submit a URL
- a trusted user can submit pasted text
- the bot produces a structured draft
- hard validation errors block approval
- warnings are visible in preview
- any trusted user can approve
- approved recipes are inserted into the catalogue database
- approved recipes can be suggested by the existing meal flow
- slash commands remain shortcuts
- normal use is button-first
- every screen has a clear Menu button
