# 0001 Local ChromaDB Storage Isolation

## Context and Decision

When running ChromaDB inside a cloud-synced directory (e.g., Google Drive), background sync processes frequently lock `chroma.sqlite3` during batch vector ingestion and HNSW compaction. To prevent database corruption and `[Errno 1] Operation not permitted` file locking errors, we isolated ChromaDB's persistent storage path to the user's local home directory (`~/.ibm_flashsystem_kb/vector_db/`).

## Status

Accepted
