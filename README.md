# Star Wars Unlimited Card Scraper

A Python-based scraper for collecting card data from the Star Wars Unlimited API.

## Project Structure

```
swu-ow-scraper/
├── data/
│   ├── schema.sql      # Database schema definition
│   ├── db.py          # Database management class
│   └── db/            # Database files
│       └── swu_cards.db   # SQLite database (generated)
├── images/            # Downloaded card images (generated)
│   ├── front/        # Front card artwork
│   ├── back/         # Back card artwork (leaders)
│   └── thumbnail/    # Thumbnail images
├── logs/             # Log files (generated)
│   └── scraper.log   # Scraper execution logs
├── config.ini         # Configuration file
├── scraper.py         # Main scraper script
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Database Schema

The database includes tables for:

- **cards** - Main card data (title, cost, power, hp, text, etc.)
- **card_images** - Card artwork URLs and metadata
- **types** - Card types (Leader, Unit, Event, etc.)
- **aspects** - Card aspects (Command, Aggression, Vigilance, etc.)
- **traits** - Card traits (Rebel, Imperial, Jedi, etc.)
- **arenas** - Arena types (Ground, Space)
- **keywords** - Card keywords (Ambush, Overwhelm, etc.)
- **rarities** - Card rarities (Common, Rare, Special, etc.)
- **expansions** - Card sets/expansions
- **variant_types** - Card variant information
- **card_localizations** - Translations for different languages

Junction tables handle many-to-many relationships between cards and their attributes.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python data/db.py
```

3. (Optional) Configure settings in `config.ini`

## Configuration

Edit `config.ini` to customize:
- **Database path** - Where to store the SQLite database
- **API settings** - Rate limiting, pagination size, locale
- **Image download** - Enable/disable, formats to download (card, thumbnail, etc.)
- **Logging** - Log level and file location
- **Scraper behavior** - Retry attempts, timeouts, delays

## Usage

Run the scraper to fetch all cards from the API:

```bash
python scraper.py
```

The scraper will:
1. Automatically fetch all pages of card data from the Star Wars Unlimited API
2. Parse and normalize the JSON response
3. Store cards and related data (types, aspects, traits, etc.) in the SQLite database
4. Download card images to the `images/` folder (if enabled in config)
5. Handle pagination, retries, and rate limiting automatically
6. Log progress and errors to `logs/scraper.log`

**Note:** The scraper will prompt for confirmation before starting. Press Enter to begin or Ctrl+C to cancel.

## API Endpoint

The scraper targets:
```
https://admin.starwarsunlimited.com/api/card-list
```

With various filters and pagination parameters.

## Database Usage Example

```python
from data.db import Database

# Initialize and create schema
with Database() as db:
    db.initialize_schema()
    
    # Check card count
    count = db.get_cards_count()
    print(f"Total cards: {count}")
    
    # Get a specific card
    card = db.get_card_by_uid("3859010573")
    if card:
        print(f"Card: {card['title']} - {card['subtitle']}")
```

## Features

- ✅ Automatic pagination - fetches all cards without manual intervention
- ✅ Complete data extraction - cards, types, aspects, traits, keywords, expansions, and more
- ✅ Multi-language support - stores localizations for different languages
- ✅ Image downloading - organized by type (front/back/thumbnail) with multiple format options
- ✅ Retry logic - handles network failures with exponential backoff
- ✅ Rate limiting - respects API limits to avoid being blocked
- ✅ Progress tracking - detailed logging and statistics
- ✅ Safe execution - uses database transactions, can be re-run safely

## License

This project is for educational purposes only. Star Wars Unlimited is a trademark of Fantasy Flight Games and Lucasfilm Ltd.
