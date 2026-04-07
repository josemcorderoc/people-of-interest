import { useQuery } from "@tanstack/react-query";
import { fetchPersonDetail } from "../api/client";
import PersonImage from "./PersonImage";
import Sparkline from "./Sparkline";
import CategoryBadge from "./CategoryBadge";

interface PersonDetailProps {
  personId: string;
  window: string;
  onClose: () => void;
}

export default function PersonDetail({
  personId,
  window: windowProp,
  onClose,
}: PersonDetailProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["personDetail", personId, windowProp],
    queryFn: () => fetchPersonDetail(personId, windowProp),
  });

  if (isLoading) {
    return (
      <tr>
        <td colSpan={7} className="px-6 py-8 text-center text-sm text-gray-500">
          Loading details...
        </td>
      </tr>
    );
  }

  if (error || !data) {
    return (
      <tr>
        <td colSpan={7} className="px-6 py-4 text-center text-sm text-red-500">
          Failed to load details.
          <button onClick={onClose} className="ml-2 underline">Close</button>
        </td>
      </tr>
    );
  }

  const maxLangViews = Math.max(...data.language_breakdown.map((l) => l.views), 1);

  return (
    <tr className="bg-indigo-50">
      <td colSpan={7} className="px-6 py-6">
        <div className="flex gap-6">
          {/* Left: image + metadata */}
          <div className="flex-shrink-0">
            <PersonImage src={data.image_url} alt={data.name} size={120} />
          </div>

          <div className="flex-1 space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{data.name}</h3>
                <div className="flex gap-2 mt-1">
                  <CategoryBadge category={data.category} />
                  <span className="text-sm text-gray-500">{data.gender}</span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 text-xl leading-none"
                aria-label="Close detail panel"
              >
                x
              </button>
            </div>

            {/* Dates & Nationality */}
            <div className="text-sm text-gray-600 space-y-0.5">
              {data.birth_date && <div>Born: {data.birth_date}</div>}
              {data.death_date && <div>Died: {data.death_date}</div>}
              {data.nationality && <div>Nationality: {data.nationality}</div>}
              {data.occupations.length > 0 && (
                <div>Occupations: {data.occupations.join(", ")}</div>
              )}
            </div>

            {/* Sparkline charts */}
            <div className="flex gap-6">
              <div>
                <div className="text-xs text-gray-500 mb-1">30 days</div>
                <Sparkline data={data.sparkline_30d} width={120} height={32} />
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">12 weeks</div>
                <Sparkline data={data.sparkline_12w} width={120} height={32} color="#10b981" />
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">12 months</div>
                <Sparkline data={data.sparkline_12m} width={120} height={32} color="#f59e0b" />
              </div>
            </div>

            {/* Language breakdown */}
            {data.language_breakdown.length > 0 && (
              <div>
                <div className="text-xs text-gray-500 mb-1">Language breakdown (30d)</div>
                <div className="space-y-1">
                  {data.language_breakdown.slice(0, 8).map((lb) => (
                    <div key={lb.lang} className="flex items-center gap-2 text-xs">
                      <span className="w-6 text-gray-600 font-mono">{lb.lang}</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[200px]">
                        <div
                          className="bg-indigo-500 h-2 rounded-full"
                          style={{
                            width: `${(lb.views / maxLangViews) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-gray-500 w-16 text-right">
                        {lb.views.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Wikipedia links */}
            <div className="flex flex-wrap gap-2">
              {data.wikipedia_links.map((link) => (
                <a
                  key={link.lang}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-white border border-gray-300 text-indigo-600 hover:bg-indigo-50"
                >
                  {link.lang}.wikipedia
                </a>
              ))}
            </div>
          </div>
        </div>
      </td>
    </tr>
  );
}
