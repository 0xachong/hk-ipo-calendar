#!/usr/bin/env python3
"""Build ipo.ics from data/ipo.json"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from ics import Calendar, Event, DisplayAlarm

HKT = timezone(timedelta(hours=8))


def date_to_dt(date_str, hour, minute):
    y, m, d = map(int, date_str.split("-"))
    return datetime(y, m, d, hour, minute, tzinfo=HKT)


def make_event(uid, title, when, duration_min, description, alarm_minutes):
    e = Event()
    e.uid = uid
    e.name = title
    e.begin = when
    e.duration = timedelta(minutes=duration_min)
    e.description = description
    for m in alarm_minutes:
        e.alarms.append(DisplayAlarm(trigger=timedelta(minutes=-m), display_text=title))
    return e


def build(ipos):
    cal = Calendar()
    for ipo in ipos:
        code = ipo["code"]
        name = ipo["name"]
        lines = [f"代號: {code}.HK", f"名稱: {name}"]
        if ipo.get("industry"): lines.append(f"行業: {ipo[\"industry\"]}")
        if ipo.get("price"): lines.append(f"招股價: {ipo[\"price\"]}")
        if ipo.get("lot_size"): lines.append(f"每手: {ipo[\"lot_size\"]}")
        if ipo.get("entry_fee"): lines.append(f"入場費: {ipo[\"entry_fee\"]}")
        lines.append("資料: AAStocks")
        info = "\n".join(lines)

        if ipo.get("subscription_end_date"):
            cal.events.add(make_event(
                uid=f"ipo-{code}-sub-end@hkipo",
                title=f"招股截止: {name} ({code})",
                when=date_to_dt(ipo["subscription_end_date"], 12, 0),
                duration_min=30,
                description=info,
                alarm_minutes=[240, 30],
            ))
        if ipo.get("dark_pool_date"):
            cal.events.add(make_event(
                uid=f"ipo-{code}-dark@hkipo",
                title=f"暗盤: {name} ({code})",
                when=date_to_dt(ipo["dark_pool_date"], 16, 15),
                duration_min=135,
                description=info,
                alarm_minutes=[30],
            ))
        if ipo.get("listing_date"):
            cal.events.add(make_event(
                uid=f"ipo-{code}-list@hkipo",
                title=f"上市: {name} ({code})",
                when=date_to_dt(ipo["listing_date"], 9, 30),
                duration_min=30,
                description=info,
                alarm_minutes=[30],
            ))
    return cal


def main():
    in_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/ipo.json")
    out_path = Path(sys.argv[2] if len(sys.argv) > 2 else "ipo.ics")
    ipos = json.loads(in_path.read_text())
    cal = build(ipos)
    out_path.write_text(str(cal))
    print(f"wrote {out_path}: {len(cal.events)} events from {len(ipos)} IPOs")


if __name__ == "__main__":
    main()
