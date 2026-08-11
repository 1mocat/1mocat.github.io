#!/usr/bin/env python3
"""
Chromium Card Information Extractor
Extracts and processes card information from Chromium-based browsers
"""

import re
import sqlite3
import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import platform


class ChromiumCardExtractor:
    """Extract card information from Chromium-based browsers"""

    # Common Chromium browser paths
    BROWSER_PATHS = {
        'Windows': {
            'Chrome': os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google/Chrome/User Data'),
            'Edge': os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft/Edge/User Data'),
            'Brave': os.path.join(os.environ.get('LOCALAPPDATA', ''), 'BraveSoftware/Brave-Browser/User Data'),
            'Opera': os.path.join(os.environ.get('APPDATA', ''), 'Opera Software/Opera Stable'),
        },
        'Darwin': {  # macOS
            'Chrome': os.path.expanduser('~/Library/Application Support/Google/Chrome'),
            'Edge': os.path.expanduser('~/Library/Application Support/Microsoft Edge'),
            'Brave': os.path.expanduser('~/Library/Application Support/BraveSoftware/Brave-Browser'),
            'Opera': os.path.expanduser('~/Library/Application Support/com.operasoftware.Opera'),
        },
        'Linux': {
            'Chrome': os.path.expanduser('~/.config/google-chrome'),
            'Edge': os.path.expanduser('~/.config/microsoft-edge'),
            'Brave': os.path.expanduser('~/.config/BraveSoftware/Brave-Browser'),
            'Opera': os.path.expanduser('~/.config/opera'),
        }
    }

    def __init__(self):
        self.system = platform.system()
        self.card_patterns = {
            'card_number': r'\b(?:\d{4}[\s\-]?){3}\d{4}\b',  # 16 digit card numbers
            'expiry': r'\b(?:0[1-9]|1[0-2])[/\-](?:\d{2}|\d{4})\b',  # MM/YY or MM/YYYY
            'cvv': r'\b\d{3,4}\b',  # 3 or 4 digit CVV
        }

    def remove_hash_prefixes(self, text: str) -> str:
        """
        Remove hash prefixes and clean the text
        Removes patterns like #[...], #(...), etc.
        """
        # Remove #[...] patterns
        text = re.sub(r'#\[.*?\]', '', text)
        # Remove #(...) patterns
        text = re.sub(r'#\(.*?\)', '', text)
        # Remove standalone # symbols
        text = re.sub(r'#', '', text)
        return text.strip()

    def extract_card_numbers(self, text: str, remove_hashes: bool = True) -> List[str]:
        """
        Extract card numbers from text with optional hash removal
        """
        if remove_hashes:
            text = self.remove_hash_prefixes(text)

        matches = re.findall(self.card_patterns['card_number'], text)
        # Normalize card numbers (remove spaces and dashes)
        card_numbers = [re.sub(r'[\s\-]', '', match) for match in matches]
        return card_numbers

    def extract_expiry_dates(self, text: str) -> List[str]:
        """Extract expiry dates from text"""
        matches = re.findall(self.card_patterns['expiry'], text)
        return matches

    def extract_cvv(self, text: str) -> List[str]:
        """Extract CVV codes from text"""
        matches = re.findall(self.card_patterns['cvv'], text)
        return matches

    def validate_luhn(self, card_number: str) -> bool:
        """
        Validate card number using Luhn algorithm
        """
        def digits_of(n):
            return [int(d) for d in str(n)]

        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0

    def identify_card_type(self, card_number: str) -> str:
        """Identify card type based on number pattern"""
        card_number = re.sub(r'[\s\-]', '', card_number)

        patterns = {
            'Visa': r'^4[0-9]{12}(?:[0-9]{3})?$',
            'MasterCard': r'^5[1-5][0-9]{14}$|^2(?:2(?:2[1-9]|[3-9][0-9])|[3-6][0-9][0-9]|7(?:[01][0-9]|20))[0-9]{12}$',
            'American Express': r'^3[47][0-9]{13}$',
            'Discover': r'^6(?:011|5[0-9]{2})[0-9]{12}$',
            'Diners Club': r'^3(?:0[0-5]|[68][0-9])[0-9]{11}$',
            'JCB': r'^(?:2131|1800|35\d{3})\d{11}$',
        }

        for card_type, pattern in patterns.items():
            if re.match(pattern, card_number):
                return card_type
        return 'Unknown'

    def get_browser_db_path(self, browser: str, profile: str = 'Default') -> Optional[Path]:
        """Get the path to the browser's Web Data database"""
        if self.system not in self.BROWSER_PATHS:
            return None

        browser_paths = self.BROWSER_PATHS[self.system]
        if browser not in browser_paths:
            return None

        base_path = Path(browser_paths[browser])
        db_path = base_path / profile / 'Web Data'

        return db_path if db_path.exists() else None

    def extract_from_database(self, db_path: Path) -> List[Dict]:
        """
        Extract card information from Chromium Web Data database
        Note: Actual card numbers are encrypted in modern browsers
        """
        cards = []
        temp_db = Path(f"{db_path}.temp")

        try:
            # Copy database to avoid lock issues
            shutil.copy2(db_path, temp_db)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            # Query credit cards table
            cursor.execute("""
                SELECT name_on_card, expiration_month, expiration_year,
                       card_number_encrypted, date_modified
                FROM credit_cards
            """)

            for row in cursor.fetchall():
                card_info = {
                    'name_on_card': row[0],
                    'expiration_month': row[1],
                    'expiration_year': row[2],
                    'card_number_encrypted': '<encrypted>',  # Cannot decrypt without OS credentials
                    'date_modified': row[4],
                    'source': 'database'
                }
                cards.append(card_info)

            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if temp_db.exists():
                temp_db.unlink()

        return cards

    def extract_from_text(self, text: str) -> Dict:
        """
        Extract all card information from text
        """
        card_numbers = self.extract_card_numbers(text, remove_hashes=True)
        expiry_dates = self.extract_expiry_dates(text)
        cvv_codes = self.extract_cvv(text)

        results = {
            'card_numbers': [],
            'expiry_dates': expiry_dates,
            'cvv_codes': cvv_codes,
            'raw_text': text
        }

        for card_num in card_numbers:
            card_info = {
                'number': card_num,
                'masked': self.mask_card_number(card_num),
                'type': self.identify_card_type(card_num),
                'valid_luhn': self.validate_luhn(card_num)
            }
            results['card_numbers'].append(card_info)

        return results

    def mask_card_number(self, card_number: str, visible_digits: int = 4) -> str:
        """Mask card number showing only last N digits"""
        card_number = re.sub(r'[\s\-]', '', card_number)
        if len(card_number) <= visible_digits:
            return card_number
        masked = '*' * (len(card_number) - visible_digits) + card_number[-visible_digits:]
        return masked

    def search_browsers(self, browsers: Optional[List[str]] = None) -> Dict:
        """
        Search specified browsers for card information
        """
        if browsers is None:
            browsers = ['Chrome', 'Edge', 'Brave', 'Opera']

        results = {}
        for browser in browsers:
            db_path = self.get_browser_db_path(browser)
            if db_path:
                try:
                    cards = self.extract_from_database(db_path)
                    results[browser] = {
                        'found': len(cards),
                        'cards': cards,
                        'path': str(db_path)
                    }
                except Exception as e:
                    results[browser] = {
                        'error': str(e)
                    }
            else:
                results[browser] = {
                    'found': 0,
                    'message': 'Browser not found or database not accessible'
                }

        return results


