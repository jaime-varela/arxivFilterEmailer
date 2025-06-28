import feedparser
import json
import os
from datetime import datetime
from html import escape

FEED_URL = "https://www.jmlr.org/jmlr.xml"
STORAGE_FILE = "stored_jmlr_feed.json"

def fetch_feed(url):
    return feedparser.parse(url)


def get_new_entries(current_entries, stored_entries):
    stored_ids = set(stored_entries.get("entry_ids", []))
    new_items = [entry for entry in current_entries if entry.id not in stored_ids]
    return new_items

