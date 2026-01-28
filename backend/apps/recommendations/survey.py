"""
Survey configuration for Book DNA micro-survey.
This defines the questions shown to users after finishing a book.
"""

# Slider questions (6 questions)
SURVEY_QUESTIONS = [
    {
        "id": "pace",
        "question": "What was the pacing like?",
        "left_label": "Slow, contemplative",
        "right_label": "Fast, page-turner",
        "icon": "gauge"
    },
    {
        "id": "emotional_intensity",
        "question": "Emotional intensity?",
        "left_label": "Light, relaxing",
        "right_label": "Intense, emotional",
        "icon": "heart"
    },
    {
        "id": "complexity",
        "question": "How complex was it?",
        "left_label": "Accessible, straightforward",
        "right_label": "Dense, demanding",
        "icon": "brain"
    },
    {
        "id": "character_focus",
        "question": "Story focus?",
        "left_label": "Plot & events",
        "right_label": "Characters & relationships",
        "icon": "users"
    },
    {
        "id": "darkness",
        "question": "Overall tone?",
        "left_label": "Light, hopeful",
        "right_label": "Dark, heavy",
        "icon": "moon"
    },
    {
        "id": "introspection",
        "question": "What drives the narrative?",
        "left_label": "External action & events",
        "right_label": "Inner world & reflection",
        "icon": "sparkles"
    },
]

# Theme options for selection
THEME_OPTIONS = [
    # Core literary themes
    {"id": "identity", "label": "Identity", "icon": "fingerprint"},
    {"id": "love", "label": "Love", "icon": "heart"},
    {"id": "mortality", "label": "Mortality", "icon": "hourglass"},
    {"id": "family", "label": "Family", "icon": "home"},
    {"id": "friendship", "label": "Friendship", "icon": "users"},
    {"id": "coming_of_age", "label": "Coming of Age", "icon": "sprout"},

    # Psychological
    {"id": "obsession", "label": "Obsession", "icon": "target"},
    {"id": "madness", "label": "Madness", "icon": "brain"},
    {"id": "trauma", "label": "Trauma", "icon": "heart-crack"},
    {"id": "alienation", "label": "Alienation", "icon": "user-x"},
    {"id": "guilt", "label": "Guilt & Conscience", "icon": "scale"},

    # Philosophical
    {"id": "philosophy", "label": "Philosophy", "icon": "lightbulb"},
    {"id": "existentialism", "label": "Existentialism", "icon": "help-circle"},
    {"id": "moral_dilemma", "label": "Moral Dilemma", "icon": "scale"},
    {"id": "faith", "label": "Faith & Spirituality", "icon": "church"},

    # Dark themes
    {"id": "crime", "label": "Crime", "icon": "alert-triangle"},
    {"id": "suffering", "label": "Suffering & Pain", "icon": "heart-crack"},
    {"id": "revenge", "label": "Revenge", "icon": "sword"},
    {"id": "deception", "label": "Deception", "icon": "eye-off"},

    # Social/Political
    {"id": "power", "label": "Power & Politics", "icon": "crown"},
    {"id": "social_critique", "label": "Social Critique", "icon": "megaphone"},
    {"id": "class", "label": "Class & Status", "icon": "layers"},
    {"id": "war", "label": "War", "icon": "shield"},

    # Growth & Change
    {"id": "redemption", "label": "Redemption", "icon": "sunrise"},
    {"id": "growth", "label": "Personal Growth", "icon": "trending-up"},
    {"id": "memory", "label": "Memory & Nostalgia", "icon": "clock"},

    # Other
    {"id": "nature", "label": "Nature", "icon": "leaf"},
    {"id": "art", "label": "Art & Beauty", "icon": "palette"},
    {"id": "humor", "label": "Humor & Satire", "icon": "smile"},
    {"id": "adventure", "label": "Adventure", "icon": "compass"},
]

# Mapping from old Serbian theme IDs to new English ones (for migration)
THEME_MIGRATION_MAP = {
    # Direct mappings (same ID, just label changed)
    "faith": "faith",
    "identity": "identity",
    "philosophy": "philosophy",
    "suffering": "suffering",
    "love": "love",
    "family": "family",
    "mortality": "mortality",
    "redemption": "redemption",
    "power": "power",
    "nature": "nature",
    "friendship": "friendship",
    "growth": "growth",
}

# DNA attribute keys for validation
DNA_ATTRIBUTES = ['pace', 'complexity', 'emotional_intensity', 'darkness', 'character_focus', 'introspection']
