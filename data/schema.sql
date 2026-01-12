-- Star Wars Unlimited Card Database Schema

-- Main Cards Table
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY,
    card_number INTEGER,
    title TEXT NOT NULL,
    subtitle TEXT,
    card_count INTEGER,
    artist TEXT,
    art_front_horizontal BOOLEAN,
    art_back_horizontal BOOLEAN,
    has_foil BOOLEAN,
    cost INTEGER,
    hp INTEGER,
    power INTEGER,
    upgrade_hp INTEGER,
    upgrade_power INTEGER,
    text TEXT,
    text_styled TEXT,
    deploy_box TEXT,
    deploy_box_styled TEXT,
    epic_action TEXT,
    epic_action_styled TEXT,
    rules TEXT,
    rules_styled TEXT,
    link_html TEXT,
    card_uid TEXT UNIQUE,
    serial_code TEXT,
    locale TEXT DEFAULT 'en',
    hyperspace BOOLEAN DEFAULT 0,
    unique_card BOOLEAN DEFAULT 0,
    showcase BOOLEAN DEFAULT 0,
    validation_id TEXT,
    created_at TEXT,
    updated_at TEXT,
    published_at TEXT,
    -- Foreign Keys
    type_id INTEGER,
    type2_id INTEGER,
    rarity_id INTEGER,
    expansion_id INTEGER,
    FOREIGN KEY (type_id) REFERENCES types(id),
    FOREIGN KEY (type2_id) REFERENCES types(id),
    FOREIGN KEY (rarity_id) REFERENCES rarities(id),
    FOREIGN KEY (expansion_id) REFERENCES expansions(id)
);

-- Card Images/Art
CREATE TABLE IF NOT EXISTS card_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    image_type TEXT NOT NULL, -- 'front', 'back', 'thumbnail'
    name TEXT,
    width INTEGER,
    height INTEGER,
    hash TEXT,
    ext TEXT,
    mime TEXT,
    size REAL,
    url TEXT,
    -- Format URLs
    card_url TEXT,
    small_url TEXT,
    medium_url TEXT,
    xsmall_url TEXT,
    xxsmall_url TEXT,
    xxxsmall_url TEXT,
    thumbnail_url TEXT,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

-- Types (Leader, Unit, Event, etc.)
CREATE TABLE IF NOT EXISTS types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    value TEXT,
    sort_value INTEGER,
    locale TEXT DEFAULT 'en',
    created_at TEXT,
    updated_at TEXT,
    published_at TEXT
);

-- Aspects (Command, Aggression, Vigilance, etc.)
CREATE TABLE IF NOT EXISTS aspects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    english_name TEXT,
    description TEXT,
    color TEXT,
    sort_value INTEGER,
    locale TEXT DEFAULT 'en',
    created_at TEXT,
    updated_at TEXT,
    published_at TEXT
);

-- Traits (Rebel, Imperial, Jedi, etc.)
CREATE TABLE IF NOT EXISTS traits (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    locale TEXT DEFAULT 'en',
    created_at TEXT,
    updated_at TEXT,
    published_at TEXT
);

-- Arenas (Ground, Space)
CREATE TABLE IF NOT EXISTS arenas (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    locale TEXT DEFAULT 'en',
    created_at TEXT,
    updated_at TEXT,
    published_at TEXT
);

-- Keywords (Ambush, Overwhelm, etc.)
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    locale TEXT DEFAULT 'en',
    created_at TEXT,
    updated_at TEXT,
    published_at TEXT
);

-- Rarities (Common, Uncommon, Rare, etc.)
CREATE TABLE IF NOT EXISTS rarities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    english_name TEXT,
    character TEXT,
    color TEXT,
    sort_value INTEGER,
    locale TEXT DEFAULT 'en',
    created_at TEXT,
    updated_at TEXT,
    published_at TEXT
);

-- Expansions/Sets
CREATE TABLE IF NOT EXISTS expansions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    code TEXT,
    sort_value INTEGER,
    leaderboard_start_date TEXT,
    leaderboard_end_date TEXT,
    locale TEXT DEFAULT 'en',
    created_at TEXT,
    updated_at TEXT,
    published_at TEXT
);

-- Variant Types
CREATE TABLE IF NOT EXISTS variant_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    variant_id TEXT,
    foil BOOLEAN,
    sort_value INTEGER,
    icon_url TEXT,
    locale TEXT DEFAULT 'en',
    created_at TEXT,
    updated_at TEXT,
    published_at TEXT
);

-- Junction Tables for Many-to-Many Relationships

CREATE TABLE IF NOT EXISTS card_aspects (
    card_id INTEGER NOT NULL,
    aspect_id INTEGER NOT NULL,
    PRIMARY KEY (card_id, aspect_id),
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (aspect_id) REFERENCES aspects(id)
);

CREATE TABLE IF NOT EXISTS card_traits (
    card_id INTEGER NOT NULL,
    trait_id INTEGER NOT NULL,
    PRIMARY KEY (card_id, trait_id),
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (trait_id) REFERENCES traits(id)
);

CREATE TABLE IF NOT EXISTS card_arenas (
    card_id INTEGER NOT NULL,
    arena_id INTEGER NOT NULL,
    PRIMARY KEY (card_id, arena_id),
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (arena_id) REFERENCES arenas(id)
);

CREATE TABLE IF NOT EXISTS card_keywords (
    card_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    PRIMARY KEY (card_id, keyword_id),
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (keyword_id) REFERENCES keywords(id)
);

CREATE TABLE IF NOT EXISTS card_variant_types (
    card_id INTEGER NOT NULL,
    variant_type_id INTEGER NOT NULL,
    PRIMARY KEY (card_id, variant_type_id),
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (variant_type_id) REFERENCES variant_types(id)
);

-- Card Localizations (for different language versions)
CREATE TABLE IF NOT EXISTS card_localizations (
    id INTEGER PRIMARY KEY,
    card_id INTEGER NOT NULL,
    locale TEXT NOT NULL,
    title TEXT,
    subtitle TEXT,
    text TEXT,
    text_styled TEXT,
    deploy_box TEXT,
    deploy_box_styled TEXT,
    epic_action TEXT,
    epic_action_styled TEXT,
    rules TEXT,
    rules_styled TEXT,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_cards_card_uid ON cards(card_uid);
CREATE INDEX IF NOT EXISTS idx_cards_serial_code ON cards(serial_code);
CREATE INDEX IF NOT EXISTS idx_cards_title ON cards(title);
CREATE INDEX IF NOT EXISTS idx_cards_expansion ON cards(expansion_id);
CREATE INDEX IF NOT EXISTS idx_cards_type ON cards(type_id);
CREATE INDEX IF NOT EXISTS idx_cards_rarity ON cards(rarity_id);
CREATE INDEX IF NOT EXISTS idx_card_localizations_card_id ON card_localizations(card_id);
CREATE INDEX IF NOT EXISTS idx_card_localizations_locale ON card_localizations(locale);
