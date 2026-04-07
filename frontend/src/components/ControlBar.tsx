import { useQuery } from "@tanstack/react-query";
import { fetchConfig } from "../api/client";
import type { FilterState } from "../hooks/useQueryParams";

interface ControlBarProps {
  state: FilterState;
  onUpdate: (changes: Partial<FilterState>) => void;
}

export default function ControlBar({ state, onUpdate }: ControlBarProps) {
  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: fetchConfig,
  });

  const categories = config?.categories ?? [];
  const languages = config?.languages ?? [];

  return (
    <div className="flex flex-wrap items-center gap-3 px-6 py-3 bg-gray-50 border-b border-gray-200">
      {/* View toggle */}
      <div className="flex rounded-md shadow-sm">
        {(["popularity", "trending"] as const).map((v) => (
          <button
            key={v}
            onClick={() => onUpdate({ view: v })}
            className={`px-3 py-1.5 text-sm first:rounded-l-md last:rounded-r-md border ${
              state.view === v
                ? "bg-indigo-600 text-white border-indigo-600"
                : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
            }`}
          >
            {v.charAt(0).toUpperCase() + v.slice(1)}
          </button>
        ))}
      </div>

      {/* Window selector */}
      <select
        value={state.window}
        onChange={(e) => onUpdate({ window: e.target.value })}
        className="rounded-md border border-gray-300 text-sm px-2 py-1.5 bg-white"
      >
        <option value="daily">Daily</option>
        <option value="weekly">Weekly</option>
        <option value="monthly">Monthly</option>
      </select>

      {/* Category filter (multi-select) */}
      <select
        multiple
        value={state.categories}
        onChange={(e) => {
          const selected = Array.from(e.target.selectedOptions, (o) => o.value);
          onUpdate({ categories: selected });
        }}
        className="rounded-md border border-gray-300 text-sm px-2 py-1 bg-white min-w-[120px] h-8"
        title="Categories (hold Ctrl/Cmd to multi-select)"
      >
        {categories.map((cat) => (
          <option key={cat} value={cat}>
            {cat}
          </option>
        ))}
      </select>

      {/* Language selector (multi-select) */}
      <select
        multiple
        value={state.langs}
        onChange={(e) => {
          const selected = Array.from(e.target.selectedOptions, (o) => o.value);
          onUpdate({ langs: selected.length > 0 ? selected : ["en"] });
        }}
        className="rounded-md border border-gray-300 text-sm px-2 py-1 bg-white min-w-[80px] h-8"
        title="Languages (hold Ctrl/Cmd to multi-select)"
      >
        {languages.map((lang) => (
          <option key={lang} value={lang}>
            {lang}
          </option>
        ))}
      </select>

      {/* Date picker */}
      <input
        type="date"
        value={state.date}
        onChange={(e) => onUpdate({ date: e.target.value })}
        className="rounded-md border border-gray-300 text-sm px-2 py-1.5 bg-white"
      />

      {/* Search box */}
      <input
        type="search"
        placeholder="Search people..."
        value={state.search}
        onChange={(e) => onUpdate({ search: e.target.value })}
        className="rounded-md border border-gray-300 text-sm px-3 py-1.5 bg-white ml-auto min-w-[200px]"
      />
    </div>
  );
}
