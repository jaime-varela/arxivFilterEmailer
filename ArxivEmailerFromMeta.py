import feedparser
import json

from utils.html_parsing import EntryMatch,construct_entry_text, MatchType
from utils.arg_generator import get_default_args
from utils.html_parsing import sendHtmlEmailFromGoogleAccount
from config import emailInformation
import yaml

baseUrl = "https://rss.arxiv.org/rss/"

args = get_default_args()
metaFileName = args.filter_file


# ------------------- get and update metadata json ---------------------------------

if args.use_dropbox:
    # remove old meta file
    import os
    from config import dropboxInfo
    from utils.dropbox import download_dropbox_file
    os.remove(metaFileName)
    status = download_dropbox_file(dropbox_path = "/"+metaFileName, 
                                   target_file = metaFileName
                                   ,token = dropboxInfo['token'])


ArxivMetas = []

if str(metaFileName).endswith(".json"):
    with open(metaFileName) as json_file:
        ArxivMetas = json.load(json_file)
else:
    # assume Yaml as default
    with open(metaFileName) as f:
        ArxivYamlMetas = yaml.safe_load(f)
    ArxivMetas = ArxivYamlMetas['arxiv_sites']

arxiv_topic_no_paper_count = 0

for arxivMeta in ArxivMetas:
    #### ---------------- Feed import and email message creation ------------------
    arxivSite = arxivMeta['arxivSite']

    words = arxivMeta.get('words',[])
    authors = arxivMeta.get('authors',[])

    ### ------ filter ----------------------------------
    siteUrl = baseUrl + arxivSite
    feed = feedparser.parse(siteUrl)
    ArxivEntries = feed.entries

    result = ""
    html = """\
    <html>
      <head></head>
      <body>
    """

    for entry in ArxivEntries:
        matchType = EntryMatch(entry,words,authors)
        if(matchType != MatchType.NONE):
            html_entry, text_entry = construct_entry_text(entry,matchType,words=words,authors=authors)
            html += html_entry
            result += text_entry

    html += """</body>
    </html>"""

    #### ------- e-mail generation ---------------------
    if result == "":
        print("no articles found for " + arxivSite)
        arxiv_topic_no_paper_count += 1
        continue

    text = result

    sendHtmlEmailFromGoogleAccount(toEmail=emailInformation['toEmail'],
    fromEmail=emailInformation['fromEmail'],
    subject="Filtered Arxiv " + arxivSite,
    plainText=result,
    htmlText=html,
    username=emailInformation['username'],
    password=emailInformation['password'])


if arxiv_topic_no_paper_count == len(ArxivMetas):
    print("no articles found for any arxiv topic")

    sendHtmlEmailFromGoogleAccount(toEmail=emailInformation['toEmail'],
                                   fromEmail=emailInformation['fromEmail'],
                                   subject="No articles found for any arxiv topic",
                                   plainText="No articles found for any arxiv topic",
                                   htmlText="<b>No articles found for any arxiv topic</b>",
                                   username=emailInformation['username'],
                                   password=emailInformation['password'])
