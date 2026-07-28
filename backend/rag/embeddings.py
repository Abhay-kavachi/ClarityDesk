from sentence_transformers import SentenceTransformer


class EmbeddingsModel:
    _instance = None
    
    @classmethod
    def get_model(cls):
        if cls._instance is None:
            # We use all-MiniLM-L6-v2 as requested for Phase 4
            cls._instance = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._instance

def generate_embedding(text: str) -> list[float]:
    model = EmbeddingsModel.get_model()
    # Returns numpy array, convert to list
    return model.encode(text).tolist()

def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    model = EmbeddingsModel.get_model()
    embeddings = model.encode(texts)
    return [e.tolist() for e in embeddings]
