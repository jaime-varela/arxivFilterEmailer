# ------------------- Imports ------------------------------------------------

import feedparser
import json

from utils.html_parsing import html_to_text
from utils.arg_generator import get_similarity_args
from utils.html_parsing import sendHtmlEmailFromGoogleAccount
from similarity.embedding_utils import get_mean_pooled_embeddings
from utils.html_parsing import construct_similarity_entry
from config import emailInformation
import arxiv
import datetime
from transformers import *
import re
import nltk
nltk.download('punkt')
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

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
num_sim = int(settings['num_similar_sentences'])

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

    found_target_entry_pairs = []
    for target_ind in range(len(title_targets)):
        for entry_ind in range(len(title_entries)):
            entry_title_embedding = entry_title_embedding_list[entry_ind]
            target_title_embedding = target_title_embedding_list[target_ind]
            entry_title = title_entries[entry_ind]
            target_title = title_targets[target_ind]

            counter += 1
            title_similarity = cosine_similarity(entry_title_embedding,target_title_embedding)[0,0]
            title_above_threshold = title_similarity > tau_title

            entry_sent_embed = entry_summary_embedding_list[entry_ind]
            target_sent_embed = target_summary_embedding_list[target_ind]
            sentence_sim_target_entry = cosine_similarity(target_sent_embed \
                                                          ,entry_sent_embed)
            # Find the indices with the highest similarity for each row in the matrix
            highest_similarity_indices_title_target = np.argmax(sentence_sim_target_entry, axis=1)
            target_indexes = np.arange(target_sent_embed.shape[0])

            scores_with_indexes = [(sentence_sim_target_entry[i,j],i,j) for i,j in zip(target_indexes,highest_similarity_indices_title_target)]
            # Sort values
            sorted_scores_with_indexes = sorted(scores_with_indexes, key=lambda x: x[0], reverse=True)
            target_num_sent = target_sent_embed.shape[0]
            entry_num_sent = entry_sent_embed.shape[0]
            sentence_subset = sorted_scores_with_indexes[0:min(num_sim,min(entry_num_sent,target_num_sent))]
            top_k_score = np.mean(np.array([score for score,i,j in sentence_subset]))
            sentences_above_threshold = top_k_score > tau_sen

            is_similar_paper = (title_above_threshold and sentences_above_threshold) \
                if use_and else (title_above_threshold or sentences_above_threshold) 
        
            if is_similar_paper:
                found_target_entry_pairs.append((target_ind,entry_ind))

    print(f'found {len(found_target_entry_pairs)} for site {arxivSite}')  
    entries_found = len(found_target_entry_pairs) > 0
    if entries_found:
        html_result  = """\
        <html>
          <head>
              <style>
                table {{
                  width: 100%;
                  border-collapse: collapse;
                }}
            
                td {{
                  padding: 10px;
                  border: 1px solid black;
                }}
              </style>          
          </head>
          <body>
        """
        text_result = ""

        html_result += f'<h1> Similarity Results for {arxivSite}</h1>'
        text_result += f'Similarity Results for {arxivSite}\n'
    for target_ind, entry_ind in found_target_entry_pairs:

        title_target = title_targets[target_ind]
        summary_target = summary_targets[target_ind]   
        title_entry = title_entries[entry_ind]
        summary_entry = summary_entries[entry_ind]

        html_temp ,text_temp = construct_similarity_entry(title_entry,
                                                        summary_entry,
                                                        title_target,
                                                        summary_target)
        html_result += html_temp
        text_result += text_temp

    if entries_found:
        html_result += """</body>
        </html>"""

        sendHtmlEmailFromGoogleAccount(toEmail=emailInformation['toEmail'],
            fromEmail=emailInformation['fromEmail'],
            subject="Similarity Filter for Arxiv " + arxivSite,
            plainText=text_result,
            htmlText=html_result,
            username=emailInformation['username'],
            password=emailInformation['password'])



# TODO: construct email
