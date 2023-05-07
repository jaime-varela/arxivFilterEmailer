# ------------------- Imports ------------------------------------------------

import feedparser
import json

from utils.html_parsing import wrapWordsInTags, htmlBoldWordsInText, strip_html
from utils.arg_generator import get_similarity_args
from utils.html_parsing import sendHtmlEmailFromGoogleAccount
from config import emailInformation


baseUrl = "http://export.arxiv.org/rss/"

args = get_similarity_args()
similarityFileName = args.similarity_file

# ------------------- get and update similarity json ---------------------------------
if args.use_dropbox:
    # remove old meta file
    import os
    from config import dropboxInfo
    from utils.dropbox import download_dropbox_file
    os.remove(similarityFileName)
    status = download_dropbox_file(dropbox_path = "/"+similarityFileName, 
                                   target_file = similarityFileName
                                   ,token = dropboxInfo['token'])


ArxivSimilarity = {}

with open(similarityFileName) as json_file:
    ArxivSimilarity = json.load(json_file)

settings = ArxivSimilarity['settings']

ArxivSimilarities = ArxivSimilarity['similarity_searches']

tau_title = float(settings['title_similarity_threshold'])
tau_sen = float(settings['sentence_similarity_threshold'])
use_and = settings['and_conditional']



# TODO: pull abstract and title for url link
# TODO: check the validity of url
# TODO: make utils to abstract away the similarity scoring