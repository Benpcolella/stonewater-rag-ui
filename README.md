# Stonewater RAG - Document Search & Query System

A PDF-focused Retrieval-Augmented Generation (RAG) system for Stonewater Group. Search and query market studies, underwriting files, and client project documents through a web interface.

## Features

✅ PDF-only document ingestion from organized folder structure  
✅ Recursive folder scanning for nested client projects  
✅ TF-IDF semantic search across all documents  
✅ Question answering with detailed source citations  
✅ Rich metadata preservation (document type, client project, page numbers)  
✅ Web-based chat interface (React)  
✅ Team access via GitHub Pages  
✅ Python 3.14 compatible  

## Quick Start

### Prerequisites

- Python 3.14+
- Node.js 14+ (for frontend)
- Git

### Backend Setup

1. **Create virtual environment:**
   ```bash
   cd /Users/bencolella/Desktop/SWG/SWAI\ Project
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   Edit `.env` with your API keys:
   ```
   API_KEY=your_secure_key_here
   DEEPSEEK_API_KEY=your_deepseek_key
   LLM_PROVIDER=deepseek
   ```

4. **Organize your PDFs:**
   Place PDFs in the `files/` folder structure:
   ```
   files/
   ├── market_studies/
   ├── underwriting_files/
   ├── deliverables/
   └── client_projects/
       └── Project_Name_2024/
   ```

5. **Start the backend:**
   ```bash
   python3 rag_api.py
   ```
   API runs on `http://localhost:5001`

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd stonewater-rag-ui
   npm install
   ```

2. **Start development server:**
   ```bash
   npm start
   ```
   Frontend runs on `http://localhost:3000`

3. **First time setup:**
   - Click "Connect"
   - API URL: `http://localhost:5001`
   - API Key: (same as `API_KEY` in `.env`)
   - Click "Connect"

## Project Structure

```
stonewater-rag/
├── rag_api.py                 # Flask API server
├── pdf_processor.py           # PDF extraction & chunking
├── document_sync.py           # Folder scanner for PDFs
├── vector_store.py            # TF-IDF vector search
├── llm_query_engine.py        # LLM integration
├── .env                       # Configuration
├── requirements.txt           # Python dependencies
├── files/                     # Your PDF documents
│   ├── market_studies/
│   ├── underwriting_files/
│   ├── deliverables/
│   └── client_projects/
│
└── stonewater-rag-ui/         # React frontend
    ├── src/
    │   ├── App.js
    │   ├── App.css
    │   └── index.js
    ├── public/
    └── package.json
```

## API Endpoints

### `GET /health`
Health check endpoint.

### `POST /api/sync`
Scan `files/` folder and ingest new/updated PDFs into vector store.

**Headers:** `Authorization: Bearer YOUR_API_KEY`

**Response:**
```json
{
  "status": "success",
  "new_files_processed": 3,
  "files_removed": 0,
  "total_documents": 15
}
```

### `POST /api/query`
Ask a question and get an answer with source citations.

**Headers:** `Authorization: Bearer YOUR_API_KEY`

**Body:**
```json
{
  "question": "What's the market analysis for Franklin County?"
}
```

**Response:**
```json
{
  "status": "success",
  "question": "What's the market analysis for Franklin County?",
  "answer": "Franklin County has a strong agricultural market with...",
  "citations": [
    {
      "file_name": "Franklin_County_2024.pdf",
      "doc_type": "Market Study",
      "page_start": 3,
      "page_end": 7,
      "relevance_score": 0.89
    }
  ]
}
```

### `GET /api/stats`
Get document statistics.

**Headers:** `Authorization: Bearer YOUR_API_KEY`

### `GET /api/documents`
List all tracked documents.

**Headers:** `Authorization: Bearer YOUR_API_KEY`

## Document Organization

### `market_studies/`
Regional market analysis, research, and trend reports.
- `Franklin_County_2024.pdf`
- `Williamson_County_Market.pdf`

### `underwriting_files/`
General underwriting standards, templates, and guidelines.
- `Risk_Assessment_Guidelines.pdf`
- `Financial_Analysis_Template.pdf`

### `deliverables/`
Reusable deliverable templates and standard reports.
- `Market_Analysis_Template.pdf`
- `Feasibility_Study_Template.pdf`

