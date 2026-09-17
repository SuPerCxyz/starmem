export type User = { id: string; email: string };

export type Entry = {
  id: string;
  source_id: string;
  title: string | null;
  raw_content: string;
  content_format: string;
  content_type: string;
  content_types: string[];
  source_uri: string | null;
  created_at: string;
  updated_at: string;
  event_time_start: string | null;
  event_time_end: string | null;
  deleted_at: string | null;
  is_pinned: boolean;
  is_favorite: boolean;
  importance: number;
  ai_status: string;
  ai_generation: number;
  tags: string[];
  ai_status_items: EntryAIStatusItem[];
};

export type SearchResult = {
  entry_id: string | null;
  content_unit_id: string;
  chunk_id: string | null;
  attachment_id: string | null;
  page_number: number | null;
  provenance_type: string | null;
  source_id: string;
  source_name: string;
  source_type: string;
  source_uri: string | null;
  final_url: string | null;
  external_item_id: string | null;
  external_id: string | null;
  external_url: string | null;
  external_created_at: string | null;
  imported_at: string | null;
  created_at: string | null;
  snippet: string;
  score: number;
  match_reason: string;
  exact_match: boolean;
};

export type AskSource = {
  entry_id: string | null;
  content_unit_id: string;
  chunk_id: string | null;
  attachment_id: string | null;
  page_number: number | null;
  provenance_type: string | null;
  source_id: string;
  source_name: string;
  source_type: string;
  source_uri: string | null;
  final_url: string | null;
  external_item_id: string | null;
  external_id: string | null;
  external_url: string | null;
  external_created_at: string | null;
  imported_at: string | null;
  created_at: string | null;
  snippet: string;
  score: number;
  jump_target: string | null;
};

export type AskResponse = {
  answer: string;
  confidence: number;
  is_inference: boolean;
  sources: AskSource[];
  semantic_available: boolean;
  query_understanding: Record<string, unknown>;
  chat_available: boolean;
  filtered_low_relevance?: number;
};

export type SearchResponse = {
  items: SearchResult[];
  semantic_available: boolean;
  mode: string;
  filtered_low_relevance?: number;
};

