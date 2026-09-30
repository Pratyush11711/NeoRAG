import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.config import get_settings
from app.models.responses import DocumentInfo, DocumentChunkModel, RunHistoryItem

class MetadataDB:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_settings().SQLITE_DB_PATH
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                status TEXT NOT NULL,
                element_count INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                tables_count INTEGER DEFAULT 0,
                images_count INTEGER DEFAULT 0,
                metadata_json TEXT DEFAULT '{}'
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                page_number INTEGER,
                page_content TEXT NOT NULL,
                raw_text TEXT,
                enhanced_summary TEXT,
                tables_json TEXT DEFAULT '[]',
                images_json TEXT DEFAULT '[]',
                content_types_json TEXT DEFAULT '[]',
                metadata_json TEXT DEFAULT '{}',
                FOREIGN KEY (document_id) REFERENCES documents (document_id) ON DELETE CASCADE
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                strategy TEXT NOT NULL,
                created_at TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                number_of_candidates INTEGER DEFAULT 0,
                final_answer TEXT,
                sources_json TEXT DEFAULT '[]',
                trace_json TEXT DEFAULT '[]',
                debug_json TEXT DEFAULT '{}'
            )
            """)
            conn.commit()

    def insert_document(self, document_id: str, filename: str, file_path: str, metadata: Dict[str, Any] = None) -> None:
        upload_date = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {})
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents 
                (document_id, filename, file_path, upload_date, status, metadata_json)
                VALUES (?, ?, ?, ?, 'uploaded', ?)
            """, (document_id, filename, file_path, upload_date, metadata_json))
            conn.commit()

    def update_document_status(
        self, 
        document_id: str, 
        status: str, 
        element_count: Optional[int] = None,
        chunk_count: Optional[int] = None,
        tables_count: Optional[int] = None,
        images_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = ["status = ?"]
            params = [status]
            if element_count is not None:
                updates.append("element_count = ?")
                params.append(element_count)
            if chunk_count is not None:
                updates.append("chunk_count = ?")
                params.append(chunk_count)
            if tables_count is not None:
                updates.append("tables_count = ?")
                params.append(tables_count)
            if images_count is not None:
                updates.append("images_count = ?")
                params.append(images_count)
            if metadata is not None:
                updates.append("metadata_json = ?")
                params.append(json.dumps(metadata))
            
            params.append(document_id)
            query = f"UPDATE documents SET {', '.join(updates)} WHERE document_id = ?"
            cursor.execute(query, tuple(params))
            conn.commit()

    def get_document_file_path(self, document_id: str) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM documents WHERE document_id = ?", (document_id,))
            row = cursor.fetchone()
            if row and row["file_path"]:
                return row["file_path"]
            return None

    def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return DocumentInfo(
                document_id=row["document_id"],
                filename=row["filename"],
                upload_date=row["upload_date"],
                status=row["status"],
                element_count=row["element_count"],
                chunk_count=row["chunk_count"],
                tables_count=row["tables_count"],
                images_count=row["images_count"],
                file_path=row["file_path"] if "file_path" in row.keys() else None,
                metadata=json.loads(row["metadata_json"] or "{}")
            )

    def list_documents(self) -> List[DocumentInfo]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY upload_date DESC")
            rows = cursor.fetchall()
            return [
                DocumentInfo(
                    document_id=row["document_id"],
                    filename=row["filename"],
                    upload_date=row["upload_date"],
                    status=row["status"],
                    element_count=row["element_count"],
                    chunk_count=row["chunk_count"],
                    tables_count=row["tables_count"],
                    images_count=row["images_count"],
                    file_path=row["file_path"] if "file_path" in row.keys() else None,
                    metadata=json.loads(row["metadata_json"] or "{}")
                )
                for row in rows
            ]

    def insert_chunks(self, chunks: List[DocumentChunkModel]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for idx, c in enumerate(chunks):
                cursor.execute("""
                    INSERT OR REPLACE INTO chunks
                    (chunk_id, document_id, chunk_index, page_number, page_content, raw_text, tables_json, images_json, content_types_json, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c.chunk_id,
                    c.document_id,
                    idx,
                    c.metadata.get("page_number"),
                    c.page_content,
                    c.raw_text,
                    json.dumps([t.model_dump() for t in c.tables]),
                    json.dumps([img.model_dump() for img in c.images]),
                    json.dumps(c.content_types),
                    json.dumps(c.metadata)
                ))
            conn.commit()

    def get_chunks_for_document(self, document_id: str) -> List[DocumentChunkModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index ASC", (document_id,))
            rows = cursor.fetchall()
            return [self._row_to_chunk(row) for row in rows]

    def get_chunk(self, chunk_id: str) -> Optional[DocumentChunkModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_chunk(row)

    def get_all_chunks(self) -> List[DocumentChunkModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks ORDER BY chunk_id ASC")
            rows = cursor.fetchall()
            return [self._row_to_chunk(row) for row in rows]

    def _row_to_chunk(self, row: sqlite3.Row) -> DocumentChunkModel:
        return DocumentChunkModel(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            page_content=row["page_content"],
            raw_text=row["raw_text"] or "",
            tables=json.loads(row["tables_json"] or "[]"),
            images=json.loads(row["images_json"] or "[]"),
            content_types=json.loads(row["content_types_json"] or "[]"),
            metadata=json.loads(row["metadata_json"] or "{}")
        )

    def delete_document(self, document_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            cursor.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
            conn.commit()
            return cursor.rowcount > 0

    def record_run(
        self,
        run_id: str,
        query: str,
        strategy: str,
        duration_ms: float,
        number_of_candidates: int,
        final_answer: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        trace: Optional[List[Dict[str, Any]]] = None,
        debug: Optional[Dict[str, Any]] = None
    ) -> None:
        created_at = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO pipeline_runs
                (run_id, query, strategy, created_at, duration_ms, number_of_candidates, final_answer, sources_json, trace_json, debug_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                query,
                strategy,
                created_at,
                duration_ms,
                number_of_candidates,
                final_answer,
                json.dumps(sources or []),
                json.dumps(trace or []),
                json.dumps(debug or {})
            ))
            conn.commit()

    save_run = record_run

    def get_runs(self, limit: int = 50) -> List[RunHistoryItem]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_runs ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            runs = []
            for r in rows:
                sources = json.loads(r["sources_json"] or "[]")
                runs.append(RunHistoryItem(
                    run_id=r["run_id"],
                    query=r["query"],
                    strategy=r["strategy"],
                    created_at=r["created_at"],
                    duration_ms=r["duration_ms"],
                    number_of_candidates=r["number_of_candidates"],
                    final_answer=r["final_answer"],
                    sources_count=len(sources)
                ))
            return runs

    def get_run_detail(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "run_id": row["run_id"],
                "query": row["query"],
                "strategy": row["strategy"],
                "created_at": row["created_at"],
                "duration_ms": row["duration_ms"],
                "number_of_candidates": row["number_of_candidates"],
                "final_answer": row["final_answer"],
                "sources": json.loads(row["sources_json"] or "[]"),
                "trace": json.loads(row["trace_json"] or "[]"),
                "debug": json.loads(row["debug_json"] or "{}")
            }

db_service = MetadataDB()
