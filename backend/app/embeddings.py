# embeddings.py
from transformers import AutoTokenizer, AutoModel
import torch

class TransformersEmbedding:
    def __init__(self, model_name: str = "all-mini-lm-l6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model     = AutoModel.from_pretrained(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Tokenize + forward
        encodings = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            output = self.model(**encodings).last_hidden_state  # (batch, seq, dim)
        # Mean-pool along the seq dimension
        embeddings = output.mean(dim=1)
        return embeddings.cpu().tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
