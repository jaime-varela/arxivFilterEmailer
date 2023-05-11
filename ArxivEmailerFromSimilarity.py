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
import nltk
nltk.download('punkt')
from sklearn.metrics.pairwise import cosine_similarity


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

counter = 0
for similarity_check in ArxivSimilarities:
    id_list = [link.split('/')[-1] for link in similarity_check['papers']]
    paper_targets = list(arxiv.Search(id_list=id_list).results())

    title_targets = [paper_target.title for paper_target in paper_targets]
    summary_targets = [re.sub('\n', ' ', paper_target.summary) for paper_target in paper_targets]
    assert(len(title_targets) == len(summary_targets))
    ### ------ filter ----------------------------------
    arxivSite = similarity_check['arxivSite']
    siteUrl = baseUrl + arxivSite + "/new"

    feed = feedparser.parse(siteUrl)
    ArxivEntries = feed.entries
    print(len(ArxivEntries),len(title_targets))
    title_entries = [entry['title'][0:entry['title'].find("(arXiv:")].strip() for entry in ArxivEntries]
    summary_entries = [html_to_text(entry['summary']) for entry in ArxivEntries]
    assert(len(title_entries) == len(summary_entries))
    print(f'{arxivSite} number of entries = {len(title_entries)}')

    target_title_embedding_list = []
    target_summary_embedding_list = []
    for target_ind in range(len(title_targets)):
        target_title = title_targets[target_ind]
        target_abstract = summary_targets[target_ind]
        target_sentences = nltk.sent_tokenize(target_abstract)
        target_title_embedding = get_mean_pooled_embeddings([target_title],tokenizer,model)
        target_sentence_embeddings = get_mean_pooled_embeddings(target_sentences,tokenizer,model)
        target_title_embedding_list.append(target_title_embedding)
        target_summary_embedding_list.append(target_sentence_embeddings)

    entry_title_embedding_list = []
    entry_summary_embedding_list = []
    for entry_ind in range(len(title_entries)):
        entry_title = title_entries[entry_ind]
        entry_abstract = summary_entries[entry_ind]
        entry_sentences = nltk.sent_tokenize(entry_abstract)
        entry_title_embedding = get_mean_pooled_embeddings([entry_title],tokenizer,model)
        entry_sentence_embeddings = get_mean_pooled_embeddings(entry_sentences,tokenizer,model)
        entry_title_embedding_list.append(entry_title_embedding)
        entry_summary_embedding_list.append(entry_sentence_embeddings)

    for target_ind in range(len(title_targets)):
        for entry_ind in range(len(title_entries)):
            entry_title_embedding = entry_title_embedding_list[entry_ind]
            target_title_embedding = target_title_embedding_list[target_ind]
            entry_title = title_entries[entry_ind]
            target_title = title_targets[target_ind]
            print("Anchor and positive title similarity")
            print(f'target: {target_title}')
            print(f'entry: {entry_title}')
            print(f'title similarity = {cosine_similarity(entry_title_embedding,target_title_embedding)[0,0]}')
            counter += 1

print(f'count = {counter}')            





# TODO: make utils to abstract away the similarity scoring
# TODO: construct email
# TODO: improve performance?  May not matter if we're willing to wait
# TODO: reduce memory for edge devices