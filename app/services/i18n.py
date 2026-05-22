from __future__ import annotations

from app.settings.config import settings


SUPPORTED_LANGUAGES = {"fr", "it"}


def current_language() -> str:
    language = settings.APP_LANGUAGE.lower().strip()
    if language in SUPPORTED_LANGUAGES:
        return language
    return "fr"


TRANSLATIONS: dict[str, dict[str, str]] = {
    "fr": {
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

        "commands.start": "Ouvrir le menu",
        "commands.help": "Aide",
        "commands.import": "Ajouter une recette",
        "commands.whoami": "Afficher mes IDs Telegram",
        "commands.setup": "Configuration du groupe",
    },
    "it": {
        "main.suggest": "🍽️ Proponi un pasto",
        "main.vegetarian": "🥬 Vegetariano",
        "main.fast": "⚡ Rapido",
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
