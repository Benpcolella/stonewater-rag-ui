import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple

class DocumentSync:
    """Recursively scans files/ folder for PDFs and tracks metadata."""

    FOLDER_TYPES = {
        'market_studies': 'Market Study',
        'underwriting_files': 'Underwriting Guidelines',
        'deliverables': 'Deliverable Template'
    }

    def __init__(self, root_path: str = "files", metadata_file: str = "local_metadata.json"):
        self.root_path = root_path
        self.metadata_file = metadata_file
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load previously processed file metadata."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_metadata(self):
        """Persist metadata to JSON file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def _get_file_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of file for change detection."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _extract_document_metadata(self, pdf_path: str) -> Dict:
        """Extract document type and client project from file path."""
        rel_path = os.path.relpath(pdf_path, self.root_path)
        parts = rel_path.split(os.sep)

        metadata = {
            'file_name': os.path.basename(pdf_path),
            'file_path': rel_path,
            'doc_type': None,
            'client_project': None
        }

        # Determine document type from folder
        if len(parts) > 1:
            folder = parts[0]
            if folder in self.FOLDER_TYPES:
                metadata['doc_type'] = self.FOLDER_TYPES[folder]
            elif folder == 'client_projects':
                metadata['doc_type'] = 'Client Project'
                if len(parts) > 1:
                    metadata['client_project'] = parts[1]

        return metadata

    def scan_documents(self) -> Tuple[List[Dict], List[str]]:
        """
        Recursively scan files/ folder for PDFs.
        Returns: (list of new/updated PDFs with metadata, list of removed files)
        """
        if not os.path.exists(self.root_path):
            print(f"Warning: {self.root_path} folder not found")
            return [], []

        current_files = {}
        new_or_updated = []

        # Walk through all PDF files
        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    filepath = os.path.join(root, file)
                    file_hash = self._get_file_hash(filepath)
                    rel_path = os.path.relpath(filepath, self.root_path)

                    current_files[rel_path] = file_hash

                    # Check if file is new or has been modified
                    if rel_path not in self.metadata or self.metadata[rel_path].get('hash') != file_hash:
                        metadata = self._extract_document_metadata(filepath)
                        metadata['hash'] = file_hash

                        new_or_updated.append({
                            'filepath': filepath,
                            'rel_path': rel_path,
                            'metadata': metadata
                        })

                        self.metadata[rel_path] = metadata

        # Detect removed files
        removed = [f for f in self.metadata.keys() if f not in current_files]
        for f in removed:
            del self.metadata[f]

        # Save updated metadata
        self._save_metadata()

        return new_or_updated, removed

    def get_document_count(self) -> Dict:
        """Get statistics on documents by type."""
        stats = {
            'total': len(self.metadata),
            'by_type': {}
        }

        for metadata in self.metadata.values():
            doc_type = metadata.get('doc_type', 'Unknown')
            stats['by_type'][doc_type] = stats['by_type'].get(doc_type, 0) + 1

        return stats


if __name__ == "__main__":
    sync = DocumentSync()
    new_files, removed = sync.scan_documents()
    stats = sync.get_document_count()

    print(f"Found {len(new_files)} new/updated files")
    print(f"Removed {len(removed)} files")
    print(f"Document statistics: {stats}")
