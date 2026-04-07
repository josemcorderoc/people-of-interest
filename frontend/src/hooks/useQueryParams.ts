import { useSearchParams } from "react-router-dom";
import { useCallback, useMemo } from "react";

export interface FilterState {
  view: string;
  window: string;
  categories: string[];
  langs: string[];
  date: string;
  page: number;
  perPage: number;
  sort: string;
  order: string;
  search: string;
  expandedId: string;
}

const DEFAULTS: FilterState = {
  view: "popularity",
  window: "daily",
  categories: [],
  langs: ["en"],
  date: "",
  page: 1,
  perPage: 50,
  sort: "score",
  order: "desc",
  search: "",
  expandedId: "",
};

export function useQueryParams() {
  const [searchParams, setSearchParams] = useSearchParams();

  const state: FilterState = useMemo(() => {
    const cats = searchParams.getAll("category");
    const langs = searchParams.getAll("langs");
    return {
      view: searchParams.get("view") || DEFAULTS.view,
      window: searchParams.get("window") || DEFAULTS.window,
      categories: cats.length > 0 ? cats : DEFAULTS.categories,
      langs: langs.length > 0 ? langs : DEFAULTS.langs,
      date: searchParams.get("date") || DEFAULTS.date,
      page: Number(searchParams.get("page")) || DEFAULTS.page,
      perPage: Number(searchParams.get("per_page")) || DEFAULTS.perPage,
      sort: searchParams.get("sort") || DEFAULTS.sort,
      order: searchParams.get("order") || DEFAULTS.order,
      search: searchParams.get("q") || DEFAULTS.search,
      expandedId: searchParams.get("detail") || DEFAULTS.expandedId,
    };
  }, [searchParams]);

  const update = useCallback(
    (changes: Partial<FilterState>) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);

        if (changes.view !== undefined) next.set("view", changes.view);
        if (changes.window !== undefined) next.set("window", changes.window);
        if (changes.date !== undefined) {
          if (changes.date) next.set("date", changes.date);
          else next.delete("date");
        }
        if (changes.page !== undefined) next.set("page", String(changes.page));
        if (changes.perPage !== undefined)
          next.set("per_page", String(changes.perPage));
        if (changes.sort !== undefined) next.set("sort", changes.sort);
        if (changes.order !== undefined) next.set("order", changes.order);
        if (changes.search !== undefined) {
          if (changes.search) next.set("q", changes.search);
          else next.delete("q");
        }
        if (changes.expandedId !== undefined) {
          if (changes.expandedId) next.set("detail", changes.expandedId);
          else next.delete("detail");
        }

        if (changes.categories !== undefined) {
          next.delete("category");
          changes.categories.forEach((c) => next.append("category", c));
        }
        if (changes.langs !== undefined) {
          next.delete("langs");
          changes.langs.forEach((l) => next.append("langs", l));
        }

        // Reset page to 1 when filters change (except page itself)
        if (changes.page === undefined && Object.keys(changes).length > 0) {
          next.set("page", "1");
        }

        return next;
      });
    },
    [setSearchParams],
  );

  return { state, update };
}
