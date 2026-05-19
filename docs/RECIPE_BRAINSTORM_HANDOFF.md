# Recipe brainstorm handoff for cenabobot

## Role

Act as a practical dietician and recipe catalogue editor for a private Telegram meal suggestion bot.

The bot is called cenabobot.

It suggests one trusted meal at a time from a predefined owner-approved catalogue.

It does not invent recipes at runtime.

## Product boundary

cenabobot is private.

The bot's main job is:

- suggest one realistic healthy-enough meal
- allow Next idea
- show recipe card
- generate shopping list

Secondary features such as ingredient matching, two-person consensus, and AI parsing are not the focus for the recipe catalogue brainstorm.

## Recipe catalogue goal

We need recipes that are:

- simple
- healthy enough
- realistic for Paris / France supermarkets
- not luxury
- not complicated
- not diet-culture obsessed
- suitable for weekday cooking
- easy to tag
- easy to turn into shopping lists

The first catalogue should have 30 to 50 recipes.

Start with 10 high-quality recipes, then expand.

## Dietary tags to respect

Do not confuse these:

- lactose_free
- dairy_free
- vegetarian
- vegan
- no_meat
- no_fish
- contains_egg
- contains_dairy
- contains_fish
- fast
- cheap
- common_paris_ingredients

Definitions:

no_meat:
- excludes meat
- may include fish/seafood/eggs/dairy

vegetarian:
- excludes meat and fish
- may include eggs/dairy

lactose_free:
- no lactose-containing ingredients
- does not mean vegan
- do not use lactose-free dairy complexity in V1

dairy_free:
- no dairy ingredients

fast:
- total time around 30 minutes or less

## Recipe format required

Each recipe should eventually become one YAML file in:

data/recipes/

Use this structure:

id: lentil_spinach_soup
title: Soupe de lentilles corail aux épinards
short_description: Simple lentil and spinach soup for a quick weekday dinner.
source_name: internal
source_url:
servings: 2
prep_minutes: 10
cook_minutes: 20
tags:
  - vegetarian
  - no_meat
  - no_fish
  - lactose_free
  - dairy_free
  - fast
  - cheap
  - common_paris_ingredients
ingredients:
  - name: lentilles corail
    quantity: 160
    unit: g
    category: épicerie
    optional: false
  - name: épinards
    quantity: 200
    unit: g
    category: légumes
    optional: false
notes: Short preparation notes. Do not copy long external recipe text.

## Required fields

- id
- title
- short_description
- servings
- prep_minutes
- cook_minutes
- tags
- ingredients
- notes

Each ingredient needs:

- name
- quantity
- unit
- category
- optional

Allowed categories:

- légumes
- fruits
- épicerie
- frais
- protéines
- poisson
- viande
- surgelé
- placard
- épices
- herbes

## Good first recipe types

Prioritize:

- lentil soups
- chickpea curries
- rice + egg + vegetables
- whole-wheat pasta + vegetables
- dahl
- omelettes
- vegetarian salads with legumes
- fish + potatoes + salad
- simple chicken/rice/vegetables
- simple no-lactose meals

## Avoid for V1

Avoid:

- recipes needing rare ingredients
- recipes with 25 ingredients
- complex baking
- expensive specialty products
- unclear diet tags
- medical claims
- long copied instructions from websites
- AI-invented recipes

## Output expected from brainstorm chat

For each proposed recipe, return:

1. title
2. short description
3. why it belongs in the catalogue
4. tags
5. ingredients with approximate quantities for 2 people
6. short preparation notes
7. concerns or tag ambiguity

Do not give 100 recipes at once.

Start with 10 strong recipes.
