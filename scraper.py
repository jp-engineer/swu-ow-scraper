"""
Star Wars Unlimited Card Scraper

Fetches card data from the official API and stores it in the SQLite database.
"""

import requests
import time
import logging
import configparser
from pathlib import Path
from typing import Dict, List, Optional
from data.db import Database


class SWUCardScraper:
    """Scraper for Star Wars Unlimited card data"""
    
    def __init__(self, config_path: str = "config.ini"):
        """Initialize the scraper with configuration
        
        Args:
            config_path: Path to configuration file
        """
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # API settings
        self.base_url = self.config.get('api', 'base_url')
        self.locale = self.config.get('api', 'default_locale')
        self.page_size = self.config.getint('api', 'page_size')
        self.rate_limit = self.config.getfloat('api', 'rate_limit')
        
        # Scraper settings
        self.max_retries = self.config.getint('scraper', 'max_retries')
        self.timeout = self.config.getint('scraper', 'timeout')
        self.request_delay = self.config.getfloat('scraper', 'request_delay')
        
        # Image settings
        self.download_images = self.config.getboolean('images', 'download_images')
        self.images_dir = Path(self.config.get('images', 'images_dir'))
        self.image_formats = [fmt.strip() for fmt in self.config.get('images', 'image_formats').split(',')]
        
        # Setup logging
        self._setup_logging()
        
        # HTTP headers to avoid 403 errors
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://starwarsunlimited.com/',
            'Origin': 'https://starwarsunlimited.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }
        
        # Statistics
        self.stats = {
            'cards_processed': 0,
            'cards_inserted': 0,
            'cards_updated': 0,
            'images_downloaded': 0,
            'errors': 0
        }
    
    def _setup_logging(self):
        """Configure logging"""
        log_level = self.config.get('logging', 'log_level')
        log_file = Path(self.config.get('logging', 'log_file'))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _build_api_url(self, page: int = 1) -> str:
        """Build the API URL with all filters
        
        Args:
            page: Page number for pagination
            
        Returns:
            Complete API URL
        """
        # Base filters from the example URL
        filters = {
            'locale': self.locale,
            'orderBy[expansion][id]': 'asc',
            'sort[0]': 'type.sortValue:asc, expansion.sortValue:desc,cardNumber:asc,',
            'filters[$and][0][variantOf][id][$null]': 'true',
            'pagination[page]': page,
            'pagination[pageSize]': self.page_size
        }
        
        # Type filters
        type_ids = [4, 38, 37, 36, 5, 6, 23, 22, 21, 20]
        for i, type_id in enumerate(type_ids):
            filters[f'filters[$and][1][$or][0][type][id][$in][{i}]'] = type_id
            filters[f'filters[$and][1][$or][1][type2][id][$in][{i}]'] = type_id
        
        # Additional filters
        filters['aspectMethod'] = 0
        filters['aspect'] = 0
        filters['traitMethod'] = 0
        filters['trait'] = 0
        
        # Build query string
        params = '&'.join([f'{k}={v}' for k, v in filters.items()])
        return f"{self.base_url}?{params}"
    
    def _make_request(self, url: str, retry_count: int = 0) -> Optional[Dict]:
        """Make HTTP request with retry logic
        
        Args:
            url: URL to request
            retry_count: Current retry attempt
            
        Returns:
            JSON response or None on failure
        """
        try:
            self.logger.debug(f"Making request to: {url}")
            response = requests.get(url, timeout=self.timeout, headers=self.headers)
            response.raise_for_status()
            
            # Rate limiting
            time.sleep(self.request_delay)
            
            # Try to parse JSON
            try:
                return response.json()
            except ValueError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.error(f"Response status: {response.status_code}")
                self.logger.error(f"Response headers: {response.headers}")
                self.logger.error(f"Response content (first 500 chars): {response.text[:500]}")
                raise
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            
            if retry_count < self.max_retries:
                self.logger.info(f"Retrying... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._make_request(url, retry_count + 1)
            
            self.stats['errors'] += 1
            return None
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.stats['errors'] += 1
            return None
    
    def _download_image(self, url: str, save_path: Path) -> bool:
        """Download an image from URL
        
        Args:
            url: Image URL
            save_path: Path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if save_path.exists():
                self.logger.debug(f"Image already exists: {save_path.name}")
                return True
            
            # Special headers for image downloads
            image_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://starwarsunlimited.com/cards',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            response = requests.get(url, timeout=self.timeout, stream=True, headers=image_headers)
            response.raise_for_status()
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.debug(f"Downloaded image: {save_path.name}")
            self.stats['images_downloaded'] += 1
            time.sleep(0.1)  # Small delay between image downloads
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to download image {url}: {e}")
            return False
    
    def _process_card_images(self, card_id: int, card_uid: str, art_data: Dict, image_type: str, db: Database):
        """Process and store card images
        
        Args:
            card_id: Card database ID
            card_uid: Card unique identifier
            art_data: Image data from API
            image_type: Type of image (front, back, thumbnail)
            db: Database instance
        """
        if not art_data or 'data' not in art_data or not art_data['data']:
            return
        
        img_attrs = art_data['data']['attributes']
        formats = img_attrs.get('formats', {})
        
        # Store image metadata in database
        image_data = {
            'card_id': card_id,
            'image_type': image_type,
            'name': img_attrs.get('name'),
            'width': img_attrs.get('width'),
            'height': img_attrs.get('height'),
            'hash': img_attrs.get('hash'),
            'ext': img_attrs.get('ext'),
            'mime': img_attrs.get('mime'),
            'size': img_attrs.get('size'),
            'url': img_attrs.get('url')
        }
        
        # Add format URLs
        for fmt in ['card', 'small', 'medium', 'xsmall', 'xxsmall', 'xxxsmall', 'thumbnail']:
            if fmt in formats:
                image_data[f'{fmt}_url'] = formats[fmt].get('url')
        
        # Insert into database
        sql = """
            INSERT INTO card_images (
                card_id, image_type, name, width, height, hash, ext, mime, size, url,
                card_url, small_url, medium_url, xsmall_url, xxsmall_url, xxxsmall_url, thumbnail_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            image_data.get('card_id'), image_data.get('image_type'), image_data.get('name'),
            image_data.get('width'), image_data.get('height'), image_data.get('hash'),
            image_data.get('ext'), image_data.get('mime'), image_data.get('size'),
            image_data.get('url'), image_data.get('card_url'), image_data.get('small_url'),
            image_data.get('medium_url'), image_data.get('xsmall_url'), image_data.get('xxsmall_url'),
            image_data.get('xxxsmall_url'), image_data.get('thumbnail_url')
        )
        db.cursor.execute(sql, values)
        
        # Download images if enabled
        if self.download_images:
            for fmt in self.image_formats:
                if fmt in formats and formats[fmt].get('url'):
                    url = formats[fmt]['url']
                    filename = f"{card_uid}_{image_type}_{fmt}{img_attrs.get('ext', '.png')}"
                    save_path = self.images_dir / image_type / filename
                    self._download_image(url, save_path)
    
    def _process_card(self, card_data: Dict, db: Database):
        """Process a single card and store in database
        
        Args:
            card_data: Card data from API
            db: Database instance
        """
        try:
            card_id = card_data.get('id')
            attrs = card_data.get('attributes', {})
            
            self.logger.info(f"Processing card: {attrs.get('title')} ({attrs.get('cardUid')})")
            
            # Process related entities first
            type_id = None
            if 'type' in attrs and attrs['type'].get('data'):
                type_data = attrs['type']['data']['attributes']
                type_data['id'] = attrs['type']['data']['id']
                type_id = db.insert_type(type_data)
            
            type2_id = None
            if 'type2' in attrs and attrs['type2'].get('data'):
                type2_data = attrs['type2']['data']['attributes']
                type2_data['id'] = attrs['type2']['data']['id']
                type2_id = db.insert_type(type2_data)
            
            rarity_id = None
            if 'rarity' in attrs and attrs['rarity'].get('data'):
                rarity_data = attrs['rarity']['data']['attributes']
                rarity_data['id'] = attrs['rarity']['data']['id']
                rarity_id = db.insert_rarity(rarity_data)
            
            expansion_id = None
            if 'expansion' in attrs and attrs['expansion'].get('data'):
                expansion_data = attrs['expansion']['data']['attributes']
                expansion_data['id'] = attrs['expansion']['data']['id']
                expansion_id = db.insert_expansion(expansion_data)
            
            # Prepare card data
            card_record = {
                'id': card_id,
                'cardNumber': attrs.get('cardNumber'),
                'title': attrs.get('title'),
                'subtitle': attrs.get('subtitle'),
                'cardCount': attrs.get('cardCount'),
                'artist': attrs.get('artist'),
                'artFrontHorizontal': attrs.get('artFrontHorizontal'),
                'artBackHorizontal': attrs.get('artBackHorizontal'),
                'hasFoil': attrs.get('hasFoil'),
                'cost': attrs.get('cost'),
                'hp': attrs.get('hp'),
                'power': attrs.get('power'),
                'upgradeHp': attrs.get('upgradeHp'),
                'upgradePower': attrs.get('upgradePower'),
                'text': attrs.get('text'),
                'textStyled': attrs.get('textStyled'),
                'deployBox': attrs.get('deployBox'),
                'deployBoxStyled': attrs.get('deployBoxStyled'),
                'epicAction': attrs.get('epicAction'),
                'epicActionStyled': attrs.get('epicActionStyled'),
                'rules': attrs.get('rules'),
                'rulesStyled': attrs.get('rulesStyled'),
                'linkHtml': attrs.get('linkHtml'),
                'cardUid': attrs.get('cardUid'),
                'serialCode': attrs.get('serialCode'),
                'locale': attrs.get('locale'),
                'hyperspace': attrs.get('hyperspace'),
                'unique': attrs.get('unique'),
                'showcase': attrs.get('showcase'),
                'validationId': attrs.get('validationId'),
                'createdAt': attrs.get('createdAt'),
                'updatedAt': attrs.get('updatedAt'),
                'publishedAt': attrs.get('publishedAt'),
                'type_id': type_id,
                'type2_id': type2_id,
                'rarity_id': rarity_id,
                'expansion_id': expansion_id
            }
            
            # Insert card
            inserted_id = db.insert_card(card_record)
            
            # Process aspects
            if 'aspects' in attrs and attrs['aspects'].get('data'):
                for aspect in attrs['aspects']['data']:
                    aspect_data = aspect['attributes']
                    aspect_data['id'] = aspect['id']
                    aspect_id = db.insert_aspect(aspect_data)
                    db.link_card_aspect(inserted_id, aspect_id)
            
            # Process traits
            if 'traits' in attrs and attrs['traits'].get('data'):
                for trait in attrs['traits']['data']:
                    trait_data = trait['attributes']
                    trait_data['id'] = trait['id']
                    sql = "INSERT INTO traits (id, name, description, locale, created_at, updated_at, published_at) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name"
                    db.cursor.execute(sql, (trait_data.get('id'), trait_data.get('name'), trait_data.get('description'), trait_data.get('locale'), trait_data.get('createdAt'), trait_data.get('updatedAt'), trait_data.get('publishedAt')))
                    db.cursor.execute("INSERT OR IGNORE INTO card_traits (card_id, trait_id) VALUES (?, ?)", (inserted_id, trait['id']))
            
            # Process arenas
            if 'arenas' in attrs and attrs['arenas'].get('data'):
                for arena in attrs['arenas']['data']:
                    arena_data = arena['attributes']
                    sql = "INSERT INTO arenas (id, name, description, locale, created_at, updated_at, published_at) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name"
                    db.cursor.execute(sql, (arena['id'], arena_data.get('name'), arena_data.get('description'), arena_data.get('locale'), arena_data.get('createdAt'), arena_data.get('updatedAt'), arena_data.get('publishedAt')))
                    db.cursor.execute("INSERT OR IGNORE INTO card_arenas (card_id, arena_id) VALUES (?, ?)", (inserted_id, arena['id']))
            
            # Process keywords
            if 'keywords' in attrs and attrs['keywords'].get('data'):
                for keyword in attrs['keywords']['data']:
                    keyword_data = keyword['attributes']
                    sql = "INSERT INTO keywords (id, name, description, locale, created_at, updated_at, published_at) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name"
                    db.cursor.execute(sql, (keyword['id'], keyword_data.get('name'), keyword_data.get('description'), keyword_data.get('locale'), keyword_data.get('createdAt'), keyword_data.get('updatedAt'), keyword_data.get('publishedAt')))
                    db.cursor.execute("INSERT OR IGNORE INTO card_keywords (card_id, keyword_id) VALUES (?, ?)", (inserted_id, keyword['id']))
            
            # Process variant types
            if 'variantTypes' in attrs and attrs['variantTypes'].get('data'):
                for variant in attrs['variantTypes']['data']:
                    variant_data = variant['attributes']
                    icon_url = None
                    if 'icon' in variant_data and variant_data['icon'].get('data'):
                        icon_url = variant_data['icon']['data']['attributes'].get('url')
                    
                    sql = """INSERT INTO variant_types (id, name, description, variant_id, foil, sort_value, icon_url, locale, created_at, updated_at, published_at) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name"""
                    db.cursor.execute(sql, (variant['id'], variant_data.get('name'), variant_data.get('description'), variant_data.get('variantId'), 
                                          variant_data.get('foil'), variant_data.get('sortValue'), icon_url, variant_data.get('locale'), 
                                          variant_data.get('createdAt'), variant_data.get('updatedAt'), variant_data.get('publishedAt')))
                    db.cursor.execute("INSERT OR IGNORE INTO card_variant_types (card_id, variant_type_id) VALUES (?, ?)", (inserted_id, variant['id']))
            
            # Process images
            if 'artFront' in attrs:
                self._process_card_images(inserted_id, attrs.get('cardUid'), attrs['artFront'], 'front', db)
            if 'artBack' in attrs:
                self._process_card_images(inserted_id, attrs.get('cardUid'), attrs['artBack'], 'back', db)
            if 'artThumbnail' in attrs:
                self._process_card_images(inserted_id, attrs.get('cardUid'), attrs['artThumbnail'], 'thumbnail', db)
            
            # Process localizations
            if 'localizations' in attrs and attrs['localizations'].get('data'):
                for localization in attrs['localizations']['data']:
                    loc_attrs = localization['attributes']
                    sql = """INSERT INTO card_localizations (id, card_id, locale, title, subtitle, text, text_styled, deploy_box, deploy_box_styled, epic_action, epic_action_styled, rules, rules_styled)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                    db.cursor.execute(sql, (localization['id'], inserted_id, loc_attrs.get('locale'), loc_attrs.get('title'), 
                                          loc_attrs.get('subtitle'), loc_attrs.get('text'), loc_attrs.get('textStyled'),
                                          loc_attrs.get('deployBox'), loc_attrs.get('deployBoxStyled'), loc_attrs.get('epicAction'),
                                          loc_attrs.get('epicActionStyled'), loc_attrs.get('rules'), loc_attrs.get('rulesStyled')))
            
            db.conn.commit()
            self.stats['cards_processed'] += 1
            self.stats['cards_inserted'] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to process card {card_id}: {e}", exc_info=True)
            self.stats['errors'] += 1
    
    def scrape_all_cards(self):
        """Scrape all cards from the API"""
        self.logger.info("Starting card scraping process...")
        
        with Database() as db:
            page = 1
            total_pages = None
            
            while True:
                self.logger.info(f"Fetching page {page}...")
                url = self._build_api_url(page)
                response = self._make_request(url)
                
                if not response:
                    self.logger.error(f"Failed to fetch page {page}")
                    break
                
                # Get pagination info
                meta = response.get('meta', {})
                pagination = meta.get('pagination', {})
                total_pages = pagination.get('pageCount', 1)
                total_cards = pagination.get('total', 0)
                
                self.logger.info(f"Page {page}/{total_pages} - Total cards: {total_cards}")
                
                # Process cards on this page
                cards = response.get('data', [])
                if not cards:
                    self.logger.info("No more cards found")
                    break
                
                for card in cards:
                    self._process_card(card, db)
                
                # Check if we're done
                if page >= total_pages:
                    self.logger.info("All pages processed")
                    break
                
                page += 1
        
        # Print statistics
        self._print_statistics()
    
    def _print_statistics(self):
        """Print scraping statistics"""
        self.logger.info("=" * 60)
        self.logger.info("SCRAPING COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Cards processed: {self.stats['cards_processed']}")
        self.logger.info(f"Cards inserted: {self.stats['cards_inserted']}")
        self.logger.info(f"Images downloaded: {self.stats['images_downloaded']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info("=" * 60)


if __name__ == "__main__":
    scraper = SWUCardScraper()
    
    print("=" * 60)
    print("Star Wars Unlimited Card Scraper")
    print("=" * 60)
    print("\nThis scraper will:")
    print("- Fetch all cards from the official API")
    print("- Store card data in the SQLite database")
    if scraper.download_images:
        print(f"- Download card images to: {scraper.images_dir}")
    print("\nReady to start? Press Ctrl+C to cancel, or")
    input("Press Enter to begin scraping...")
    
    scraper.scrape_all_cards()
