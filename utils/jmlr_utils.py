import os
import json
from html import escape
import pickle

def load_previous_links(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)
    return set()

def save_links(links, file_path):
    with open(file_path, "wb") as f:
        pickle.dump(links, f)

def get_new_entries(current_entries, stored_links):
    return [entry for entry in current_entries if entry.link not in stored_links]


def format_jmlr_email_content(entries):
    if not entries:
        return None, None

    html = [
        "<html><body>",
        "<h2>New JMLR Publications</h2>",
        "<ul>"
    ]
    plain = ["New JMLR Publications:\n"]

    for entry in entries:
        title = entry.get("title", "No Title")
        link = entry.get("link", "")
        pub_date = entry.get("published", "No Date")
        summary = entry.get("summary", "")

        # HTML format
        html.append(f"<li><strong>{escape(title)}</strong><br>")
        html.append(f"<em>{escape(pub_date)}</em><br>")
        html.append(f"<a href='{link}'>{link}</a><br>")
        if summary:
            html.append(f"<p>{summary}</p>")
        html.append("</li><br>")

        # Plain text format
        plain.append(f"{title}\n{pub_date}\n{link}\n")
        if summary:
            plain.append(f"{summary}\n")
        plain.append("\n")

    html.append("</ul></body></html>")
    return "\n".join(html), "\n".join(plain)

