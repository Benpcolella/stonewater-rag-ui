# 🎯 STONEWATER RAG - PROBLEM DEFINITION & FRAMEWORK (PDF-Only)

## PROBLEM STATEMENT

**What problem are we solving?**

Stonewater Group needs to search and query PDF documents (market studies, underwriting files, client deliverables) stored locally through a web interface. The system should allow team members to ask questions about these documents and receive answers with cited sources, without relying on cloud services like Azure/OneDrive.

**Current State (Before):**
- PDFs scattered across local drives/folders
- Market studies, underwriting files, and client projects in separate locations
- No unified search across all documents
- Team can't easily ask questions like "What's the market analysis for Franklin County?" or "Show me the risk assessment from the XYZ underwrite"
- Manual document review required
- Time spent searching through multiple folders and files

**Desired State (After):**
- All PDFs organized in structured local folder hierarchy
- Web-based chat interface (no installation needed)
- Team can ask questions about market studies, underwriting files, and client projects
- Get instant answers with document citations (file name, page number)
- Accessible from any browser (GitHub Pages deployed)
- Search across all document types simultaneously
- Retrieve specific underwriting documents quickly

---

## FILE ORGANIZATION STRUCTURE

```
stonewater-rag/
├── project_root/
│   ├── files/                          # Root documents folder
│   │   ├── market_studies/             # Market research PDFs
│   │   │   ├── Franklin_County_2024.pdf
│   │   │   ├── Williamson_County_Market.pdf
│   │   │   └── Regional_Trends.pdf
│   │   │
│   │   ├── underwriting_files/         # General underwriting analysis
│   │   │   ├── Underwriting_Standards.pdf
│   │   │   ├── Risk_Assessment_Guidelines.pdf
│   │   │   └── Financial_Analysis_Template.pdf
│   │   │
│   │   ├── deliverables/               # Standard deliverables/reports
│   │   │   ├── Market_Analysis_Template.pdf
│   │   │   ├── Feasibility_Study_Template.pdf
│   │   │   ├── Executive_Summary_Guidelines.pdf
│   │   │   └── Financial_Projections.pdf
│   │   │
│   │   └── client_projects/            # Client-specific underwrites
│   │       ├── Franklin_Agrihood_2024/
│   │       │   ├── Underwriting_Analysis.pdf
│   │       │   ├── Market_Study.pdf
│   │       │   ├── Financial_Model_Summary.pdf
│   │       │   ├── Feasibility_Report.pdf
│   │       │   └── Risk_Assessment.pdf
│   │       │
│   │       ├── Williamson_Mixed_Use_2024/
│   │       │   ├── Underwriting_Analysis.pdf
│   │       │   ├── Market_Study.pdf
│   │       │   └── Financial_Projections.pdf
│   │       │
│   │       └── Nashville_Development_2024/
│   │           ├── Underwriting_Analysis.pdf
│   │           ├── Site_Analysis.pdf
│   │           └── Zoning_Report.pdf
│   │
│   ├── rag_api.py                      # Flask API server
│   ├── pdf_processor.py                # PDF text extraction & chunking
│   ├── document_sync.py                # Local folder scanner for PDFs
│   ├── llm_query_engine.py             # LLM response engine
│   ├── .env                            # Configuration
│   ├── vector_store.json               # Persistent vector database
│   ├── local_metadata.json             # Processed PDF tracking
│   └── venv/                           # Python virtual environment
│
└── stonewater-rag-ui/                  # Frontend (React)
    ├── src/
    │   ├── App.js
    │   └── index.js
    ├── package.json
    └── node_modules/
```

**Key Features of Structure:**
- `files/` folder created in project root (not ~/Documents)
- Organized by document type: market_studies, underwriting_files, deliverables
- `client_projects/` subfolder for each client project with all related PDFs
- Easy to add new client projects or document types
- All PDFs in one searchable location

---

