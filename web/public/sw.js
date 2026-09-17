const CACHE = "starmem-shell-v2";
const SHELL = ["/", "/manifest.webmanifest", "/starmem-logo.png"];
const SHARE_DB = "starmem-share";
const SHARE_STORE = "payloads";
const SHARE_LIMIT = 20 * 1024 * 1024;
const SHARE_FILE_LIMIT = 4;

function openShareDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(SHARE_DB, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(SHARE_STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("storage"));
  });
}

async function storeSharePayload(request) {
  const form = await request.formData();
  const fileValues = form.getAll("files").filter((value) => value instanceof File);
  if (fileValues.length > SHARE_FILE_LIMIT) throw new Error("oversize");
  const files = [];
  let total = 0;
  for (const file of fileValues) {
    total += file.size;
    if (total > SHARE_LIMIT) throw new Error("oversize");
    files.push({ name: file.name || "shared-file", type: file.type || "application/octet-stream", size: file.size, data: await file.arrayBuffer() });
  }
  const title = String(form.get("title") || "");
  const text = String(form.get("text") || "");
  const url = String(form.get("url") || "");
  total += new TextEncoder().encode(`${title}${text}${url}`).byteLength;
  if (total > SHARE_LIMIT) throw new Error("oversize");
  const payload = {
    title,
    text,
    url,
    files,
  };
  const db = await openShareDb();
  await new Promise((resolve, reject) => {
    const transaction = db.transaction(SHARE_STORE, "readwrite");
    transaction.objectStore(SHARE_STORE).put(payload, "latest");
    transaction.oncomplete = resolve;
    transaction.onerror = () => reject(transaction.error || new Error("storage"));
  });
  db.close();
}

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (event.request.method === "POST" && url.pathname === "/share") {
    event.respondWith(
      storeSharePayload(event.request)
        .then(() => Response.redirect(new URL("/?shared=1", event.request.url).toString(), 303))
        .catch((error) => Response.redirect(new URL(`/?shared_error=${error.message === "oversize" ? "oversize" : "storage"}`, event.request.url).toString(), 303)),
    );
    return;
  }
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request).then((cached) => cached || Response.error())),
  );
});
