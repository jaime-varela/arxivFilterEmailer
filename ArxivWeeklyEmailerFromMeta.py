import feedparser
import json
import os
from utils.html_parsing import EntryMatch,construct_entry_text, MatchType
from utils.arg_generator import get_default_args
from utils.html_parsing import sendHtmlEmailFromGoogleAccount
from utils.html_parsing import construct_email_from_saved_entry_list
from utils.file_handling import append_to_pickled_array
from utils.html_parsing import match_type_to_description
from config import emailInformation
import pickle
import datetime

baseUrl = "https://rss.arxiv.org/rss/"

args = get_default_args()
metaFileName = args.filter_file


# Get the current date
today = datetime.date.today()

# Get the day of the week (0=Monday, 6=Sunday)
day_of_week = today.weekday()

DAY_OF_WEEK_TO_SEND = 6 # sending on sunday

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



with open(metaFileName) as json_file:
    ArxivMetas = json.load(json_file)

arxiv_topic_no_paper_count = 0

for arxivMeta in ArxivMetas:
    #### ---------------- Feed import and email message creation ------------------
    arxivSite = arxivMeta['arxivSite']

    words = arxivMeta['words']
    authors = arxivMeta['authors']

    ### ------ filter ----------------------------------
    siteUrl = baseUrl + arxivSite
    feed = feedparser.parse(siteUrl)
    ArxivEntries = feed.entries
    filtered_entries = []
    for entry in ArxivEntries:
        matchType = EntryMatch(entry,words,authors)
        if(matchType != MatchType.NONE):
            filtered_entries.append({'site': arxivSite,
                                     'match': match_type_to_description(matchType),
                                     'entry':entry})
    file_to_append = f'data/{arxivSite}_entries.pkl'
    append_to_pickled_array(file_to_append,filtered_entries)


if day_of_week == DAY_OF_WEEK_TO_SEND:

    for arxivMeta in ArxivMetas:
        arxivSite = arxivMeta['arxivSite']

        words = arxivMeta['words']
        authors = arxivMeta['authors']

        # load the entries
        file_to_load = f'data/{arxivSite}_entries.pkl'
        with open(file_to_load,'rb') as f:
            matched_entries = pickle.load(f)
        
        author_match_entries = [entry for entry in matched_entries if entry['match'] == 'author']
        word_match_entries = [entry for entry in matched_entries if entry['match'] != 'author']

        if len(author_match_entries) > 0:
            html_entry, plain_text_entry = construct_email_from_saved_entry_list(author_match_entries,words,authors)
            subject = f'Filtered author matches for {arxivSite}'
        else:
            subject = f"No author matches found for {arxivSite} arxiv topic"
            plain_text_entry = f"No author matches found for {arxivSite} arxiv topic"
            html_entry = f"<b>No author matches found for {arxivSite} arxiv topic</b>"
        sendHtmlEmailFromGoogleAccount(toEmail=emailInformation['toEmail'],
                                   fromEmail=emailInformation['fromEmail'],
                                   subject=subject,
                                   plainText=plain_text_entry,
                                   htmlText=html_entry,
                                   username=emailInformation['username'],
                                   password=emailInformation['password'])


        if len(word_match_entries) > 0:
            html_entry, plain_text_entry = construct_email_from_saved_entry_list(word_match_entries,words,authors)
            subject = f'Filtered matches for {arxivSite}'
        else:
            subject = f"No keyword matches found for {arxivSite} arxiv topic"
            plain_text_entry = f"No keyword matches found for {arxivSite} arxiv topic"
            html_entry = f"<b>No keyword matches found for {arxivSite} arxiv topic</b>"
        sendHtmlEmailFromGoogleAccount(toEmail=emailInformation['toEmail'],
                                   fromEmail=emailInformation['fromEmail'],
                                   subject=subject,
                                   plainText=plain_text_entry,
                                   htmlText=html_entry,
                                   username=emailInformation['username'],
                                   password=emailInformation['password'])

        # remove the file to start fresh
        os.remove(file_to_load)

