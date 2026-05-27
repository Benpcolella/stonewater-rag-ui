# Stonewater RAG Development Notes

## Project Overview
PDF-focused Retrieval-Augmented Generation (RAG) system for Stonewater Group. Allows team members to search and query market studies, underwriting files, and client project documents through a web interface.

## Technology Stack
- **Backend:** Python 3.14, Flask 3.0.0, pdfplumber, scikit-learn TF-IDF, JSON persistence
- **Frontend:** React 18.2.0, GitHub Pages deployment
- **LLM:** DeepSeek API (primary), Claude API (secondary)
- **Vector Storage:** TF-IDF vectors in JSON file (no external DB)

## Current Status

### ✅ Completed (MVP Phase 1)
- [x] Backend Flask API structure (rag_api.py)
- [x] Document sync module (document_sync.py) - recursive folder scanning
- [x] PDF processor (pdf_processor.py) - text extraction + chunking
- [x] Vector store (vector_store.py) - TF-IDF search
- [x] LLM engine (llm_query_engine.py) - answer generation with citations
- [x] React frontend (App.js) - chat interface + login
- [x] Environment configuration (.env)
- [x] Project structure and organization

### 🚀 Next Steps
1. Test backend with sample PDFs
2. Test frontend connectivity
3. Configure API keys (DeepSeek/Claude)
4. Set up GitHub repo for deployment
5. Deploy frontend to GitHub Pages
6. Test with team members

## Key Files

### Backend
- `rag_api.py` - Main Flask server with 5 endpoints
- `document_sync.py` - Recursively scans files/ folder, extracts metadata
- `pdf_processor.py` - Extracts text, creates overlapping chunks
- `vector_store.py` - TF-IDF vectorization + cosine similarity search
- `llm_query_engine.py` - DeepSeek/Claude integration with citations
- `requirements.txt` - Python dependencies

### Frontend
- `stonewater-rag-ui/src/App.js` - React app with chat interface
- `stonewater-rag-ui/src/App.css` - Styling
- `stonewater-rag-ui/package.json` - React dependencies

### Documentation
- `README.md` - Complete setup and usage guide
- `PROBLEM_DEFINITION_PDF_FOCUSED.md` - Original requirements

## Architecture Decisions

### TF-IDF Over Neural Embeddings
- Python 3.14 compatibility (many modern packages don't support it yet)
- No API calls needed for embedding generation
- Fast enough for small document sets (<200 PDFs)
- Can upgrade to neural embeddings later

### JSON Vector Store Instead of Database
- No external dependencies (PostgreSQL/Pinecone)
- Simple to understand and debug
- Sufficient for team size and document volume
- Easy to backup and version control

### Local Folder Structure
- Self-contained project (all PDFs in ./files/)
- Organized by document type + client projects
- Manual file management (team adds PDFs to correct folders)
- Avoids cloud service costs

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | /health | Health check |
| POST | /api/sync | Scan files/ and ingest PDFs |
| POST | /api/query | Ask question, get answer + citations |
| GET | /api/stats | Document statistics |
| GET | /api/documents | List all tracked documents |

All require Bearer token auth.

## Document Organization

```
files/
├── market_studies/          # Regional market analysis PDFs
├── underwriting_files/      # Underwriting standards & templates
├── deliverables/            # Reusable deliverable templates
└── client_projects/
    └── [CLIENT_NAME_YEAR]/  # Client-specific project PDFs
```

Metadata preservation:
- Document file name
- Document type (Market Study, Underwriting, Deliverable, Client Project)
- Client project name (if applicable)
- Page numbers
- File path

## Testing Checklist

Before team deployment:
- [ ] Create sample PDFs in files/ structure
- [ ] Start backend: `python3 rag_api.py`
- [ ] Test /health endpoint
- [ ] Test /api/sync endpoint
- [ ] Verify vector_store.json created
- [ ] Test /api/query with sample question
- [ ] Start frontend: `npm start` in stonewater-rag-ui/
- [ ] Test login with API URL + key
- [ ] Test sync documents button
- [ ] Test question submission
- [ ] Verify citations display correctly
- [ ] Test stats view

## Configuration (.env)

Essential to set before running:
```
API_KEY=your_secure_key_here
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_key
```

## Frontend Deployment

To GitHub Pages:
1. Update `homepage` in stonewater-rag-ui/package.json
2. Install gh-pages: `npm install --save-dev gh-pages`
3. Create GitHub repo
4. Push to GitHub
5. Run: `npm run deploy` in stonewater-rag-ui/
6. Enable GitHub Pages in repo settings

## Known Limitations

### Current (MVP)
- PDF-only (no Excel)
- Local backend (requires machine to be running)
- Shared API key (no per-user auth)
- TF-IDF search (less semantic than neural)
- HTTP only (no SSL)
- No rate limiting

### Can Upgrade Later
- Add Excel support
- Deploy backend to cloud
- Add user authentication
- Switch to neural embeddings
- Add production security
- Add rate limiting + monitoring

## Performance Targets

- Query response time: <2 seconds
- Document count: 100-200 PDFs
- Chunk count: ~50K total
- Concurrent users: 5-10
- Memory usage: ~500MB (vector store + app)

## Next Phase Ideas (Post-MVP)

1. **Cloud Backend** - Deploy Flask to AWS/Heroku
2. **Better Search** - Upgrade to neural embeddings (LangChain)
3. **User Auth** - Per-user authentication + permissions
4. **Document Upload** - UI to upload PDFs instead of manual folder management
5. **Advanced Filters** - Filter search by document type, project, date range
6. **Analytics** - Track usage patterns, popular documents
7. **Monitoring** - Logging, error tracking, performance metrics

## Useful Commands

```bash
# Setup backend
cd /Users/bencolella/Desktop/SWG/SWAI\ Project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start backend
python3 rag_api.py

# Setup frontend
cd stonewater-rag-ui
npm install
npm start

# Deploy frontend
npm run deploy

# Test API manually
curl -H "Authorization: Bearer your_api_key" \
  http://localhost:5001/api/stats
```

## Contact & Support
Ben Colella - Lead Developer
