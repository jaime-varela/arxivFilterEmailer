import feedparser
import pickle
import os
from utils.jmlr_utils import load_previous_links,save_links,get_new_entries
from utils.jmlr_utils import format_jmlr_email_content
from utils.feed_handling import fetch_feed
from utils.html_parsing import sendHtmlEmailFromGoogleAccount
from config import emailInformation

FEED_URL = "https://www.jmlr.org/jmlr.xml"
STORAGE_FILE = "jmlr_data/stored_jmlr_feed.pkl"


def main():
    feed = fetch_feed(FEED_URL)
    current_entries = feed.entries
    stored_links = load_previous_links(STORAGE_FILE)

    new_entries = get_new_entries(current_entries, stored_links)

    if new_entries:
        html_body, text_body = format_jmlr_email_content(new_entries)

        # Save updated set of links
        all_links = {entry.link for entry in current_entries}
        save_links(all_links, STORAGE_FILE)

        return html_body, text_body
    else:
        print("No new entries found.")
        return None, None

if __name__ == "__main__":
    html_email, text_email = main()
    if html_email:
        print("HTML Email Preview:\n", html_email[:500])
        print("\nPlain Text Preview:\n", text_email[:500])
        sendHtmlEmailFromGoogleAccount(toEmail=emailInformation['toEmail'],
                                   fromEmail=emailInformation['fromEmail'],
                                   subject="JMLR Recent Articles",
                                   plainText=text_email,
                                   htmlText=html_email,
                                   username=emailInformation['username'],
                                   password=emailInformation['password'])
    else:
        print("No new articles found")
    