## BUSINESS REQUIREMENTS

### Functional Requirements

1. **PDF Ingestion Only**
   - Read PDF files (.pdf) from organized folder hierarchy
   - Support nested subfolders (client_projects/PROJECT_NAME/)
   - Extract text from all pages
   - Detect when new/updated PDFs are added
   - NO Excel, NO other formats (for now)

2. **Organized Document Tracking**
   - Track documents by folder type (market_studies, underwriting_files, etc)
   - Include client project name in metadata
   - Know which document came from which folder
   - Support nested folder navigation in search results

3. **Search & Retrieval**
   - Search documents by keyword/semantic meaning
   - Return relevant excerpts from PDFs
   - Show confidence scores for results
   - Return top 5 most relevant results
   - Preserve page numbers in results

4. **Question Answering**
   - Accept natural language questions
   - Generate answers using LLM (DeepSeek/Claude)
   - Include detailed source citations:
     - Document file name
     - Folder type (market study, underwriting, etc)
     - Client project (if applicable)
     - Page number
   - Format answers clearly for web display

5. **User Interface**
   - Web-based chat interface
   - Login with API credentials
   - Chat history during session
   - Sync documents button
   - Statistics view (document count by type, etc)
   - Filter/search by document type (optional future enhancement)

6. **Team Access**
   - Multiple team members access same system
   - No individual installations needed
   - Frontend hosted publicly (GitHub Pages)
   - Backend runs on owner's machine or cloud

---

## TECHNICAL CONSTRAINTS

### Given Constraints (from Ben)

1. **PDF-Only Intake**
   - No Excel files (for MVP)
   - No Word documents
   - PDFs only (.pdf)
   - Complex multi-page PDFs acceptable (market studies, underwriting analysis)

2. **Local Folder Structure**
   - All PDFs in `files/` folder within project root
   - Subfolders: market_studies/, underwriting_files/, deliverables/
   - client_projects/ with nested project folders
   - User manually adds PDFs to appropriate folders

3. **Python 3.14 Compatibility**
   - Ben's machine runs Python 3.14
   - Many packages don't support 3.14
   - Must avoid cutting-edge dependencies with compatibility issues
   - Solution: Pure Python implementations where possible

4. **Small Team (~5-20 people)**
   - Not enterprise-scale
   - Can run backend on single machine or simple cloud VM
   - Don't need production-grade infrastructure
   - Performance: <2 seconds per query acceptable

5. **Low Cost / Free Tier Priority**
   - GitHub Pages (free)
   - DeepSeek API (free tier available)
   - Avoid expensive cloud services
   - Avoid Pinecone/paid vector databases initially

6. **No Authentication Complexity**
   - Simple API key authentication (not OAuth)
   - Same key shared with team
   - No user-specific permissions
   - All documents searchable by all team members

7. **Document Types Matter**
   - Must preserve folder context (market study vs underwriting vs client project)
   - Must track client project name for client_projects/ documents
   - Search results should show document type clearly
   - Optional: Filter results by document type

---

