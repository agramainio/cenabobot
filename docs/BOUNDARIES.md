# cenabobot boundaries

## 1. Product purpose

cenabobot is a private Telegram meal suggestion bot.

Its core job is to answer one simple question:

What can we eat?

The bot suggests one trusted meal at a time from a predefined, owner-approved recipe catalogue.

Default flow:

- suggest one meal
- user can accept or tap Next idea
- user can view recipe
- user can generate shopping list

The bot is not primarily a poll bot, ingredient consensus bot, meal planner, diet tracker, or AI chef.

## 2. Core product rule

cenabobot suggests one trusted meal at a time.

It should not show three default suggestions unless a later feature explicitly asks for a list.

Main buttons:

- Show recipe
- Shopping list
- Next idea
- Save
- Not this

## 3. Privacy boundary

cenabobot is private.

It may exist on Telegram and have a searchable username, but its functionality is locked by code.

Only approved Telegram user IDs and approved Telegram chat/group IDs can use it.

Unknown users or groups should receive only a private-bot message, for example:

This bot is private.

The owner decides who can use it.

## 4. Access model

Version 1 access control may use environment variables:

- ALLOWED_USER_IDS
- ALLOWED_CHAT_IDS

Later, this can move to database tables.

Roles:

Owner:
- decides who can use the bot
- approves groups
- approves recipes
- edits recipe catalogue

Approved user:
- can ask for meal suggestions
- can save favorites
- can generate shopping lists
- can use private or approved group chat

Unknown user/group:
- cannot use the bot

## 5. Telegram group boundary

Best use case:

private Telegram group with owner, selected contact, and bot.

The bot should not need to read every normal message.

Version 1 should rely on:

- buttons
- commands
- direct replies to the bot

Telegram privacy mode should remain enabled unless there is a strong reason to disable it.

## 6. Data boundary

The bot may store:

- Telegram user ID
- Telegram chat ID
- first name / username if useful
- favorites
- recent suggestions
- light feedback such as Not this
- chosen recipes

The bot should not store:

- full chat history
- private conversations
- medical data
- weight
- health conditions
- sensitive profiling

## 7. Recipe source boundary

Recipes come from an owner-approved catalogue.

The bot must not pull random recipes from the internet at runtime.

Allowed recipe sources:

- recipes the owner already cooks
- recipes manually approved by the owner
- public-health style recipes manually reviewed by the owner
- external recipes adapted into short internal notes

Every suggestable meal must exist as a saved recipe record.

Hard rule:

No recipe record = no suggestion.

## 8. Recipe ownership and copyright boundary

The bot does not copy long copyrighted recipe pages.

For external recipes, store:

- recipe title
- source name
- source URL
- structured ingredients
- short internal notes
- shopping-list data
- diet tags

Avoid copying full external recipe instructions unless the source license clearly allows it.

For owner-created recipes, full internal notes are allowed.

## 9. AI boundary

Version 1 has no AI.

Later AI may parse messy user requests, for example:

"something with rice and no milk stuff"

into:

- ingredients: rice
- avoid: milk/dairy/lactose
- filters: lactose_free

AI may:

- extract ingredients
- recognize avoidances
- translate ingredient names
- map synonyms
- rank existing recipes

AI may not:

- invent recipes
- invent recipe titles
- invent cooking steps
- invent quantities
- invent nutrition claims
- invent source links
- claim a recipe is lactose-free unless tagged

Hard rule:

AI parses. Database decides. Only saved recipe IDs can be suggested.

## 10. Nutrition boundary

cenabobot is not a doctor.

It can suggest ordinary healthy meals:

- vegetables
- legumes
- whole grains
- eggs/fish/tofu/legumes as protein
- olive/colza/walnut oil
- less processed food
- less cream/cheese/processed meat

It must not say:

- this treats a medical condition
- this lowers cholesterol
- this is medically recommended for you
- this will make you lose weight

Allowed wording:

- balanced weekday meal
- simple dinner
- good protein from lentils
- vegetarian
- lactose-free
- no meat
- quick

## 11. Diet tag boundary

Do not confuse:

- lactose-free
- dairy-free
- vegetarian
- vegan
- no meat
- no fish
- egg-free

Important distinctions:

- No meat may still include fish.
- Vegetarian excludes meat and fish.
- Vegetarian may include eggs and dairy.
- Lactose-free does not mean vegan.
- Dairy-free is stricter than lactose-free.

Version 1 filters:

- normal healthy
- vegetarian
- no lactose
- no meat
- fast

## 12. Version 1 scope

Version 1 includes:

- private Telegram bot
- approved user/chat access
- button-first interface
- one meal suggestion at a time
- Next idea
- predefined recipe catalogue
- recipe card
- shopping list
- favorites
- basic Not this feedback
- filters: vegetarian, no lactose, no meat, fast

Version 1 does not include:

- AI
- weekly meal planning
- barcode scanning
- Open Food Facts
- supermarket prices
- Carrefour/Monoprix cart generation
- medical diet profiles
- calorie tracking
- public user accounts
- web dashboard
- recipe scraping from random websites

## 13. Success test

The success test is not:

Does the bot feel smart?

The success test is:

When tired, can I tap one button and get one meal I might actually cook tonight?
