#!/bin/bash
cd /Users/bencolella/Desktop/SWG/SWAI\ Project
git add vector_store.json local_metadata.json
git commit -m "Auto-backup vector store - $(date)" || true
git push origin main
