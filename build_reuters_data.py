import sys
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

DOCS_PATH = "documents.txt"
EMBED_PATH = "embeddings.npy"
VECT_PATH = "vectorizer.pkl"

def download_reuters():
    try:
        import nltk
        from nltk.corpus import reuters
    except Exception as exc:
        print("NLTK is required. Install it with: pip install nltk", file=sys.stderr)
        raise SystemExit(1) from exc

    nltk.download("reuters")
    nltk.download("punkt")
    nltk.download("stopwords")
    try:
        nltk.download("punkt_tab")
    except Exception:
        pass

    docs = [reuters.raw(fid).replace("\n", " ").strip() for fid in reuters.fileids()]
    docs = [d for d in docs if d]
    if not docs:
        print("Reuters corpus is empty after download.", file=sys.stderr)
        raise SystemExit(1)
    return docs

def write_documents(docs, path):
    with open(path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(doc + "\n")

def build_embeddings(docs, embed_path, vect_path):
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(docs)
    embeddings = matrix.astype(np.float32).toarray()
    np.save(embed_path, embeddings)
    joblib.dump(vectorizer, vect_path)

def main():
    docs = download_reuters()
    write_documents(docs, DOCS_PATH)
    build_embeddings(docs, EMBED_PATH, VECT_PATH)
    print(f"Wrote {DOCS_PATH}, {EMBED_PATH}, and {VECT_PATH}.")

if __name__ == "__main__":
    main()
