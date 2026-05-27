import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from document_sync import DocumentSync
from pdf_processor import PDFProcessor
from vector_store import VectorStore
from llm_query_engine import LLMQueryEngine

load_dotenv()

app = Flask(__name__)
CORS(app, origins=[os.getenv('FRONTEND_URL', 'http://localhost:3000')])

# Initialize components
doc_sync = DocumentSync()
pdf_processor = PDFProcessor(
    chunk_size=int(os.getenv('CHUNK_SIZE', '1000')),
    chunk_overlap=int(os.getenv('CHUNK_OVERLAP', '200'))
)
vector_store = VectorStore()
llm_engine = LLMQueryEngine()

# API Key validation
API_KEY = os.getenv('API_KEY', 'your_api_key_here')


def validate_api_key():
    """Validate Bearer token in request headers."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header[7:]
    return token == API_KEY


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'Stonewater RAG API is running'})


@app.route('/api/sync', methods=['POST'])
def sync_documents():
    """
    Scan files/ folder for new/updated PDFs and add to vector store.
    """
    if not validate_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        new_files, removed = doc_sync.scan_documents()

        processed_count = 0
        for file_info in new_files:
            filepath = file_info['filepath']
            metadata = file_info['metadata']

            # Process PDF
            chunks = pdf_processor.process_pdf(filepath, metadata)
            if chunks:
                vector_store.add_chunks(chunks)
                processed_count += 1

        return jsonify({
            'status': 'success',
            'new_files_processed': processed_count,
            'files_removed': len(removed),
            'total_documents': vector_store.get_stats()['unique_documents']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/query', methods=['POST'])
def query():
    """
    Accept a question and return answer with source citations.
    """
    if not validate_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    question = data.get('question', '')

    if not question:
        return jsonify({'error': 'Question is required'}), 400

    try:
        # Search vector store
        search_results = vector_store.search(question, top_k=5)

        # Generate answer with LLM
        result = llm_engine.generate_answer(question, search_results)

        return jsonify({
            'status': 'success',
            'question': question,
            'answer': result['answer'],
            'citations': result['citations'],
            'error': result['error']
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    """
    Return document statistics.
    """
    if not validate_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        store_stats = vector_store.get_stats()
        doc_stats = doc_sync.get_document_count()

        return jsonify({
            'status': 'success',
            'vector_store': store_stats,
            'documents': doc_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents', methods=['GET'])
def documents():
    """
    List all tracked documents with metadata.
    """
    if not validate_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        doc_list = []
        seen = set()

        for chunk in vector_store.chunks:
            metadata = chunk.get('metadata', {})
            file_path = metadata.get('file_path')

            if file_path and file_path not in seen:
                doc_list.append({
                    'file_name': metadata.get('file_name'),
                    'doc_type': metadata.get('doc_type'),
                    'client_project': metadata.get('client_project'),
                    'file_path': metadata.get('file_path')
                })
                seen.add(file_path)

        return jsonify({
            'status': 'success',
            'documents': doc_list,
            'count': len(doc_list)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5001))
    app.run(debug=True, port=port)
