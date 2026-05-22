from __future__ import annotations

from contextvars import ContextVar, Token

from app.settings.config import settings


SUPPORTED_LANGUAGES = {"fr", "it"}
_LANGUAGE_CONTEXT: ContextVar[str | None] = ContextVar("cenabobot_language", default=None)


def normalize_language(language: str | None) -> str:
    value = (language or "").lower().strip()
    if value in SUPPORTED_LANGUAGES:
        return value
    return "fr"


def fallback_language() -> str:
    return normalize_language(settings.APP_LANGUAGE)


def set_language_context(language: str | None) -> Token[str | None]:
    return _LANGUAGE_CONTEXT.set(normalize_language(language))


def reset_language_context(token: Token[str | None]) -> None:
    _LANGUAGE_CONTEXT.reset(token)


def current_language() -> str:
    context_language = _LANGUAGE_CONTEXT.get()
    if context_language in SUPPORTED_LANGUAGES:
        return context_language

    return fallback_language()


TRANSLATIONS: dict[str, dict[str, str]] = {
    "fr": {
        "language.fr": "Français",
        "language.it": "Italiano",

        "menu.prompt": "Choisis une action",
        "menu.placeholder": "Choisis une action",

        "main.suggest": "🍽️ Proposer un repas",
        "main.vegetarian": "🥬 Végétarien",
        "main.fast": "⚡ Rapide",
        "main.no_meat": "🚫 Sans viande",
        "main.no_lactose": "🥛 Sans lactose",
        "main.favorites": "⭐ Favoris",
        "main.add_recipe": "📝 Ajouter une recette",
        "main.pending": "📚 En attente",
        "main.settings": "⚙️ Réglages",

        "import.from_url": "🔗 Depuis un lien",
        "import.from_text": "📋 Depuis un texte",
        "import.pending": "📚 Recettes en attente",
        "import.open": "📝 {title}",
        "import.approve": "✅ Approuver",
        "import.reject": "🗑️ Refuser",
        "import.yaml": "👀 Voir YAML",

        "settings.language": "🌐 Langue",
        "settings.help": "❔ Aide",
        "settings.setup": "⚙️ Configuration",
        "settings.menu": "⬅️ Menu",
        "settings.title": "⚙️ <b>Réglages</b>",
        "settings.body": "Langue actuelle : <b>{language}</b>\n\nLes IDs de recettes et les tags restent internes et non traduits.\nLes nouvelles recettes importées par OpenAI suivent la langue choisie ici.",
        "settings.language_title": "🌐 <b>Langue</b>",
        "settings.language_body": "Choisis la langue de cette conversation.\n\nCela change l’interface du bot et la langue des nouveaux brouillons de recettes générés par OpenAI.\nLes anciennes recettes ne sont pas traduites automatiquement.",
        "settings.language_saved": "Langue mise à jour.",
        "settings.help_title": "❔ <b>Aide</b>",
        "settings.help_body": "cenabobot propose une recette fiable à la fois depuis le catalogue privé.\n\nEn groupe, chacun peut répondre :\n✅ Ça me va\n🙅 Pas ce soir\n\nTu peux aussi ajouter une recette depuis un lien ou un texte. Le bot prépare un brouillon, mais rien n’entre dans le catalogue sans approbation.",
        "settings.setup_title": "⚙️ <b>Configuration</b>",
        "settings.setup_body": "User ID : <code>{user_id}</code>\nChat ID : <code>{chat_id}</code>\n\nSur le VPS :\n1. Ouvre <code>/opt/cenabobot/.env.production</code>\n2. Ajoute ce Chat ID à <code>ALLOWED_CHAT_IDS</code> si nécessaire\n3. Redémarre le bot.",

        "meal.ok": "✅ Ça me va",
        "meal.no": "🙅 Pas ce soir",
        "meal.recipe": "👀 Recette",
        "meal.shopping": "🛒 Courses",
        "meal.final_list": "🛒 Liste finale",
        "meal.next": "🔁 Autre idée",
        "meal.save": "⭐ Garder",
        "meal.reject": "🙅 Pas ce repas",
        "meal.done": "✅ Marquer comme fait",

        "open": "👀 Ouvrir {number}",
        "menu": "⬅️ Menu",

        "filter.any": "repas simple",
        "filter.vegetarian": "végétarien",
        "filter.no_lactose": "sans lactose",
        "filter.no_meat": "sans viande",
        "filter.fast": "rapide",

        "recipe.portions": "Portions",
        "recipe.time": "Temps",
        "recipe.tags": "Tags",
        "recipe.ingredients": "Ingrédients",
        "recipe.summary": "Résumé",
        "recipe.preparation": "Préparation",
        "recipe.source": "Source",
        "recipe.no_summary": "Pas encore de résumé.",
        "recipe.no_preparation": "Pas encore de préparation détaillée.",
        "recipe.no_ingredients": "- Aucun ingrédient renseigné",
        "recipe.private_idea": "Une idée simple depuis ton catalogue privé.",
        "recipe.preference": "Préférence",
        "recipe.unknown_time": "temps non renseigné",

        "shopping.title": "Liste de courses pour {servings} personne{plural}",

        "tag.vegetarian": "végétarien",
        "tag.vegan": "vegan",
        "tag.no_meat": "sans viande",
        "tag.no_fish": "sans poisson",
        "tag.lactose_free": "sans lactose",
        "tag.dairy_free": "sans produits laitiers",
        "tag.contains_egg": "contient œuf",
        "tag.contains_dairy": "contient produits laitiers",
        "tag.contains_fish": "contient poisson",
        "tag.contains_meat": "contient viande",
        "tag.fast": "rapide",
        "tag.cheap": "économique",
        "tag.common_paris_ingredients": "ingrédients courants",
        "tag.unknown": "{value}",

        "commands.start": "Ouvrir le menu",
        "commands.help": "Aide",
        "commands.import": "Ajouter une recette",
        "commands.whoami": "Afficher mes IDs Telegram",
        "commands.setup": "Configuration du groupe",
    },
    "it": {
        "language.fr": "Français",
        "language.it": "Italiano",

        "menu.prompt": "Scegli un’azione",
        "menu.placeholder": "Scegli un’azione",

        "main.suggest": "🍽️ Suggerisci una ricetta",
        "main.vegetarian": "🥬 Vegetariano",
        "main.fast": "⚡ Veloce",
        "main.no_meat": "🚫 Senza carne",
        "main.no_lactose": "🥛 Senza lattosio",
        "main.favorites": "⭐ Preferiti",
        "main.add_recipe": "📝 Aggiungi ricetta",
        "main.pending": "📚 In attesa",
        "main.settings": "⚙️ Impostazioni",

        "import.from_url": "🔗 Da un link",
        "import.from_text": "📋 Da un testo",
        "import.pending": "📚 Ricette in attesa",
        "import.open": "📝 {title}",
        "import.approve": "✅ Approva",
        "import.reject": "🗑️ Rifiuta",
        "import.yaml": "👀 Vedi YAML",

        "settings.language": "🌐 Lingua",
        "settings.help": "❔ Aiuto",
        "settings.setup": "⚙️ Configurazione",
        "settings.menu": "⬅️ Menu",
        "settings.title": "⚙️ <b>Impostazioni</b>",
        "settings.body": "Lingua attuale: <b>{language}</b>\n\nGli ID delle ricette e i tag restano interni e non tradotti.\nLe nuove ricette importate con OpenAI seguono la lingua scelta qui.",
        "settings.language_title": "🌐 <b>Lingua</b>",
        "settings.language_body": "Scegli la lingua di questa conversazione.\n\nQuesto cambia l’interfaccia del bot e la lingua delle nuove bozze di ricette generate da OpenAI.\nLe ricette già esistenti non vengono tradotte automaticamente.",
        "settings.language_saved": "Lingua aggiornata.",
        "settings.help_title": "❔ <b>Aiuto</b>",
        "settings.help_body": "cenabobot propone una ricetta affidabile alla volta dal catalogo privato.\n\nNel gruppo, ognuno può rispondere:\n✅ Va bene\n🙅 Non stasera\n\nPuoi anche aggiungere una ricetta da un link o da un testo. Il bot prepara una bozza, ma nulla entra nel catalogo senza approvazione.",
        "settings.setup_title": "⚙️ <b>Configurazione</b>",
        "settings.setup_body": "User ID: <code>{user_id}</code>\nChat ID: <code>{chat_id}</code>\n\nSul VPS:\n1. Apri <code>/opt/cenabobot/.env.production</code>\n2. Aggiungi questo Chat ID a <code>ALLOWED_CHAT_IDS</code> se necessario\n3. Riavvia il bot.",

        "meal.ok": "✅ Va bene",
        "meal.no": "🙅 Non stasera",
        "meal.recipe": "👀 Ricetta",
        "meal.shopping": "🛒 Spesa",
        "meal.final_list": "🛒 Lista finale",
        "meal.next": "🔁 Altra idea",
        "meal.save": "⭐ Salva",
        "meal.reject": "🙅 Non questo",
        "meal.done": "✅ Segna come fatto",

        "open": "👀 Apri {number}",
        "menu": "⬅️ Menu",

        "filter.any": "pasto semplice",
        "filter.vegetarian": "vegetariano",
        "filter.no_lactose": "senza lattosio",
        "filter.no_meat": "senza carne",
        "filter.fast": "veloce",

        "recipe.portions": "Porzioni",
        "recipe.time": "Tempo",
        "recipe.tags": "Tag",
        "recipe.ingredients": "Ingredienti",
        "recipe.summary": "Riassunto",
        "recipe.preparation": "Preparazione",
        "recipe.source": "Fonte",
        "recipe.no_summary": "Nessun riassunto disponibile.",
        "recipe.no_preparation": "Nessuna preparazione dettagliata.",
        "recipe.no_ingredients": "- Nessun ingrediente indicato",
        "recipe.private_idea": "Un’idea semplice dal tuo catalogo privato.",
        "recipe.preference": "Preferenza",
        "recipe.unknown_time": "tempo non indicato",

        "shopping.title": "Lista della spesa per {servings} persona{plural}",

        "tag.vegetarian": "vegetariano",
        "tag.vegan": "vegano",
        "tag.no_meat": "senza carne",
        "tag.no_fish": "senza pesce",
        "tag.lactose_free": "senza lattosio",
        "tag.dairy_free": "senza latticini",
        "tag.contains_egg": "contiene uova",
        "tag.contains_dairy": "contiene latticini",
        "tag.contains_fish": "contiene pesce",
        "tag.contains_meat": "contiene carne",
        "tag.fast": "veloce",
        "tag.cheap": "economico",
        "tag.common_paris_ingredients": "ingredienti comuni",
        "tag.unknown": "{value}",

        "commands.start": "Apri il menu",
        "commands.help": "Aiuto",
        "commands.import": "Aggiungi una ricetta",
        "commands.whoami": "Mostra i miei ID Telegram",
        "commands.setup": "Configurazione del gruppo",
    },
}


def t(key: str, **kwargs: object) -> str:
    language = current_language()
    template = TRANSLATIONS.get(language, TRANSLATIONS["fr"]).get(
        key,
        TRANSLATIONS["fr"].get(key, key),
    )
    return template.format(**kwargs)


def filter_label(filter_key: str | None) -> str:
    key = filter_key or "any"
    return t(f"filter.{key}") if f"filter.{key}" in TRANSLATIONS[current_language()] else t("filter.any")



def language_name(language: str | None = None) -> str:
    normalized = normalize_language(language or current_language())
    return t(f"language.{normalized}")
