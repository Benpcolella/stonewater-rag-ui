import json
import os
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class VectorStore:
    """TF-IDF based vector store with JSON persistence."""

    def __init__(self, store_file: str = "vector_store.json"):
        self.store_file = store_file
        self.chunks = []
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.vectors = None
        self.load()

    def load(self):
        """Load vector store from JSON file."""
        if os.path.exists(self.store_file):
            try:
                with open(self.store_file, 'r') as f:
                    data = json.load(f)
                    self.chunks = data.get('chunks', [])
                    if self.chunks:
                        self._rebuild_vectors()
            except Exception as e:
                print(f"Error loading vector store: {e}")
                self.chunks = []

    def save(self):
        """Persist vector store to JSON file."""
        with open(self.store_file, 'w') as f:
            json.dump({'chunks': self.chunks}, f, indent=2)

    def _rebuild_vectors(self):
        """Rebuild TF-IDF vectors from stored chunks."""
        if not self.chunks:
            self.vectors = None
            return

        texts = [chunk['text'] for chunk in self.chunks]
        try:
            self.vectorizer.fit(texts)
            self.vectors = self.vectorizer.transform(texts)
        except Exception as e:
            print(f"Error rebuilding vectors: {e}")
            self.vectors = None

    def add_chunks(self, chunks: List[Dict]):
        """Add new chunks to store and rebuild vectors."""
        self.chunks.extend(chunks)
        self._rebuild_vectors()
        self.save()

    def clear(self):
        """Clear all chunks and vectors."""
        self.chunks = []
        self.vectors = None
        self.save()

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Search for relevant chunks using cosine similarity.
        Returns list of (chunk, similarity_score) tuples.
        """
        if not self.chunks or self.vectors is None:
            return []

        try:
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.vectors)[0]

            # Get top k results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            results = [
                (self.chunks[idx], float(similarities[idx]))
                for idx in top_indices
                if similarities[idx] > 0
            ]

            return results
        except Exception as e:
            print(f"Error searching: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get statistics about stored chunks."""
        doc_types = {}
        for chunk in self.chunks:
            doc_type = chunk.get('metadata', {}).get('doc_type', 'Unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        return {
            'total_chunks': len(self.chunks),
            'chunks_by_type': doc_types,
            'unique_documents': len(set(c.get('metadata', {}).get('file_name') for c in self.chunks))
        }


if __name__ == "__main__":
    store = VectorStore()

    # Test with sample data
    sample_chunks = [
        {
            'text': 'Franklin County has a strong agricultural market with growth potential',
            'metadata': {
                'file_name': 'Franklin_County_2024.pdf',
                'doc_type': 'Market Study',
                'client_project': None,
                'page_start': 1,
                'page_end': 3,
                'file_path': 'files/market_studies/Franklin_County_2024.pdf'
            }
        }
    ]

    # Don't add test data to persistent store
    stats = store.get_stats()
    print(f"Store statistics: {stats}")
