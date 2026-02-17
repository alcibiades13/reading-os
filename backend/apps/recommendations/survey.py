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

# Theme categories — organized by thematic group (most used first)
THEME_CATEGORIES = [
    {
        "id": "relational_emotional",
        "label": "Relational & Emotional",
        "themes": [
            {"id": "love", "label": "Love", "icon": "heart"},
            {"id": "family", "label": "Family", "icon": "home"},
            {"id": "friendship", "label": "Friendship", "icon": "users"},
            {"id": "betrayal", "label": "Betrayal", "icon": "shield-off"},
            {"id": "loss_grief", "label": "Loss & Grief", "icon": "cloud-rain"},
            {"id": "loneliness", "label": "Loneliness", "icon": "user-minus"},
            {"id": "belonging", "label": "Belonging", "icon": "heart-handshake"},
            {"id": "jealousy", "label": "Jealousy", "icon": "flame"},
            {"id": "marriage", "label": "Marriage", "icon": "gem"},
            {"id": "parenthood", "label": "Parenthood", "icon": "baby"},
            {"id": "brotherhood", "label": "Brotherhood / Sisterhood", "icon": "handshake"},
            {"id": "toxic_relationships", "label": "Toxic Relationships", "icon": "link-2-off"},
            {"id": "unrequited_love", "label": "Unrequited Love", "icon": "heart-off"},
        ]
    },
    {
        "id": "romance",
        "label": "Romance",
        "themes": [
            {"id": "romantic", "label": "Romantic", "icon": "heart"},
            {"id": "slow_romance", "label": "Slow Romance", "icon": "heart-handshake"},
            {"id": "passionate", "label": "Passionate", "icon": "flame"},
            {"id": "tragic_love", "label": "Tragic Love", "icon": "heart-crack"},
            {"id": "forbidden_love", "label": "Forbidden Love", "icon": "lock"},
        ]
    },
    {
        "id": "psychological",
        "label": "Psychological",
        "themes": [
            {"id": "trauma", "label": "Trauma", "icon": "heart-crack"},
            {"id": "alienation", "label": "Alienation", "icon": "user-x"},
            {"id": "obsession", "label": "Obsession", "icon": "target"},
            {"id": "madness", "label": "Madness", "icon": "brain"},
            {"id": "guilt", "label": "Guilt & Conscience", "icon": "scale"},
            {"id": "anxiety", "label": "Anxiety", "icon": "activity"},
            {"id": "depression", "label": "Depression", "icon": "cloud"},
            {"id": "addiction", "label": "Addiction", "icon": "pill"},
            {"id": "self_discovery", "label": "Self-Discovery", "icon": "search"},
            {"id": "identity_crisis", "label": "Identity Crisis", "icon": "circle-help"},
            {"id": "manipulation", "label": "Manipulation", "icon": "eye-off"},
            {"id": "power_dynamics", "label": "Power Dynamics", "icon": "arrow-up-down"},
            {"id": "suffering", "label": "Suffering & Pain", "icon": "heart-crack"},
            {"id": "revenge", "label": "Revenge", "icon": "sword"},
            {"id": "deception", "label": "Deception", "icon": "eye-off"},
        ]
    },
    {
        "id": "existential",
        "label": "Existential & Philosophical",
        "themes": [
            {"id": "philosophy", "label": "Philosophy", "icon": "lightbulb"},
            {"id": "existentialism", "label": "Existentialism", "icon": "infinity"},
            {"id": "moral_dilemma", "label": "Moral & Inner Conflict", "icon": "scale"},
            {"id": "faith", "label": "Faith & Spirituality", "icon": "church"},
            {"id": "redemption", "label": "Redemption", "icon": "sunrise"},
            {"id": "mortality", "label": "Mortality", "icon": "hourglass"},
            {"id": "freedom", "label": "Freedom", "icon": "wind"},
            {"id": "fate_free_will", "label": "Fate vs Free Will", "icon": "shuffle"},
            {"id": "absurdity", "label": "Absurdity", "icon": "ban"},
            {"id": "meaning_of_life", "label": "Meaning of Life", "icon": "compass"},
            {"id": "isolation", "label": "Isolation", "icon": "mountain"},
            {"id": "time_impermanence", "label": "Time & Impermanence", "icon": "timer"},
        ]
    },
    {
        "id": "social_political",
        "label": "Social & Political",
        "themes": [
            {"id": "power", "label": "Power & Politics", "icon": "crown"},
            {"id": "social_critique", "label": "Social Critique", "icon": "megaphone"},
            {"id": "war", "label": "War", "icon": "shield"},
            {"id": "class", "label": "Class & Status", "icon": "layers"},
            {"id": "oppression", "label": "Oppression", "icon": "lock"},
            {"id": "revolution", "label": "Revolution", "icon": "flag"},
            {"id": "migration", "label": "Migration", "icon": "map-pin"},
            {"id": "colonialism", "label": "Colonialism", "icon": "globe"},
            {"id": "gender_roles", "label": "Gender & Roles", "icon": "equal"},
            {"id": "tech_society", "label": "Technology & Society", "icon": "cpu"},
        ]
    },
    {
        "id": "mystery_action",
        "label": "Mystery / Action / Adventure",
        "themes": [
            {"id": "mystery", "label": "Mystery", "icon": "search"},
            {"id": "suspense", "label": "Suspense", "icon": "eye"},
            {"id": "action", "label": "Action", "icon": "swords"},
            {"id": "adventure", "label": "Adventure", "icon": "compass"},
            {"id": "journey", "label": "Journey", "icon": "map"},
            {"id": "quest", "label": "Quest", "icon": "compass"},
            {"id": "travel", "label": "Travel", "icon": "plane"},
            {"id": "survival", "label": "Survival", "icon": "shield"},
            {"id": "danger", "label": "Danger", "icon": "alert-triangle"},
            {"id": "heros_journey", "label": "Hero's Journey", "icon": "sword"},
            {"id": "investigation", "label": "Investigation", "icon": "fingerprint"},
            {"id": "conspiracy", "label": "Conspiracy", "icon": "eye"},
            {"id": "crime", "label": "Crime", "icon": "alert-triangle"},
        ]
    },
    {
        "id": "children_ya",
        "label": "Children / Young Adult",
        "themes": [
            {"id": "childhood", "label": "Childhood", "icon": "baby"},
            {"id": "growing_up", "label": "Growing Up", "icon": "sprout"},
            {"id": "friendship_adventure", "label": "Friendship Adventure", "icon": "users"},
            {"id": "school_life", "label": "School Life", "icon": "graduation-cap"},
            {"id": "imagination", "label": "Imagination", "icon": "lightbulb"},
            {"id": "fairy_tale", "label": "Fairy Tale", "icon": "crown"},
            {"id": "talking_animals", "label": "Talking Animals", "icon": "cat"},
            {"id": "magic", "label": "Magic", "icon": "wand-2"},
            {"id": "family_bonds", "label": "Family Bonds", "icon": "home"},
            {"id": "moral_lesson", "label": "Moral Lesson", "icon": "book-open"},
        ]
    },
    {
        "id": "experience_mood",
        "label": "Experience & Mood",
        "themes": [
            {"id": "bleak", "label": "Bleak", "icon": "cloud-drizzle"},
            {"id": "cathartic", "label": "Cathartic", "icon": "droplets"},
            {"id": "disturbing", "label": "Disturbing", "icon": "alert-octagon"},
            {"id": "comforting", "label": "Comforting", "icon": "coffee"},
            {"id": "bittersweet", "label": "Bittersweet", "icon": "cloud-sun"},
            {"id": "wholesome", "label": "Wholesome", "icon": "flower-2"},
            {"id": "dark_humor", "label": "Dark Humor", "icon": "smile"},
            {"id": "satire", "label": "Satire", "icon": "drama"},
            {"id": "gothic", "label": "Gothic", "icon": "castle"},
            {"id": "nature", "label": "Nature", "icon": "leaf"},
            {"id": "art", "label": "Art & Beauty", "icon": "palette"},
            {"id": "intellectual", "label": "Intellectual", "icon": "lightbulb"},
            {"id": "poetic", "label": "Poetic", "icon": "feather"},
            {"id": "melancholic", "label": "Melancholic", "icon": "cloud-rain"},
        ]
    },
    {
        "id": "growth_change",
        "label": "Growth & Change",
        "themes": [
            {"id": "coming_of_age", "label": "Coming of Age", "icon": "sprout"},
            {"id": "growth", "label": "Personal Growth", "icon": "trending-up"},
            {"id": "memory", "label": "Memory & Nostalgia", "icon": "clock"},
            {"id": "identity", "label": "Identity", "icon": "fingerprint"},
        ]
    },
    {
        "id": "positive_light",
        "label": "Positive / Fun / Light",
        "themes": [
            {"id": "hopeful", "label": "Hopeful", "icon": "sun"},
            {"id": "fun", "label": "Fun", "icon": "party-popper"},
            {"id": "playful", "label": "Playful", "icon": "gamepad-2"},
            {"id": "whimsical", "label": "Whimsical", "icon": "wand-2"},
            {"id": "heartwarming", "label": "Heartwarming", "icon": "heart-handshake"},
            {"id": "joy", "label": "Joy", "icon": "smile"},
            {"id": "optimism", "label": "Optimism", "icon": "sunrise"},
            {"id": "humor", "label": "Humorous", "icon": "laugh"},
            {"id": "lighthearted", "label": "Lighthearted", "icon": "feather"},
            {"id": "cozy", "label": "Cozy", "icon": "coffee"},
            {"id": "feel_good", "label": "Feel-Good", "icon": "thumbs-up"},
            {"id": "uplifting", "label": "Uplifting", "icon": "trending-up"},
        ]
    },
    {
        "id": "format_type",
        "label": "Format / Type",
        "themes": [
            {"id": "diary", "label": "Diary", "icon": "book-open"},
            {"id": "memoir", "label": "Memoir", "icon": "user"},
            {"id": "autobiography", "label": "Autobiography", "icon": "user"},
            {"id": "biography", "label": "Biography", "icon": "user"},
            {"id": "letters", "label": "Letters", "icon": "mail"},
            {"id": "short_stories", "label": "Short Stories", "icon": "layers"},
            {"id": "essays_lit", "label": "Essays", "icon": "file-text"},
            {"id": "self_help_lit", "label": "Self-Help", "icon": "compass"},
            {"id": "spiritual_guide", "label": "Spiritual Guide", "icon": "church"},
            {"id": "classic_lit", "label": "Classic", "icon": "book-marked"},
            {"id": "modern_lit", "label": "Modern", "icon": "zap"},
            {"id": "experimental", "label": "Experimental", "icon": "flask-conical"},
        ]
    },
]

