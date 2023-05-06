# ------------------- Imports ------------------------------------------------

import feedparser
import json

from utils.html_parsing import wrapWordsInTags, htmlBoldWordsInText, strip_html
from utils.arg_generator import get_default_args
from utils.html_parsing import sendHtmlEmailFromGoogleAccount
from config import emailInformation

# ------------------- Set base metadata here ---------------------------------
baseUrl = "http://export.arxiv.org/rss/"

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

with open(metaFileName) as json_file:
    ArxivMetas = json.load(json_file)

from enum import Enum
class MatchType(Enum):
    AUTHOR=1
    TITLE=2
    SUMMARY=3
    NONE=4

## filters
def EntryMatch(entry,words,authors):
    # author has the highest priority
    if(any(entry['author'].find(author) > 0 for author in authors)): return MatchType.AUTHOR
    if(any(entry['title'].lower().find(word.lower()) > 0 for word in words)): return MatchType.TITLE
    if(any(entry['summary'].lower().find(word.lower()) > 0 for word in words)): return MatchType.SUMMARY
    return MatchType.NONE



for arxivMeta in ArxivMetas:
    #### ---------------- Feed import and email message creation ------------------
    arxivSite = arxivMeta['arxivSite']

    words = arxivMeta['words']
    authors = arxivMeta['authors']

    ### ------ filter ----------------------------------
    siteUrl = baseUrl + arxivSite + "/new"
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
            TITLE = entry['title'][0:entry['title'].find("(arXiv:")]
            result += TITLE + "\n \t"
            sep = ", "
            entryAuthors = entry['author'].split(sep)
            entryAuthors = [strip_html(entry) for entry in entryAuthors]
            result += sep.join(entryAuthors) + "\n \n"
            result += entry['summary'][3:-4] + "\n \n"
            ## html entry
            html += """<div>"""
            html += """<p style="color:blue;font-size:1.17em;"><b><a href=\"""" + entry['id'] + """\">""" + wrapWordsInTags(TITLE, words,"""<span style="color:darkblue">""","""</span>""") + """</a></b></p>"""
            if(matchType != MatchType.AUTHOR):
                html += """<p><i>""" + sep.join(entryAuthors) + """<i></p><br>"""
            else:
                html += """<p><i>"""
                for authName in entryAuthors:
                    if any(authName.find(author) >= 0 for author in authors):
                        html += """<b>""" + authName + """</b>""" + " , "
                    else:
                        html += authName + " , "
                html = html[:len(html)-2]
                html +=  """<i></p><br>"""
            html += """<p>""" + htmlBoldWordsInText(entry['summary'][3:-4], words)+ """</p>"""
            html += """<br><br></div>"""

    html += """</body>
    </html>"""

    #### ------- e-mail generation ---------------------
    if result == "":
        print("no articles found for " + arxivSite)
        continue

    text = result

    sendHtmlEmailFromGoogleAccount(toEmail=emailInformation['toEmail'],
    fromEmail=emailInformation['fromEmail'],
    subject="Filtered Arxiv " + arxivSite,
    plainText=result,
    htmlText=html,
    username=emailInformation['username'],
    password=emailInformation['password'])