## SYSTEM ARCHITECTURE

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│ USER DOCUMENTS (PDFs)                                       │
│ files/                                                      │
│ ├── market_studies/                                         │
│ │   ├── Franklin_County_2024.pdf                            │
│ │   └── Williamson_County_Market.pdf                        │
│ ├── underwriting_files/                                     │
│ │   ├── Risk_Assessment_Guidelines.pdf                      │
│ │   └── Financial_Analysis_Template.pdf                     │
│ ├── deliverables/                                           │
│ │   └── Market_Analysis_Template.pdf                        │
│ └── client_projects/                                        │
│     ├── Franklin_Agrihood_2024/                             │
│     │   ├── Underwriting_Analysis.pdf                       │
│     │   ├── Market_Study.pdf                                │
│     │   └── Risk_Assessment.pdf                             │
│     └── Williamson_Mixed_Use_2024/                          │
│         ├── Underwriting_Analysis.pdf                       │
│         └── Financial_Model.pdf                             │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND (Python Flask) - Runs on Ben's machine              │
│                                                              │
│ 1. Document Sync                                            │
│    ├── Recursively scan files/ folder                       │
│    ├── Detect PDF files at all nesting levels               │
│    ├── Identify document type (folder name)                 │
│    ├── Extract client project name (if in client_projects/) │
│    ├── Compare against processed files (hash)               │
│    └── Return new/updated PDFs with metadata                │
│                                                              │
│ 2. PDF Processing                                           │
│    ├── Extract text from all PDF pages                      │
│    ├── Track page numbers in content                        │
│    ├── Split into 1000-token chunks (200 overlap)           │
│    ├── Store with rich metadata:                            │
│    │   - Document file name                                 │
│    │   - Document type (market_studies, etc)                │
│    │   - Client project (if applicable)                     │
│    │   - Page numbers                                       │
│    │   - File path                                          │
│    └── Store chunks with full context                       │
│                                                              │
│ 3. Vector Storage                                           │
│    ├── Create TF-IDF vectors for chunks                     │
│    ├── Store in vector_store.json (persistent)              │
│    └── No external vector DB needed                         │
│                                                              │
│ 4. Query Processing                                         │
│    ├── Vectorize incoming question                          │
│    ├── Search vector store (cosine similarity)              │
│    ├── Get top 5 relevant chunks with metadata              │
│    └── Return with rich context for LLM                     │
│                                                              │
│ 5. LLM Integration                                          │
│    ├── Send question + context to DeepSeek                 │
│    ├── Get generated answer                                 │
│    ├── Format source citations:                             │
│    │   - File name: Franklin_County_2024.pdf                │
│    │   - Type: Market Study                                 │
│    │   - Pages: 3-5                                         │
│    ├── Include client project if applicable                 │
│    └── Return answer + detailed citations                   │
└────────────┬────────────────────────────────────────────────┘
             │ REST API (port 5001)
             ↓
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (React) - GitHub Pages                             │
│ https://USERNAME.github.io/stonewater-rag-ui/              │
│                                                              │
│ 1. Login Screen                                             │
│    ├── API URL input                                        │
│    ├── API Key input                                        │
│    └── Connect button                                       │
│                                                              │
│ 2. Chat Interface                                           │
│    ├── Question input box                                   │
│    ├── Answer display with rich sources:                    │
│    │   - Document name (clickable if web URL)               │
│    │   - Document type (Market Study / Underwriting / etc)   │
│    │   - Client project (if applicable)                     │
│    │   - Page number                                        │
│    │   - Relevance score                                    │
│    ├── Sync documents button (🔄)                           │
│    └── Statistics button (📊)                               │
│        - Docs by type (market studies: 5, underwriting: 3)  │
│        - Total PDFs ingested                                │
│        - Total pages indexed                                │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────┐
│ TEAM MEMBERS (Browsers)                                     │
│ ├── Open frontend URL                                       │
│ ├── Enter API URL (Ben's IP:5001)                           │
│ ├── Enter API Key                                           │
│ ├── Ask questions about:                                    │
│ │   - Market studies for specific regions                   │
│ │   - Underwriting standards and guidelines                 │
│ │   - Specific client project details                       │
│ │   - Cross-document analysis                               │
│ └── Get answers with full source citations                  │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

**Backend Components:**

1. **document_sync.py** (replaces onedrive_sync.py)
   - Recursively scans `files/` folder for PDFs
   - Identifies document type by folder (market_studies, underwriting_files, deliverables, client_projects)
   - For client_projects, extracts project name from folder
   - Tracks processed files by hash
   - Identifies new/updated PDFs
   - Returns file list with document type and project metadata

2. **pdf_processor.py** (replaces document_processor.py)
   - Extracts text from PDFs using pdfplumber
   - Preserves page numbers during extraction
   - Splits text into 1000-token chunks (200-token overlap)
   - Creates TF-IDF vectors
   - Stores chunks + rich metadata:
     ```json
     {
       "text": "chunk content...",
       "metadata": {
         "file_name": "Franklin_County_2024.pdf",
         "doc_type": "market_studies",
         "client_project": null,
         "page_start": 3,
         "page_end": 5,
         "file_path": "files/market_studies/Franklin_County_2024.pdf"
       }
     }
     ```

3. **vector_store** (in-memory + JSON persistence)
   - Scikit-learn TfidfVectorizer
   - Cosine similarity search
   - JSON file for persistence (no DB)
   - Preserves all metadata in results

4. **llm_query_engine.py**
   - Calls DeepSeek API (or Claude)
   - Takes question + retrieved context
   - Returns answer + detailed source citations

5. **rag_api.py** (Flask)
   - /api/query - Accept question, return answer with citations
   - /api/sync - Trigger document sync from files/ folder
   - /api/stats - Return document statistics by type
   - /health - Health check
   - Bearer token authentication

**Frontend Components:**

1. **src/App.js** (React)
   - Login form (API URL + key)
   - Chat interface
   - Message history
   - Sync/stats buttons
   - Rich source display:
     - Document name + type
     - Page numbers
     - Client project (if applicable)
     - Relevance scores

2. **Configuration** (package.json)
   - Deployed to GitHub Pages
   - Hardcoded homepage path
   - Deploy script

---

## DESIGN DECISIONS & RATIONALE

### 1. PDF-Only Intake (No Excel for MVP)
**Decision:** Support only PDFs, not Excel files
**Why:**
- Market studies and underwriting files are primarily PDFs
- Simpler text extraction (no sheet logic)
- Faster MVP delivery
- Can add Excel later if needed
**Trade-off:** Must convert any Excel data to PDF or wait for future enhancement

### 2. Local Folder Structure with Project Root
**Decision:** `files/` folder in project root, not ~/Documents
**Why:**
- Self-contained project structure
- Organized by document type + client projects
- Easier to backup entire project
- Clearer for team members where files go
- Can version control structure (not content)
**Trade-off:** Team needs to know to add files to specific subfolders

### 3. Rich Metadata in Results
**Decision:** Include document type, client project, page numbers in all results
**Why:**
- Source citations matter for professional work
- Team can quickly locate documents
- Page numbers essential for PDFs
- Client project context valuable
**Trade-off:** More complex metadata tracking

### 4. Recursive Folder Scanning
**Decision:** Scan all nested folders in files/
**Why:**
- Supports unlimited client projects
- client_projects can have any number of projects
- Easier to add new clients
- No hardcoded project names
**Trade-off:** Must handle complex folder hierarchies

### 5. TF-IDF Vector Search Instead of Neural Embeddings
**Decision:** Use scikit-learn TfidfVectorizer instead of dense embeddings
**Why:**
- Python 3.14 compatibility
- Fast enough for small document set
- No API calls for embeddings
- Lightweight
**Trade-off:** Less semantic understanding (can upgrade later)

### 6. In-Memory Vector Store Instead of External DB
**Decision:** Store vectors in JSON file, load on startup
**Why:**
- No external database needed
- Python 3.14 compatible
- Free (no API costs)
- Sufficient for ~100-200 PDFs
**Trade-off:** Limited to single machine

### 7. DeepSeek LLM by Default
**Decision:** Default to DeepSeek, support Claude as option
**Why:**
- Cheaper API calls
- Free tier available
- Faster for testing
- Easy to switch in .env
**Trade-off:** May need Claude for better quality later

### 8. GitHub Pages for Frontend
**Decision:** Deploy to GitHub Pages
**Why:**
- Free
- No maintenance
- Team can access anywhere
- Easy deployment (npm run deploy)
**Trade-off:** Can't run backend logic (must be separate)

---

## TECHNOLOGY STACK

### Backend
- **Framework:** Flask 3.0.0 (lightweight web server)
- **Language:** Python 3.14
- **PDF Processing:** pdfplumber (text extraction), python-pdf2image (optional)
- **Text Processing:** Pure Python (no NLTK/LangChain)
- **Vector Search:** scikit-learn TfidfVectorizer + cosine similarity
- **Storage:** JSON files (vector_store.json, local_metadata.json)
- **LLM Integration:** requests library (HTTP to APIs)
- **Configuration:** python-dotenv
- **File System:** os, pathlib (recursive folder scanning)

### Frontend
- **Framework:** React 18.2.0
- **Build Tool:** Create React App (react-scripts)
- **Deployment:** GitHub Pages (gh-pages)
- **Styling:** Inline CSS
- **State:** React hooks (useState)

### Infrastructure
- **Frontend Hosting:** GitHub Pages (free)
- **Backend Hosting:** Local machine initially
- **Version Control:** Git + GitHub

---

## FILE ORGANIZATION RULES

**Folder Structure Expectations:**

```
files/
├── market_studies/          # Market research & analysis PDFs
├── underwriting_files/      # General underwriting docs, standards, templates
├── deliverables/            # Reusable deliverable templates & reports
└── client_projects/         # Client-specific projects
    └── [CLIENT_NAME_YEAR]/  # Each project in named subfolder
        ├── Underwriting_Analysis.pdf
        ├── Market_Study.pdf
        ├── Financial_Model.pdf
        └── [other project docs].pdf
```

**Guidelines:**

1. **market_studies/**
   - Regional market analysis
   - Market research PDFs
   - Trend reports
   - Example: Franklin_County_2024.pdf

2. **underwriting_files/**
   - Underwriting standards & guidelines
   - Financial analysis templates
   - Risk assessment frameworks
   - Example: Risk_Assessment_Guidelines.pdf

3. **deliverables/**
   - Reusable deliverable templates
   - Standard reports
   - Guidelines for standard documents
   - Example: Market_Analysis_Template.pdf

4. **client_projects/[CLIENT_NAME_YEAR]/**
   - All documents for specific client project
   - Include client name and year
   - Example: Franklin_Agrihood_2024/
   - Each project contains all related PDFs

---

## CONSTRAINTS & LIMITATIONS

### Hard Constraints (Can't Change)
1. Python 3.14 (Ben's system)
2. PDF-only intake (no Excel for MVP)
3. Local files folder (no cloud integration)
4. Team access via web (GitHub Pages)
5. Free/low-cost (no expensive services)
6. Small team (<20 people)

### Soft Constraints (Can Change Later)
1. Backend on local machine (can move to cloud)
2. Shared API key (can add per-user auth)
3. TF-IDF search (can upgrade to neural embeddings)
4. JSON vector store (can use Pinecone)
5. DeepSeek LLM (can use Claude/OpenAI)
6. No Excel (can add later)

### Performance Limits
- **Query time:** <2 seconds acceptable
- **Document count:** ~200 PDFs, ~50K chunks tested
- **Concurrent users:** 5-10 realistic
- **Update frequency:** Documents sync on demand

### Security Limitations (Development)
- API key in plain text (shared)
- No user authentication
- No encryption
- HTTP only (localhost)
- No rate limiting

---

## SUCCESS CRITERIA

### MVP (What we're building)
✅ PDFs read from organized local folder structure
✅ Recursive folder scanning for nested client projects
✅ Text extraction from all PDF pages with page tracking
✅ Semantic search across all documents
✅ Question answering with detailed source citations
✅ Document type and client project tracking
✅ Web interface (React)
✅ Team access (GitHub Pages)
✅ Works with Python 3.14
✅ Free/low-cost

### Nice to Have
- Deploy frontend to GitHub Pages
- Team successfully accessing
- Search quality improvements
- Optional: Filter results by document type
- Optional: Client project analytics

### Future (Post-MVP)
- Cloud-hosted backend
- Per-user authentication
- Neural embeddings
- Excel file support
- Document upload UI
- Advanced search filters
- Production security

---

## DEVELOPMENT WORKFLOW

### Phase 1: Backend Development (Core)
- [ ] Flask API structure
- [ ] PDF folder scanner (recursive)
- [ ] PDF text extraction with page tracking
- [ ] Vector storage with metadata
- [ ] LLM integration with citations
- [ ] API endpoints with rich metadata

### Phase 2: Frontend Development
- [ ] React setup
- [ ] Login component
- [ ] Chat interface with rich source display
- [ ] API integration
- [ ] Local testing

### Phase 3: Integration Testing
- [ ] Backend ↔ Frontend connection
- [ ] Document syncing
- [ ] Query processing
- [ ] Answer generation with citations

### Phase 4: Deployment
- [ ] Deploy frontend to GitHub Pages
- [ ] Share with team
- [ ] Monitor performance

### Phase 5: Optimization (Optional)
- [ ] Improve search quality
- [ ] Scale if needed
- [ ] Add monitoring
- [ ] Security hardening

---

## EXAMPLE USER SCENARIOS

### Scenario 1: Market Study Search
**User:** "What's the market analysis for Franklin County?"
**System:**
1. Searches across all PDFs
2. Finds Franklin_County_2024.pdf in market_studies/
3. Returns relevant excerpts from pages 3-7
4. LLM generates answer about market size, growth, competition
5. Citations show: "Franklin_County_2024.pdf (Market Study, Pages 3-7)"

### Scenario 2: Client Project Query
**User:** "What are the key risks in the Williamson project?"
**System:**
1. Searches files, finds client_projects/Williamson_Mixed_Use_2024/
2. Returns excerpts from Risk_Assessment.pdf and Underwriting_Analysis.pdf
3. LLM synthesizes risks from multiple documents
4. Citations show: 
   - "Underwriting_Analysis.pdf (Williamson Mixed Use 2024, Pages 2-4)"
   - "Risk_Assessment.pdf (Williamson Mixed Use 2024, Page 1)"

### Scenario 3: Underwriting Standards
**User:** "What are the financial analysis guidelines?"
**System:**
1. Searches underwriting_files/ folder
2. Finds Financial_Analysis_Template.pdf
3. Returns relevant sections
4. LLM explains standards
5. Citations show: "Financial_Analysis_Template.pdf (Underwriting Guidelines)"

---

## ASSUMPTIONS & DECISIONS LOG

### Assumption 1: PDFs are Primary Document Type
- Market studies in PDF format
- Underwriting files in PDF
- All client project documents in PDF
- Excel data converted to PDF if needed

### Assumption 2: Local Folder is Acceptable
- files/ folder in project root
- Manual file management
- Team manually adds files to correct subfolder
- Sufficient for small team

### Assumption 3: Rich Metadata Essential
- Document type matters (market study vs underwriting)
- Client project context important
- Page numbers required for PDFs
- All preserved in search results

### Assumption 4: Page Numbers Preserved
- pdfplumber preserves page numbers
- Included in all citations
- Helps team locate exact information

---

## SUMMARY

**What we're building:** A PDF-focused RAG system that lets Stonewater Group search market studies, underwriting files, and client project documents.

**Key difference from original:** PDF-only (no Excel), organized folder structure with document types and client projects, rich metadata preservation.

**How it works:** Python backend processes PDFs from organized local folder, preserves document type/client project info, React frontend lets team search with detailed source citations.

**Key constraint:** Python 3.14 drives technology choices.

**Scale:** Small team MVP, designed to upgrade if needed.

---

**Next Step:** Build PDF processor with metadata, deploy to GitHub Pages, share with team.