# Flat list derived from categories (for backward-compatible validation)
THEME_OPTIONS = []
for _cat in THEME_CATEGORIES:
    for _theme in _cat["themes"]:
        THEME_OPTIONS.append({**_theme, "category": _cat["id"]})

# Genre tag options (stored separately from themes)
GENRE_TAG_OPTIONS = [
    {"id": "literary_fiction", "label": "Literary Fiction", "icon": "book-open"},
    {"id": "science_fiction", "label": "Science Fiction", "icon": "rocket"},
    {"id": "fantasy", "label": "Fantasy", "icon": "wand-2"},
    {"id": "mystery", "label": "Mystery", "icon": "search"},
    {"id": "thriller", "label": "Thriller", "icon": "zap"},
    {"id": "horror", "label": "Horror", "icon": "skull"},
    {"id": "romance", "label": "Romance", "icon": "heart"},
    {"id": "historical_fiction", "label": "Historical Fiction", "icon": "landmark"},
    {"id": "dystopian", "label": "Dystopian", "icon": "radio-tower"},
    {"id": "magical_realism", "label": "Magical Realism", "icon": "sparkles"},
    {"id": "biography_memoir", "label": "Biography / Memoir", "icon": "user"},
    {"id": "philosophy_nf", "label": "Philosophy", "icon": "lightbulb"},
    {"id": "psychology_nf", "label": "Psychology", "icon": "brain"},
    {"id": "science_nf", "label": "Science", "icon": "flask-conical"},
    {"id": "history_nf", "label": "History", "icon": "scroll"},
    {"id": "poetry", "label": "Poetry", "icon": "feather"},
    {"id": "essays", "label": "Essays", "icon": "file-text"},
    {"id": "satire", "label": "Satire", "icon": "drama"},
    {"id": "drama", "label": "Drama", "icon": "drama"},
    {"id": "young_adult", "label": "Young Adult", "icon": "sprout"},
    {"id": "graphic_novel", "label": "Graphic Novel", "icon": "image"},
    {"id": "self_help", "label": "Self-Help", "icon": "compass"},
    {"id": "true_crime", "label": "True Crime", "icon": "shield-alert"},
    {"id": "classics", "label": "Classics", "icon": "book-marked"},
    {"id": "childrens", "label": "Children's", "icon": "baby"},
    {"id": "religion", "label": "Religion & Theology", "icon": "church"},
    {"id": "tragedy", "label": "Tragedy", "icon": "heart-crack"},
]

# Helper sets for validation
VALID_THEME_IDS = {t['id'] for t in THEME_OPTIONS}
VALID_GENRE_TAG_IDS = {t['id'] for t in GENRE_TAG_OPTIONS}

# Mapping from old theme IDs to new (for migration)
THEME_MIGRATION_MAP = {
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
