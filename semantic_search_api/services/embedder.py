from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")

def embed_text(text: str) -> list[float]:
    return model.encode(text).tolist()