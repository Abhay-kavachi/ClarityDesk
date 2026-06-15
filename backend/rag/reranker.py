from sentence_transformers import CrossEncoder

class RerankerModel:
    _instance = None
    
    @classmethod
    def get_model(cls):
        if cls._instance is None:
            cls._instance = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        return cls._instance

def cross_encoder_rerank(question: str, candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []
        
    model = RerankerModel.get_model()
    
    # Prepare input pairs
    pairs = [[question, chunk["text"]] for chunk in candidates]
    
    # Get scores
    scores = model.predict(pairs)
    
    # Attach scores and sort
    reranked = []
    for i, candidate in enumerate(candidates):
        c = candidate.copy()
        c["rerank_score"] = float(scores[i])
        reranked.append(c)
        
    # Sort descending by rerank_score
    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    return reranked