def main():
    """Main function demonstrating usage"""
    extractor = ChromiumCardExtractor()

    # Example 1: Extract from text with hash symbols
    print("=" * 60)
    print("Example 1: Extract card info from text")
    print("=" * 60)

    sample_text = """
    Payment info: #[4532-1234-5678-9010]
    Expiry: 12/25
    CVV: #(123)
    Another card: 5425-2334-3010-9903 exp 06/2026
    """

    result = extractor.extract_from_text(sample_text)
    print(json.dumps(result, indent=2))

    # Example 2: Search browsers
    print("\n" + "=" * 60)
    print("Example 2: Search Chromium browsers")
    print("=" * 60)

    browser_results = extractor.search_browsers()
    print(json.dumps(browser_results, indent=2, default=str))

    # Example 3: Card validation
    print("\n" + "=" * 60)
    print("Example 3: Validate card numbers")
    print("=" * 60)

    test_cards = [
        "4532015112830366",  # Valid Visa
        "5425233430109903",  # Valid MasterCard
        "1234567890123456",  # Invalid
    ]

    for card in test_cards:
        card_type = extractor.identify_card_type(card)
        is_valid = extractor.validate_luhn(card)
        masked = extractor.mask_card_number(card)
        print(f"Card: {masked} | Type: {card_type} | Valid: {is_valid}")


if __name__ == "__main__":
    main()
