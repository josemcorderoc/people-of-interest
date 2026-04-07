const API_BASE = "/api";

export interface PersonResult {
  wikidata_id: string;
  rank: number;
  name: string;
  category: string;
  score: number | null;
  image_url: string | null;
  sparkline_7d: number[];
}

export interface PersonsResponse {
  total: number;
  page: number;
  per_page: number;
  results: PersonResult[];
}

export interface PersonsParams {
  view?: string;
  window?: string;
  category?: string[];
  langs?: string[];
  date?: string;
  page?: number;
  per_page?: number;
  sort?: string;
  order?: string;
}

export interface WikiLink {
  lang: string;
  url: string;
  title: string;
}

export interface LanguageBreakdown {
  lang: string;
  views: number;
}

export interface PersonDetailResponse {
  wikidata_id: string;
  name: string;
  names_by_lang: Record<string, string>;
  category: string;
  birth_date: string | null;
  death_date: string | null;
  nationality: string | null;
  occupations: string[];
  gender: string;
  image_url: string | null;
  scores: Record<string, number | null>;
  sparkline_30d: number[];
  sparkline_12w: number[];
  sparkline_12m: number[];
  language_breakdown: LanguageBreakdown[];
  wikipedia_links: WikiLink[];
}

export interface SearchResult {
  wikidata_id: string;
  name: string;
  category: string;
  image_url: string | null;
}

export interface SearchResponse {
  results: SearchResult[];
}

export interface ConfigResponse {
  categories: string[];
  languages: string[];
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function fetchPersons(params: PersonsParams): Promise<PersonsResponse> {
  const sp = new URLSearchParams();
  if (params.view) sp.set("view", params.view);
  if (params.window) sp.set("window", params.window);
  if (params.category) params.category.forEach((c) => sp.append("category", c));
  if (params.langs) params.langs.forEach((l) => sp.append("langs", l));
  if (params.date) sp.set("date", params.date);
  if (params.page) sp.set("page", String(params.page));
  if (params.per_page) sp.set("per_page", String(params.per_page));
  if (params.sort) sp.set("sort", params.sort);
  if (params.order) sp.set("order", params.order);
  return fetchJson<PersonsResponse>(`${API_BASE}/persons?${sp.toString()}`);
}

export function fetchPersonDetail(
  id: string,
  window?: string,
): Promise<PersonDetailResponse> {
  const sp = new URLSearchParams();
  if (window) sp.set("window", window);
  return fetchJson<PersonDetailResponse>(
    `${API_BASE}/persons/${id}/detail?${sp.toString()}`,
  );
}

export function searchPersons(
  q: string,
  limit = 20,
): Promise<SearchResponse> {
  const sp = new URLSearchParams({ q, limit: String(limit) });
  return fetchJson<SearchResponse>(
    `${API_BASE}/persons/search?${sp.toString()}`,
  );
}

export function fetchConfig(): Promise<ConfigResponse> {
  return fetchJson<ConfigResponse>(`${API_BASE}/config`);
}
