export type SharedFile = {
  name: string;
  type: string;
  size: number;
  data: ArrayBuffer;
};

export type SharedPayload = {
  title: string;
  text: string;
  url: string;
  files: SharedFile[];
  error?: string;
};

const DB_NAME = "starmem-share";
const STORE_NAME = "payloads";

function openShareDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE_NAME);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("IndexedDB unavailable"));
  });
}

export async function readAndClearSharedPayload(): Promise<SharedPayload | null> {
  if (!("indexedDB" in window)) return { title: "", text: "", url: "", files: [], error: "storage" };
  const db = await openShareDb();
  try {
    const payload = await new Promise<SharedPayload | undefined>((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, "readwrite");
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get("latest");
      let value: SharedPayload | undefined;
      request.onsuccess = () => {
        value = request.result as SharedPayload | undefined;
        store.delete("latest");
      };
      request.onerror = () => reject(request.error ?? new Error("Shared payload read failed"));
      transaction.oncomplete = () => resolve(value);
      transaction.onerror = () => reject(transaction.error ?? new Error("Shared payload transaction failed"));
    });
    if (!payload) return null;
    return {
      ...payload,
      files: (payload.files ?? []).map((file) => ({
        ...file,
        data: file.data instanceof ArrayBuffer ? file.data : new Uint8Array(file.data).buffer,
      })),
    };
  } finally {
    db.close();
  }
}

export function sharedFiles(payload: SharedPayload): File[] {
  return payload.files.map((file) => new File([file.data], file.name, { type: file.type }));
}
