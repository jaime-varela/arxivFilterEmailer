# Uses scibert: https://github.com/allenai/scibert
# and follows a sentence embedding approach as described : https://towardsdatascience.com/bert-for-measuring-text-similarity-eec91c6bf9e1

import torch
from transformers import *
import numpy as np
import json
from embedding_utils import get_mean_pooled_embeddings
import nltk
nltk.download('punkt')
from sklearn.metrics.pairwise import cosine_similarity
# Decide how many similar sentences to print
num_sim = 4

# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained('allenai/scibert_scivocab_uncased')
model = AutoModel.from_pretrained('allenai/scibert_scivocab_uncased')
# Put the model in "evaluation" mode, meaning feed-forward operation.
model.eval()

# Load the JSON files
with open('paper_anchor.json', 'r') as file:
    anchor_paper = json.load(file)
with open('paper_positive.json', 'r') as file:
    positive_paper = json.load(file)
with open('paper_negative.json', 'r') as file:
    negative_paper = json.load(file)

sentences_anchor = nltk.sent_tokenize(anchor_paper['abstract'])
sentences_positive = nltk.sent_tokenize(positive_paper['abstract'])
sentences_negative = nltk.sent_tokenize(negative_paper['abstract'])

# get the sentence embeddings
abstract_embeddings_anchor = get_mean_pooled_embeddings(sentences_anchor,tokenizer,model)
abstract_embeddings_positive = get_mean_pooled_embeddings(sentences_positive,tokenizer,model)
abstract_embeddings_negative = get_mean_pooled_embeddings(sentences_negative,tokenizer,model)

anchor_title = anchor_paper['title']
positive_title = positive_paper['title']
negative_title = negative_paper['title']
title_embeddings_anchor = get_mean_pooled_embeddings([anchor_title],tokenizer,model)
title_embeddings_positive = get_mean_pooled_embeddings([positive_title],tokenizer,model)
title_embeddings_negative = get_mean_pooled_embeddings([negative_title],tokenizer,model)

print('\n\n')
print("Abstract sentences shapes: anchor,positive,negative")
print(abstract_embeddings_anchor.shape,abstract_embeddings_positive.shape,abstract_embeddings_negative.shape)

print("Title sizes")
print(title_embeddings_anchor.shape,title_embeddings_positive.shape,title_embeddings_negative.shape)

print("Anchor and positive title similarity")
print(f'title similarity = {cosine_similarity(title_embeddings_anchor,title_embeddings_positive)[0,0]}')
print(f'anchor title: { anchor_title }')
print(f'positive title: { positive_title}')
print('\n')
print("Anchor and negative title similarity")
print(f'title similarity = {cosine_similarity(title_embeddings_anchor,title_embeddings_negative)[0,0]}')
print(f'anchor title: { anchor_title }')
print(f'negative title: { negative_title}')


sentence_sim_a_p = cosine_similarity(abstract_embeddings_anchor,abstract_embeddings_positive)
sentence_sim_a_n = cosine_similarity(abstract_embeddings_anchor,abstract_embeddings_negative) 

print(sentence_sim_a_p.shape)
print(sentence_sim_a_n.shape)

# Find the indices with the highest similarity for each row in the matrix
highest_similarity_indices_a_p = np.argmax(sentence_sim_a_p, axis=1)
highest_similarity_indices_a_n = np.argmax(sentence_sim_a_n,axis=1)
anchor_indexes = np.arange(abstract_embeddings_anchor.shape[0])

scores_with_indexes_a_p = [(sentence_sim_a_p[i,j],i,j) for i,j in zip(anchor_indexes,highest_similarity_indices_a_p)]
scores_with_indexes_a_n = [(sentence_sim_a_n[i,j],i,j) for i,j in zip(anchor_indexes,highest_similarity_indices_a_n)]

# Sort values
anchor_positive_combinations = sorted(scores_with_indexes_a_p, key=lambda x: x[0], reverse=True)
print(f'Top {num_sim} sentence pairs for anchor and positive')
score_sum = 0
for score,anchor_ind,positive_ind in anchor_positive_combinations[0:num_sim]:
    print(f'score: {score}')
    print(f'anchor sentence: {sentences_anchor[anchor_ind]}')
    print(f'positive sentence: {sentences_positive[positive_ind]}')
    print('\n')
    score_sum += score
print(f'average top {num_sim} score {score_sum/num_sim} \n')


anchor_negative_combinations = sorted(scores_with_indexes_a_n, key=lambda x: x[0], reverse=True)
print(f'Top {num_sim} sentence pairs for anchor and negative')
score_sum = 0
for score,anchor_ind,negative_ind in anchor_negative_combinations[0:num_sim]:
    print(f'score: {score}')
    print(f'anchor sentence: {sentences_anchor[anchor_ind]}')
    print(f'negative sentence: {sentences_negative[negative_ind]}')
    print('\n')
    score_sum += score

print(f'average top {num_sim} score {score_sum/num_sim} \n')
