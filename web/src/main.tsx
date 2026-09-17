import { QueryClient, QueryClientProvider, useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Archive,
  BrainCircuit,
  Check,
  ChevronDown,
  Clock3,
  Copy,
  Download,
  ExternalLink,
  FileText,
  Inbox,
  Link2,
  Pin,
  RotateCcw,
  Search,
  Settings,
  Sparkles,
  Star,
  Trash2,
  Upload,
  X,
  Plus,
  ArrowUp,
  Paperclip,
  MoreHorizontal,
} from "./components/icons";
import { AIStatus, DetailRail, EmptyState, ErrorState, FilterBar, LoadingState, ManagementNav, PageFrame, PageHeader, SectionHeader, SourceItem, aiStatusKind, ui } from "./components/ui";
import { recentQuestions, recentSearches } from "./lib/recent-activity";
import { activeShellPage, navigateTo, parseRoute, type ManagementSection, type PromptView, type ShellPage, type WorkspaceRoute } from "./lib/routes";
import { DragEvent, FormEvent, KeyboardEvent, useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import { createRoot } from "react-dom/client";
import { api, AIJob, Entry, EntryMetadata, EntryVersion, Ingestion, Memory, Relation, SearchResult, WorkbenchItem } from "./api";
import { AppShell } from "./components/AppShell";
import { TablerTypographyFixture } from "./components/TablerTypographyFixture";
import { initTabler, watchTheme } from "./theme/tabler";
import { readAndClearSharedPayload, sharedFiles, SharedPayload } from "./share";
import "./styles.css";

const queryClient = new QueryClient();
const DRAFT_KEY = "starmem:capture-draft";

function parseJsonObject(value: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? (parsed as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    void navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  });
}

type Page = WorkspaceRoute["page"];

