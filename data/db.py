import sqlite3
import os
from pathlib import Path


class Database:
    """SQLite database manager for Star Wars Unlimited cards"""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection
        
        Args:
            db_path: Path to SQLite database file. Defaults to data/db/swu_cards.db
        """
        if db_path is None:
            db_path = Path(__file__).parent / "db" / "swu_cards.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        # Enable foreign keys
        self.cursor.execute("PRAGMA foreign_keys = ON")
        return self
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.close()
    
    def initialize_schema(self, schema_path: str = None):
        """Create all tables from schema file
        
        Args:
            schema_path: Path to schema.sql file
        """
        if schema_path is None:
            schema_path = Path(__file__).parent / "schema.sql"
        
        schema_path = Path(schema_path)
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        self.cursor.executescript(schema_sql)
        self.conn.commit()
        print(f"Database schema initialized at {self.db_path}")
    
    def insert_card(self, card_data: dict) -> int:
        """Insert a card record
        
        Args:
            card_data: Dictionary containing card attributes
            
        Returns:
            Inserted card ID
        """
        sql = """
            INSERT INTO cards (
                id, card_number, title, subtitle, card_count, artist,
                art_front_horizontal, art_back_horizontal, has_foil,
                cost, hp, power, upgrade_hp, upgrade_power,
                text, text_styled, deploy_box, deploy_box_styled,
                epic_action, epic_action_styled, rules, rules_styled,
                link_html, card_uid, serial_code, locale,
                hyperspace, unique_card, showcase, validation_id,
                created_at, updated_at, published_at,
                type_id, type2_id, rarity_id, expansion_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                card_number=excluded.card_number,
                title=excluded.title,
                subtitle=excluded.subtitle,
                updated_at=excluded.updated_at
        """
        
        values = (
            card_data.get('id'),
            card_data.get('cardNumber'),
            card_data.get('title'),
            card_data.get('subtitle'),
            card_data.get('cardCount'),
            card_data.get('artist'),
            card_data.get('artFrontHorizontal'),
            card_data.get('artBackHorizontal'),
            card_data.get('hasFoil'),
            card_data.get('cost'),
            card_data.get('hp'),
            card_data.get('power'),
            card_data.get('upgradeHp'),
            card_data.get('upgradePower'),
            card_data.get('text'),
            card_data.get('textStyled'),
            card_data.get('deployBox'),
            card_data.get('deployBoxStyled'),
            card_data.get('epicAction'),
            card_data.get('epicActionStyled'),
            card_data.get('rules'),
            card_data.get('rulesStyled'),
            card_data.get('linkHtml'),
            card_data.get('cardUid'),
            card_data.get('serialCode'),
            card_data.get('locale'),
            card_data.get('hyperspace'),
            card_data.get('unique'),
            card_data.get('showcase'),
            card_data.get('validationId'),
            card_data.get('createdAt'),
            card_data.get('updatedAt'),
            card_data.get('publishedAt'),
            card_data.get('type_id'),
            card_data.get('type2_id'),
            card_data.get('rarity_id'),
            card_data.get('expansion_id')
        )
        
        self.cursor.execute(sql, values)
        self.conn.commit()
        return self.cursor.lastrowid or card_data.get('id')
    
    def insert_aspect(self, aspect_data: dict) -> int:
        """Insert or update an aspect"""
        sql = """
            INSERT INTO aspects (id, name, english_name, description, color, sort_value, locale, created_at, updated_at, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                updated_at=excluded.updated_at
        """
        values = (
            aspect_data.get('id'),
            aspect_data.get('name'),
            aspect_data.get('englishName'),
            aspect_data.get('description'),
            aspect_data.get('color'),
            aspect_data.get('sortValue'),
            aspect_data.get('locale'),
            aspect_data.get('createdAt'),
            aspect_data.get('updatedAt'),
            aspect_data.get('publishedAt')
        )
        self.cursor.execute(sql, values)
        self.conn.commit()
        return aspect_data.get('id')
    
    def insert_type(self, type_data: dict) -> int:
        """Insert or update a type"""
        sql = """
            INSERT INTO types (id, name, description, value, sort_value, locale, created_at, updated_at, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                updated_at=excluded.updated_at
        """
        values = (
            type_data.get('id'),
            type_data.get('name'),
            type_data.get('description'),
            type_data.get('value'),
            type_data.get('sortValue'),
            type_data.get('locale'),
            type_data.get('createdAt'),
            type_data.get('updatedAt'),
            type_data.get('publishedAt')
        )
        self.cursor.execute(sql, values)
        self.conn.commit()
        return type_data.get('id')
    
    def insert_expansion(self, expansion_data: dict) -> int:
        """Insert or update an expansion"""
        sql = """
            INSERT INTO expansions (id, name, description, code, sort_value, leaderboard_start_date, leaderboard_end_date, locale, created_at, updated_at, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                updated_at=excluded.updated_at
        """
        values = (
            expansion_data.get('id'),
            expansion_data.get('name'),
            expansion_data.get('description'),
            expansion_data.get('code'),
            expansion_data.get('sortValue'),
            expansion_data.get('leaderboardStartDate'),
            expansion_data.get('leaderboardEndDate'),
            expansion_data.get('locale'),
            expansion_data.get('createdAt'),
            expansion_data.get('updatedAt'),
            expansion_data.get('publishedAt')
        )
        self.cursor.execute(sql, values)
        self.conn.commit()
        return expansion_data.get('id')
    
    def insert_rarity(self, rarity_data: dict) -> int:
        """Insert or update a rarity"""
        sql = """
            INSERT INTO rarities (id, name, english_name, character, color, sort_value, locale, created_at, updated_at, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                updated_at=excluded.updated_at
        """
        values = (
            rarity_data.get('id'),
            rarity_data.get('name'),
            rarity_data.get('englishName'),
            rarity_data.get('character'),
            rarity_data.get('color'),
            rarity_data.get('sortValue'),
            rarity_data.get('locale'),
            rarity_data.get('createdAt'),
            rarity_data.get('updatedAt'),
            rarity_data.get('publishedAt')
        )
        self.cursor.execute(sql, values)
        self.conn.commit()
        return rarity_data.get('id')
    
    def link_card_aspect(self, card_id: int, aspect_id: int):
        """Link a card to an aspect"""
        sql = "INSERT OR IGNORE INTO card_aspects (card_id, aspect_id) VALUES (?, ?)"
        self.cursor.execute(sql, (card_id, aspect_id))
        self.conn.commit()
    
    def get_all_cards(self):
        """Retrieve all cards"""
        self.cursor.execute("SELECT * FROM cards")
        return self.cursor.fetchall()
    
    def get_card_by_uid(self, card_uid: str):
        """Get a card by its unique ID"""
        self.cursor.execute("SELECT * FROM cards WHERE card_uid = ?", (card_uid,))
        return self.cursor.fetchone()
    
    def get_cards_count(self) -> int:
        """Get total number of cards in database"""
        self.cursor.execute("SELECT COUNT(*) as count FROM cards")
        return self.cursor.fetchone()['count']


if __name__ == "__main__":
    # Example usage: Initialize the database
    with Database() as db:
        db.initialize_schema()
        print(f"Database created successfully!")
        print(f"Total cards: {db.get_cards_count()}")
