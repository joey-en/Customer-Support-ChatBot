import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

# Load precomputed document embeddings (Assuming embeddings.npy and documents.txt exist)
with open("documents.txt", "r", encoding="utf-8") as f:
    documents = f.readlines()

vectorizer = TfidfVectorizer(stop_words="english")
matrix = vectorizer.fit_transform(documents)
embeddings = matrix.astype(np.float32).toarray()
joblib.dump(vectorizer, "vectorizer.pkl")


def retrieve_top_k(query_embedding, embeddings, k=10):
    """Retrieve top-k most similar documents using cosine similarity."""
    similarities = cosine_similarity(query_embedding.reshape(1, -1), embeddings)[0]
    top_k_indices = similarities.argsort()[-k:][::-1]
    return [(documents[i], similarities[i]) for i in top_k_indices]

# Streamlit UI
st.title("Reuters tfidf document search")

# Input query
query = st.text_input("Enter your query:")

# Load or compute query embedding (Placeholder: Replace with actual embedding model)
def get_query_embedding(query):
    query_vec = vectorizer.transform([query]).astype(np.float32).toarray()
    return query_vec[0]

if st.button("Search"):
    query_embedding = get_query_embedding(query)
    results = retrieve_top_k(query_embedding, embeddings)
    # Display results
    st.write("### Top 10 Relevant Documents:")
    for doc, score in results:
        st.write(f"- **{doc.strip()}** (Score: {score:.4f})")

# ===== RUN WITH =====  
# streamlit run app.py
# =====================