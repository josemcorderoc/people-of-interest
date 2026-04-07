import { useQuery } from "@tanstack/react-query";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { fetchPersons, searchPersons } from "../api/client";
import type { PersonResult } from "../api/client";
import type { FilterState } from "../hooks/useQueryParams";
import PersonImage from "./PersonImage";
import CategoryBadge from "./CategoryBadge";
import Sparkline from "./Sparkline";
import Pagination from "./Pagination";
import PersonDetail from "./PersonDetail";

interface PersonTableProps {
  state: FilterState;
  onUpdate: (changes: Partial<FilterState>) => void;
}

const columnHelper = createColumnHelper<PersonResult>();

function getWikipediaUrl(name: string, langs: string[]) {
  const lang = langs[0] || "en";
  return `https://${lang}.wikipedia.org/wiki/${encodeURIComponent(name.replace(/ /g, "_"))}`;
}

export default function PersonTable({ state, onUpdate }: PersonTableProps) {
  const isSearch = state.search.length >= 2;

  const personsQuery = useQuery({
    queryKey: [
      "persons",
      state.view,
      state.window,
      state.categories,
      state.langs,
      state.date,
      state.page,
      state.perPage,
      state.sort,
      state.order,
    ],
    queryFn: () =>
      fetchPersons({
        view: state.view,
        window: state.window,
        category: state.categories.length > 0 ? state.categories : undefined,
        langs: state.langs,
        date: state.date || undefined,
        page: state.page,
        per_page: state.perPage,
        sort: state.sort,
        order: state.order,
      }),
    enabled: !isSearch,
  });

  const searchQuery = useQuery({
    queryKey: ["search", state.search],
    queryFn: () => searchPersons(state.search),
    enabled: isSearch,
  });

  const data: PersonResult[] = isSearch
    ? (searchQuery.data?.results ?? []).map((r, i) => ({
        ...r,
        rank: i + 1,
        score: null,
        sparkline_7d: [],
      }))
    : personsQuery.data?.results ?? [];

  const totalPages = isSearch
    ? 1
    : Math.ceil((personsQuery.data?.total ?? 0) / state.perPage);

  const isLoading = isSearch ? searchQuery.isLoading : personsQuery.isLoading;
  const isError = isSearch ? searchQuery.isError : personsQuery.isError;

  const columns = [
    columnHelper.accessor("rank", {
      header: "#",
      cell: (info) => (
        <span className="text-gray-500 text-sm">{info.getValue()}</span>
      ),
      size: 50,
    }),
    columnHelper.display({
      id: "image",
      header: "",
      cell: (info) => (
        <PersonImage
          src={info.row.original.image_url}
          alt={info.row.original.name}
          size={40}
        />
      ),
      size: 56,
    }),
    columnHelper.accessor("name", {
      header: "Name",
      cell: (info) => (
        <a
          href={getWikipediaUrl(info.getValue(), state.langs)}
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-600 hover:text-indigo-800 font-medium"
        >
          {info.getValue()}
        </a>
      ),
    }),
    columnHelper.accessor("category", {
      header: "Category",
      cell: (info) => <CategoryBadge category={info.getValue()} />,
      size: 120,
    }),
    columnHelper.accessor("score", {
      header: "Score",
      cell: (info) => {
        const v = info.getValue();
        if (v === null) return <span className="text-gray-400">-</span>;
        return (
          <span className="font-mono text-sm">
            {state.view === "trending" ? v.toFixed(2) : v.toLocaleString()}
          </span>
        );
      },
      size: 100,
    }),
    columnHelper.accessor("sparkline_7d", {
      header: "7d",
      cell: (info) => <Sparkline data={info.getValue()} />,
      size: 100,
    }),
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    style={{ width: header.getSize() }}
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext(),
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading && (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-6 py-12 text-center text-sm text-gray-500"
                >
                  Loading...
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-6 py-12 text-center text-sm text-red-500"
                >
                  Failed to load data. Check the API connection.
                </td>
              </tr>
            )}
            {!isLoading && !isError && data.length === 0 && (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-6 py-12 text-center text-sm text-gray-500"
                >
                  No data available. Connect to the API to see trending people.
                </td>
              </tr>
            )}
            {table.getRowModel().rows.map((row) => (
              <>
                <tr
                  key={row.id}
                  className={`hover:bg-gray-50 cursor-pointer ${
                    state.expandedId === row.original.wikidata_id
                      ? "bg-indigo-50"
                      : ""
                  }`}
                  onClick={() =>
                    onUpdate({
                      expandedId:
                        state.expandedId === row.original.wikidata_id
                          ? ""
                          : row.original.wikidata_id,
                    })
                  }
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 whitespace-nowrap">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </td>
                  ))}
                </tr>
                {state.expandedId === row.original.wikidata_id && (
                  <PersonDetail
                    key={`detail-${row.original.wikidata_id}`}
                    personId={row.original.wikidata_id}
                    window={state.window}
                    onClose={() => onUpdate({ expandedId: "" })}
                  />
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {!isSearch && (
        <Pagination
          page={state.page}
          totalPages={totalPages}
          onPageChange={(p) => onUpdate({ page: p })}
        />
      )}
    </div>
  );
}
