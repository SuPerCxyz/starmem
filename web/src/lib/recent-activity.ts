/**
 * 最近搜索 / 最近提问的本地记录。
 *
 * StarMem 是单用户自托管产品，后端没有搜索与提问历史接口；
 * 这里只记录用户在本机的真实操作，不产生任何伪造数据，也不参与跨设备同步。
 */

const SEARCH_KEY = "starmem.recent-searches";
const QUESTION_KEY = "starmem.recent-questions";
const LIMIT = 6;

function read(key: string): string[] {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is string => typeof item === "string" && item.length > 0);
  } catch {
    return [];
  }
}

function push(key: string, value: string): string[] {
  const trimmed = value.trim();
  if (!trimmed) return read(key);
  const next = [trimmed, ...read(key).filter((item) => item !== trimmed)].slice(0, LIMIT);
  try {
    window.localStorage.setItem(key, JSON.stringify(next));
  } catch {
    // 隐私模式或配额限制时静默降级，不影响主流程
  }
  return next;
}

export const recentSearches = {
  list: () => read(SEARCH_KEY),
  add: (value: string) => push(SEARCH_KEY, value),
};

export const recentQuestions = {
  list: () => read(QUESTION_KEY),
  add: (value: string) => push(QUESTION_KEY, value),
};
