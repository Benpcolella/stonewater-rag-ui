import os
import requests
from typing import List, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()


class LLMQueryEngine:
    """Handles LLM integration and answer generation with source citations."""

    def __init__(self, provider: str = None):
        self.provider = provider or os.getenv('LLM_PROVIDER', 'deepseek')
        self.deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        self.claude_key = os.getenv('CLAUDE_API_KEY')
        self.timeout = int(os.getenv('API_TIMEOUT', '30'))

    def _format_context(self, search_results: List[Tuple[Dict, float]]) -> Tuple[str, List[Dict]]:
        """Format search results as context for LLM and extract citations."""
        context_parts = []
        citations = []
        seen_docs = set()

        for chunk, score in search_results:
            metadata = chunk.get('metadata', {})
            text = chunk.get('text', '')

            # Format context
            context_parts.append(f"[Source: {metadata.get('file_name')}]\n{text}")

            # Track unique sources for citations
            doc_key = metadata.get('file_path')
            if doc_key and doc_key not in seen_docs:
                citations.append({
                    'file_name': metadata.get('file_name'),
                    'doc_type': metadata.get('doc_type'),
                    'client_project': metadata.get('client_project'),
                    'page_start': metadata.get('page_start'),
                    'page_end': metadata.get('page_end'),
                    'file_path': metadata.get('file_path'),
                    'relevance_score': float(score)
                })
                seen_docs.add(doc_key)

        context = "\n\n".join(context_parts)
        return context, citations

    def query_deepseek(self, question: str, context: str) -> str:
        """Query DeepSeek API with context."""
        if not self.deepseek_key:
            return "Error: DEEPSEEK_API_KEY not configured"

        try:
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.deepseek_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant analyzing documents. Answer based on the provided context."
                        },
                        {
                            "role": "user",
                            "content": f"Based on the following context, answer this question:\n\nContext:\n{context}\n\nQuestion: {question}"
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error: DeepSeek API returned {response.status_code}"
        except requests.exceptions.Timeout:
            return "Error: DeepSeek API request timed out"
        except Exception as e:
            return f"Error querying DeepSeek: {str(e)}"

    def query_claude(self, question: str, context: str) -> str:
        """Query Claude API with context."""
        if not self.claude_key:
            return "Error: CLAUDE_API_KEY not configured"

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.claude_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-opus-4-1",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Based on the following context, answer this question:\n\nContext:\n{context}\n\nQuestion: {question}"
                        }
                    ]
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()['content'][0]['text']
            else:
                return f"Error: Claude API returned {response.status_code}"
        except requests.exceptions.Timeout:
            return "Error: Claude API request timed out"
        except Exception as e:
            return f"Error querying Claude: {str(e)}"

    def generate_answer(self, question: str, search_results: List[Tuple[Dict, float]]) -> Dict:
        """
        Generate answer using LLM with search results as context.
        Returns dict with answer and citations.
        """
        if not search_results:
            return {
                'answer': "I could not find relevant documents to answer your question.",
                'citations': [],
                'error': 'No search results found'
            }

        context, citations = self._format_context(search_results)

        # Query LLM based on provider
        if self.provider == 'claude':
            answer = self.query_claude(question, context)
        else:
            answer = self.query_deepseek(question, context)

        return {
            'answer': answer,
            'citations': citations,
            'error': None
        }


if __name__ == "__main__":
    engine = LLMQueryEngine()
    print(f"Using LLM provider: {engine.provider}")
