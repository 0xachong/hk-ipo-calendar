#!/usr/bin/env python3
"""Fetch HK IPO calendar from AAStocks → data/ipo.json"""
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.aastocks.com/tc/stocks/market/ipo/upcomingipo/company-summary"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.aastocks.com/tc/stocks/market/ipo/",
}


def parse_company_cell(text):
    m = re.search(r"^(.+?)\s+(\d{4,5})\.HK", text)
    if not m:
        return text.strip(), ""
    return m.group(1).strip(), m.group(2)


def parse_date(s):
    s = s.strip()
    if not s or s == "-" or s.upper() == "N/A":
        return None
    m = re.match(r"(\d{4})/(\d{1,2})/(\d{1,2})", s)
    if not m:
        return None
    y, mo, d = m.groups()
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def find_upcoming_table(soup):
    for t in soup.find_all("table"):
        rows = t.find_all("tr")
        if not rows:
            continue
        head = " ".join(c.get_text(" ", strip=True) for c in rows[0].find_all(["td", "th"]))
        if "招股截止日" in head and "暗盤日期" in head and "上市日期" in head:
            return t
    return None


def parse(html):
    soup = BeautifulSoup(html, "lxml")
    table = find_upcoming_table(soup)
    if table is None:
        raise RuntimeError("upcoming-IPO table not found")
    out = []
    for row in table.find_all("tr")[1:]:
        cells = [c.get_text(" ", strip=True) for c in row.find_all("td")]
        if len(cells) < 9:
            continue
        name, code = parse_company_cell(cells[1])
        if not code:
            continue
        out.append({
            "code": code,
            "name": name,
            "industry": cells[2] or None,
            "price": cells[3] or None,
            "lot_size": cells[4] or None,
            "entry_fee": cells[5] or None,
            "subscription_end_date": parse_date(cells[6]),
            "dark_pool_date": parse_date(cells[7]),
            "listing_date": parse_date(cells[8]),
        })
    return out


def main():
    Path("data").mkdir(exist_ok=True)
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    Path("data/raw.html").write_text(r.text)

    data = parse(r.text)
    Path("data/ipo.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"parsed {len(data)} upcoming IPOs:")
    for ipo in data:
        print(f"  {ipo[\"code\"]} {ipo[\"name\"]}: end={ipo[\"subscription_end_date\"]} dark={ipo[\"dark_pool_date\"]} list={ipo[\"listing_date\"]}")
    if not data:
        print("WARNING: 0 IPOs parsed", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