function LoginScreen() {
  const [email, setEmail] = useState("admin@starmem.local");
  const [password, setPassword] = useState("");
  const login = useMutation({ mutationFn: () => api.login(email, password) });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    login.mutate();
  }

  useEffect(() => {
    if (login.isSuccess) queryClient.invalidateQueries({ queryKey: ["me"] });
  }, [login.isSuccess]);

  return (
    <main className="page page-center" id="content">
      <div className="container container-tight py-4">
        <div className="text-center mb-4">
          <a href="/" className="navbar-brand navbar-brand-autodark">
            <img src="/starmem-logo.png" width="32" height="32" alt="" className="navbar-brand-image" aria-hidden="true" />
            <span>StarMem</span>
          </a>
        </div>
        <form className="card card-md" onSubmit={submit}>
          <div className="card-body">
            <h1 className="h2 text-center mb-4">欢迎回到 StarMem</h1>
            <p className="text-secondary text-center mb-4">你负责忘记，StarMem 负责记住。</p>
            <div className="mb-3">
              <label className="form-label" htmlFor="login-email">邮箱</label>
              <input id="login-email" className="form-control" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="login-password">密码</label>
              <input id="login-password" type="password" className="form-control" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
            </div>
            {login.error && <div className="alert alert-danger" role="alert">{login.error.message}</div>}
            <button className="btn btn-primary w-100" disabled={login.isPending}>
              {login.isPending ? "正在登录…" : "登录 StarMem"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}

function Capture({ onSaved, onOpenInbox, sharedPayload }: { onSaved: () => void; onOpenInbox: () => void; sharedPayload?: SharedPayload | null }) {
  const [content, setContent] = useState(() => localStorage.getItem(DRAFT_KEY) ?? "");
  const [mode, setMode] = useState<"text" | "url" | "file">("text");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [sharedUrl, setSharedUrl] = useState("");
  const [sharedTitle, setSharedTitle] = useState("");
  const [message, setMessage] = useState("");
  const [dragging, setDragging] = useState(false);
  // Tabler data API 负责官方交互；React 状态只管理业务提交与动态列表。
  const [addMenuOpen, setAddMenuOpen] = useState(false);
  const save = useMutation({
    mutationFn: () => api.createEntry(content, sharedTitle || undefined),
    onSuccess: () => {
      setContent("");
      setSharedUrl("");
      setSharedTitle("");
      localStorage.removeItem(DRAFT_KEY);
      setMessage("已保存到时间线。");
      onSaved();
    },
  });
  const importUrl = useMutation({
    mutationFn: () => api.ingestUrl(url, sharedTitle || undefined),
    onSuccess: () => {
      setUrl("");
      setSharedUrl("");
      setSharedTitle("");
      setMessage("网页已进入 Inbox，正在抓取快照。");
      onSaved();
    },
  });
  const importFile = useMutation({
    mutationFn: () => api.ingestFile(file!, sharedTitle || undefined),
    onSuccess: () => {
      setFile(null);
      setSharedTitle("");
      setMessage("文件已进入 Inbox，正在处理。");
      onSaved();
    },
  });

  useEffect(() => {
    if (!sharedPayload) return;
    if (sharedPayload.error) {
      setMessage(sharedPayload.error === "oversize" ? "分享内容超过本地上限，请改用 Capture 文件入口。" : "没有读取到分享内容，请重新分享或直接输入。");
      return;
    }
    setSharedTitle(sharedPayload.title || "");
    if (sharedPayload.files.length > 0) {
      try {
        setFile(sharedFiles(sharedPayload)[0]);
        setMode("file");
        setMessage(`已接收分享文件：${sharedPayload.files[0].name}`);
      } catch {
        setMessage("分享文件无法在此浏览器中读取，请重新选择文件。");
      }
      return;
    }
    if (sharedPayload.text.trim()) {
      setContent(sharedPayload.text);
      setSharedUrl(sharedPayload.url.trim());
      setMode("text");
      setMessage("已接收分享文本，可编辑后保存。");
      return;
    }
    if (sharedPayload.url.trim()) {
      setUrl(sharedPayload.url.trim());
      setMode("url");
      setMessage("已接收分享网页，可确认后保存。");
      return;
    }
    setMessage("分享内容为空，请重新分享或直接输入。");
  }, [sharedPayload]);

  useEffect(() => {
    localStorage.setItem(DRAFT_KEY, content);
  }, [content]);

  function submitText(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (content.trim()) save.mutate();
  }

  function handleTextKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      if (!content.trim()) {
        setMessage("内容为空，无法保存。");
        return;
      }
      save.mutate();
    }
  }

  function submitUrl(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (url.trim()) importUrl.mutate();
  }

  function submitFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (file) importFile.mutate();
  }

  function handleDrop(event: DragEvent<HTMLFormElement>) {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  const pending = save.isPending || importUrl.isPending || importFile.isPending;
  const error = save.error ?? importUrl.error ?? importFile.error;

  const menuItemClass = "dropdown-item d-flex align-items-center gap-2";
  const primaryButtonClass = "btn btn-primary";
  const fieldClass = "form-control";

  return (
    <div>
      {message && <p className="mb-3 text-sm text-secondary" aria-live="polite">{message}</p>}

      {mode === "text" && (
        <form onSubmit={submitText}>
          <div className="bg-body-tertiary border border-secondary rounded ">
            <label className="visually-hidden" htmlFor="capture-content">记录内容</label>
            <div className="pb-2 px-2">
              <textarea
                id="capture-content"
                className="overflow-auto mt-2 pt-4 pb-2 ps-2 pe-4 d-block w-100 bg-transparent border-0 text-body       overflow-auto   "
                value={content}
                onChange={(event) => setContent(event.target.value)}
                onKeyDown={handleTextKeyDown}
                placeholder="记录想法、日志、命令、配置或任何需要记住的内容…"
              />
              <div className="pt-2 d-flex justify-content-between align-items-center column-gap-1">
                <div className="d-flex align-items-center column-gap-1">
                  <div className="dropdown">
                    <button
                      id="capture-add"
                      type="button"
                      className="btn btn-action"
                      data-bs-toggle="dropdown"
                      aria-haspopup="menu"
                      aria-expanded={addMenuOpen}
                      aria-label="添加内容"
                      onClick={() => setAddMenuOpen((value) => !value)}
                    >
                      <Plus className="flex-shrink-0 icon icon-sm" aria-hidden="true" />
                    </button>
                    <div
                      className={`dropdown-menu${addMenuOpen ? " show" : ""}`}
                      role="menu"
                      aria-orientation="vertical"
                      aria-labelledby="capture-add"
                    >
                      <div className="p-1 space-y-1">
                        <button type="button" className={menuItemClass} onClick={() => { setAddMenuOpen(false); setMode("url"); }}>
                          <Link2 className="flex-shrink-0 icon icon-sm" aria-hidden="true" />
                          网页 URL
                        </button>
                        <button type="button" className={menuItemClass} onClick={() => { setAddMenuOpen(false); setMode("file"); }}>
                          <Paperclip className="flex-shrink-0 icon icon-sm" aria-hidden="true" />
                          文件 / 图片
                        </button>
                        {sharedUrl && (
                          <button type="button" className={menuItemClass} onClick={() => { setAddMenuOpen(false); setUrl(sharedUrl); setMode("url"); }}>
                            <ExternalLink className="flex-shrink-0 icon icon-sm" aria-hidden="true" />
                            改用分享的网页
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="d-flex align-items-center column-gap-1">
                  <span className="d-none d-sm-block small text-secondary me-1">支持 Markdown 和代码块</span>
                  <button type="submit" className={`${primaryButtonClass} icon icon-lg p-0`} disabled={!content.trim() || pending} aria-label="保存记录">
                    <ArrowUp className="flex-shrink-0 icon icon-sm" aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </form>
      )}

      {mode === "url" && (
        <form onSubmit={submitUrl} className="bg-body-tertiary border border-secondary rounded  p-3 space-y-3">
          <label className="d-block" htmlFor="capture-url">
            <span className="d-block mb-2 text-sm text-body">网页地址</span>
            <input id="capture-url" type="url" className={fieldClass} value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com/article" required />
          </label>
          <div className="d-flex align-items-center justify-content-between column-gap-2">
            <span className="small text-secondary">保存原 URL 与网页快照，后续可在 Inbox 查看</span>
            <div className="d-flex align-items-center column-gap-1">
              <button type="button" className="btn btn-ghost-secondary" onClick={() => setMode("text")}>返回文字</button>
              <button type="submit" className={primaryButtonClass} disabled={!url.trim() || pending}>{importUrl.isPending ? "正在排队…" : "保存网页"}</button>
            </div>
          </div>
        </form>
      )}

      {mode === "file" && (
        <form
          onSubmit={submitFile}
          className={`dropzone${dragging ? " dz-drag-hover" : ""}`}
          onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={(event) => { event.preventDefault(); setDragging(false); }}
          onDrop={handleDrop}
        >
          <div className="fallback visually-hidden">
            <input id="capture-file" aria-label="选择文件" type="file" className="visually-hidden" accept=".txt,.md,.markdown,.json,.yaml,.yml,.log,.pdf,image/png,image/jpeg,image/webp,image/gif,image/bmp,image/tiff" onChange={(event) => setFile(event.target.files?.[0] ?? null)} required={!file} />
          </div>
          <div className="dz-message">
            <Upload className="icon icon-lg text-secondary" aria-hidden="true" />
            <h3 className="dropzone-msg-title mt-2">拖放文件到这里</h3>
            <span className="dropzone-msg-desc small text-secondary">支持 TXT、Markdown、JSON、YAML、Log、PDF 和图片</span>
            <label className="btn btn-sm mt-3" htmlFor="capture-file">选择文件</label>
          </div>
          {file && <div className="d-flex align-items-center justify-content-between column-gap-3 rounded border border-secondary bg-body-tertiary px-3 py-2 text-sm">
            <span className="d-flex  align-items-center column-gap-2 text-body"><Paperclip className="icon icon-sm flex-shrink-0 text-secondary" aria-hidden="true" /><span className="text-truncate">{file.name}</span><span className="flex-shrink-0 small text-secondary">{(file.size / 1024).toFixed(1)} KB</span></span>
            <button className="btn btn-link p-0 flex-shrink-0" type="button" onClick={() => setFile(null)}>移除</button>
          </div>}
          <div className="d-flex align-items-center justify-content-between column-gap-2">
            <span className="small text-secondary">文件会先进入 Inbox，再异步处理。</span>
            <div className="d-flex align-items-center column-gap-1">
              <button type="button" className="btn btn-ghost-secondary" onClick={() => setMode("text")}>返回文字</button>
              <button type="submit" className={primaryButtonClass} disabled={!file || pending}>{importFile.isPending ? "正在排队…" : "导入文件"}</button>
            </div>
          </div>
        </form>
      )}

      {error && <p className="mt-3 text-sm text-danger" role="alert">{error.message}</p>}
      {message && <button className="btn btn-link p-0 mt-3" type="button" onClick={onOpenInbox}>查看 Inbox 状态</button>}
    </div>
  );
}

function EntryCard({ entry, focused = false, onOpenEntry, onOpenDetail, variant = "card" }: { entry: Entry; focused?: boolean; onOpenEntry?: (entryId: string) => void; onOpenDetail?: (entryId: string) => void; variant?: "card" | "feed" }) {
  const client = useQueryClient();
  const [detailOpen, setDetailOpen] = useState(false);
  const [fullText, setFullText] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(entry.raw_content);
  const safety = useQuery({ queryKey: ["safety", entry.id], queryFn: () => api.safety(entry.id), enabled: detailOpen });
  const related = useQuery({ queryKey: ["related", entry.id], queryFn: () => api.related(entry.id), enabled: detailOpen });
  const relations = useQuery({ queryKey: ["relations", entry.id], queryFn: () => api.relations(entry.id), enabled: detailOpen });
  const metadata = useQuery({ queryKey: ["entry-metadata", entry.id], queryFn: () => api.entryMetadata(entry.id), enabled: detailOpen });
  const tags = useQuery({ queryKey: ["entry-tags", entry.id], queryFn: () => api.entryTags(entry.id), enabled: detailOpen });
  const entities = useQuery({ queryKey: ["entry-entities", entry.id], queryFn: () => api.entryEntities(entry.id), enabled: detailOpen });
  const versions = useQuery({ queryKey: ["entry-versions", entry.id], queryFn: () => api.entryVersions(entry.id), enabled: historyOpen });
  const [metadataDraft, setMetadataDraft] = useState<EntryMetadata | null>(null);
  const [tagDraft, setTagDraft] = useState("");
  const [entityDraft, setEntityDraft] = useState("");
  const [entityTypeDraft, setEntityTypeDraft] = useState("host");
  const [metadataMessage, setMetadataMessage] = useState("");
  // Tabler data API 负责官方交互；React 状态只管理业务提交与动态列表。
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (metadata.data) setMetadataDraft(metadata.data);
  }, [metadata.data]);

  // 动态列表挂载后初始化官方 Tabler data API。
  useEffect(() => {
    initTabler();
  }, []);
  const saveMetadata = useMutation({
    mutationFn: (changes: Partial<EntryMetadata>) => api.updateEntryMetadata(entry.id, changes),
    onSuccess: (result) => {
      setMetadataDraft(result);
      setMetadataMessage("Metadata 已保存，AI 重跑不会覆盖用户锁定值。");
      client.invalidateQueries({ queryKey: ["entry-metadata", entry.id] });
      client.invalidateQueries({ queryKey: ["entries"] });
    },
    onError: (error) => setMetadataMessage(error.message),
  });
  const addTag = useMutation({
    mutationFn: () => api.addEntryTag(entry.id, tagDraft.trim()),
    onSuccess: () => {
      setTagDraft("");
      setMetadataMessage("标签已锁定为用户确认。");
      client.invalidateQueries({ queryKey: ["entry-tags", entry.id] });
    },
    onError: (error) => setMetadataMessage(error.message),
  });
  const removeTag = useMutation({
    mutationFn: (tagId: string) => api.removeEntryTag(entry.id, tagId),
    onSuccess: () => client.invalidateQueries({ queryKey: ["entry-tags", entry.id] }),
  });
  const addEntity = useMutation({
    mutationFn: () => api.addEntryEntity(entry.id, { name: entityDraft.trim(), entity_type: entityTypeDraft.trim() || "host" }),
    onSuccess: () => {
      setEntityDraft("");
      setMetadataMessage("实体已标记为用户来源。");
      client.invalidateQueries({ queryKey: ["entry-entities", entry.id] });
    },
    onError: (error) => setMetadataMessage(error.message),
  });
  const update = useMutation({
    mutationFn: (changes: Partial<Pick<Entry, "raw_content" | "is_pinned" | "is_favorite">>) => api.updateEntry(entry.id, changes),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["entries"] });
      client.invalidateQueries({ queryKey: ["safety", entry.id] });
      client.invalidateQueries({ queryKey: ["related", entry.id] });
    },
  });
  const remove = useMutation({
    mutationFn: () => api.deleteEntry(entry.id),
    onSuccess: () => client.invalidateQueries({ queryKey: ["entries"] }),
  });
  const reprocess = useMutation({
    mutationFn: () => api.reprocessEntry(entry.id),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["entries"] });
      client.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
  const retryStep = useMutation({
    mutationFn: (jobId: string) => api.retryJob(jobId),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["entries"] });
      client.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const timestamp = new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit" }).format(new Date(entry.created_at));
  const statusText = entry.ai_status === "pending" ? "等待 AI 处理" : entry.ai_status === "retrying" ? "等待重试" : entry.ai_status === "partial" ? "部分处理完成" : entry.ai_status === "failed" ? "AI 处理失败" : "已索引";
  const displayTypes = metadataDraft?.content_types?.length ? metadataDraft.content_types : (entry.content_types.length ? entry.content_types : [entry.content_type]);

  async function copyContent() {
    await navigator.clipboard?.writeText(entry.raw_content);
  }

  const iconButtonClass = "btn btn-action";

  return (
    <article className={`${variant === "card" ? `${ui.card} p-4` : "entry-feed border-bottom border-secondary py-4 "} entry-card ${focused ? "border-primary" : ""}`} id={`entry-${entry.id}`}>
      <div className="entry-meta d-flex flex-wrap align-items-center column-gap-2 row-gap-1 mb-2">
        <time dateTime={entry.created_at} className="small font-monospace text-secondary">{timestamp}</time>
        {displayTypes.map((type) => <span className={ui.chip} key={type}>{type}</span>)}
        {entry.is_pinned && <Pin aria-label="已置顶" className="icon icon-sm text-secondary" />}
        {entry.tags.length > 0 && <span className="d-flex flex-wrap align-items-center column-gap-1" aria-label="标签">{entry.tags.slice(0, 4).map((tag) => <span className={ui.chip} key={tag}>{tag}</span>)}</span>}
      </div>

      {editing ? (
        <div className="space-y-3">
          <label className="visually-hidden" htmlFor={`entry-${entry.id}`}>编辑记录</label>
          <textarea id={`entry-${entry.id}`} className={ui.input} value={draft} onChange={(event) => setDraft(event.target.value)} rows={7} />
          <div className="d-flex align-items-center justify-content-end column-gap-2">
            <button className={ui.secondaryButton} onClick={() => { setDraft(entry.raw_content); setEditing(false); }} type="button">取消</button>
            <button className={ui.primaryButton} onClick={() => update.mutate({ raw_content: draft })} disabled={!draft.trim() || update.isPending} type="button">保存修改</button>
          </div>
        </div>
      ) : (
        <button className="entry-content btn btn-link p-0 w-100 d-block overflow-hidden text-start text-body text-decoration-none" type="button" onClick={() => setFullText((value) => !value)} aria-expanded={fullText}>
          <ReactMarkdown components={{ pre: ({ children }) => <pre className="mw-100 overflow-auto text-break">{children}</pre> }}>{fullText ? entry.raw_content : `${entry.raw_content.slice(0, 420)}${entry.raw_content.length > 420 ? "…" : ""}`}</ReactMarkdown>
        </button>
      )}

      <div className="entry-ai-steps mt-3 d-flex align-items-center justify-content-between column-gap-2 border-top border-secondary pt-2">
        <div className="d-flex  align-items-center column-gap-3"><AIStatus status={aiStatusKind(entry.ai_status)} onClick={() => setDetailOpen(true)} />{onOpenDetail && <button className={`${ui.textButton} flex-shrink-0`} type="button" onClick={() => onOpenDetail(entry.id)}>详情</button>}</div>
        <div className="d-flex align-items-center column-gap-1">
          <button className={iconButtonClass} type="button" aria-label={entry.is_favorite ? "取消收藏" : "收藏记录"} onClick={() => update.mutate({ is_favorite: !entry.is_favorite })}>
            <Star className={entry.is_favorite ? "icon icon-sm text-primary" : "icon icon-sm"} aria-hidden="true" />
          </button>
          <div className="dropdown">
            <button id={`entry-menu-${entry.id}`} type="button" className={iconButtonClass} data-bs-toggle="dropdown" aria-label="更多操作" aria-haspopup="menu" aria-expanded={menuOpen} onClick={() => setMenuOpen((value) => !value)}>
              <MoreHorizontal className="icon icon-sm" aria-hidden="true" />
            </button>
            <div className={`dropdown-menu dropdown-menu-end${menuOpen ? " show" : ""}`} role="menu" aria-orientation="vertical" aria-labelledby={`entry-menu-${entry.id}`}>
              <div className="p-1 space-y-1">
                <button type="button" className={ui.menuItem} onClick={() => { setMenuOpen(false); void copyContent(); }}><Copy className="flex-shrink-0 icon icon-sm" aria-hidden="true" />复制</button>
                <button type="button" className={ui.menuItem} onClick={() => { setMenuOpen(false); update.mutate({ is_pinned: !entry.is_pinned }); }}><Pin className="flex-shrink-0 icon icon-sm" aria-hidden="true" />{entry.is_pinned ? "取消固定" : "固定"}</button>
                <button type="button" className={ui.menuItem} onClick={() => { setMenuOpen(false); setEditing(true); }}><FileText className="flex-shrink-0 icon icon-sm" aria-hidden="true" />编辑</button>
                <button type="button" className={ui.menuItem} onClick={() => { setMenuOpen(false); setHistoryOpen(true); }}><Clock3 className="flex-shrink-0 icon icon-sm" aria-hidden="true" />查看历史</button>
                <button type="button" className={ui.menuItem} onClick={() => { setMenuOpen(false); reprocess.mutate(); }} disabled={reprocess.isPending}><RotateCcw className="flex-shrink-0 icon icon-sm" aria-hidden="true" />重新 AI 处理</button>
                <button type="button" className={`${ui.menuItem} text-danger`} onClick={() => { setMenuOpen(false); remove.mutate(); }}><Trash2 className="flex-shrink-0 icon icon-sm" aria-hidden="true" />删除</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {detailOpen && (
        <>
          <button className="offcanvas-backdrop fade show" type="button" aria-label="关闭 AI 详情" onClick={() => setDetailOpen(false)} />
          <div className="offcanvas offcanvas-end show" tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby={`entry-detail-${entry.id}`}>
            <div className="offcanvas-header">
              <h3 id={`entry-detail-${entry.id}`} className="text-sm fw-medium text-body">AI 详情</h3>
              <button className={iconButtonClass} type="button" aria-label="关闭" onClick={() => setDetailOpen(false)}><X className="icon icon-sm" aria-hidden="true" /></button>
            </div>
            <div className="offcanvas-body space-y-5 text-sm">
              <section className="space-y-2">
                <h4 className={ui.sectionTitle}>处理进度</h4>
                {entry.ai_status_items.length === 0 && <p className="text-secondary">暂无 AI 处理项。</p>}
                {entry.ai_status_items.map((item) => (
                  <div className="d-flex flex-wrap align-items-center column-gap-2 text-secondary" key={item.job_type} title={item.error ?? undefined}>
                    <span>{item.label}：{item.status === "done" ? "完成" : item.status === "failed" || item.status === "prompt_validation_failed" ? "失败" : item.status === "running" ? "处理中" : item.status === "skipped" ? (item.error === "provider_not_configured" ? "已跳过（未配置）" : "已跳过") : "等待"}</span>
                    {["failed", "prompt_validation_failed", "retrying"].includes(item.status) && <button className={ui.textButton} type="button" onClick={() => retryStep.mutate(item.job_id)} disabled={retryStep.isPending}>重试</button>}
                  </div>
                ))}
              </section>

              <section className="space-y-2">
                <h4 className={ui.sectionTitle}>本地安全扫描</h4>
                {safety.isPending && <span className="d-block text-secondary">正在检查…</span>}
                {safety.data?.detected && <div className="d-flex flex-wrap align-items-center column-gap-3 row-gap-1 rounded border border-danger bg-body-tertiary px-3 py-2 text-danger" role="status"><strong>发现可能的敏感信息</strong><span className="flex-grow-1">{safety.data.findings.map((finding) => `${finding.type}（第 ${finding.line} 行）`).join("、")}</span><button className={ui.textButton} type="button" onClick={() => void safety.refetch()} disabled={safety.isFetching}>重新扫描</button></div>}
                {safety.data && !safety.data.detected && <span className="d-block text-primary">未发现已知敏感模式</span>}
              </section>

              <section className="space-y-3">
                <h4 className={ui.sectionTitle}>AI Metadata（可人工修正）</h4>
                <div className="d-flex flex-wrap align-items-center column-gap-3 row-gap-1 small text-secondary"><span>Source</span><code className="text-break">{entry.source_id}</code><span>Generation</span><strong className="text-body">{entry.ai_generation}</strong><span>Status</span><strong className="text-body">{statusText}</strong></div>
                {metadataDraft?.image_description && <div className="space-y-1"><strong className="d-block fw-medium text-body">图片描述（AI 派生）</strong><p className="text-secondary">{metadataDraft.image_description}</p></div>}
                {metadataDraft?.image_description_status === "skipped" && <span className="d-block text-secondary">图片描述已降级：{metadataDraft.image_description_detail === "image_description_disabled" ? "未启用图片描述 Provider" : metadataDraft.image_description_detail ?? "Provider 不可用"}</span>}
                {metadataDraft && <div className="space-y-3">
                  <label className="d-block"><span className={ui.label}>类型（多个用逗号分隔，第一个为主分类）{metadataDraft.content_types_locked && <span className={ui.chip}>用户锁定</span>}</span><input className={ui.input} aria-label="Metadata 类型" value={metadataDraft.content_types.join(", ")} onChange={(event) => setMetadataDraft({ ...metadataDraft, content_types: event.target.value.split(",").map((value) => value.trim()).filter(Boolean) })} /></label>
                  <label className="d-block"><span className={ui.label}>Importance（0–100）</span><input className={ui.input} aria-label="Metadata Importance" type="number" min={0} max={100} value={metadataDraft.importance} onChange={(event) => setMetadataDraft({ ...metadataDraft, importance: Number(event.target.value) })} /></label>
                  <label className="d-block"><span className={ui.label}>Summary {metadataDraft.summary_locked && <span className={ui.chip}>用户锁定</span>}</span><textarea className={ui.input} aria-label="Metadata Summary" rows={3} value={metadataDraft.summary ?? ""} onChange={(event) => setMetadataDraft({ ...metadataDraft, summary: event.target.value })} placeholder="留空表示撤销用户 Summary 锁定" /></label>
                  <label className="d-block"><span className={ui.label}>Project {metadataDraft.project_locked && <span className={ui.chip}>用户锁定</span>}</span><input className={ui.input} aria-label="Metadata Project" value={metadataDraft.project ?? ""} onChange={(event) => setMetadataDraft({ ...metadataDraft, project: event.target.value })} placeholder="需已存在于 Workbench" /></label>
                  <label className="d-block"><span className={ui.label}>Topic {metadataDraft.topic_locked && <span className={ui.chip}>用户锁定</span>}</span><input className={ui.input} aria-label="Metadata Topic" value={metadataDraft.topic ?? ""} onChange={(event) => setMetadataDraft({ ...metadataDraft, topic: event.target.value })} placeholder="需已存在于 Workbench" /></label>
                  <div className="d-flex flex-wrap align-items-center column-gap-3 row-gap-2"><button className={ui.primaryButton} type="button" disabled={saveMetadata.isPending} onClick={() => saveMetadata.mutate({ content_types: metadataDraft.content_types, importance: metadataDraft.importance, summary: metadataDraft.summary?.trim() ? metadataDraft.summary : null, project: metadataDraft.project?.trim() ? metadataDraft.project : null, topic: metadataDraft.topic?.trim() ? metadataDraft.topic : null })}>{saveMetadata.isPending ? "保存中…" : "保存 Metadata"}</button></div>
                  <div className="row g-3 row-cols-sm-2">
                    <div><strong className="d-block fw-medium text-body">标签</strong>{tags.data?.length ? tags.data.map((tag) => <span className="d-flex align-items-center justify-content-between column-gap-2 border-top border-secondary py-1" key={tag.id}><span>{tag.name}{tag.user_confirmed ? "（用户）" : ""}</span><button className={ui.textButton} type="button" onClick={() => removeTag.mutate(tag.id)}>移除</button></span>) : <span className="text-secondary">暂无标签</span>}<div className="mt-2 d-flex flex-wrap align-items-center gap-2"><input className={`${ui.input}  flex-grow-1`} aria-label="新标签" value={tagDraft} onChange={(event) => setTagDraft(event.target.value)} placeholder="添加标签" /><button className={ui.secondaryButton} type="button" disabled={!tagDraft.trim() || addTag.isPending} onClick={() => addTag.mutate()}>添加</button></div></div>
                    <div><strong className="d-block fw-medium text-body">实体</strong>{entities.data?.length ? entities.data.map((entity) => <span className="d-flex align-items-center justify-content-between column-gap-2 border-top border-secondary py-1" key={entity.id}><span>{entity.canonical_name} · {entity.entity_type}{entity.source === "user" ? "（用户）" : ""}</span></span>) : <span className="text-secondary">暂无实体</span>}<div className="mt-2 d-flex flex-wrap align-items-center gap-2"><input className={`${ui.input}  flex-grow-1`} aria-label="新实体名称" value={entityDraft} onChange={(event) => setEntityDraft(event.target.value)} placeholder="名称" /><input className={`${ui.input}  flex-grow-1`} aria-label="新实体类型" value={entityTypeDraft} onChange={(event) => setEntityTypeDraft(event.target.value)} placeholder="类型" /><button className={ui.secondaryButton} type="button" disabled={!entityDraft.trim() || addEntity.isPending} onClick={() => addEntity.mutate()}>添加</button></div></div>
                  </div>
                  {metadataMessage && <p className="text-secondary" role="status">{metadataMessage}</p>}
                </div>}
              </section>

              <section className="space-y-2">
                <h4 className={ui.sectionTitle}>相关记录</h4>
                {related.isPending && <span className="d-block text-secondary">正在查找相关记录…</span>}
                {related.data && related.data.length === 0 && <span className="d-block text-secondary">暂无可复用的相关记录。</span>}
                {related.data?.map((candidate) => <div className="d-flex align-items-center justify-content-between column-gap-3 border-top border-secondary pt-2" key={candidate.entry_id}><span className="">{candidate.title || candidate.snippet.slice(0, 80)} <small className="d-block small fw-normal text-secondary">{Math.round(candidate.score * 100)}% · {candidate.reasons.join(" / ")}</small></span>{onOpenEntry && <button className={`${ui.textButton} flex-shrink-0`} type="button" onClick={() => onOpenEntry(candidate.entry_id)}>查看</button>}</div>)}
              </section>

              <section className="space-y-2">
                <h4 className={ui.sectionTitle}>AI 关系</h4>
                {relations.isPending && <span className="d-block text-secondary">正在读取关系…</span>}
                {relations.error && <span className="d-block text-danger" role="alert">相关记录读取失败：{relations.error.message}</span>}
                {relations.data && relations.data.length === 0 && <span className="d-block text-secondary">暂无 AI 关系；重新处理 Entry 后可能生成。</span>}
                {relations.data?.map((relation: Relation) => <div className="d-flex align-items-center justify-content-between column-gap-3 border-top border-secondary pt-2" key={relation.id}><span className="">{relation.direction === "outbound" ? "→" : "←"} {relation.relation_type} · {relation.target?.title || relation.target?.snippet.slice(0, 80) || `${relation.target_type} ${relation.target_id.slice(0, 8)}`} <small className="d-block small fw-normal text-secondary">{relation.confidence !== null ? `${Math.round(relation.confidence * 100)}% · ` : ""}{relation.source}</small></span>{relation.target && onOpenEntry && <button className={`${ui.textButton} flex-shrink-0`} type="button" onClick={() => onOpenEntry(relation.target!.id)}>查看</button>}</div>)}
              </section>
            </div>
          </div>
        </>
      )}

      {historyOpen && (
        <>
          <button className="offcanvas-backdrop fade show" type="button" aria-label="关闭历史" onClick={() => setHistoryOpen(false)} />
          <div className="offcanvas offcanvas-end show" tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby={`entry-history-${entry.id}`}>
            <div className="offcanvas-header">
              <h3 id={`entry-history-${entry.id}`} className="text-sm fw-medium text-body">查看历史</h3>
              <button className={iconButtonClass} type="button" aria-label="关闭" onClick={() => setHistoryOpen(false)}><X className="icon icon-sm" aria-hidden="true" /></button>
            </div>
            <div className="offcanvas-body space-y-3">
              {versions.isPending && <p className="text-sm text-secondary">正在读取版本…</p>}
              {versions.error && <p className="text-sm text-danger" role="alert">{versions.error.message}</p>}
              {versions.data && versions.data.length === 0 && <p className="text-sm text-secondary">尚无历史版本。</p>}
              {versions.data?.map((version) => (
                <div className="rounded border border-secondary bg-body p-3" key={version.id}>
                  <div className="d-flex flex-wrap align-items-center column-gap-2 row-gap-1 small text-secondary">
                    <span className={ui.chip}>v{version.version_number}</span>
                    <span>{version.change_source}</span>
                    <span>{new Date(version.created_at).toLocaleString("zh-CN")}</span>
                  </div>
                  <pre className="mt-2 overflow-auto overflow-auto text-break small text-body">{version.raw_content}</pre>
                  <VersionDiff entryId={entry.id} versionNumber={version.version_number} />
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </article>
  );
}

function VersionDiff({ entryId, versionNumber }: { entryId: string; versionNumber: number }) {
  const [open, setOpen] = useState(false);
  const diff = useQuery({
    queryKey: ["entry-version-diff", entryId, versionNumber],
    queryFn: () => api.entryVersionDiff(entryId, versionNumber),
    enabled: open,
  });
  return (
    <div className="mt-2">
      <button className={ui.textButton} type="button" onClick={() => setOpen((value) => !value)}>{open ? "收起差异" : "查看差异"}</button>
      {open && <pre className="mt-2 overflow-auto overflow-auto text-break rounded border border-secondary bg-body-tertiary p-2 small text-body">{diff.isPending ? "正在计算…" : diff.data?.diff || "无差异"}</pre>}
    </div>
  );
}

function Timeline({ focusEntryId, onOpenEntry, onOpenDetail }: { focusEntryId?: string | null; onOpenEntry?: (entryId: string) => void; onOpenDetail?: (entryId: string) => void }) {
  const [preset, setPreset] = useState("all");
  const [flag, setFlag] = useState("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const range = useMemo(() => {
    if (startDate || endDate) {
      return {
        ...(startDate ? { start: new Date(`${startDate}T00:00:00`).toISOString() } : {}),
        ...(endDate ? { end: new Date(`${endDate}T23:59:59`).toISOString() } : {}),
      };
    }
    if (preset === "all") return {};
    const now = new Date();
    const today = new Date(now);
    today.setHours(0, 0, 0, 0);
    if (preset === "today") return { start: today.toISOString() };
    if (preset === "yesterday") {
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      return { start: yesterday.toISOString(), end: today.toISOString() };
    }
    if (preset === "week") {
      const week = new Date(today);
      week.setDate(week.getDate() - ((week.getDay() + 6) % 7));
      return { start: week.toISOString() };
    }
    const month = new Date(today.getFullYear(), today.getMonth(), 1);
    return { start: month.toISOString() };
  }, [preset, startDate, endDate]);
  const entries = useInfiniteQuery({
    queryKey: ["entries", preset, flag, startDate, endDate],
    queryFn: ({ pageParam }) => api.entries(pageParam, { ...range, ...(flag === "pinned" ? { pinned: true } : {}), ...(flag === "favorite" ? { favorite: true } : {}) }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  });
  const groups = useMemo(() => {
    const values = entries.data?.pages.flatMap((page) => page.items) ?? [];
    return values.reduce<Record<string, Entry[]>>((all, entry) => {
      const date = new Date(entry.created_at);
      const day = `${new Intl.DateTimeFormat("zh-CN", { month: "long", day: "numeric" }).format(date)} · ${new Intl.DateTimeFormat("zh-CN", { weekday: "long" }).format(date)}`;
      (all[day] ??= []).push(entry);
      return all;
    }, {});
  }, [entries.data]);

  useEffect(() => {
    if (!focusEntryId || !entries.data) return;
    document.getElementById(`entry-${focusEntryId}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [entries.data, focusEntryId]);

  // 列表数据渲染后重新初始化官方 Tabler 交互组件。
  useEffect(() => {
    initTabler();
  }, [entries.data]);

  const items = entries.data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <PageFrame width="browse" labelledBy="timeline-heading">
      <PageHeader id="timeline-heading" title="时间线" description="按时间浏览和找回所有记录。" />
      <FilterBar count={items.length} countLabel="条记录">
        <select aria-label="时间范围" className={ui.select} value={preset} onChange={(event) => { setPreset(event.target.value); setStartDate(""); setEndDate(""); }}><option value="all">全部时间</option><option value="today">今天</option><option value="yesterday">昨天</option><option value="week">本周</option><option value="month">本月</option></select>
        <input aria-label="起始日期" type="date" className={ui.select} value={startDate} onChange={(event) => setStartDate(event.target.value)} />
        <input aria-label="结束日期" type="date" className={ui.select} value={endDate} onChange={(event) => setEndDate(event.target.value)} />
        <select aria-label="记录筛选" className={ui.select} value={flag} onChange={(event) => setFlag(event.target.value)}><option value="all">全部记录</option><option value="pinned">仅置顶</option><option value="favorite">仅收藏</option></select>
      </FilterBar>

      {entries.isPending && <LoadingState label="正在载入时间线…" />}
      {entries.error && <ErrorState message={entries.error.message} onRetry={() => void entries.refetch()} />}
      {!entries.isPending && !entries.error && !items.length && (
        <EmptyState
          title="没有匹配的记录"
          description="调整时间范围或筛选条件后再试。"
          suggestions={["放宽时间范围", "切换到「全部记录」", "清除自定义起止日期"]}
        />
      )}

      {Object.entries(groups).map(([day, dayEntries]) => (
        <section className="mb-6" key={day} aria-label={day}>
          <h3 className="d-flex align-items-center column-gap-3 mb-3 text-sm fw-medium text-secondary">
            <span>{day}</span>
            <span className="flex-grow-1 border-top border-secondary" />
          </h3>
          <div className="space-y-3">
            {dayEntries.map((entry) => <EntryCard entry={entry} variant="feed" focused={entry.id === focusEntryId} onOpenEntry={onOpenEntry} onOpenDetail={onOpenDetail} key={entry.id} />)}
          </div>
        </section>
      ))}

      {entries.hasNextPage && <button className={`${ui.secondaryButton} w-100`} type="button" onClick={() => entries.fetchNextPage()} disabled={entries.isFetchingNextPage}>{entries.isFetchingNextPage ? "正在加载…" : "加载更多"}</button>}
    </PageFrame>
  );
}

function RecentEntries({ focusEntryId, onOpenEntry, onOpenDetail, onViewAll }: { focusEntryId?: string | null; onOpenEntry?: (entryId: string) => void; onOpenDetail?: (entryId: string) => void; onViewAll: () => void }) {
  const entries = useQuery({ queryKey: ["entries", "recent"], queryFn: () => api.entries(null, {}) });
  const items = (entries.data?.items ?? []).slice(0, 8);

  useEffect(() => {
    initTabler();
  }, [entries.data]);

  useEffect(() => {
    if (!focusEntryId || !entries.data) return;
    document.getElementById(`entry-${focusEntryId}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [entries.data, focusEntryId]);

  return (
    <section aria-labelledby="recent-heading">
      <div className="mb-3 d-flex align-items-center justify-content-between column-gap-3">
        <h2 id="recent-heading" className={ui.sectionTitle}>最近记录</h2>
        <button className={ui.textButton} type="button" onClick={onViewAll}>查看全部</button>
      </div>
      {entries.isPending && <LoadingState label="正在载入最近记录…" rows={2} />}
      {entries.error && <ErrorState message={entries.error.message} onRetry={() => void entries.refetch()} />}
      {!entries.isPending && !entries.error && items.length === 0 && (
        <EmptyState title="还没有记录" description="先把第一个念头交给 StarMem。" />
      )}
      <div className="space-y-3">
        {items.map((entry) => <EntryCard entry={entry} variant="feed" focused={entry.id === focusEntryId} onOpenEntry={onOpenEntry} onOpenDetail={onOpenDetail} key={entry.id} />)}
      </div>
    </section>
  );
}

function SearchPage({ onOpenEntry, onOpenDetail }: { onOpenEntry: (entryId: string) => void; onOpenDetail?: (entryId: string) => void }) {
  const client = useQueryClient();
  const [query, setQuery] = useState("");
  const [sourceScope, setSourceScope] = useState("all");
  const [mode, setMode] = useState("hybrid");
  const [contentType, setContentType] = useState("");
  const [tag, setTag] = useState("");
  const [entity, setEntity] = useState("");
  const [project, setProject] = useState("");
  const [topic, setTopic] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [savedName, setSavedName] = useState("");
  const filters = useMemo(() => ({
    mode,
    content_type: contentType || undefined,
    tag: tag || undefined,
    entity: entity || undefined,
    project: project || undefined,
    topic: topic || undefined,
    start: startDate ? new Date(`${startDate}T00:00:00`).toISOString() : undefined,
    end: endDate ? new Date(`${endDate}T23:59:59`).toISOString() : undefined,
  }), [mode, contentType, tag, entity, project, topic, startDate, endDate]);
  const filtersJson = useMemo(() => Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== undefined && value !== "").map(([key, value]) => [key, value as string])), [filters]);
  const search = useMutation({
    mutationFn: (override?: { query?: string; filters?: typeof filters }) =>
      api.search(override?.query ?? query, sourceScope, override?.filters ?? filters),
  });
  const savedSearches = useQuery({ queryKey: ["saved-searches"], queryFn: api.savedSearches });
  const runSaved = useMutation({ mutationFn: api.savedSearchResults });
  const saveSearch = useMutation({
    mutationFn: () => api.createSavedSearch({ name: savedName, query, source_scope: sourceScope, filters_json: filtersJson }),
    onSuccess: () => {
      setSavedName("");
      client.invalidateQueries({ queryKey: ["saved-searches"] });
    },
  });
  const removeSaved = useMutation({
    mutationFn: api.deleteSavedSearch,
    onSuccess: () => client.invalidateQueries({ queryKey: ["saved-searches"] }),
  });
  const results = runSaved.data ?? search.data;

  function applySaved(saved: { id: string; query: string; source_scope: string; filters_json: Record<string, unknown> }) {
    setQuery(saved.query);
    setSourceScope(saved.source_scope);
    const savedFilters = saved.filters_json ?? {};
    setMode(typeof savedFilters.mode === "string" ? savedFilters.mode : "hybrid");
    setContentType(typeof savedFilters.content_type === "string" ? savedFilters.content_type : "");
    setTag(typeof savedFilters.tag === "string" ? savedFilters.tag : "");
    setEntity(typeof savedFilters.entity === "string" ? savedFilters.entity : "");
    setProject(typeof savedFilters.project === "string" ? savedFilters.project : "");
    setTopic(typeof savedFilters.topic === "string" ? savedFilters.topic : "");
    setStartDate(typeof savedFilters.start === "string" ? savedFilters.start.slice(0, 10) : "");
    setEndDate(typeof savedFilters.end === "string" ? savedFilters.end.slice(0, 10) : "");
    runSaved.mutate(saved.id);
  }

  const [recent, setRecent] = useState<string[]>(() => recentSearches.list());
  const knowledgeProjects = useQuery({ queryKey: ["search-projects"], queryFn: api.projects });
  const knowledgeEntities = useQuery({ queryKey: ["search-entities"], queryFn: api.entities });

  function runSearch(override?: { query?: string; filters?: typeof filters }) {
    runSaved.reset();
    setRecent(recentSearches.add(override?.query ?? query));
    search.mutate(override);
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (query.trim()) runSearch();
  }

  const noticeClass = "py-2 px-3 mb-3 text-sm rounded bg-body-tertiary border border-secondary text-secondary";

  return (
    <PageFrame width="search" labelledBy="search-heading">
      <PageHeader id="search-heading" title="搜索任何记忆" description="支持全文、语义、实体、时间和来源检索。" />

      <form className="scope-form bg-body-tertiary border border-secondary rounded  p-2 mb-4" onSubmit={submit}>
        <div className="d-flex flex-column flex-sm-row align-items-sm-center gap-2">
          <div className="position-relative flex-grow-1">
            <Search className="position-absolute top-50 start-0 translate-middle-y icon icon-sm text-secondary" aria-hidden="true" />
            <label className="visually-hidden" htmlFor="search-query">搜索记录</label>
            <input id="search-query" className="py-2 ps-3 pe-3 d-block w-100 bg-transparent border-0 text-sm text-body   " value={query} onChange={(event) => setQuery(event.target.value)} placeholder="关键词、WWN、主机名、模糊印象…" />
          </div>
          <div className="d-flex align-items-center gap-2">
            <select aria-label="检索模式" className={ui.select} value={mode} onChange={(event) => setMode(event.target.value)}><option value="hybrid">混合</option><option value="fulltext">全文</option><option value="semantic">语义</option></select>
            <select aria-label="来源范围" className={ui.select} value={sourceScope} onChange={(event) => setSourceScope(event.target.value)}><option value="all">全部来源</option><option value="native">仅我的记录</option><option value="external">仅外部知识</option></select>
            <button className={ui.primaryButton} disabled={!query.trim() || search.isPending}>{search.isPending ? "搜索中…" : "搜索"}</button>
          </div>
        </div>
      </form>

      <details className="search-filters group bg-body border border-secondary rounded mb-4">
        <summary className="d-flex align-items-center justify-content-between column-gap-2 py-3 px-4 text-sm fw-medium text-body cursor-pointer list-unstyled">
          高级过滤器
          <ChevronDown className="icon icon-sm text-secondary  " aria-hidden="true" />
        </summary>
        <div className="row row-cols-sm-2 row-cols-lg-3 g-3 p-4 border-top border-secondary">
          <label className="d-block"><span className={ui.label}>内容类型</span><input className={ui.input} aria-label="内容类型过滤" value={contentType} onChange={(event) => setContentType(event.target.value)} placeholder="decision" /></label>
          <label className="d-block"><span className={ui.label}>标签</span><input className={ui.input} aria-label="标签过滤" value={tag} onChange={(event) => setTag(event.target.value)} placeholder="tag" /></label>
          <label className="d-block"><span className={ui.label}>实体</span><input className={ui.input} aria-label="实体过滤" value={entity} onChange={(event) => setEntity(event.target.value)} placeholder="host-name" /></label>
          <label className="d-block"><span className={ui.label}>项目</span><input className={ui.input} aria-label="项目过滤" value={project} onChange={(event) => setProject(event.target.value)} placeholder="Project" /></label>
          <label className="d-block"><span className={ui.label}>主题</span><input className={ui.input} aria-label="主题过滤" value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="Topic" /></label>
          <label className="d-block"><span className={ui.label}>起始日期</span><input className={ui.input} aria-label="搜索起始日期" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
          <label className="d-block"><span className={ui.label}>结束日期</span><input className={ui.input} aria-label="搜索结束日期" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></label>
        </div>
      </details>

      {(search.error || runSaved.error || saveSearch.error) && <ErrorState message={(search.error ?? runSaved.error ?? saveSearch.error)?.message ?? "搜索失败"} onRetry={() => runSearch()} />}

      {results ? (
        <>
          {!results.semantic_available && <p className={noticeClass}>当前为全文检索；本地 Embedding 初始化后将自动启用语义与混合检索。</p>}
          {(results.filtered_low_relevance ?? 0) > 0 && <p className={noticeClass}>已过滤 {results.filtered_low_relevance} 条低相关结果（相似度低于阈值）。</p>}

          <div className="mb-3 d-flex flex-wrap align-items-center justify-content-between column-gap-3 row-gap-2">
            <span className="text-sm text-secondary">共 {results.items.length} 条结果</span>
            <div className="d-flex flex-wrap align-items-center gap-2">
              <label className="visually-hidden" htmlFor="saved-name">保存搜索名称</label>
              <input id="saved-name" className={`${ui.input} mw-100`} aria-label="保存搜索名称" value={savedName} onChange={(event) => setSavedName(event.target.value)} placeholder="给这次搜索起个名字" />
              <button className={ui.secondaryButton} type="button" onClick={() => saveSearch.mutate()} disabled={!query.trim() || !savedName.trim() || saveSearch.isPending}>{saveSearch.isPending ? "保存中…" : "保存搜索"}</button>
            </div>
          </div>

          {!results.items.length ? (
            <EmptyState
              title="没有找到匹配内容"
              description={query.trim() ? `没有与「${query.trim()}」匹配的记录。` : "没有匹配的记录。"}
              suggestions={["缩短关键词", "切换到语义搜索", "放宽来源范围", "移除部分筛选条件"]}
            />
          ) : (
            <div className="space-y-3">
              {results.items.map((item) => <SearchCard item={item} key={item.content_unit_id} onOpenEntry={onOpenEntry} onOpenDetail={onOpenDetail} />)}
            </div>
          )}
        </>
      ) : (
        <div className="space-y-6">
          {recent.length > 0 && (
            <section aria-labelledby="recent-searches-heading">
              <h3 id="recent-searches-heading" className={`${ui.sectionTitle} mb-2`}>最近搜索</h3>
              <div className="d-flex flex-wrap gap-2">
                {recent.map((item) => (
                  <button className={`${ui.chip}  `} type="button" key={item} onClick={() => { setQuery(item); runSearch({ query: item }); }}>{item}</button>
                ))}
              </div>
            </section>
          )}

          {savedSearches.data && savedSearches.data.length > 0 && (
            <section aria-labelledby="saved-searches-heading">
              <div className="mb-2 d-flex align-items-center justify-content-between column-gap-2">
                <h3 id="saved-searches-heading" className={ui.sectionTitle}>保存的搜索</h3>
                <span className="small text-secondary">{savedSearches.data.length} 个</span>
              </div>
              <div className={`${ui.card}  `}>
                {savedSearches.data.map((saved) => (
                  <div className="saved-search-row d-flex align-items-center column-gap-3 py-2 px-4" key={saved.id}>
                    <button className="btn btn-link p-0 text-start text-truncate fw-medium text-primary" type="button" onClick={() => applySaved(saved)}>{saved.name}</button>
                    <span className="d-none d-sm-block flex-grow-1 text-truncate text-sm text-secondary">{saved.query}</span>
                    <button className={`${ui.dangerTextButton} flex-shrink-0`} type="button" onClick={() => removeSaved.mutate(saved.id)} disabled={removeSaved.isPending}>删除</button>
                  </div>
                ))}
              </div>
            </section>
          )}

          {(Boolean(knowledgeProjects.data?.length) || Boolean(knowledgeEntities.data?.length)) && (
            <section aria-labelledby="knowledge-objects-heading">
              <div className="mb-2 d-flex align-items-center justify-content-between column-gap-2">
                <h3 id="knowledge-objects-heading" className={ui.sectionTitle}>知识对象</h3>
                <span className="small text-secondary">来自 Knowledge Workbench</span>
              </div>
              <div className="d-flex flex-wrap gap-2">
                {knowledgeProjects.data?.slice(0, 8).map((item) => (
                  <button className={`${ui.chip}  `} type="button" key={`project-${item.id}`} onClick={() => { setQuery(item.name); setProject(item.name); runSearch({ query: item.name, filters: { ...filters, project: item.name } }); }}>{item.name}</button>
                ))}
                {knowledgeEntities.data?.slice(0, 8).map((item) => (
                  <button className={`${ui.chip}  `} type="button" key={`entity-${item.id}`} onClick={() => { setQuery(item.name); setEntity(item.name); runSearch({ query: item.name, filters: { ...filters, entity: item.name } }); }}>{item.name}</button>
                ))}
              </div>
            </section>
          )}

          {!recent.length && !savedSearches.data?.length && !knowledgeProjects.data?.length && !knowledgeEntities.data?.length && (
            <EmptyState title="开始搜索你的记忆" description="输入关键词、主机名或模糊印象，StarMem 会在原文与外部来源中检索。" />
          )}
        </div>
      )}
    </PageFrame>
  );
}

function matchLabel(item: SearchResult): string {
  if (item.exact_match) return "精确匹配";
  const reason = item.match_reason ?? "";
  if (/hybrid|混合/i.test(reason)) return "混合匹配";
  if (/语义|semantic/i.test(reason)) return "语义匹配";
  if (/实体|entity/i.test(reason)) return "实体匹配";
  if (/memory|记忆/i.test(reason)) return "记忆匹配";
  return reason;
}

function SearchCard({ item, onOpenEntry, onOpenDetail }: { item: SearchResult; onOpenEntry: (entryId: string) => void; onOpenDetail?: (entryId: string) => void }) {
  const fragments = item.snippet.split(/(<mark>.*?<\/mark>)/g);
  const exact = Boolean(item.exact_match);
  return (
    <article className="search-result-row space-y-2 border-bottom border-secondary py-4 pt-0 ">
      <div className="d-flex flex-wrap align-items-center gap-2">
        <span className={exact ? "d-inline-flex align-items-center py-1 px-2 rounded-pill small border border-primary text-primary" : ui.chip}>{matchLabel(item)}</span>
        <span className="small text-secondary">{item.match_reason}</span>
      </div>
      <p className="text-sm text-body">
        {fragments.map((fragment, index) => fragment.startsWith("<mark>") ? <mark className="bg-primary-lt text-primary rounded px-1" key={index}>{fragment.slice(6, -7)}</mark> : fragment)}
      </p>
      <footer className="d-flex flex-wrap align-items-center column-gap-3 row-gap-1 small text-secondary">
        <span>{item.source_name}{item.external_id ? ` · ${item.external_id}` : ""}{item.page_number ? ` · 第 ${item.page_number} 页` : ""}{item.provenance_type ? ` · ${item.provenance_type}` : ""}</span>
        <span>{item.created_at ? new Date(item.created_at).toLocaleString("zh-CN") : ""}</span>
      </footer>
      <div className="d-flex flex-wrap align-items-center column-gap-3">
        {item.external_url && <a className={ui.textButton} href={item.external_url} target="_blank" rel="noreferrer">原来源</a>}
        {item.source_uri && <a className={ui.textButton} href={item.source_uri} target="_blank" rel="noreferrer">原 URL</a>}
        {item.attachment_id && <a className={ui.textButton} href={`/api/v1/attachments/${item.attachment_id}`}>附件</a>}
        {item.entry_id && <button className={ui.secondaryButton} type="button" onClick={() => onOpenEntry(item.entry_id!)}><ExternalLink className="icon icon-sm" aria-hidden="true" />查看原文</button>}
        {item.entry_id && onOpenDetail && <button className={ui.textButton} type="button" onClick={() => onOpenDetail(item.entry_id!)}>详情</button>}
      </div>
    </article>
  );
}

function AskPage({ onOpenEntry }: { onOpenEntry: (entryId: string) => void }) {
  const [query, setQuery] = useState("");
  const [sourceScope, setSourceScope] = useState("all");
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [lastQuestion, setLastQuestion] = useState("");
  const ask = useMutation({ mutationFn: (question?: string) => api.ask(question ?? query, sourceScope) });

  const [recent, setRecent] = useState<string[]>(() => recentQuestions.list());

  function runAsk(question?: string) {
    const effective = (question ?? query).trim();
    if (!effective) return;
    setQuery(effective);
    setLastQuestion(effective);
    setRecent(recentQuestions.add(effective));
    ask.mutate(effective);
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    runAsk();
  }

  useEffect(() => {
    if (!sourcesOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [sourcesOpen]);

  const noticeClass = "py-2 px-3 text-sm rounded bg-body-tertiary border border-secondary text-secondary";
  const examples = ["我的 V100 最后设置多少瓦？", "之前那个 iSCSI 残留问题怎么处理？", "最近对 Lumen 做了哪些决策？"];

  const suggestionChips = (items: string[]) => (
    <div className="d-flex flex-wrap gap-2">
      {items.map((item) => (
        <button className={`${ui.chip}  `} type="button" key={item} onClick={() => runAsk(item)}>{item}</button>
      ))}
    </div>
  );

  const sourcesList = (
    <>
      {ask.data?.sources.map((source, index) => (
        <SourceItem
          key={`${source.content_unit_id}-${source.chunk_id ?? index}`}
          source={{
            index: index + 1,
            title: source.source_name,
            meta: [
              source.page_number ? `第 ${source.page_number} 页` : source.provenance_type ?? "",
              source.created_at ? new Date(source.created_at).toLocaleString("zh-CN") : "",
            ],
            snippet: source.snippet.replace(/<\/?mark>/g, ""),
            href: source.source_uri ?? (source.attachment_id ? `/api/v1/attachments/${source.attachment_id}` : undefined),
            hrefLabel: source.source_uri ? "原 URL" : "打开附件",
          }}
          onOpenEntry={source.entry_id ? () => onOpenEntry(source.entry_id!) : undefined}
        />
      ))}
      {!ask.data?.sources.length && <p className="text-sm text-secondary">没有可靠来源，StarMem 不会编造确定答案。</p>}
    </>
  );

  return (
    <PageFrame width="ai" labelledBy="ask-heading">
      <PageHeader id="ask-heading" title="问记忆" description="基于你的记录和来源回答，并始终附带引用。" />

      <form className="bg-body-tertiary border border-secondary rounded  p-2 mb-6" onSubmit={submit}>
        <div className="d-flex flex-column flex-sm-row align-items-sm-center gap-2">
          <div className="position-relative flex-grow-1">
            <Sparkles className="position-absolute top-50 start-0 translate-middle-y icon icon-sm text-secondary" aria-hidden="true" />
            <label className="visually-hidden" htmlFor="ask-query">问题</label>
            <input id="ask-query" className="py-2 ps-3 pe-3 d-block w-100 bg-transparent border-0 text-sm text-body   " value={query} onChange={(event) => setQuery(event.target.value)} placeholder="例如：我的 V100 最后设置多少瓦？" />
          </div>
          <div className="d-flex align-items-center gap-2">
            <select aria-label="来源范围" className={ui.select} value={sourceScope} onChange={(event) => setSourceScope(event.target.value)}><option value="all">全部来源</option><option value="native">仅我的记录</option><option value="external">仅外部知识</option></select>
            <button className={ui.primaryButton} disabled={!query.trim() || ask.isPending}>{ask.isPending ? "检索中…" : "询问"}</button>
          </div>
        </div>
      </form>

      {ask.error && <ErrorState message={ask.error.message} onRetry={() => runAsk()} />}
      {ask.isPending && <LoadingState label="正在检索记忆…" rows={2} />}

      {ask.data ? (
        <div className="row g-4">
          <div className=" space-y-3 col-lg-8">
            {!ask.data.chat_available && <p className={noticeClass}>Chat 暂不可用，当前展示基于已保存来源的确定性摘要。</p>}
            {!ask.data.semantic_available && <p className={noticeClass}>本次使用全文检索降级；Embedding 可用后会自动加入语义候选。</p>}
            {(ask.data.filtered_low_relevance ?? 0) > 0 && <p className={noticeClass}>已过滤 {ask.data.filtered_low_relevance} 条低相关结果（相似度低于阈值）。</p>}

            {lastQuestion && (
              <article className={`${ui.card} p-4`}>
                <span className={ui.chip}>你问</span>
                <p className="mt-2 text-sm fw-medium text-body">{lastQuestion}</p>
              </article>
            )}

            <article className={`${ui.card} p-5`}>
              <div className="d-flex align-items-center justify-content-between column-gap-2 mb-3">
                <span className={ui.chip}>{ask.data.is_inference ? "推断" : "来源事实"}</span>
                <span className="small text-secondary">置信度 {Math.round(ask.data.confidence * 100)}%</span>
              </div>
            <div className="text-sm text-body">
                <ReactMarkdown components={{ pre: ({ children }) => <pre className="mw-100 overflow-auto text-break">{children}</pre> }}>{ask.data.answer}</ReactMarkdown>
              </div>
            </article>

            <section aria-labelledby="followup-heading" className="space-y-2 pt-1">
              <h3 id="followup-heading" className={ui.sectionTitle}>继续追问</h3>
              {suggestionChips(examples)}
              <p className="small text-secondary">追问会作为一次新的提问（当前不保留多轮上下文）。</p>
            </section>
          </div>

          <aside aria-labelledby="sources-heading" className="d-none  space-y-3 col-lg-4 d-lg-block">
            <div className="d-flex align-items-center justify-content-between column-gap-2">
              <h3 id="sources-heading" className={ui.sectionTitle}>来源</h3>
              <span className="small text-secondary">{ask.data.sources.length} 条</span>
            </div>
            {sourcesList}
          </aside>
        </div>
      ) : (
        <div className="space-y-6">
          <section aria-labelledby="ask-examples-heading">
            <h3 id="ask-examples-heading" className={`${ui.sectionTitle} mb-2`}>可以这样问</h3>
            {suggestionChips(examples)}
          </section>

          {recent.length > 0 && (
            <section aria-labelledby="recent-questions-heading">
              <h3 id="recent-questions-heading" className={`${ui.sectionTitle} mb-2`}>最近提问</h3>
              {suggestionChips(recent)}
            </section>
          )}

          <EmptyState
            icon={<Sparkles className="icon icon-lg" aria-hidden="true" />}
            title="问 StarMem"
            description="基于你的记录与来源作答；没有可靠来源时不会给出确定答案。"
          />
        </div>
      )}

      {ask.data && (
        <div className="d-lg-none mt-4">
          <button className={`${ui.secondaryButton} w-100`} type="button" onClick={() => setSourcesOpen(true)}>
            <Link2 className="icon icon-sm" aria-hidden="true" />查看 {ask.data.sources.length} 条来源
          </button>
        </div>
      )}

      {sourcesOpen && ask.data && (
        <div className="offcanvas offcanvas-bottom show d-lg-none" tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby="sources-sheet-heading">
          <button className="offcanvas-backdrop fade show" type="button" aria-label="关闭来源面板" onClick={() => setSourcesOpen(false)} />
          <div className="offcanvas-header">
              <h3 id="sources-sheet-heading" className={ui.sectionTitle}>来源 · {ask.data.sources.length} 条</h3>
              <button className="btn btn-action" type="button" onClick={() => setSourcesOpen(false)} aria-label="关闭">
                <X className="icon icon-sm" aria-hidden="true" />
              </button>
          </div>
          <div className="offcanvas-body space-y-3 safe-area-bottom">{sourcesList}</div>
        </div>
      )}
    </PageFrame>
  );
}

const inboxStatusLabels: Record<string, string> = {
  new: "新建",
  processing: "处理中",
  processed: "已处理",
  failed: "失败",
};

function InboxPage({ onOpenEntry, onOpenDetail }: { onOpenEntry: (entryId: string) => void; onOpenDetail?: (entryId: string) => void }) {
  const client = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const inbox = useQuery({ queryKey: ["inbox", statusFilter], queryFn: () => api.inbox(statusFilter || undefined) });
  const retry = useMutation({
    mutationFn: api.retryIngestion,
    onSuccess: () => client.invalidateQueries({ queryKey: ["inbox"] }),
  });
  const [correctedJobId, setCorrectedJobId] = useState("");
  const correct = useMutation({
    mutationFn: ({ id, title, content_type }: { id: string; title: string; content_type: string }) =>
      api.correctIngestion(id, { title, content_type }),
    onSuccess: (_result, variables) => {
      setCorrectedJobId(variables.id);
      client.invalidateQueries({ queryKey: ["inbox"] });
      client.invalidateQueries({ queryKey: ["entries"] });
    },
  });
  const secondaryButtonClass = "btn btn-outline-secondary";

  return (
    <PageFrame width="browse" labelledBy="inbox-heading">
      <PageHeader
        id="inbox-heading"
        title="所有输入都在这里处理"
        description="查看网页、文件、PDF 和图片的原始输入与异步处理状态。"
        actions={<button className={secondaryButtonClass} type="button" onClick={() => void inbox.refetch()} disabled={inbox.isFetching}><Inbox className="icon icon-sm" aria-hidden="true" />刷新</button>}
      />
      <FilterBar count={inbox.data?.length ?? 0} countLabel="条输入">
        <select aria-label="Inbox 状态" className={ui.select} value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="">全部状态</option>
          <option value="new">新建</option>
          <option value="processing">处理中</option>
          <option value="processed">已处理</option>
          <option value="failed">失败</option>
        </select>
      </FilterBar>
      {inbox.isPending && <LoadingState label="正在载入 Inbox…" />}
      {inbox.error && <ErrorState message={inbox.error.message} onRetry={() => void inbox.refetch()} />}
      {!inbox.isPending && !inbox.error && !inbox.data?.length && <EmptyState title="Inbox 还是空的" description="从 Capture 保存网页、文件或图片后，处理进度会在这里出现。" />}
      <div className=" ">
        {inbox.data?.map((item) => <InboxCard item={item} key={item.job_id} onOpenEntry={onOpenEntry} onOpenDetail={onOpenDetail} onRetry={(id) => retry.mutate(id)} onCorrect={(id, title, content_type) => correct.mutate({ id, title, content_type })} retrying={retry.isPending} correcting={correct.isPending} correctionError={correct.isError ? correct.error.message : ""} corrected={correctedJobId === item.job_id} />)}
      </div>
    </PageFrame>
  );
}

const inboxStatusClass: Record<string, string> = {
  new: "status-blue",
  processing: "status-blue",
  processed: "status-green",
  failed: "status-red",
};

function InboxCard({ item, onOpenEntry, onOpenDetail, onRetry, onCorrect, retrying, correcting, correctionError, corrected }: { item: Ingestion; onOpenEntry: (entryId: string) => void; onOpenDetail?: (entryId: string) => void; onRetry: (jobId: string) => void; onCorrect: (jobId: string, title: string, contentType: string) => void; retrying: boolean; correcting: boolean; correctionError: string; corrected: boolean }) {
  const [correctingOpen, setCorrectingOpen] = useState(false);
  const [titleDraft, setTitleDraft] = useState(item.original_name ?? "");
  const [typeDraft, setTypeDraft] = useState(String(item.metadata_json.content_type ?? ""));
  const label = item.input_kind === "url" ? "网页" : "文件";
  const name = item.input_kind === "url" ? item.source_uri : item.original_name;
  const pageCount = item.metadata_json.page_count;
  const chipClass = "badge bg-secondary-lt";
  const statusClass = `status ${inboxStatusClass[item.status] ?? "status-blue"}`;
  const inputClass = "form-control";
  const primaryButtonClass = "btn btn-primary";
  const secondaryButtonClass = "btn btn-outline-secondary";
  return (
    <article className="inbox-row space-y-3 py-4 pt-0 ">
      <div className="d-flex flex-wrap align-items-start justify-content-between column-gap-3 row-gap-2">
        <div className="">
          <span className={chipClass}>{label}</span>
          <h3 className="mt-1 text-sm fw-medium text-body text-break">{name || "未命名输入"}</h3>
        </div>
        <span className={statusClass}>{inboxStatusLabels[item.status] ?? item.status}</span>
      </div>
      <div className="d-flex flex-wrap align-items-center column-gap-3 row-gap-1 small text-secondary">
        {item.media_type && <span>{item.media_type}</span>}
        <span>尝试 {item.attempt}</span>
        {typeof pageCount === "number" && <span>{pageCount} 页</span>}
        <time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString("zh-CN")}</time>
      </div>
      {item.error && <p className="text-sm text-danger">{item.error_code ? `${item.error_code}：` : ""}{item.error}</p>}
      {item.attachments.length > 0 && (
        <div className="d-flex flex-wrap gap-2">
          {item.attachments.map((attachment) => (
            <a className="d-inline-flex align-items-center column-gap-2 py-2 px-3 rounded bg-body-tertiary border border-secondary text-sm text-body  " href={attachment.download_url} key={attachment.id}>
              <Upload className="icon icon-sm text-secondary" aria-hidden="true" />
              <span>{attachment.original_filename}</span>
              <small className="small text-secondary">{(attachment.size_bytes / 1024).toFixed(1)} KB · {attachment.processing_status}</small>
            </a>
          ))}
        </div>
      )}
      <footer className="d-flex flex-wrap align-items-center column-gap-3 row-gap-2">
        <button className={secondaryButtonClass} type="button" onClick={() => onOpenEntry(item.entry_id)}>查看 Entry</button>
        {onOpenDetail && <button className="btn btn-link p-0" type="button" onClick={() => onOpenDetail(item.entry_id)}>详情</button>}
        <button className="btn btn-link p-0" type="button" onClick={() => setCorrectingOpen((value) => !value)}>修正标题 / 类型</button>
        {item.status === "failed" && <button className="btn btn-link p-0 d-inline-flex align-items-center column-gap-2" type="button" onClick={() => onRetry(item.job_id)} disabled={retrying}><RotateCcw className="icon icon-sm" aria-hidden="true" />重新处理</button>}
      </footer>
      {correctingOpen && (
        <div className="border-top border-secondary pt-3 space-y-3">
          <label className="d-block"><span className="d-block mb-1 text-sm text-secondary">标题</span><input className={inputClass} aria-label="修正标题" value={titleDraft} onChange={(event) => setTitleDraft(event.target.value)} /></label>
          <label className="d-block"><span className="d-block mb-1 text-sm text-secondary">内容类型</span><input className={inputClass} aria-label="修正内容类型" value={typeDraft} onChange={(event) => setTypeDraft(event.target.value)} /></label>
          {correctionError && <p className="text-sm text-danger" role="alert">{correctionError}</p>}
          {corrected && <p className="py-2 px-3 text-sm rounded bg-body-tertiary border border-secondary text-secondary" role="status">修正已保存到 Entry，附件与来源保持不变。</p>}
          <div className="d-flex flex-wrap align-items-center column-gap-3 row-gap-2">
            <button className={primaryButtonClass} type="button" disabled={correcting || item.status === "processing"} onClick={() => onCorrect(item.job_id, titleDraft, typeDraft)}>{correcting ? "保存中…" : "保存修正"}</button>
            {item.status === "processing" && <span className="text-sm text-secondary">处理中，暂不能修正</span>}
          </div>
        </div>
      )}
    </article>
  );
}

function WorkbenchItems({ items, onOpenEntry }: { items: WorkbenchItem[]; onOpenEntry: (entryId: string) => void }) {
  if (!items.length) return <p className="text-sm text-secondary">当前没有匹配项。</p>;
  return (
    <div className=" ">
      {items.map((item) => (
        <div className="d-flex flex-wrap align-items-start justify-content-between column-gap-3 row-gap-2 py-2" key={`${item.kind}-${item.id}`}>
          <div className="">
            <strong className="d-block text-sm fw-medium text-body">{item.title}</strong>
            {item.detail && <p className="text-sm text-secondary">{item.detail}</p>}
            <small className="small text-secondary">{item.status ?? ""}{item.created_at ? ` · ${new Date(item.created_at).toLocaleString("zh-CN")}` : ""}</small>
          </div>
          {item.entry_id && <button className="btn btn-link p-0 flex-shrink-0" type="button" onClick={() => onOpenEntry(item.entry_id!)}>查看记录</button>}
        </div>
      ))}
    </div>
  );
}

function WorkbenchPage({ onOpenEntry, onOpenDetail, initialKind, initialId }: { onOpenEntry: (entryId: string) => void; onOpenDetail?: (kind: "project" | "topic" | "entity", id: string) => void; initialKind?: "project" | "topic" | "entity"; initialId?: string }) {
  const client = useQueryClient();
  const [kind, setKind] = useState<"project" | "topic" | "entity">(initialKind ?? "project");
  const [selectedId, setSelectedId] = useState<string | null>(initialId ?? null);
  const [selectedView, setSelectedView] = useState("problems");
  const [reviewPeriod, setReviewPeriod] = useState("week");
  const [managementMessage, setManagementMessage] = useState("");
  const [renameDraft, setRenameDraft] = useState("");
  const [mergeTarget, setMergeTarget] = useState("");
  const projects = useQuery({ queryKey: ["workbench", "projects"], queryFn: api.projects });
  const topics = useQuery({ queryKey: ["workbench", "topics"], queryFn: api.topics });
  const entities = useQuery({ queryKey: ["workbench", "entities"], queryFn: api.entities });
  const smartViews = useQuery({ queryKey: ["smart-views"], queryFn: api.smartViews });
  const review = useQuery({ queryKey: ["review", reviewPeriod], queryFn: () => api.review(reviewPeriod) });
  const knowledge = useQuery({ queryKey: ["knowledge"], queryFn: api.knowledge });
  const summaries = kind === "project" ? projects.data : kind === "topic" ? topics.data : entities.data;
  const selectedSummary = summaries?.find((summary) => summary.id === selectedId) ?? null;
  const detail = useQuery({
    queryKey: ["workbench-detail", kind, selectedId],
    queryFn: () => kind === "project" ? api.project(selectedId!) : kind === "topic" ? api.topic(selectedId!) : api.entity(selectedId!),
    enabled: Boolean(selectedId) && selectedSummary !== null,
  });
  const view = useQuery({ queryKey: ["smart-view", selectedView], queryFn: () => api.smartView(selectedView) });
  const generate = useMutation({
    mutationFn: () => api.createKnowledgeSummary({ scope_type: kind, scope_value: detail.data?.name }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["knowledge"] }),
  });
  const refreshWorkbench = () => {
    client.invalidateQueries({ queryKey: ["workbench"] });
    client.invalidateQueries({ queryKey: ["workbench-detail"] });
  };
  const selectKind = (next: "project" | "topic" | "entity") => {
    if (next !== kind) setSelectedId(null);
    setKind(next);
  };
  const rename = useMutation({
    mutationFn: () => api.renameWorkbenchObject(kind, selectedId!, renameDraft.trim()),
    onSuccess: () => { setManagementMessage("已重命名，来源观测同步指向新名称。"); refreshWorkbench(); },
    onError: (error) => setManagementMessage(error.message),
  });
  const merge = useMutation({
    mutationFn: () => api.mergeWorkbenchObject(kind, selectedId!, mergeTarget),
    onSuccess: () => { setManagementMessage("已合并；源对象标记为 merged，证据保留。"); setMergeTarget(""); refreshWorkbench(); },
    onError: (error) => setManagementMessage(error.message),
  });
  const exclude = useMutation({
    mutationFn: () => api.excludeWorkbenchObject(kind, selectedId!),
    onSuccess: () => { setManagementMessage("已从默认列表排除，原始 Entry 未删除。"); refreshWorkbench(); },
    onError: (error) => setManagementMessage(error.message),
  });
  const restore = useMutation({
    mutationFn: () => api.restoreWorkbenchObject(kind, selectedId!),
    onSuccess: () => { setManagementMessage("已恢复为 active。"); refreshWorkbench(); },
    onError: (error) => setManagementMessage(error.message),
  });

  useEffect(() => {
    setSelectedId((current) => current && summaries?.some((summary) => summary.id === current) ? current : summaries?.[0]?.id ?? null);
  }, [kind, summaries]);
  useEffect(() => {
    if (initialKind) setKind(initialKind);
    if (initialId) setSelectedId(initialId);
  }, [initialKind, initialId]);

  const cardClass = "card p-4";
  const chipClass = "badge bg-secondary-lt";
  const inputClass = "form-control";
  const selectClass = "form-select";
  const secondaryButtonClass = "btn btn-outline-secondary";
  const textButtonClass = "btn btn-link p-0";
  const tabClass = (active: boolean) => active ? "btn btn-primary" : "btn btn-outline-secondary";
  const listRowClass = (active: boolean) => active
    ? "btn btn-link w-100 d-flex align-items-center justify-content-between column-gap-2 p-2 rounded bg-primary-lt text-start text-decoration-none"
    : "btn btn-link w-100 d-flex align-items-center justify-content-between column-gap-2 p-2 rounded text-start text-decoration-none";
  const viewButtonClass = (active: boolean) => active
    ? "btn btn-ghost-primary flex-grow-1 p-2 text-start"
    : "btn btn-ghost-secondary flex-grow-1 p-2 text-start";

  return (
    <PageFrame width="browse" labelledBy="workbench-heading">
      <PageHeader id="workbench-heading" title="知识工作台" description="从 Project、Topic、Entity、Smart View 和时间回顾进入可解释的知识工作台。" />

      <div className="d-inline-flex align-items-center column-gap-1 mb-4" role="tablist" aria-label="知识对象">
        {(["project", "topic", "entity"] as const).map((item) => (
          <button role="tab" aria-selected={kind === item} className={tabClass(kind === item)} type="button" key={item} onClick={() => selectKind(item)}>{item === "project" ? "项目" : item === "topic" ? "主题" : "实体"}</button>
        ))}
      </div>

      <div className="row g-4 mb-4">
        <section className={`${cardClass} col-lg-4`} aria-label="对象列表">
          <div className="d-flex align-items-center justify-content-between column-gap-2 mb-3">
            <h3 className="text-sm fw-medium text-body">{kind === "project" ? "项目" : kind === "topic" ? "主题" : "实体"}</h3>
            <span className="small text-secondary">{summaries?.length ?? 0}</span>
          </div>
          {!summaries?.length && <p className="text-sm text-secondary">还没有可展示的派生对象。重新处理 Entry 后，Project、Topic 和 Entity 会在这里出现。</p>}
          <div className="space-y-1">
            {summaries?.map((summary) => (
              <button type="button" className={listRowClass(summary.id === selectedId)} key={summary.id} onClick={() => setSelectedId(summary.id)}>
                <span className="">
                  <strong className="d-block text-sm fw-medium text-body text-truncate">{summary.name}</strong>
                  <small className="d-block small text-secondary">{summary.entity_type ?? summary.kind} · {summary.entry_count} 条记录</small>
                </span>
                <span className="flex-shrink-0 small text-secondary">{summary.memory_count} M</span>
              </button>
            ))}
          </div>
        </section>

        <section className={`${cardClass} col-lg-8`} aria-label="对象详情">
          {detail.isPending && selectedId && <p className="text-sm text-secondary">正在读取详情…</p>}
          {detail.data ? (
            <>
              <div className="d-flex flex-wrap align-items-center justify-content-between column-gap-3 row-gap-2 mb-3">
                <div className="">
                  <span className={chipClass}>{detail.data.entity_type ?? detail.data.kind}</span>
                  <h3 className="mt-1 text-sm fw-medium text-body">{detail.data.name}</h3>
                </div>
                <div className="d-flex flex-wrap align-items-center gap-2"><span className="small text-secondary">{detail.data.entry_count} 条 Entry</span>{onOpenDetail && selectedId && <button className={textButtonClass} type="button" onClick={() => onOpenDetail(kind, selectedId)}>独立详情</button>}</div>
              </div>
              <p className="text-sm text-secondary">{detail.data.description ?? "没有额外描述；统计来自已保存证据。"}</p>

              <div className="row row-cols-3 g-3 my-4">
                <div className="rounded bg-body-tertiary border border-secondary p-3 text-center"><strong className="d-block fs-3 fw-semibold text-body">{detail.data.entry_count}</strong><span className="small text-secondary">Entries</span></div>
                <div className="rounded bg-body-tertiary border border-secondary p-3 text-center"><strong className="d-block fs-3 fw-semibold text-body">{detail.data.memory_count}</strong><span className="small text-secondary">Memory</span></div>
                <div className="rounded bg-body-tertiary border border-secondary p-3 text-center"><strong className="d-block fs-3 fw-semibold text-body">{detail.data.related.length}</strong><span className="small text-secondary">关联对象</span></div>
              </div>

              <p className="small text-secondary mb-4">首次 {detail.data.first_seen ? new Date(detail.data.first_seen).toLocaleString("zh-CN") : "—"} · 最近 {detail.data.last_seen ? new Date(detail.data.last_seen).toLocaleString("zh-CN") : "—"}</p>

              <div className="space-y-2 mb-4">
                <strong className="d-block text-sm fw-medium text-body">关联证据</strong>
                <div className="d-flex flex-wrap gap-2">
                  {detail.data.entry_ids.slice(0, 8).map((entryId) => (
                    <button className="btn btn-outline-secondary btn-sm" type="button" key={entryId} onClick={() => onOpenEntry(entryId)}>Entry {entryId.slice(0, 8)}</button>
                  ))}
                </div>
                {detail.data.related.length > 0 && <p className="text-sm text-secondary">相关：{detail.data.related.join("、")}</p>}
              </div>

              <div className="space-y-3 border-top border-secondary pt-4">
                <strong className="d-block text-sm fw-medium text-body">管理（不删除原始证据）</strong>
                <div className="d-flex flex-column flex-sm-row align-items-sm-center gap-2">
                  <input className={inputClass} aria-label="重命名对象" value={renameDraft} onChange={(event) => setRenameDraft(event.target.value)} placeholder="新名称" />
                  <button className={secondaryButtonClass} type="button" disabled={!renameDraft.trim() || rename.isPending} onClick={() => rename.mutate()}>重命名</button>
                </div>
                {kind !== "entity" && (
                  <div className="d-flex flex-column flex-sm-row align-items-sm-center gap-2">
                    <select className={selectClass} aria-label="合并目标" value={mergeTarget} onChange={(event) => setMergeTarget(event.target.value)}>
                      <option value="">选择合并目标</option>
                      {summaries?.filter((summary) => summary.id !== selectedId).map((summary) => <option key={summary.id} value={summary.id!}>{summary.name}</option>)}
                    </select>
                    <button className={secondaryButtonClass} type="button" disabled={!mergeTarget || merge.isPending} onClick={() => merge.mutate()}>合并到目标</button>
                  </div>
                )}
                <div className="d-flex flex-wrap align-items-center column-gap-4 row-gap-2">
                  <button className={textButtonClass} type="button" onClick={() => exclude.mutate()} disabled={exclude.isPending}>排除错误归类</button>
                  <button className={textButtonClass} type="button" onClick={() => restore.mutate()} disabled={restore.isPending}>恢复为 active</button>
                </div>
                {managementMessage && <p className="text-sm text-secondary" role="status">{managementMessage}</p>}
                <button className={secondaryButtonClass} type="button" onClick={() => generate.mutate()} disabled={generate.isPending || !detail.data.entry_count}>{generate.isPending ? "生成中…" : "生成 Knowledge Summary"}</button>
              </div>
            </>
          ) : <p className="text-sm text-secondary">选择一个对象查看详情。</p>}
        </section>
      </div>

      <div className="row g-4 row-cols-lg-2 mb-4">
        <section className={cardClass} aria-labelledby="smart-view-heading">
          <div className="d-flex align-items-center justify-content-between column-gap-2 mb-3">
            <h3 id="smart-view-heading" className="text-sm fw-medium text-body">Smart Views</h3>
            <span className="small text-secondary">动态查询</span>
          </div>
          <div className="d-flex flex-wrap gap-2 mb-3">
            {smartViews.data?.map((item) => (
              <button type="button" className={viewButtonClass(selectedView === item.id)} key={item.id} onClick={() => setSelectedView(item.id)}>
                <strong className="d-block text-sm fw-medium text-body">{item.name}</strong>
                <small className="d-block small text-secondary">{item.description}</small>
              </button>
            ))}
          </div>
          {view.data && (
            <div>
              <div className="d-flex align-items-center justify-content-between column-gap-2 mb-2">
                <strong className="text-sm fw-medium text-body">{view.data.name}</strong>
                <span className="small text-secondary">{view.data.items.length} 项</span>
              </div>
              <WorkbenchItems items={view.data.items.slice(0, 12)} onOpenEntry={onOpenEntry} />
            </div>
          )}
        </section>

        <section className={cardClass} aria-labelledby="review-heading">
          <div className="d-flex flex-wrap align-items-center justify-content-between column-gap-2 row-gap-2 mb-3">
            <h3 id="review-heading" className="text-sm fw-medium text-body">时间回顾</h3>
            <select className={selectClass} aria-label="回顾范围" value={reviewPeriod} onChange={(event) => setReviewPeriod(event.target.value)}>
              <option value="today">今天</option>
              <option value="week">最近七天</option>
              <option value="month">最近三十天</option>
            </select>
          </div>
          {review.data && (
            <>
              <div className="row row-cols-4 g-2 mb-3">
                {Object.entries(review.data.counts).slice(0, 8).map(([label, count]) => (
                  <div className="rounded bg-body-tertiary border border-secondary p-2 text-center" key={label}>
                    <strong className="d-block text-sm fw-semibold text-body">{count}</strong>
                    <span className="small text-secondary">{label.replaceAll("_", " ")}</span>
                  </div>
                ))}
              </div>
              <WorkbenchItems items={review.data.items.slice(0, 8)} onOpenEntry={onOpenEntry} />
            </>
          )}
        </section>
      </div>

      <section className={cardClass} aria-labelledby="knowledge-heading">
        <div className="d-flex align-items-center justify-content-between column-gap-2 mb-3">
          <h3 id="knowledge-heading" className="text-sm fw-medium text-body">Derived Knowledge</h3>
          <span className="small text-secondary">不替代 Raw / Atomic Memory</span>
        </div>
        {generate.isSuccess && <p className="py-2 px-3 mb-3 text-sm rounded bg-body-tertiary border border-secondary text-secondary">Summary 已生成并保留来源 ID。</p>}
        {!knowledge.data?.length && <p className="text-sm text-secondary">还没有 Summary；从上方选中有证据的项目、主题或实体即可生成。</p>}
        <div className=" ">
          {knowledge.data?.slice(0, 6).map((item) => (
            <article className="d-flex flex-wrap align-items-start justify-content-between column-gap-3 row-gap-2 py-3" key={item.id}>
              <div className="">
                <strong className="d-block text-sm fw-medium text-body">{item.title}</strong>
                <small className="small text-secondary">更新于 {new Date(item.updated_at).toLocaleString("zh-CN")} · {item.status}</small>
              </div>
              <div className="d-flex flex-wrap gap-2">
                {Array.isArray(item.metadata_json.entry_ids) && item.metadata_json.entry_ids.slice(0, 4).map((entryId) => (
                  <button type="button" className={textButtonClass} key={String(entryId)} onClick={() => onOpenEntry(String(entryId))}>来源 Entry</button>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </PageFrame>
  );
}

function MorePage({ onOpenInbox, onOpenWorkbench, onOpenMemory, onPromptNavigate, section = "overview", promptName, promptView = "editor", onNavigate }: { onOpenInbox: () => void; onOpenWorkbench: () => void; onOpenMemory?: (memoryId: string) => void; onPromptNavigate?: (promptName: string, view: PromptView) => void; section?: ManagementSection; promptName?: string; promptView?: PromptView; onNavigate: (section: ManagementSection) => void }) {
  const client = useQueryClient();
  const status = useQuery({ queryKey: ["status"], queryFn: api.status });
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: api.jobs });
  const prompts = useQuery({ queryKey: ["prompts"], queryFn: api.prompts });
  const [memoryStatus, setMemoryStatus] = useState("active");
  const memories = useQuery({ queryKey: ["memories", memoryStatus], queryFn: () => api.memories(memoryStatus) });
  const confirmMemory = useMutation({ mutationFn: api.confirmMemory, onSuccess: () => client.invalidateQueries({ queryKey: ["memories"] }) });
  const expireMemory = useMutation({ mutationFn: api.expireMemory, onSuccess: () => client.invalidateQueries({ queryKey: ["memories"] }) });
  const deleteMemory = useMutation({ mutationFn: api.deleteMemory, onSuccess: () => client.invalidateQueries({ queryKey: ["memories"] }) });
  const settingsQuery = useQuery({ queryKey: ["settings"], queryFn: api.settings });
  const [selectedPrompt, setSelectedPrompt] = useState("");
  const [activePromptView, setActivePromptView] = useState<PromptView>(promptView);
  const [instructions, setInstructions] = useState("");
  const [taskPrompt, setTaskPrompt] = useState("");
  const [promptParams, setPromptParams] = useState({ provider: "", model: "", temperature: "", top_p: "", max_tokens: "" });
  const [promptMessage, setPromptMessage] = useState("");
  const [globalInstructions, setGlobalInstructions] = useState("");
  const [importMessage, setImportMessage] = useState("");
  const [caseName, setCaseName] = useState("");
  const [caseInput, setCaseInput] = useState("{}");
  const [caseExpected, setCaseExpected] = useState("");
  const retry = useMutation({ mutationFn: api.retryJob, onSuccess: () => client.invalidateQueries({ queryKey: ["jobs"] }) });
  const draft = useMutation({
    mutationFn: () => api.draftPrompt(selectedPrompt, {
      user_instructions: instructions || null,
      prompt_text: taskPrompt || null,
      provider: promptParams.provider || null,
      model: promptParams.model || null,
      temperature: promptParams.temperature ? Number(promptParams.temperature) : null,
      top_p: promptParams.top_p ? Number(promptParams.top_p) : null,
      max_tokens: promptParams.max_tokens ? Number(promptParams.max_tokens) : null,
    }),
    onSuccess: (version) => {
      setPromptMessage(`已保存 Draft v${version.version_number}。`);
      client.invalidateQueries({ queryKey: ["prompts"] });
      client.invalidateQueries({ queryKey: ["prompt-preview", selectedPrompt] });
    },
    onError: (error) => setPromptMessage(error.message),
  });
  const clonePrompt = useMutation({
    mutationFn: () => api.clonePrompt(selectedPrompt),
    onSuccess: (version) => {
      setPromptMessage(`已克隆内置 Prompt 为 Draft v${version.version_number}，Production 不受影响。`);
      client.invalidateQueries({ queryKey: ["prompts"] });
      client.invalidateQueries({ queryKey: ["prompt-test-cases", selectedPrompt] });
    },
    onError: (error) => setPromptMessage(error.message),
  });
  const previewPrompt = useQuery({
    queryKey: ["prompt-preview", selectedPrompt],
    queryFn: () => api.previewPrompt(selectedPrompt),
    enabled: Boolean(selectedPrompt),
  });
  const testDraft = useMutation({
    mutationFn: (version: number) => api.testPrompt(selectedPrompt, version),
    onSuccess: () => setPromptMessage("Draft 测试已完成。"),
    onError: (error) => setPromptMessage(error.message),
  });
  const testCases = useQuery({
    queryKey: ["prompt-test-cases", selectedPrompt],
    queryFn: () => api.promptTestCases(selectedPrompt),
    enabled: Boolean(selectedPrompt),
  });
  const createCase = useMutation({
    mutationFn: () => api.createPromptTestCase(selectedPrompt, {
      name: caseName.trim(),
      input_json: parseJsonObject(caseInput),
      expected_json: caseExpected.trim() ? parseJsonObject(caseExpected) : null,
    }),
    onSuccess: () => {
      setCaseName("");
      setCaseInput("{}");
      setCaseExpected("");
      setPromptMessage("已新增 Test Case。");
      client.invalidateQueries({ queryKey: ["prompt-test-cases", selectedPrompt] });
    },
    onError: (error) => setPromptMessage(error.message),
  });
  const removeCase = useMutation({
    mutationFn: (caseId: string) => api.deletePromptTestCase(selectedPrompt, caseId),
    onSuccess: () => client.invalidateQueries({ queryKey: ["prompt-test-cases", selectedPrompt] }),
    onError: (error) => setPromptMessage(error.message),
  });
  const promote = useMutation({
    mutationFn: (version: number) => api.promotePrompt(selectedPrompt, version),
    onSuccess: () => client.invalidateQueries({ queryKey: ["prompts"] }),
  });
  const saveSettings = useMutation({ mutationFn: () => api.updateSettings({ global_ai_instructions: globalInstructions || null, default_source_scope: settingsQuery.data?.default_source_scope ?? "all" }), onSuccess: () => client.invalidateQueries({ queryKey: ["settings"] }) });
  const [batchMessage, setBatchMessage] = useState("");
  const [batchScope, setBatchScope] = useState("all");
  const [batchContentType, setBatchContentType] = useState("");
  const batch = useMutation({
    mutationFn: () => api.reprocessBatch({ source_scope: batchScope, content_type: batchContentType || null }),
    onSuccess: (result) => {
      setBatchMessage(`已提交 ${result.submitted_count} 条，失败 ${result.failed_count} 条。`);
      client.invalidateQueries({ queryKey: ["entries"] });
      client.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (error) => setBatchMessage(error.message),
  });
  const rebuild = useMutation({
    mutationFn: api.rebuildEmbeddings,
    onSuccess: (result) => setBatchMessage(result.detail),
    onError: (error) => setBatchMessage(error.message),
  });
  const importNative = useMutation({
    mutationFn: api.importNative,
    onSuccess: (result) => {
      setImportMessage(`已导入 ${result.created_count} 条，跳过 ${result.skipped_count} 条。${result.errors.length ? ` ${result.errors.length} 条失败。` : ""}`);
      client.invalidateQueries({ queryKey: ["entries"] });
      client.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (error) => setImportMessage(error.message),
  });
  const failed = jobs.data?.filter((job) => ["failed", "retrying", "prompt_validation_failed"].includes(job.status)) ?? [];
  const activePrompt = prompts.data?.find((prompt) => prompt.name === selectedPrompt);
  const draftVersion = activePrompt?.versions.find((version) => version.status === "draft");

  useEffect(() => {
    if (!selectedPrompt && prompts.data?.[0]) setSelectedPrompt(prompts.data[0].name);
    if (promptName && prompts.data?.some((prompt) => prompt.name === promptName)) setSelectedPrompt(promptName);
  }, [prompts.data, promptName, selectedPrompt]);
  useEffect(() => setActivePromptView(promptView), [promptView]);
  useEffect(() => {
    const draftVersion = activePrompt?.versions.find((version) => version.status === "draft");
    const source = draftVersion ?? activePrompt?.versions.find((version) => version.status === "production");
    setInstructions(source?.user_instructions ?? "");
    setTaskPrompt(source?.prompt_text ?? "");
    setPromptParams({
      provider: source?.provider ?? "",
      model: source?.model ?? "",
      temperature: source?.temperature != null ? String(source.temperature) : "",
      top_p: source?.top_p != null ? String(source.top_p) : "",
      max_tokens: source?.max_tokens != null ? String(source.max_tokens) : "",
    });
  }, [activePrompt]);
  useEffect(() => {
    if (settingsQuery.data) setGlobalInstructions(settingsQuery.data.global_ai_instructions ?? "");
  }, [settingsQuery.data]);

  const cardClass = "card p-4";
  const chipClass = "badge bg-secondary-lt";
  const inputClass = "form-control";
  const selectClass = "form-select";
  const primaryButtonClass = "btn btn-primary";
  const secondaryButtonClass = "btn btn-outline-secondary";
  const textButtonClass = "btn btn-link p-0";
  const dangerTextButtonClass = "btn btn-link p-0 text-danger";
  const sectionTitleClass = "card-title mb-0";
  const sectionHintClass = "text-secondary mt-1";
  const labelClass = "form-label";
  const sectionTitle = managementNavigationItems.find((item) => item.id === section)?.label ?? "设置";

  return (
    <PageFrame width="management" labelledBy="more-heading">
      <PageHeader id="more-heading" title={section === "overview" ? "设置与操作" : sectionTitle} description="Provider、AI 任务、Prompt Studio、Memory 与数据搬迁。" />
      <ManagementNav items={managementNavigationItems} active={section} onSelect={(value) => onNavigate(value as ManagementSection)} />
      {section === "models" && status.isPending && <LoadingState label="正在载入模型 Provider 状态…" rows={2} />}
      {section === "models" && status.error && <ErrorState message={status.error.message} onRetry={() => void status.refetch()} />}
      {section === "prompts" && prompts.isPending && <LoadingState label="正在载入 Prompt…" rows={2} />}
      {section === "prompts" && prompts.error && <ErrorState message={prompts.error.message} onRetry={() => void prompts.refetch()} />}
      {section === "memory" && memories.isPending && <LoadingState label="正在载入 Memory…" rows={2} />}
      {section === "memory" && memories.error && <ErrorState message={memories.error.message} onRetry={() => void memories.refetch()} />}

      <div className="row g-4 row-cols-sm-2 mb-4">
        <section className={`${cardClass} ${section === "overview" || section === "models" ? "" : "d-none"}`} aria-labelledby="provider-heading">
          <div className="d-flex align-items-center column-gap-2 mb-2"><Settings className="icon icon-sm text-secondary" aria-hidden="true" /><h3 id="provider-heading" className={sectionTitleClass}>Provider 状态</h3></div>
          <div className="space-y-1 text-sm">
            <div className="d-flex justify-content-between column-gap-3"><span className="text-secondary">Chat</span><span className="text-body text-end">{status.data?.chat_configured ? "已配置" : "未配置运行时 Key"}{status.data?.chat_model ? ` · ${status.data.chat_model}` : ""}</span></div>
            <div className="d-flex justify-content-between column-gap-3"><span className="text-secondary">Embedding</span><span className="text-body text-end">{status.data?.embedding_provider ?? "读取中…"}{status.data?.embedding_model ? ` · ${status.data.embedding_model}` : ""}</span></div>
            <div className="d-flex justify-content-between column-gap-3"><span className="text-secondary">限流</span><span className="text-body text-end">{status.data?.rate_limit_per_minute ?? "—"} req/min</span></div>
          </div>
          <p className="mt-2 small text-secondary">密钥只在服务端运行时环境中使用，不在页面展示。</p>
          {section === "models" && <div className="mt-4 space-y-4 border-top border-secondary pt-4" aria-label="模型 Provider 详情">
            <dl className="row g-3 row-cols-sm-2 text-sm">
              <div><dt className="small text-secondary">Provider</dt><dd className="mt-1 text-body">{status.data?.chat_configured ? "OpenAI-compatible" : "未配置"}</dd></div>
              <div><dt className="small text-secondary">Base URL</dt><dd className="mt-1 text-body">仅服务端运行时配置</dd></div>
              <div><dt className="small text-secondary">Chat Model</dt><dd className="mt-1 text-body">{status.data?.chat_model || "—"}</dd></div>
              <div><dt className="small text-secondary">Embedding Model</dt><dd className="mt-1 text-body">{status.data?.embedding_model || "—"}</dd></div>
              <div><dt className="small text-secondary">Reranker</dt><dd className="mt-1 text-body">由当前检索配置决定</dd></div>
              <div><dt className="small text-secondary">API Key</dt><dd className="mt-1 text-body">不在 UI 回显</dd></div>
            </dl>
            <button className={secondaryButtonClass} type="button" onClick={() => void status.refetch()} disabled={status.isFetching}>{status.isFetching ? "读取中…" : "读取能力状态"}</button>
          </div>}
        </section>

        <section className={`${cardClass} ${section === "overview" || section === "jobs" ? "" : "d-none"}`} aria-labelledby="jobs-heading">
          <div className="d-flex align-items-center column-gap-2 mb-2"><Check className="icon icon-sm text-secondary" aria-hidden="true" /><h3 id="jobs-heading" className={sectionTitleClass}>AI Jobs</h3></div>
          <p className="text-sm text-body">{jobs.data ? `${jobs.data.length} 个任务，${failed.length} 个需关注` : "正在读取任务…"}</p>
          <div className="mt-2  ">
            {failed.slice(0, 5).map((job) => (
              <div className="d-flex align-items-center justify-content-between column-gap-3 py-2" key={job.id}>
                <span className="text-truncate text-sm text-body">{job.job_type}</span>
                <span className="d-flex flex-shrink-0 align-items-center column-gap-3">
                  <span className={chipClass}>{job.status}</span>
                  <button className="btn btn-link p-0 d-inline-flex align-items-center column-gap-1" type="button" onClick={() => retry.mutate(job.id)} disabled={retry.isPending}><RotateCcw className="icon icon-sm" aria-hidden="true" />重试</button>
                </span>
              </div>
            ))}
            {!failed.length && <p className="py-2 text-sm text-secondary">没有需要关注的任务。</p>}
          </div>
        </section>
      </div>

      <div className={`${section === "overview" ? "row" : "d-none"} g-4 row-cols-sm-2 mb-4`}>
        <section className={cardClass}>
          <div className="d-flex align-items-center column-gap-2 mb-2"><Inbox className="icon icon-sm text-secondary" aria-hidden="true" /><h3 className={sectionTitleClass}>Import Inbox</h3></div>
          <p className={sectionHintClass}>查看 URL、文件、PDF 和图片的原始输入与处理状态。</p>
          <button className={`${secondaryButtonClass} mt-3`} type="button" onClick={onOpenInbox}>打开 Inbox</button>
        </section>
        <section className={cardClass}>
          <div className="d-flex align-items-center column-gap-2 mb-2"><Archive className="icon icon-sm text-secondary" aria-hidden="true" /><h3 className={sectionTitleClass}>Knowledge Workbench</h3></div>
          <p className={sectionHintClass}>从 Project、Topic、Entity、Smart View 和时间回顾进入可解释的知识工作台。</p>
          <button className={`${secondaryButtonClass} mt-3`} type="button" onClick={onOpenWorkbench}>打开知识工作台</button>
        </section>
      </div>

      <div className={`${section === "overview" || section === "backup" || section === "prompts" || section === "memory" ? "bg-body border border-secondary rounded   " : "d-none"}`}>
        <section className={`${section === "backup" ? "" : "d-none"} p-4 p-sm-4`} aria-labelledby="batch-heading">
          <div className="d-flex align-items-center column-gap-2 mb-2"><RotateCcw className="icon icon-sm text-secondary" aria-hidden="true" /><h3 id="batch-heading" className={sectionTitleClass}>批量重处理</h3></div>
          <p className={sectionHintClass}>按过滤器重新分析最多 200 条 Entry；会创建新 generation 的 AI Job，不修改原文。</p>
          <div className="d-flex flex-column flex-sm-row align-items-sm-center gap-2 mt-3">
            <select className={selectClass} aria-label="批量来源范围" value={batchScope} onChange={(event) => setBatchScope(event.target.value)}>
              <option value="all">全部来源</option>
              <option value="native">仅原生</option>
              <option value="external">仅外部</option>
            </select>
            <input className={`${inputClass} mw-100`} aria-label="批量内容类型" value={batchContentType} onChange={(event) => setBatchContentType(event.target.value)} placeholder="内容类型（可选）" />
          </div>
          <div className="d-flex flex-wrap align-items-center column-gap-3 row-gap-2 mt-3">
            <button className={secondaryButtonClass} type="button" disabled={batch.isPending} onClick={() => { if (window.confirm("确认提交批量重处理？超过 200 条会返回 422 且不创建任务。")) batch.mutate(); }}>{batch.isPending ? "提交中…" : "提交批量重处理"}</button>
            <button className={textButtonClass} type="button" disabled={rebuild.isPending} onClick={() => { if (window.confirm("确认重建全库 Embedding？不会删除原始 Entry。")) rebuild.mutate(); }}>{rebuild.isPending ? "排队中…" : "重建全库 Embedding"}</button>
          </div>
          {batchMessage && <p className="mt-2 text-sm text-secondary" role="status">{batchMessage}</p>}
        </section>

        <section className={`${section === "backup" ? "" : "d-none"} p-4 p-sm-4`} aria-labelledby="portability-heading">
          <div className="d-flex align-items-center column-gap-2 mb-2"><Download className="icon icon-sm text-secondary" aria-hidden="true" /><h3 id="portability-heading" className={sectionTitleClass}>数据搬迁</h3></div>
          <p className={sectionHintClass}>导出 StarMem 原生备份，或导入之前导出的 JSON / JSONL。导入只新增或跳过重复记录，不会覆盖已有内容。</p>
          <div className="d-flex flex-wrap gap-2 mt-3" aria-label="导出格式">
            {([["json", "导出 JSON"], ["jsonl", "导出 JSONL"], ["markdown", "导出 Markdown"], ["zip", "导出 ZIP（含附件）"]] as const).map(([format, label]) => <a className={secondaryButtonClass} key={format} href={`/api/v1/export?format=${format}`} download>{label}</a>)}
          </div>
          <label className="dropzone d-block mt-4 text-center" htmlFor="native-import-file">
            <span className="dz-message d-block">
              <Upload className="icon text-secondary" aria-hidden="true" />
              <span className="dropzone-msg-title d-block mt-2">选择原生备份文件</span>
              <span className="dropzone-msg-desc d-block mt-1 small text-secondary">点击选择 JSON / JSONL，导入只新增或跳过重复记录</span>
            </span>
            <input id="native-import-file" className="visually-hidden" aria-label="选择原生备份文件" type="file" accept=".json,.jsonl,application/json,application/x-ndjson" disabled={importNative.isPending} onChange={(event) => { const file = event.target.files?.[0]; if (file) { setImportMessage(""); importNative.mutate(file); event.target.value = ""; } }} />
          </label>
          {(importNative.isPending || importMessage) && <p className={`mt-2 text-sm ${importNative.isError ? "text-danger" : "text-secondary"}`} role="status">{importNative.isPending ? "正在导入…" : importMessage}</p>}
        </section>

        <section className={`${section === "overview" ? "" : "d-none"} p-4 p-sm-4`}>
          <div className="d-flex align-items-center column-gap-2 mb-2"><Settings className="icon icon-sm text-secondary" aria-hidden="true" /><h3 className={sectionTitleClass}>全局 AI 指令</h3></div>
          <p className={sectionHintClass}>会作为 Prompt 的 User Instructions 层参与后续派生，不会修改系统安全契约。</p>
          <textarea className={`${inputClass} mt-3`} value={globalInstructions} onChange={(event) => setGlobalInstructions(event.target.value)} rows={3} placeholder="例如：技术故障优先提取现象、根因、命令和最终解决方案。" />
          <button className={`${primaryButtonClass} mt-3`} type="button" onClick={() => saveSettings.mutate()} disabled={saveSettings.isPending}>{saveSettings.isPending ? "保存中…" : "保存设置"}</button>
        </section>

        <section className={`${section === "prompts" ? "" : "d-none"} prompt-studio-card p-4 p-sm-4`} aria-labelledby="prompt-studio-heading">
          <div className="d-flex align-items-center column-gap-2 mb-2"><Sparkles className="icon icon-sm text-secondary" aria-hidden="true" /><h3 id="prompt-studio-heading" className={sectionTitleClass}>Prompt Studio</h3></div>
          <p className={sectionHintClass}>可编辑 Layer 2 Task Prompt 与模型参数；系统安全契约和 Output Schema 保持只读。</p>

          <ul className="nav nav-tabs mt-4" role="tablist" aria-label="Prompt Studio 页面">
            {([['editor', '编辑'], ['versions', '版本历史'], ['tests', '测试用例']] as const).map(([value, label]) => <li className="nav-item" key={value}><button className={`nav-link${activePromptView === value ? " active" : ""}`} type="button" role="tab" aria-selected={activePromptView === value} onClick={() => { setActivePromptView(value); if (selectedPrompt && onPromptNavigate) onPromptNavigate(selectedPrompt, value); }}>{label}</button></li>)}
          </ul>

          <div className="mt-4 row g-4">
            <aside className=" col-lg-4" aria-labelledby="prompt-list-heading">
              <SectionHeader id="prompt-list-heading" title="Prompt List" description="选择一个 Prompt 编辑或查看历史。" />
              <div className="mt-3  ">
                {prompts.data?.map((prompt) => <button className={`btn btn-link d-block w-100 p-2 text-start text-decoration-none ${selectedPrompt === prompt.name ? "bg-primary-lt" : ""}`} type="button" key={prompt.name} onClick={() => setSelectedPrompt(prompt.name)}><strong className="d-block text-truncate fw-medium text-body">{prompt.name}</strong><span className="mt-1 d-block small text-secondary">{prompt.versions.length} 个版本 · {prompt.description || "无描述"}</span></button>)}
              </div>
            </aside>
            <div className=" col-lg-8">
          {activePromptView === "editor" && <div className="space-y-3 mt-3">
            <label className="d-block">
              <span className={labelClass}>Prompt</span>
              <select className={selectClass} value={selectedPrompt} onChange={(event) => setSelectedPrompt(event.target.value)}>
                {prompts.data?.map((prompt) => <option key={prompt.name} value={prompt.name}>{prompt.name}</option>)}
              </select>
            </label>
            <label className="d-block">
              <span className={labelClass}>Task Prompt（Layer 2）</span>
              <textarea className={inputClass} aria-label="Task Prompt" value={taskPrompt} onChange={(event) => setTaskPrompt(event.target.value)} rows={4} />
            </label>
            <label className="d-block">
              <span className={labelClass}>User Instructions</span>
              <textarea className={inputClass} value={instructions} onChange={(event) => setInstructions(event.target.value)} rows={3} placeholder="可选：告诉 StarMem 更关注什么…" />
            </label>
            <div className="row row-cols-sm-2 row-cols-lg-3 g-3">
              <label className="d-block"><span className={labelClass}>Provider</span><input className={inputClass} aria-label="Prompt Provider" value={promptParams.provider} onChange={(event) => setPromptParams({ ...promptParams, provider: event.target.value })} /></label>
              <label className="d-block"><span className={labelClass}>Model</span><input className={inputClass} aria-label="Prompt Model" value={promptParams.model} onChange={(event) => setPromptParams({ ...promptParams, model: event.target.value })} /></label>
              <label className="d-block"><span className={labelClass}>Temperature</span><input className={inputClass} aria-label="Prompt Temperature" type="number" min={0} max={2} step={0.1} value={promptParams.temperature} onChange={(event) => setPromptParams({ ...promptParams, temperature: event.target.value })} /></label>
              <label className="d-block"><span className={labelClass}>Top P</span><input className={inputClass} aria-label="Prompt Top P" type="number" min={0} max={1} step={0.05} value={promptParams.top_p} onChange={(event) => setPromptParams({ ...promptParams, top_p: event.target.value })} /></label>
              <label className="d-block"><span className={labelClass}>Max Tokens</span><input className={inputClass} aria-label="Prompt Max Tokens" type="number" min={1} max={32000} value={promptParams.max_tokens} onChange={(event) => setPromptParams({ ...promptParams, max_tokens: event.target.value })} /></label>
            </div>
            <div className="d-flex flex-wrap align-items-center column-gap-3 row-gap-2">
              <button className={primaryButtonClass} type="button" onClick={() => draft.mutate()} disabled={!selectedPrompt || draft.isPending}>{draft.isPending ? "保存中…" : "保存 Draft"}</button>
              <button className={secondaryButtonClass} type="button" onClick={() => clonePrompt.mutate()} disabled={!selectedPrompt || clonePrompt.isPending}>克隆内置</button>
              {draftVersion && <button className={secondaryButtonClass} type="button" onClick={() => promote.mutate(draftVersion.version_number)} disabled={promote.isPending}>Promote v{draftVersion.version_number}</button>}
              {draftVersion && <button className={secondaryButtonClass} type="button" onClick={() => testDraft.mutate(draftVersion.version_number)} disabled={testDraft.isPending}>{testDraft.isPending ? "测试中…" : "运行 Draft 测试"}</button>}
            </div>
          </div>}

          {promptMessage && <p className="mt-3 text-sm text-secondary" role="status">{promptMessage}</p>}

          {activePromptView === "editor" && testDraft.data && (
            <div className="mt-3 rounded bg-body-tertiary border border-secondary p-3">
              <strong className="d-block mb-1 text-sm fw-medium text-body">Draft 测试结果</strong>
              {testDraft.data.results.map((result, index) => (
                <div className="d-flex flex-column row-gap-1 py-1 text-sm" key={index}>
                  <span className="text-body">{String(result.name)}：{result.passed ? "通过" : "未通过"}</span>
                  {result.error ? <small className="small text-secondary">{String(result.error)}</small> : null}
                </div>
              ))}
            </div>
          )}

          {activePromptView === "editor" && activePrompt && <p className="mt-3 small text-secondary">Production：v{activePrompt.versions.find((version) => version.status === "production")?.version_number ?? "—"} · 历史版本 {activePrompt.versions.length}</p>}

          {activePromptView === "editor" && <details className="prompt-preview group mt-3 bg-body-tertiary border border-secondary rounded">
            <summary className="d-flex align-items-center justify-content-between column-gap-2 py-2 px-3 text-sm fw-medium text-body cursor-pointer list-unstyled">
              预览最终 Prompt
              <ChevronDown className="icon icon-sm text-secondary  " aria-hidden="true" />
            </summary>
            <pre className="overflow-auto overflow-auto border-top border-secondary p-3 small text-body text-break">{previewPrompt.data?.content ?? "正在读取预览…"}</pre>
          </details>}

          {activePromptView === "versions" && <div className="mt-4  " aria-label="Prompt 版本列表">{activePrompt?.versions.map((version) => <article className="py-3" key={version.id}><div className="d-flex flex-wrap align-items-center gap-2"><span className={chipClass}>v{version.version_number}</span><span className="small text-secondary">{version.status} · {new Date(version.created_at).toLocaleString("zh-CN")}</span></div><p className="mt-2 text-sm text-body">{version.prompt_text}</p><p className="mt-1 small text-secondary">{version.provider || "—"} / {version.model || "—"} · schema {version.output_schema_version || "—"}</p></article>)}</div>}

          {activePromptView === "tests" && <div className="mt-4 test-case-editor">
            <div className="d-flex flex-wrap align-items-center justify-content-between gap-2"><strong className="d-block text-sm fw-medium text-body">Test Cases</strong>{draftVersion && <button className={primaryButtonClass} type="button" onClick={() => testDraft.mutate(draftVersion.version_number)} disabled={testDraft.isPending}>{testDraft.isPending ? "运行中…" : "运行 Draft 测试"}</button>}</div>
            <div className=" ">
              {testCases.data?.map((item) => (
                <div className="similar-row d-flex align-items-center justify-content-between column-gap-3 py-2 text-sm" key={item.id}>
                  <details className=""><summary className="cursor-pointer text-body">{item.name}{item.is_builtin ? "（内置）" : ""}</summary><div className="mt-2 space-y-2 small text-secondary"><pre className="overflow-auto text-break rounded bg-body-tertiary p-2">Input: {JSON.stringify(item.input_json, null, 2)}</pre>{item.expected_json && <pre className="overflow-auto text-break rounded bg-body-tertiary p-2">Expected: {JSON.stringify(item.expected_json, null, 2)}</pre>}</div></details>
                  {!item.is_builtin && <button className={dangerTextButtonClass} type="button" onClick={() => removeCase.mutate(item.id)} disabled={removeCase.isPending}>删除</button>}
                </div>
              ))}
            </div>
            {testCases.data && testCases.data.length === 0 && <p className="mt-2 text-sm text-secondary">暂无 Test Case。</p>}
            <div className="space-y-2 mt-3">
              <input className={inputClass} aria-label="Test Case 名称" value={caseName} onChange={(event) => setCaseName(event.target.value)} placeholder="用例名称" />
              <textarea className={inputClass} aria-label="Test Case 输入 JSON" value={caseInput} onChange={(event) => setCaseInput(event.target.value)} rows={2} placeholder='输入 JSON，例如 {"raw_content":"..."}' />
              <textarea className={inputClass} aria-label="Test Case 期望 JSON" value={caseExpected} onChange={(event) => setCaseExpected(event.target.value)} rows={2} placeholder='期望 JSON（可选）' />
              <button className={secondaryButtonClass} type="button" disabled={!selectedPrompt || !caseName.trim() || createCase.isPending} onClick={() => createCase.mutate()}>{createCase.isPending ? "新增中…" : "新增 Test Case"}</button>
            </div>
            {testDraft.data && <div className="mt-4 space-y-2 rounded border border-secondary bg-body-tertiary p-3" aria-label="Prompt 测试结果"><strong className="d-block text-sm fw-medium text-body">Run Status / Results</strong>{testDraft.data.results.map((result, index) => <div className="border-top border-secondary pt-2 text-sm" key={index}><p className="text-body">{String(result.name)}：{result.passed ? "通过" : "未通过"}</p>{result.expected !== undefined && <p className="mt-1 small text-secondary">Expected: {String(result.expected)}</p>}{result.actual !== undefined && <p className="mt-1 small text-secondary">Actual: {String(result.actual)}</p>}{result.diff !== undefined && <pre className="mt-1 overflow-auto text-break small text-danger">Diff: {String(result.diff)}</pre>}{result.error ? <p className="mt-1 small text-danger">{String(result.error)}</p> : null}</div>)}</div>}
          </div>}
            </div>
          </div>
        </section>

        <section className={`${section === "memory" ? "" : "d-none"} p-4 p-sm-4`} aria-labelledby="memory-heading">
          <div className="d-flex flex-wrap align-items-center justify-content-between column-gap-3 row-gap-2 mb-2">
            <div className="d-flex align-items-center column-gap-2"><BrainCircuit className="icon icon-sm text-secondary" aria-hidden="true" /><h3 id="memory-heading" className={sectionTitleClass}>Memory 生命周期</h3></div>
            <select className={selectClass} aria-label="Memory 状态筛选" value={memoryStatus} onChange={(event) => setMemoryStatus(event.target.value)}>
              <option value="active">active</option>
              <option value="conflicted">conflicted</option>
              <option value="superseded">superseded</option>
              <option value="expired">expired</option>
              <option value="deleted">deleted</option>
              <option value="all">全部</option>
            </select>
          </div>
          {!memories.data?.length && <p className="text-sm text-secondary">当前筛选下没有 Memory。</p>}
          <div className=" ">
            {memories.data?.slice(0, 12).map((memory) => (
              <div className="memory-row d-flex flex-wrap align-items-start justify-content-between column-gap-3 row-gap-2 py-2" key={memory.id}>
                <span className=" text-sm text-body">{memory.memory_text}</span>
                <span className="d-flex flex-wrap align-items-center column-gap-2 row-gap-1">
                  <span className={chipClass}>{memory.status}</span>
                  <span className={chipClass}>{memory.salience}</span>
                  {onOpenMemory && <button className={textButtonClass} type="button" onClick={() => onOpenMemory(memory.id)}>详情</button>}
                  {memory.status !== "active" && <button className={textButtonClass} type="button" onClick={() => confirmMemory.mutate(memory.id)} disabled={confirmMemory.isPending}>确认</button>}
                  {memory.status !== "expired" && memory.status !== "deleted" && <button className={textButtonClass} type="button" onClick={() => expireMemory.mutate(memory.id)} disabled={expireMemory.isPending}>标记过期</button>}
                  {memory.status !== "deleted" && <button className={dangerTextButtonClass} type="button" onClick={() => { if (window.confirm("确认删除该 Memory？不会移除原始 Entry。")) deleteMemory.mutate(memory.id); }} disabled={deleteMemory.isPending}>删除</button>}
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </PageFrame>
  );
}

function SourcesPage({ onOpenEntry }: { onOpenEntry: (entryId: string) => void }) {
  const sources = useInfiniteQuery({
    queryKey: ["sources"],
    queryFn: ({ pageParam }) => api.entries(pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  });
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const entries = sources.data?.pages.flatMap((page) => page.items) ?? [];
  const groups = useMemo(() => {
    const grouped = new Map<string, { key: string; sourceId: string; uri: string | null; entries: Entry[] }>();
    for (const entry of entries) {
      const key = `${entry.source_id}:${entry.source_uri ?? ""}`;
      const current = grouped.get(key) ?? { key, sourceId: entry.source_id, uri: entry.source_uri, entries: [] };
      current.entries.push(entry);
      grouped.set(key, current);
    }
    return [...grouped.values()];
  }, [entries]);
  const selected = groups.find((group) => group.key === selectedKey) ?? groups[0] ?? null;

  useEffect(() => {
    if (!selectedKey && groups[0]) setSelectedKey(groups[0].key);
  }, [groups, selectedKey]);

  return (
    <PageFrame width="browse" labelledBy="sources-heading">
      <PageHeader id="sources-heading" title="来源" description="从真实 Entry provenance 浏览来源与回溯关系；当前没有 Connector Sync 管理接口。" />
      {sources.isPending && <LoadingState label="正在载入来源…" />}
      {sources.error && <ErrorState message={sources.error.message} onRetry={() => void sources.refetch()} />}
      {!sources.isPending && !sources.error && !groups.length && <EmptyState title="还没有来源证据" description="保存第一条记录或导入网页/文件后，来源会在这里按真实 provenance 汇总。" />}
      {groups.length > 0 && (
        <div className="row g-4">
          <section className=" col-lg-8" aria-labelledby="source-list-heading">
            <SectionHeader id="source-list-heading" title="来源列表" description={`${groups.length} 个来源，基于当前已加载的 Entry。`} />
            <div className="mt-3  ">
              {groups.map((group) => (
                <button className={`btn btn-link d-flex w-100 align-items-start justify-content-between column-gap-4 p-3 text-start text-decoration-none ${selected?.key === group.key ? "bg-primary-lt" : ""}`} type="button" key={group.key} onClick={() => setSelectedKey(group.key)}>
                  <span className="">
                    <strong className="d-block text-truncate text-sm fw-medium text-body">{group.uri || `Source ${group.sourceId.slice(0, 8)}`}</strong>
                    <span className="mt-1 d-block text-truncate small text-secondary">{group.sourceId} · {group.entries.length} 条 Entry</span>
                  </span>
                  <span className={ui.chip}>{group.uri ? "URL" : "Native"}</span>
                </button>
              ))}
            </div>
            {sources.hasNextPage && <button className={`${ui.secondaryButton} mt-4 w-100`} type="button" onClick={() => sources.fetchNextPage()} disabled={sources.isFetchingNextPage}>{sources.isFetchingNextPage ? "正在载入…" : "加载更多来源"}</button>}
          </section>
          <aside className={`${ui.surface} h-auto p-4`} aria-labelledby="source-detail-heading">
            <SectionHeader id="source-detail-heading" title="来源详情" description="仅展示当前已有 provenance。" />
            {selected && (
              <div className="mt-4 space-y-4 text-sm">
                <dl className="row row-gap-2">
                  <div><dt className="small text-secondary">Source ID</dt><dd className="mt-1 text-break text-body">{selected.sourceId}</dd></div>
                  <div><dt className="small text-secondary">来源地址</dt><dd className="mt-1 text-break text-body">{selected.uri || "StarMem Native / 本地记录"}</dd></div>
                  <div><dt className="small text-secondary">Entry 数量</dt><dd className="mt-1 text-body">{selected.entries.length}</dd></div>
                </dl>
                <div className="border-top border-secondary pt-3">
                  <h3 className={ui.sectionTitle}>最近证据</h3>
                  <div className="mt-2  ">
                    {selected.entries.slice(0, 5).map((entry) => <button className="btn btn-link d-block w-100 p-0 text-start text-primary" type="button" key={entry.id} onClick={() => onOpenEntry(entry.id)}>{entry.title || entry.raw_content.slice(0, 72) || "未命名 Entry"}</button>)}
                  </div>
                </div>
                <p className="rounded border border-secondary bg-body-tertiary px-3 py-2 small text-secondary">Connector、Sync Status 和外部 Source 管理不在当前 API 范围内。</p>
              </div>
            )}
          </aside>
        </div>
      )}
    </PageFrame>
  );
}

const jobStatusLabels: Record<string, string> = {
  pending: "等待",
  running: "处理中",
  succeeded: "成功",
  done: "成功",
  failed: "失败",
  retrying: "重试中",
  prompt_validation_failed: "Prompt 校验失败",
};

const managementNavigationItems = [
  { id: "overview", label: "概览", description: "管理入口和运行状态" },
  { id: "models", label: "模型与 Provider", description: "运行时模型状态" },
  { id: "prompts", label: "Prompt Studio", description: "编辑、历史和测试" },
  { id: "jobs", label: "AI 任务", description: "处理任务和重试" },
  { id: "memory", label: "Memory", description: "生命周期与证据" },
  { id: "backup", label: "数据搬迁", description: "导入、导出和批处理" },
] satisfies Array<{ id: ManagementSection; label: string; description: string }>;

function AIJobsPage({ onOpenEntry, onOpenDetail, onNavigate }: { onOpenEntry: (entryId: string) => void; onOpenDetail: (jobId: string) => void; onNavigate?: (section: ManagementSection) => void }) {
  const client = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [showAll, setShowAll] = useState(false);
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: api.jobs });
  const retry = useMutation({ mutationFn: api.retryJob, onSuccess: () => client.invalidateQueries({ queryKey: ["jobs"] }) });
  const filtered = jobs.data?.filter((job) => !statusFilter || job.status === statusFilter) ?? [];
  const visibleJobs = showAll ? filtered : filtered.slice(0, 50);

  return (
    <PageFrame width="management" labelledBy="jobs-page-heading">
      <PageHeader id="jobs-page-heading" title="AI 任务" description="查看派生任务、处理状态、Provider、耗时与失败恢复。" actions={<button className={ui.secondaryButton} type="button" onClick={() => void jobs.refetch()} disabled={jobs.isFetching}>刷新</button>} />
      <ManagementNav items={managementNavigationItems} active="jobs" onSelect={(value) => onNavigate?.(value as ManagementSection)} />
      <FilterBar count={filtered.length} countLabel="个任务">
        <select className={ui.select} aria-label="AI Job 状态" value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setShowAll(false); }}>
          <option value="">全部状态</option>
          <option value="pending">等待</option>
          <option value="running">处理中</option>
          <option value="succeeded">成功</option>
          <option value="failed">失败</option>
          <option value="retrying">重试中</option>
        </select>
      </FilterBar>
      {jobs.isPending && <LoadingState label="正在载入 AI 任务…" />}
      {jobs.error && <ErrorState message={jobs.error.message} onRetry={() => void jobs.refetch()} />}
      {!jobs.isPending && !jobs.error && !filtered.length && <EmptyState title="没有匹配的 AI 任务" description="任务会在 Entry 保存后异步出现；调整状态筛选或返回记录页。" />}
      <div className="d-none d-lg-grid border-bottom border-secondary py-2 small text-secondary row-cols-lg-6 g-lg-3"><span className="col-lg-8">任务 / Entry</span><span>状态</span><span>Provider / Model</span><span>Latency / Attempts</span><span className="text-end">操作</span></div>
      <div className=" ">
        {visibleJobs.map((job) => (
          <article className="job-row row gap-3 py-4 row-cols-sm-2 row-cols-lg-6 align-items-lg-center" key={job.id}>
            <div className="col-lg-8"><button className="btn btn-link p-0 d-block mw-100 text-truncate text-start fw-medium text-primary" type="button" onClick={() => onOpenDetail(job.id)}>{job.job_type}</button><span className="mt-1 d-block text-truncate small text-secondary">Entry {job.entry_id.slice(0, 8)}</span></div>
            <div className="small text-secondary"><span className={ui.chip}>{jobStatusLabels[job.status] ?? job.status}</span></div>
            <div className="small text-secondary">{job.provider || "—"}<br />{job.model || "—"}</div>
            <div className="small font-monospace text-secondary">{job.latency_ms != null ? `${job.latency_ms} ms` : "—"}<br />尝试 {job.attempt}</div>
            <div className="d-flex flex-wrap align-items-center column-gap-3 row-gap-1 justify-content-lg-end"><button className={ui.textButton} type="button" onClick={() => onOpenEntry(job.entry_id)}>查看 Entry</button>{["failed", "retrying", "prompt_validation_failed"].includes(job.status) && <button className={ui.textButton} type="button" onClick={() => retry.mutate(job.id)} disabled={retry.isPending}>重试</button>}</div>
          </article>
        ))}
      </div>
      {filtered.length > visibleJobs.length && <button className={`${ui.secondaryButton} mt-4 w-100`} type="button" onClick={() => setShowAll(true)}>显示全部 {filtered.length} 个任务</button>}
    </PageFrame>
  );
}

function AIJobDetailPage({ jobId, onBack, onOpenEntry }: { jobId: string; onBack: () => void; onOpenEntry: (entryId: string) => void }) {
  const client = useQueryClient();
  const job = useQuery({ queryKey: ["job", jobId], queryFn: () => api.job(jobId) });
  const retry = useMutation({ mutationFn: () => api.retryJob(jobId), onSuccess: () => { client.invalidateQueries({ queryKey: ["job", jobId] }); client.invalidateQueries({ queryKey: ["jobs"] }); } });
  if (job.isPending) return <PageFrame width="detail" labelledBy="job-detail-heading"><PageHeader id="job-detail-heading" title="AI 任务详情" actions={<button className={ui.secondaryButton} type="button" onClick={onBack}>返回</button>} /><LoadingState label="正在载入 AI 任务详情…" /></PageFrame>;
  if (job.error || !job.data) return <PageFrame width="detail" labelledBy="job-detail-heading"><PageHeader id="job-detail-heading" title="AI 任务详情" actions={<button className={ui.secondaryButton} type="button" onClick={onBack}>返回</button>} /><ErrorState message={job.error?.message ?? "任务不存在"} onRetry={() => void job.refetch()} /></PageFrame>;
  const item = job.data;
  return (
    <PageFrame width="detail" labelledBy="job-detail-heading">
      <PageHeader id="job-detail-heading" title={item.job_type} description={`AI 任务 · ${jobStatusLabels[item.status] ?? item.status}`} actions={<><button className={ui.secondaryButton} type="button" onClick={onBack}>返回任务列表</button>{["failed", "retrying", "prompt_validation_failed"].includes(item.status) && <button className={ui.primaryButton} type="button" onClick={() => retry.mutate()} disabled={retry.isPending}>{retry.isPending ? "重试中…" : "重试任务"}</button>}</>} />
      <DetailRail
        main={<article className={`${ui.surface} space-y-5 p-5 p-sm-4`}><SectionHeader title="任务摘要" description="处理输入与结果状态。" /><dl className="row g-4 row-cols-sm-2"><div><dt className="small text-secondary">Job ID</dt><dd className="mt-1 text-break text-sm text-body">{item.id}</dd></div><div><dt className="small text-secondary">Entry</dt><dd className="mt-1 text-sm"><button className={ui.textButton} type="button" onClick={() => onOpenEntry(item.entry_id)}>{item.entry_id}</button></dd></div><div><dt className="small text-secondary">创建时间</dt><dd className="mt-1 text-sm text-body">{new Date(item.created_at).toLocaleString("zh-CN")}</dd></div><div><dt className="small text-secondary">完成时间</dt><dd className="mt-1 text-sm text-body">{item.finished_at ? new Date(item.finished_at).toLocaleString("zh-CN") : "—"}</dd></div></dl>{item.error && <div className="rounded border border-danger bg-body-tertiary p-3 text-sm text-danger" role="alert">{item.error}</div>}</article>}
        rail={<aside className={`${ui.surface} space-y-4 p-4`}><SectionHeader title="运行元数据" /><dl className="row row-gap-3 text-sm"><div><dt className="small text-secondary">状态</dt><dd className="mt-1"><span className={ui.chip}>{jobStatusLabels[item.status] ?? item.status}</span></dd></div><div><dt className="small text-secondary">Provider / Model</dt><dd className="mt-1 text-break text-body">{item.provider || "—"} / {item.model || "—"}</dd></div><div><dt className="small text-secondary">Latency</dt><dd className="mt-1 text-body">{item.latency_ms != null ? `${item.latency_ms} ms` : "—"}</dd></div><div><dt className="small text-secondary">Token Usage</dt><dd className="mt-1 text-body">{item.token_usage ?? "—"}</dd></div><div><dt className="small text-secondary">Generation / Attempts</dt><dd className="mt-1 text-body">{item.generation} / {item.attempt}</dd></div></dl></aside>}
      />
    </PageFrame>
  );
}

function MemoryDetailPage({ memoryId, onBack, onOpenEntry }: { memoryId: string; onBack: () => void; onOpenEntry: (entryId: string) => void }) {
  const client = useQueryClient();
  const memory = useQuery({ queryKey: ["memory", memoryId], queryFn: () => api.memory(memoryId) });
  const confirm = useMutation({ mutationFn: () => api.confirmMemory(memoryId), onSuccess: () => client.invalidateQueries({ queryKey: ["memory", memoryId] }) });
  const expire = useMutation({ mutationFn: () => api.expireMemory(memoryId), onSuccess: () => client.invalidateQueries({ queryKey: ["memory", memoryId] }) });
  const remove = useMutation({ mutationFn: () => api.deleteMemory(memoryId), onSuccess: onBack });
  if (memory.isPending) return <PageFrame width="detail" labelledBy="memory-detail-heading"><PageHeader id="memory-detail-heading" title="Memory 详情" actions={<button className={ui.secondaryButton} type="button" onClick={onBack}>返回</button>} /><LoadingState label="正在载入 Memory 详情…" /></PageFrame>;
  if (memory.error || !memory.data) return <PageFrame width="detail" labelledBy="memory-detail-heading"><PageHeader id="memory-detail-heading" title="Memory 详情" actions={<button className={ui.secondaryButton} type="button" onClick={onBack}>返回</button>} /><ErrorState message={memory.error?.message ?? "Memory 不存在"} onRetry={() => void memory.refetch()} /></PageFrame>;
  const item = memory.data;
  return (
    <PageFrame width="detail" labelledBy="memory-detail-heading">
      <PageHeader id="memory-detail-heading" title="Memory 详情" description="Current Fact、证据、生命周期和来源回溯。" actions={<button className={ui.secondaryButton} type="button" onClick={onBack}>返回 Memory</button>} />
      <DetailRail
        main={<article className={`${ui.surface} space-y-5 p-5 p-sm-4`}><SectionHeader title="Current Fact" /><p className="fs-4 lh-lg text-body">{item.memory_text}</p><div className="border-top border-secondary pt-4"><SectionHeader title="Value" /><pre className="mt-3 overflow-auto text-break rounded bg-body-tertiary p-3 small text-body">{JSON.stringify(item.value_json, null, 2)}</pre></div></article>}
        rail={<aside className={`${ui.surface} space-y-4 p-4`}><SectionHeader title="生命周期" /><div className="d-flex flex-wrap gap-2"><span className={ui.chip}>{item.status}</span><span className={ui.chip}>{item.salience}</span>{item.durable && <span className={ui.chip}>durable</span>}</div><dl className="row row-gap-3 text-sm"><div><dt className="small text-secondary">Subject / Predicate</dt><dd className="mt-1 text-break text-body">{item.subject_type}:{item.subject_key} · {item.predicate}</dd></div><div><dt className="small text-secondary">Confidence</dt><dd className="mt-1 text-body">{Math.round(item.confidence * 100)}%</dd></div><div><dt className="small text-secondary">Valid From / To</dt><dd className="mt-1 text-body">{item.valid_from || "—"} / {item.valid_to || "—"}</dd></div><div><dt className="small text-secondary">Expired At</dt><dd className="mt-1 text-body">{item.expired_at || "—"}</dd></div></dl>{item.source_entry_id && <button className={ui.textButton} type="button" onClick={() => onOpenEntry(item.source_entry_id!)}>查看证据 Entry</button>}<div className="d-flex flex-wrap gap-2 border-top border-secondary pt-4"><button className={ui.secondaryButton} type="button" onClick={() => confirm.mutate()} disabled={confirm.isPending}>确认</button><button className={ui.secondaryButton} type="button" onClick={() => expire.mutate()} disabled={expire.isPending || item.status === "expired"}>标记过期</button><button className={ui.dangerTextButton} type="button" onClick={() => { if (window.confirm("确认删除该 Memory？不会移除原始 Entry。")) remove.mutate(); }} disabled={remove.isPending}>删除</button></div></aside>}
      />
    </PageFrame>
  );
}

function EntryDetailPage({ entryId, onBack, onOpenEntry, onOpenHistory }: { entryId: string; onBack: () => void; onOpenEntry: (entryId: string) => void; onOpenHistory: () => void }) {
  const client = useQueryClient();
  const entry = useQuery({ queryKey: ["entry", entryId], queryFn: () => api.entry(entryId) });
  const metadata = useQuery({ queryKey: ["entry-metadata", entryId], queryFn: () => api.entryMetadata(entryId), enabled: Boolean(entry.data) });
  const related = useQuery({ queryKey: ["related", entryId], queryFn: () => api.related(entryId), enabled: Boolean(entry.data) });
  const relations = useQuery({ queryKey: ["relations", entryId], queryFn: () => api.relations(entryId), enabled: Boolean(entry.data) });
  const attachments = useQuery({ queryKey: ["attachments", entryId], queryFn: () => api.attachments(entryId), enabled: Boolean(entry.data) });
  const update = useMutation({ mutationFn: (changes: Partial<Pick<Entry, "is_pinned" | "is_favorite">>) => api.updateEntry(entryId, changes), onSuccess: () => { client.invalidateQueries({ queryKey: ["entry", entryId] }); client.invalidateQueries({ queryKey: ["entries"] }); } });
  const reprocess = useMutation({ mutationFn: () => api.reprocessEntry(entryId), onSuccess: () => { client.invalidateQueries({ queryKey: ["entry", entryId] }); client.invalidateQueries({ queryKey: ["jobs"] }); } });
  if (entry.isPending) return <PageFrame width="detail" labelledBy="entry-detail-heading"><PageHeader id="entry-detail-heading" title="Entry 详情" actions={<button className={ui.secondaryButton} type="button" onClick={onBack}>返回</button>} /><LoadingState label="正在载入 Entry 详情…" /></PageFrame>;
  if (entry.error || !entry.data) return <PageFrame width="detail" labelledBy="entry-detail-heading"><PageHeader id="entry-detail-heading" title="Entry 详情" actions={<button className={ui.secondaryButton} type="button" onClick={onBack}>返回</button>} /><ErrorState message={entry.error?.message ?? "Entry 不存在"} onRetry={() => void entry.refetch()} /></PageFrame>;
  const item = entry.data;
  return (
    <PageFrame width="detail" labelledBy="entry-detail-heading">
      <PageHeader id="entry-detail-heading" title={item.title || "Entry 详情"} description={`${new Date(item.created_at).toLocaleString("zh-CN")} · ${item.source_uri || `Source ${item.source_id.slice(0, 8)}`}`} actions={<><button className={ui.secondaryButton} type="button" onClick={onBack}>返回列表</button><button className={ui.secondaryButton} type="button" onClick={onOpenHistory}>查看历史</button></>} />
      <DetailRail
        main={<article className={`${ui.surface} p-5 p-sm-4`}><div className="d-flex flex-wrap align-items-center gap-2 border-bottom border-secondary pb-4"><span className={ui.chip}>{item.content_type}</span>{item.content_types.filter((type) => type !== item.content_type).map((type) => <span className={ui.chip} key={type}>{type}</span>)}{item.is_pinned && <span className={ui.chip}>已置顶</span>}{item.is_favorite && <span className={ui.chip}>已收藏</span>}</div><div className="mt-5 space-y-3 text-sm lh-lg text-body"><ReactMarkdown components={{ pre: ({ children }) => <pre className="mw-100 overflow-auto text-break">{children}</pre> }}>{item.raw_content}</ReactMarkdown></div><div className="mt-6 d-flex flex-wrap align-items-center gap-2 border-top border-secondary pt-4"><button className={ui.secondaryButton} type="button" onClick={() => update.mutate({ is_favorite: !item.is_favorite })}>{item.is_favorite ? "取消收藏" : "收藏"}</button><button className={ui.secondaryButton} type="button" onClick={() => update.mutate({ is_pinned: !item.is_pinned })}>{item.is_pinned ? "取消置顶" : "置顶"}</button><button className={ui.secondaryButton} type="button" onClick={() => reprocess.mutate()} disabled={reprocess.isPending}>{reprocess.isPending ? "排队中…" : "重新 AI 处理"}</button></div></article>}
        rail={<aside className="space-y-4"><section className={`${ui.surface} space-y-4 p-4`}><SectionHeader title="Metadata" description="AI 派生与人工锁定字段。" />{metadata.isPending && <LoadingState label="正在载入 Metadata…" rows={1} />}{metadata.error && <ErrorState message={metadata.error.message} onRetry={() => void metadata.refetch()} />}{metadata.data && <dl className="row row-gap-3 text-sm"><div><dt className="small text-secondary">Summary</dt><dd className="mt-1 text-body">{metadata.data.summary || "—"}</dd></div><div><dt className="small text-secondary">Project / Topic</dt><dd className="mt-1 text-body">{metadata.data.project || "—"} / {metadata.data.topic || "—"}</dd></div><div><dt className="small text-secondary">Importance</dt><dd className="mt-1 text-body">{metadata.data.importance}</dd></div><div><dt className="small text-secondary">AI Status</dt><dd className="mt-1"><AIStatus status={aiStatusKind(item.ai_status)} /></dd></div></dl>}</section><section className={`${ui.surface} space-y-3 p-4`}><SectionHeader title="Source / Attachments" />{item.source_uri && <a className={ui.textButton} href={item.source_uri} target="_blank" rel="noreferrer">打开原 URL</a>}{attachments.data?.map((attachment) => <a className="d-block text-truncate text-sm text-primary " href={attachment.download_url} key={attachment.id}>{attachment.original_filename} · {(attachment.size_bytes / 1024).toFixed(1)} KB</a>)}<p className="text-break small text-secondary">Source ID: {item.source_id}</p></section><section className={`${ui.surface} space-y-3 p-4`}><SectionHeader title="Related / Relations" />{related.isPending || relations.isPending ? <LoadingState label="正在载入关联…" rows={1} /> : null}{related.data?.map((candidate) => <div className="border-top border-secondary pt-2  pt-0" key={candidate.entry_id}><button className="text-start text-sm text-primary " type="button" onClick={() => onOpenEntry(candidate.entry_id)}>{candidate.title || candidate.snippet.slice(0, 80)}</button><p className="small text-secondary">{candidate.reasons.join(" / ")} · {Math.round(candidate.score * 100)}%</p></div>)}{relations.data?.map((relation) => <div className="border-top border-secondary pt-2 text-sm text-body" key={relation.id}>{relation.direction === "outbound" ? "→" : "←"} {relation.relation_type} · {relation.target?.title || relation.target_id.slice(0, 8)}</div>)}{related.data?.length === 0 && relations.data?.length === 0 && <p className="text-sm text-secondary">暂无关联证据。</p>}</section></aside>}
      />
    </PageFrame>
  );
}

function EntryHistoryPage({ entryId, onBack }: { entryId: string; onBack: () => void }) {
  const versions = useQuery({ queryKey: ["entry-versions", entryId], queryFn: () => api.entryVersions(entryId) });
  return (
    <PageFrame width="detail" labelledBy="entry-history-heading">
      <PageHeader id="entry-history-heading" title="Entry 版本历史" description="保留每个原文版本与差异，来源可回溯。" actions={<button className={ui.secondaryButton} type="button" onClick={onBack}>返回 Entry</button>} />
      {versions.isPending && <LoadingState label="正在载入版本历史…" />}
      {versions.error && <ErrorState message={versions.error.message} onRetry={() => void versions.refetch()} />}
      {!versions.isPending && !versions.error && !versions.data?.length && <EmptyState title="尚无历史版本" description="Entry 被编辑或导入后，版本会显示在这里。" />}
      <div className=" ">
        {versions.data?.map((version: EntryVersion) => <article className="py-5" key={version.id}><div className="d-flex flex-wrap align-items-center gap-2"><span className={ui.chip}>v{version.version_number}</span><span className="small text-secondary">{version.change_source} · {new Date(version.created_at).toLocaleString("zh-CN")}</span></div><h2 className="mt-2 text-sm fw-medium text-body">{version.title || "未命名版本"}</h2><pre className="mt-3 overflow-auto overflow-auto text-break rounded bg-body-tertiary p-4 small text-body">{version.raw_content}</pre><VersionDiff entryId={entryId} versionNumber={version.version_number} /></article>)}
      </div>
    </PageFrame>
  );
}

function NotFoundPage({ onNavigate }: { onNavigate: () => void }) {
  return (
    <PageFrame width="management" labelledBy="not-found-heading" className="d-flex  flex-column justify-content-center">
      <PageHeader id="not-found-heading" title="页面不存在" description="这个地址没有对应的 StarMem 页面。" />
      <EmptyState title="找不到这个页面" description="核心记录仍然安全保存在仓库中。" actions={<button className={ui.primaryButton} type="button" onClick={onNavigate}>回到记录</button>} />
    </PageFrame>
  );
}

function Workspace({ onLogout, sharedPayload }: { onLogout: () => void; sharedPayload?: SharedPayload | null }) {
  const [route, setRoute] = useState<WorkspaceRoute>(() => parseRoute(window.location.pathname));
  const [focusEntryId, setFocusEntryId] = useState<string | null>(null);
  const client = useQueryClient();
  const logout = useMutation({ mutationFn: api.logout, onSuccess: onLogout });
  const refresh = () => client.invalidateQueries({ queryKey: ["entries"] });
  useEffect(() => {
    const handlePopState = () => setRoute(parseRoute(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);
  const navigate = (nextRoute: WorkspaceRoute, replace = false) => {
    navigateTo(nextRoute, replace);
    setRoute(nextRoute);
  };
  const openEntry = (entryId: string) => {
    setFocusEntryId(entryId);
    navigate({ page: "timeline" });
  };
  const openEntryDetail = (entryId: string) => navigate({ page: "entry", id: entryId });
  const navigateShell = (target: ShellPage) => {
    if (target === "more") return navigate({ page: "more", managementSection: "overview" });
    if (target === "jobs") return navigate({ page: "jobs", managementSection: "jobs" });
    navigate({ page: target });
  };

  return (
    <AppShell page={activeShellPage(route)} onNavigate={navigateShell} onLogout={() => logout.mutate()}>
      {route.page === "capture" && (
        <PageFrame width="capture" labelledBy="capture-heading">
          <PageHeader id="capture-heading" title="有什么需要记住的？" description="记录之后，StarMem 会自动整理和关联。" />
          <div className="row g-4">
            <div className="col-lg-8"><Capture onSaved={refresh} onOpenInbox={() => navigate({ page: "inbox" })} sharedPayload={sharedPayload} /></div>
            <div className="col-lg-4 space-y-6">
              <RecentEntries focusEntryId={focusEntryId} onOpenEntry={openEntry} onOpenDetail={openEntryDetail} onViewAll={() => navigate({ page: "timeline" })} />
              <section className={`${ui.surface} p-4`} aria-labelledby="capture-context-heading">
                <SectionHeader id="capture-context-heading" title="输入入口" description="所有输入先保留原文，再异步进入处理队列。" />
                <ul className="mt-4   text-sm">
                  <li className="d-flex align-items-center column-gap-3 py-3 pt-0"><Link2 className="icon icon-sm flex-shrink-0 text-secondary" aria-hidden="true" /><span><strong className="fw-medium text-body">网页 URL</strong><span className="mt-1 d-block small text-secondary">保存地址与网页快照</span></span></li>
                  <li className="d-flex align-items-center column-gap-3 py-3"><Paperclip className="icon icon-sm flex-shrink-0 text-secondary" aria-hidden="true" /><span><strong className="fw-medium text-body">文件 / 图片</strong><span className="mt-1 d-block small text-secondary">支持 PDF、Markdown、JSON、YAML 和图片</span></span></li>
                  <li className="d-flex align-items-center column-gap-3 py-3 "><Inbox className="icon icon-sm flex-shrink-0 text-secondary" aria-hidden="true" /><span><strong className="fw-medium text-body">处理 Inbox</strong><span className="mt-1 d-block small text-secondary">查看 OCR、附件和异步任务状态</span></span></li>
                </ul>
                <button className={`${ui.secondaryButton} mt-4 w-100`} type="button" onClick={() => navigate({ page: "inbox" })}>查看 Inbox</button>
              </section>
            </div>
          </div>
        </PageFrame>
      )}
      {route.page === "timeline" && <Timeline focusEntryId={focusEntryId} onOpenEntry={openEntry} onOpenDetail={openEntryDetail} />}
      {route.page === "search" && <SearchPage onOpenEntry={openEntry} onOpenDetail={openEntryDetail} />}
      {route.page === "ask" && <AskPage onOpenEntry={openEntry} />}
      {route.page === "more" && <MorePage section={route.managementSection ?? "overview"} promptName={route.promptName} promptView={route.promptView ?? "editor"} onNavigate={(section) => navigate({ page: section === "jobs" ? "jobs" : "more", managementSection: section })} onPromptNavigate={(name, view) => navigate(view === "editor" ? { page: "more", managementSection: "prompts" } : { page: "more", managementSection: "prompts", promptName: name, promptView: view })} onOpenInbox={() => navigate({ page: "inbox" })} onOpenWorkbench={() => navigate({ page: "workbench" })} onOpenMemory={(id) => navigate({ page: "memory-detail", id })} />}
      {route.page === "jobs" && <AIJobsPage onOpenEntry={openEntry} onOpenDetail={(id) => navigate({ page: "job-detail", id })} onNavigate={(section) => navigate({ page: section === "jobs" ? "jobs" : "more", managementSection: section })} />}
      {route.page === "inbox" && <InboxPage onOpenEntry={openEntry} onOpenDetail={openEntryDetail} />}
      {route.page === "sources" && <SourcesPage onOpenEntry={openEntry} />}
      {route.page === "workbench" && <WorkbenchPage onOpenEntry={openEntry} onOpenDetail={(kind, id) => navigate({ page: "workbench", workbenchKind: kind, workbenchId: id })} initialKind={route.workbenchKind} initialId={route.workbenchId} />}
      {route.page === "entry" && route.id && <EntryDetailPage entryId={route.id} onBack={() => navigate({ page: "timeline" })} onOpenEntry={openEntryDetail} onOpenHistory={() => navigate({ page: "entry-history", id: route.id })} />}
      {route.page === "entry-history" && route.id && <EntryHistoryPage entryId={route.id} onBack={() => navigate({ page: "entry", id: route.id })} />}
      {route.page === "job-detail" && route.id && <AIJobDetailPage jobId={route.id} onBack={() => navigate({ page: "jobs", managementSection: "jobs" })} onOpenEntry={openEntry} />}
      {route.page === "memory-detail" && route.id && <MemoryDetailPage memoryId={route.id} onBack={() => navigate({ page: "more", managementSection: "memory" })} onOpenEntry={openEntry} />}
      {route.page === "not-found" && <NotFoundPage onNavigate={() => navigate({ page: "capture" })} />}
    </AppShell>
  );
}

function App() {
  const isTypographyFixture = [
    "/__ui/tabler-typography-fixture",
    "/__ui/tabler-font-fixture",
  ].includes(window.location.pathname);
  const me = useQuery({ queryKey: ["me"], queryFn: api.me, retry: false, enabled: !isTypographyFixture });
  const [sharedPayload, setSharedPayload] = useState<SharedPayload | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const shared = params.get("shared");
    const sharedError = params.get("shared_error");
    if (!shared && !sharedError) return;
    history.replaceState(null, "", window.location.pathname);
    if (sharedError) {
      setSharedPayload({ title: "", text: "", url: "", files: [], error: sharedError });
      return;
    }
    void readAndClearSharedPayload()
      .then((payload) => setSharedPayload(payload ?? { title: "", text: "", url: "", files: [], error: "missing" }))
      .catch(() => setSharedPayload({ title: "", text: "", url: "", files: [], error: "storage" }));
  }, []);
  if (isTypographyFixture) return <TablerTypographyFixture />;
  if (me.isPending) return <main className="row min-vh-100 align-items-center justify-content-center p-6"><LoadingState label="正在连接你的记忆仓库…" rows={2} /></main>;
  if (me.isError) return <LoginScreen />;
  return <Workspace onLogout={() => queryClient.invalidateQueries({ queryKey: ["me"] })} sharedPayload={sharedPayload} />;
}

watchTheme();

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}><App /></QueryClientProvider>,
);
