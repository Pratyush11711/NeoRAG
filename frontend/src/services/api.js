const API_BASE = ''; // Uses Vite proxy in development

function getHeaders(custom = {}) {
  const headers = { ...custom };
  const key = typeof localStorage !== 'undefined' ? localStorage.getItem('RAG_API_KEY') : null;
  const envKey = typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env.VITE_API_KEY : null;
  const apiKey = key || envKey;
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  return headers;
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`, {
    headers: getHeaders()
  });
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/api/documents`, {
    headers: getHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: 'POST',
    headers: getHeaders(), // note: do not set Content-Type for FormData
    body: formData
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error?.message || 'Upload failed';
    throw new Error(msg);
  }
  return data;
}

export async function ingestDocument(documentId, options = {}) {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}/ingest`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(options)
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error?.message || 'Ingestion failed';
    throw new Error(msg);
  }
  return data;
}

export async function deleteDocument(documentId) {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}`, {
    method: 'DELETE',
    headers: getHeaders()
  });
  if (!res.ok) throw new Error('Failed to delete document');
  return res.json();
}

export async function executeSearch(params) {
  const res = await fetch(`${API_BASE}/api/retrieval/search`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(params)
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error?.message || 'Search execution failed';
    throw new Error(msg);
  }
  return data;
}

export async function executeChat(params) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(params)
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error?.message || 'Chat generation failed';
    throw new Error(msg);
  }
  return data;
}

export async function fetchRuns(limit = 30) {
  const res = await fetch(`${API_BASE}/api/retrieval/runs?limit=${limit}`, {
    headers: getHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch run history');
  return res.json();
}

export async function fetchRunDetail(runId) {
  const res = await fetch(`${API_BASE}/api/retrieval/runs/${runId}`, {
    headers: getHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch run details');
  return res.json();
}

export function getDocumentDownloadUrl(documentId) {
  return `${API_BASE}/api/documents/${documentId}/download`;
}

export function getDocumentViewUrl(documentId) {
  return `${API_BASE}/api/documents/${documentId}/view`;
}

export function getReferenceDocumentUrl(filename = 'attention-is-all-you-need.pdf', download = false) {
  return `${API_BASE}/api/documents/reference/${filename}${download ? '?download=true' : ''}`;
}

export async function fetchDocumentDetails(documentId) {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}`, {
    headers: getHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch document details');
  return res.json();
}

export async function fetchDocumentRawContent(documentId) {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}/content`, {
    headers: getHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch document content');
  return res.json();
}

export async function uploadAndIngestDocument(file, onProgress = () => {}) {
  // Step 1: Upload
  onProgress({ stage: 'uploading', percent: 25, message: `Uploading ${file.name}...` });
  const uploadRes = await uploadDocument(file);
  const docId = uploadRes.document_id;

  // Step 2: Ingest
  onProgress({ stage: 'ingesting', percent: 60, message: `Parsing structure, tables, and images...` });
  const ingestRes = await ingestDocument(docId, {
    force_reprocess: true,
    max_characters: 3000,
    new_after_n_chars: 2400
  });

  onProgress({ stage: 'completed', percent: 100, message: `Ready! ${ingestRes.chunk_count} chunks indexed.` });
  return {
    ...uploadRes,
    ...ingestRes,
    document_id: docId
  };
}

export async function loadSampleDocuments() {
  const res = await fetch(`${API_BASE}/api/documents/load-sample`, {
    method: 'POST',
    headers: getHeaders()
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error?.message || 'Failed to load sample documents';
    throw new Error(msg);
  }
  return data;
}