export type AIJob = {
  id: string;
  entry_id: string;
  job_type: string;
  status: string;
  provider: string | null;
  model: string | null;
  attempt: number;
  generation: number;
  error: string | null;
  latency_ms: number | null;
  token_usage: number | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export type PromptVersion = {
  id: string;
  version_number: number;
  status: string;
  prompt_text: string;
  user_instructions: string | null;
  provider: string | null;
  model: string | null;
  temperature: number | null;
  top_p: number | null;
  max_tokens: number | null;
  input_schema_version: string | null;
  output_schema_version: string | null;
  prompt_hash: string;
  created_at: string;
  created_by: string;
};

export type Prompt = { name: string; description: string | null; versions: PromptVersion[] };

export type PromptTestCase = {
  id: string;
  name: string;
  input_json: Record<string, unknown>;
  expected_json: Record<string, unknown> | null;
  is_builtin: boolean;
};

export type EntryVersion = {
  id: string;
  version_number: number;
  raw_content: string;
  title: string | null;
  change_source: string;
  created_at: string;
};

export type EntryAIStatusItem = {
  job_id: string;
  job_type: string;
  label: string;
  status: string;
  error: string | null;
};

export type EntryAIStatus = {
  entry_id: string;
  ai_status: string;
  generation: number;
  items: EntryAIStatusItem[];
};

export type RelatedEntry = {
  entry_id: string;
  title: string | null;
  score: number;
  reasons: string[];
  snippet: string;
  created_at: string;
};

export type Memory = {
  id: string;
  subject_type: string;
  subject_key: string;
  predicate: string;
  value_json: Record<string, unknown>;
  memory_text: string;
  status: string;
  salience: string;
  durable: boolean;
  confidence: number;
  recorded_at: string | null;
  observed_at: string | null;
  valid_from: string | null;
  valid_to: string | null;
  superseded_at: string | null;
  expired_at: string | null;
  source_entry_id: string | null;
  source_chunk_id: string | null;
};

export type UserSettings = {
  global_ai_instructions: string | null;
  default_source_scope: string;
  model_routing: Record<string, { provider: string; model: string }>;
};

export type SafetyScan = {
  entry_id: string;
  detected: boolean;
  findings: Array<{ type: string; line: number; column: number }>;
  content_hash: string;
  scanner_version: string;
  scanned_at: string;
};

export type SimilarEntry = {
  entry_id: string;
  title: string | null;
  score: number;
  reason: string;
  snippet: string;
  created_at: string;
};

export type Relation = {
  id: string;
  relation_type: string;
  direction: "outbound" | "inbound" | string;
  source_type: string;
  source_id: string;
  target_type: string;
  target_id: string;
  confidence: number | null;
  source: string;
  created_at: string;
  target: { id: string; title: string | null; snippet: string; created_at: string } | null;
};

export type EntryMetadata = {
  entry_id: string;
  content_type: string;
  content_types: string[];
  content_types_locked: boolean;
  importance: number;
  summary: string | null;
  summary_locked: boolean;
  project: string | null;
  project_locked: boolean;
  topic: string | null;
  topic_locked: boolean;
  image_description: string | null;
  image_description_status: string | null;
  image_description_detail: string | null;
};

export type WorkbenchSummary = {
  id: string | null;
  name: string;
  kind: string;
  status: string;
  entity_type: string | null;
  description: string | null;
  first_seen: string | null;
  last_seen: string | null;
  entry_count: number;
  memory_count: number;
  entry_ids: string[];
  memory_ids: string[];
  related: string[];
};

export type WorkbenchItem = {
  id: string;
  kind: string;
  title: string;
  entry_id: string | null;
  memory_id: string | null;
  job_id: string | null;
  status: string | null;
  detail: string | null;
  created_at: string | null;
  score: number | null;
};

export type SmartView = { id: string; name: string; description: string; items: WorkbenchItem[] };

export type Review = {
  start: string | null;
  end: string | null;
  counts: Record<string, number>;
  items: WorkbenchItem[];
};

export type Knowledge = {
  id: string;
  title: string;
  content: string;
  status: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type SavedSearch = {
  id: string;
  name: string;
  query: string;
  source_scope: string;
  filters_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type BatchReprocessResult = {
  submitted_count: number;
  failed_count: number;
  entry_ids: string[];
};

export type Attachment = {
  id: string;
  entry_id: string;
  original_filename: string;
  media_type: string;
  size_bytes: number;
  content_hash: string;
  processing_status: string;
  metadata_json: Record<string, unknown>;
  download_url: string;
  created_at: string;
};

export type Ingestion = {
  job_id: string;
  entry_id: string;
  input_kind: string;
  status: string;
  phase: string | null;
  attempt: number;
  original_name: string | null;
  media_type: string | null;
  source_uri: string | null;
  metadata_json: Record<string, unknown>;
  error_code: string | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  attachments: Attachment[];
};

export type ImportResult = {
  created_count: number;
  skipped_count: number;
  entry_ids: string[];
  errors: Array<{ index: number; error: string }>;
};

function csrfToken() {
  return document.cookie
    .split("; ")
    .find((part) => part.startsWith("starmem_csrf="))
    ?.split("=")[1];
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(init.method ?? "GET")) {
    const token = csrfToken();
    if (token) headers.set("X-CSRF-Token", decodeURIComponent(token));
  }
  const response = await fetch(`/api/v1${path}`, { ...init, headers, credentials: "include" });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? "请求失败，请稍后重试。");
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

export const api = {
  me: () => request<User>("/auth/me"),
  login: (email: string, password: string) =>
    request<{ user: User }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  entries: (cursor?: string | null, filters: { start?: string; end?: string; pinned?: boolean; favorite?: boolean } = {}) =>
    request<{ items: Entry[]; next_cursor: string | null }>(
      `/entries?${new URLSearchParams({
        ...(cursor ? { cursor } : {}),
        ...(filters.start ? { start: filters.start } : {}),
        ...(filters.end ? { end: filters.end } : {}),
        ...(filters.pinned !== undefined ? { pinned: String(filters.pinned) } : {}),
        ...(filters.favorite !== undefined ? { favorite: String(filters.favorite) } : {}),
      })}`,
    ),
  entry: (id: string) => request<Entry>(`/entries/${encodeURIComponent(id)}`),
  createEntry: (raw_content: string, title?: string) => request<Entry>("/entries", { method: "POST", body: JSON.stringify({ raw_content, ...(title ? { title } : {}) }) }),
  importNative: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<ImportResult>("/import", { method: "POST", body });
  },
  ingestUrl: (url: string, title?: string) =>
    request<Ingestion>("/ingest/url", { method: "POST", body: JSON.stringify({ url, title: title || null }) }),
  ingestFile: (file: File, title?: string) => {
    const body = new FormData();
    body.append("file", file);
    if (title) body.append("title", title);
    return request<Ingestion>("/ingest/file", { method: "POST", body });
  },
  inbox: (status?: string) => request<Ingestion[]>(`/inbox${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  retryIngestion: (id: string) => request<Ingestion>(`/inbox/${id}/retry`, { method: "POST" }),
  correctIngestion: (id: string, payload: { title?: string | null; content_type?: string | null }) =>
    request<Ingestion>(`/inbox/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  attachments: (entryId: string) => request<Attachment[]>(`/entries/${entryId}/attachments`),
  updateEntry: (id: string, changes: Partial<Pick<Entry, "title" | "raw_content" | "is_pinned" | "is_favorite">>) =>
    request<Entry>(`/entries/${id}`, { method: "PATCH", body: JSON.stringify(changes) }),
  deleteEntry: (id: string) => request<void>(`/entries/${id}`, { method: "DELETE" }),
  search: (
    query: string,
    source_scope = 'all',
    filters: {
      mode?: string;
      content_type?: string;
      tag?: string;
      entity?: string;
      project?: string;
      topic?: string;
      start?: string;
      end?: string;
      limit?: number;
    } = {},
  ) =>
    request<SearchResponse>(
      `/search?${new URLSearchParams({
        q: query,
        source_scope,
        ...(filters.mode ? { mode: filters.mode } : {}),
        ...(filters.content_type ? { content_type: filters.content_type } : {}),
        ...(filters.tag ? { tag: filters.tag } : {}),
        ...(filters.entity ? { entity: filters.entity } : {}),
        ...(filters.project ? { project: filters.project } : {}),
        ...(filters.topic ? { topic: filters.topic } : {}),
        ...(filters.start ? { start: filters.start } : {}),
        ...(filters.end ? { end: filters.end } : {}),
        ...(filters.limit ? { limit: String(filters.limit) } : {}),
      })}`,
    ),
  ask: (query: string, source_scope = 'all') =>
    request<AskResponse>('/ask', { method: 'POST', body: JSON.stringify({ query, source_scope }) }),
  jobs: () => request<AIJob[]>('/ai-jobs'),
  job: (id: string) => request<AIJob>(`/ai-jobs/${encodeURIComponent(id)}`),
  retryJob: (id: string) => request<AIJob>(`/ai-jobs/${id}/retry`, { method: 'POST' }),
  reprocessEntry: (id: string) => request<Entry>(`/entries/${id}/reprocess`, { method: 'POST' }),
  prompts: () => request<Prompt[]>('/prompts'),
  prompt: (name: string) => request<Prompt>(`/prompts/${encodeURIComponent(name)}`),
  draftPrompt: (
    name: string,
    payload: {
      user_instructions?: string | null;
      prompt_text?: string | null;
      provider?: string | null;
      model?: string | null;
      temperature?: number | null;
      top_p?: number | null;
      max_tokens?: number | null;
    },
  ) => request<PromptVersion>(`/prompts/${name}/draft`, { method: 'POST', body: JSON.stringify(payload) }),
  clonePrompt: (name: string) => request<PromptVersion>(`/prompts/${name}/clone`, { method: 'POST' }),
  previewPrompt: (name: string) =>
    request<{ name: string; version: number; schema_version: string | null; prompt_hash: string; content: string }>(
      `/prompts/${name}/preview`,
    ),
  testPrompt: (name: string, version: number) =>
    request<{ version: number; results: Array<Record<string, unknown>> }>(
      `/prompts/${name}/versions/${version}/test`,
      { method: 'POST' },
    ),
  promptTestCases: (name: string) => request<PromptTestCase[]>(`/prompts/${name}/test-cases`),
  createPromptTestCase: (name: string, payload: { name: string; input_json: Record<string, unknown>; expected_json?: Record<string, unknown> | null }) =>
    request<PromptTestCase>(`/prompts/${name}/test-cases`, { method: 'POST', body: JSON.stringify(payload) }),
  updatePromptTestCase: (name: string, caseId: string, payload: { name: string; input_json: Record<string, unknown>; expected_json?: Record<string, unknown> | null }) =>
    request<PromptTestCase>(`/prompts/${name}/test-cases/${caseId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deletePromptTestCase: (name: string, caseId: string) =>
    request<void>(`/prompts/${name}/test-cases/${caseId}`, { method: 'DELETE' }),
  promotePrompt: (name: string, version: number) =>
    request<PromptVersion>(`/prompts/${name}/versions/${version}/promote`, { method: 'POST' }),
  memories: (status = 'active') => request<Memory[]>(`/memories?status=${encodeURIComponent(status)}`),
  memory: (id: string) => request<Memory>(`/memories/${encodeURIComponent(id)}`),
  confirmMemory: (id: string) => request<Memory>(`/memories/${id}/confirm`, { method: 'POST' }),
  expireMemory: (id: string) => request<Memory>(`/memories/${id}/expire`, { method: 'POST' }),
  deleteMemory: (id: string) => request<void>(`/memories/${id}`, { method: 'DELETE' }),
  settings: () => request<UserSettings>('/settings'),
  updateSettings: (settings: Partial<UserSettings>) =>
    request<UserSettings>('/settings', { method: 'PATCH', body: JSON.stringify(settings) }),
  safety: (entryId: string) => request<SafetyScan>(`/entries/${entryId}/safety`),
  rescanSafety: (entryId: string) => request<SafetyScan>(`/entries/${entryId}/safety/rescan`, { method: 'POST' }),
  similar: (entryId: string) => request<SimilarEntry[]>(`/entries/${entryId}/similar`),
  related: (entryId: string) => request<RelatedEntry[]>(`/entries/${entryId}/related`),
  entryAiStatus: (entryId: string) => request<EntryAIStatus>(`/entries/${entryId}/ai-status`),
  entryVersions: (entryId: string) => request<EntryVersion[]>(`/entries/${entryId}/versions`),
  entryVersionDiff: (entryId: string, versionNumber: number) =>
    request<{ diff: string }>(`/entries/${entryId}/versions/${versionNumber}/diff`),
  relations: (entryId: string) => request<Relation[]>(`/entries/${entryId}/relations`),
  entryMetadata: (entryId: string) => request<EntryMetadata>(`/entries/${entryId}/metadata`),
  updateEntryMetadata: (
    entryId: string,
    payload: {
      content_type?: string | null;
      content_types?: string[] | null;
      summary?: string | null;
      project?: string | null;
      topic?: string | null;
      importance?: number | null;
    },
  ) => request<EntryMetadata>(`/entries/${entryId}/metadata`, { method: "PATCH", body: JSON.stringify(payload) }),
  entryTags: (entryId: string) => request<Array<{ id: string; name: string; source: string; user_confirmed: boolean }>>(`/entries/${entryId}/tags`),
  addEntryTag: (entryId: string, name: string) =>
    request<{ id: string; name: string; source: string; user_confirmed: boolean }>(`/entries/${entryId}/tags`, { method: "POST", body: JSON.stringify({ name }) }),
  removeEntryTag: (entryId: string, tagId: string) => request<void>(`/entries/${entryId}/tags/${tagId}`, { method: "DELETE" }),
  entryEntities: (entryId: string) => request<Array<{ id: string; canonical_name: string; entity_type: string; source: string }>>(`/entries/${entryId}/entities`),
  addEntryEntity: (entryId: string, payload: { name: string; entity_type: string }) =>
    request<{ id: string; canonical_name: string; entity_type: string; source: string }>(`/entries/${entryId}/entities`, { method: "POST", body: JSON.stringify(payload) }),
  renameWorkbenchObject: (kind: string, id: string, name: string) =>
    request<Record<string, unknown>>(`/${kind}s/${id}`, { method: "PATCH", body: JSON.stringify({ name }) }),
  mergeWorkbenchObject: (kind: string, id: string, targetId: string) =>
    request<Record<string, unknown>>(`/${kind}s/${id}/merge`, { method: "POST", body: JSON.stringify({ target_id: targetId }) }),
  excludeWorkbenchObject: (kind: string, id: string) =>
    request<Record<string, unknown>>(`/${kind}s/${id}/exclude`, { method: "POST" }),
  restoreWorkbenchObject: (kind: string, id: string) =>
    request<Record<string, unknown>>(`/${kind}s/${id}/restore`, { method: "POST" }),
  reprocessBatch: (payload: { entry_ids?: string[]; source_scope?: string; content_type?: string | null }) =>
    request<BatchReprocessResult>("/entries/reprocess-batch", { method: "POST", body: JSON.stringify(payload) }),
  rebuildEmbeddings: () =>
    request<{ accepted: boolean; detail: string }>("/maintenance/rebuild-embeddings", { method: "POST" }),
  projects: () => request<WorkbenchSummary[]>('/projects'),
  project: (id: string) => request<WorkbenchSummary>(`/projects/${id}`),
  topics: () => request<WorkbenchSummary[]>('/topics'),
  topic: (id: string) => request<WorkbenchSummary>(`/topics/${id}`),
  entities: () => request<WorkbenchSummary[]>('/entities'),
  entity: (id: string) => request<WorkbenchSummary>(`/entities/${id}`),
  review: (period = 'week') => request<Review>(`/reviews?period=${encodeURIComponent(period)}`),
  smartViews: () => request<SmartView[]>('/smart-views'),
  smartView: (id: string) => request<SmartView>(`/smart-views/${encodeURIComponent(id)}`),
  savedSearches: () => request<SavedSearch[]>('/saved-searches'),
  createSavedSearch: (payload: { name: string; query: string; source_scope: string; filters_json: Record<string, unknown> }) =>
    request<SavedSearch>('/saved-searches', { method: 'POST', body: JSON.stringify(payload) }),
  updateSavedSearch: (id: string, payload: Partial<Pick<SavedSearch, 'name' | 'query' | 'source_scope' | 'filters_json'>>) =>
    request<SavedSearch>(`/saved-searches/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteSavedSearch: (id: string) => request<void>(`/saved-searches/${id}`, { method: 'DELETE' }),
    savedSearchResults: (id: string) => request<SearchResponse>(`/saved-searches/${id}/results`),
  knowledge: () => request<Knowledge[]>('/knowledge'),
  createKnowledgeSummary: (payload: { scope_type: string; scope_value?: string | null; source_scope?: string }) =>
    request<Knowledge>('/knowledge/summaries', { method: 'POST', body: JSON.stringify(payload) }),
  status: () =>
    fetch('/api/v1/status', { credentials: 'include' }).then(async (response) => {
      if (!response.ok) throw new Error('状态读取失败');
      return (await response.json()) as {
        chat_configured: boolean;
        chat_model: string | null;
        embedding_provider: string;
        embedding_model: string;
        rate_limit_per_minute: number;
      };
    }),
};
