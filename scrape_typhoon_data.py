import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import time
from datetime import datetime

def create_database():
    """Create SQLite database and typhoon table"""
    conn = sqlite3.connect('typhoon.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS typhoons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            number INTEGER NOT NULL,
            japanese_name TEXT,
            english_name TEXT,
            start_date TEXT,
            end_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    return conn

def scrape_typhoon_year(year):
    """Scrape typhoon data for a specific year"""
    url = f"https://weathernews.jp/onebox/typhoon/{year}/"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Find all links containing typhoon information
        typhoon_links = soup.find_all('a', href=re.compile(r'/onebox/typhoon/\d+/\d+/'))

        typhoons = []

        for link in typhoon_links:
            text = link.get_text(strip=True)

            typhoon = None

            # Pattern 1: "2025年 台風1号 ウーティップ(WUTIP)2025/06/11 21:00〜2025/06/15 03:00"
            # New format with Japanese name and English name in parentheses
            pattern1 = r'(\d{4})年\s*台風(\d+)号\s*([^\(]+)\(([^\)]+)\)(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})〜(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})'
            match = re.search(pattern1, text)
            if match:
                typhoon = {
                    'year': int(match.group(1)),
                    'number': int(match.group(2)),
                    'japanese_name': match.group(3).strip(),
                    'english_name': match.group(4).strip(),
                    'start_date': match.group(5),
                    'end_date': match.group(6)
                }

            # Pattern 2: "1951年 台風11号 MARGE1951/08/11 09:00〜1951/08/24 21:00"
            # Old format with English name only (no parentheses)
            if not typhoon:
                pattern2 = r'(\d{4})年\s*台風(\d+)号\s*([A-Z]+)(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})〜(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})'
                match = re.search(pattern2, text)
                if match:
                    typhoon = {
                        'year': int(match.group(1)),
                        'number': int(match.group(2)),
                        'japanese_name': None,
                        'english_name': match.group(3).strip(),
                        'start_date': match.group(4),
                        'end_date': match.group(5)
                    }

            # Pattern 3: "1951年 台風1号 1951/02/20 09:00〜1951/02/21 15:00"
            # Old format with no name
            if not typhoon:
                pattern3 = r'(\d{4})年\s*台風(\d+)号\s*(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})〜(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})'
                match = re.search(pattern3, text)
                if match:
                    typhoon = {
                        'year': int(match.group(1)),
                        'number': int(match.group(2)),
                        'japanese_name': None,
                        'english_name': None,
                        'start_date': match.group(3),
                        'end_date': match.group(4)
                    }

            if typhoon:
                typhoons.append(typhoon)

        return typhoons

    except requests.RequestException as e:
        print(f"Error fetching data for year {year}: {e}")
        return []

def insert_typhoons(conn, typhoons):
    """Insert typhoon data into database"""
    cursor = conn.cursor()

    for typhoon in typhoons:
        cursor.execute('''
            INSERT INTO typhoons (year, number, japanese_name, english_name, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            typhoon['year'],
            typhoon['number'],
            typhoon['japanese_name'],
            typhoon['english_name'],
            typhoon['start_date'],
            typhoon['end_date']
        ))

    conn.commit()

def main():
    """Main function to scrape typhoon data from 1951 to 2025"""
    print("Creating database...")
    conn = create_database()

    start_year = 1951
    end_year = 2025

    total_typhoons = 0

    for year in range(start_year, end_year + 1):
        print(f"Scraping year {year}...", end=' ')

        typhoons = scrape_typhoon_year(year)

        if typhoons:
            insert_typhoons(conn, typhoons)
            total_typhoons += len(typhoons)
            print(f"Found {len(typhoons)} typhoons")
        else:
            print("No data found")

        # Be polite to the server
        time.sleep(1)

    conn.close()
    print(f"\nCompleted! Total typhoons collected: {total_typhoons}")

if __name__ == "__main__":
    main()
