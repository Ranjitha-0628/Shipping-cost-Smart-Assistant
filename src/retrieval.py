import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
TOP_K = 6


class NoteRetriever:
    def __init__(self, notes):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is required to use NoteRetriever. Install it with: pip install sentence-transformers")

        self.notes = notes.reset_index(drop=True)
        self.model = SentenceTransformer(MODEL_NAME)
        docs = (self.notes["applies_to"] + ". " + self.notes["note"]).tolist()
        self.doc_vecs = self.model.encode(docs, normalize_embeddings=True)

    def search(self, route, week_of, k=TOP_K):
        query = QUERY_PREFIX + f"Why did freight cost rise on the {route} route in the week of {week_of:%d %B %Y}?"
        q = self.model.encode([query], normalize_embeddings=True)[0]
        scores = np.round(self.doc_vecs @ q, 6)
        order = sorted(range(len(scores)), key=lambda i: (-scores[i], self.notes.loc[i, "note_id"]))
        return [self.notes.iloc[i] for i in order[:k]]

    