### `client_projects/PROJECT_NAME/`
Client-specific project documents.
- `Franklin_Agrihood_2024/Underwriting_Analysis.pdf`
- `Franklin_Agrihood_2024/Market_Study.pdf`
- `Williamson_Mixed_Use_2024/Financial_Projections.pdf`

## Technology Stack

**Backend:**
- Python 3.14
- Flask 3.0.0 (web framework)
- pdfplumber (PDF extraction)
- scikit-learn (TF-IDF vectorization)
- JSON (vector storage)
- DeepSeek/Claude API (LLM)

**Frontend:**
- React 18.2.0
- React Hooks (state management)
- GitHub Pages (deployment)

## Example Workflows

### Scenario 1: Market Study Search
```
Q: "What's the market analysis for Franklin County?"

System:
1. Searches vector store for "Franklin County"
2. Finds Franklin_County_2024.pdf in market_studies/
3. Returns relevant excerpts from pages 3-7
4. LLM generates summary
5. Shows citation: Franklin_County_2024.pdf (Market Study, Pages 3-7)
```

### Scenario 2: Client Project Query
```
Q: "What are the key risks in the Williamson project?"

System:
1. Searches across all documents
2. Finds Williamson_Mixed_Use_2024/ client project files
3. Returns excerpts from Risk_Assessment.pdf and Underwriting_Analysis.pdf
4. LLM synthesizes risks from multiple documents
5. Shows citations with project context
```

## Deployment

### Deploy Frontend to GitHub Pages

1. **Create GitHub repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/USERNAME/stonewater-rag.git
   git push -u origin main
   ```

2. **Update homepage in `package.json`:**
   ```json
   "homepage": "https://USERNAME.github.io/stonewater-rag-ui/"
   ```

3. **Install gh-pages:**
   ```bash
   cd stonewater-rag-ui
   npm install --save-dev gh-pages
   ```

4. **Deploy:**
   ```bash
   npm run deploy
   ```

5. **Enable GitHub Pages:**
   - Go to Settings → Pages
   - Set Source to `gh-pages` branch

### Backend Deployment Options

- **Local machine** (development): Run Flask on your machine, share IP with team
- **Cloud VM** (production): Deploy to AWS, DigitalOcean, Heroku, etc.
- **Docker** (scalable): Containerize Flask app for easy deployment

## Configuration

All settings in `.env`:

| Setting | Default | Purpose |
|---------|---------|---------|
| `FLASK_PORT` | 5001 | Backend port |
| `API_KEY` | your_api_key_here | Bearer token for API |
| `LLM_PROVIDER` | deepseek | LLM to use (deepseek/claude) |
| `CHUNK_SIZE` | 1000 | Tokens per document chunk |
| `CHUNK_OVERLAP` | 200 | Token overlap between chunks |
| `DEEPSEEK_API_KEY` | - | DeepSeek API key |
| `CLAUDE_API_KEY` | - | Claude API key |

## Troubleshooting

### Backend won't start
- Check Python version: `python3 --version` (need 3.14+)
- Check dependencies: `pip install -r requirements.txt`
- Check port 5001 is available: `lsof -i :5001`

### No documents found during sync
- Check `files/` folder exists
- Check PDFs are in correct subfolders
- Run manually: `python3 document_sync.py`

### API key authentication fails
- Verify `API_KEY` in `.env` matches what you enter in UI
- Check `Authorization: Bearer` header is correct

### LLM API errors
- Verify `DEEPSEEK_API_KEY` or `CLAUDE_API_KEY` is correct
- Check API keys are not expired
- Verify API provider is specified correctly in `.env`

## Performance Notes

- **Chunk Size:** Default 1000 tokens works well for most PDFs
- **Search Speed:** <2 seconds typical for 100-200 PDFs
- **Concurrent Users:** 5-10 realistic with local backend
- **Vector Store Size:** ~50K chunks fits in memory

## Roadmap

### MVP (Current)
✅ PDF-only ingestion  
✅ Local folder organization  
✅ TF-IDF semantic search  
✅ Question answering with citations  
✅ Web chat interface  

### Phase 2 (Future)
- Cloud-hosted backend
- Neural embeddings (LangChain/Hugging Face)
- Per-user authentication
- Document upload UI
- Advanced search filters
- Client project analytics

### Phase 3 (Future)
- Excel file support
- Pinecone vector database
- Production security
- Rate limiting
- Audit logging

## License

Internal project for Stonewater Group

## Support

For issues, questions, or suggestions, contact Ben Colella.
