import { useState } from "react";
import { Search } from "lucide-react";

interface SearchBarProps {
  initialQuery?: string;
  initialPageSize?: number;
  initialCategories?: string[];
  initialDateFrom?: string;
  onSearch: (query: string, pageSize: number, categories: string[], dateFrom: string) => void;
  loading: boolean;
}

export default function SearchBar({
  initialQuery = "",
  initialPageSize = 10,
  initialCategories = [],
  initialDateFrom = "",
  onSearch,
  loading,
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [categories, setCategories] = useState(initialCategories.join(", "));
  const [dateFrom, setDateFrom] = useState(initialDateFrom);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    const cats = categories
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);
    onSearch(query.trim(), pageSize, cats, dateFrom);
  };

  const inputClass =
    "rounded border border-border bg-surface px-2 py-1 text-[13px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring transition-colors";

  return (
    <form onSubmit={handleSubmit} className="border-b px-4 py-3">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search size={13} className="absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search papers (natural language)…"
            className={`${inputClass} w-full pl-7`}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="rounded border border-primary/30 bg-primary px-4 py-1 text-xs font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-4 text-xs">
        <label className="flex items-center gap-1.5 text-muted-foreground">
          <span>Results</span>
          <select
            value={pageSize}
            onChange={(e) => setPageSize(Number(e.target.value))}
            className={`${inputClass} w-14`}
          >
            {[1, 5, 10, 20].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1.5 text-muted-foreground">
          <span>Categories</span>
          <input
            type="text"
            value={categories}
            onChange={(e) => setCategories(e.target.value)}
            placeholder="cs.LG, cs.AI"
            className={`${inputClass} w-36`}
          />
        </label>
        <label className="flex items-center gap-1.5 text-muted-foreground">
          <span>From</span>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className={inputClass}
          />
        </label>
      </div>
    </form>
  );
}