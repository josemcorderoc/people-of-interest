const CATEGORY_COLORS: Record<string, string> = {
  politician: "bg-blue-100 text-blue-800",
  athlete: "bg-green-100 text-green-800",
  artist: "bg-purple-100 text-purple-800",
  scientist: "bg-orange-100 text-orange-800",
  business: "bg-gray-100 text-gray-800",
  writer: "bg-teal-100 text-teal-800",
  historical: "bg-amber-100 text-amber-800",
  other: "bg-slate-100 text-slate-800",
};

interface CategoryBadgeProps {
  category: string;
}

export default function CategoryBadge({ category }: CategoryBadgeProps) {
  const colors = CATEGORY_COLORS[category] || CATEGORY_COLORS.other;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors}`}
    >
      {category}
    </span>
  );
}
