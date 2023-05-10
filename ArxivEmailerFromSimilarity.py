# ------------------- Imports ------------------------------------------------

import feedparser
import json

from utils.html_parsing import html_to_text
from utils.arg_generator import get_similarity_args
from utils.html_parsing import sendHtmlEmailFromGoogleAccount
from similarity.embedding_utils import get_mean_pooled_embeddings
from config import emailInformation
import arxiv
import datetime
from transformers import *
import re
# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained('allenai/scibert_scivocab_uncased')
model = AutoModel.from_pretrained('allenai/scibert_scivocab_uncased')

# Set up

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


for similarity_check in ArxivSimilarities:
    id_list = [link.split('/')[-1] for link in similarity_check['papers']]
    paper_targets = list(arxiv.Search(id_list=id_list).results())

    title_targets = [paper_target.title for paper_target in paper_targets]
    summary_targets = [re.sub('\n', ' ', paper_target.summary) for paper_target in paper_targets]

    ### ------ filter ----------------------------------
    arxivSite = similarity_check['arxivSite']
    siteUrl = baseUrl + arxivSite + "/new"
    feed = feedparser.parse(siteUrl)
    ArxivEntries = feed.entries

    title_entries = [entry['title'][0:entry['title'].find("(arXiv:")].strip() for entry in ArxivEntries]
    summary_entries = [html_to_text(entry['summary']) for entry in ArxivEntries]

    embedded_title_targets = get_mean_pooled_embeddings(title_targets,tokenizer,model)
    embedded_title_entries = get_mean_pooled_embeddings(title_entries,tokenizer,model)

    # TODO sentence embeddings

    print(embedded_title_targets.shape,embedded_title_entries.shape)
# TODO: make utils to abstract away the similarity scoring
# TODO: construct email
# TODO: reduce memory for edge devices