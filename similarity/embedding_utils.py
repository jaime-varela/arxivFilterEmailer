import torch

def get_mean_pooled_embeddings(sentences,tokenizer,model):
    #Encode all sentences
    tokenized_sentences = tokenizer(sentences, truncation=True, padding=True)
    tokens_tensor = torch.tensor(tokenized_sentences['input_ids'])
    attention_mask = torch.tensor(tokenized_sentences['attention_mask'])
    encoded_layers = model(tokens_tensor,attention_mask=attention_mask)
    embeddings = encoded_layers.last_hidden_state

    mask = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
    masked_embeddings = embeddings * mask

    masked_embeddings = embeddings * mask

    summed = torch.sum(masked_embeddings, 1)

    summed_mask = torch.clamp(mask.sum(1), min=1e-9)

    mean_pooled = summed / summed_mask
    return mean_pooled.detach().numpy()