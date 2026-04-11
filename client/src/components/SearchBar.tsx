import { useState } from "react";
import { Search } from "lucide-react";

interface SearchBarProps {
  initialQuery?: string;
  initialDateFrom?: string;
  onSearch: (query: string, dateFrom: string) => void;
  loading: boolean;
}

export default function SearchBar({
  initialQuery = "",
  initialDateFrom = "",
  onSearch,
  loading,
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [dateFrom, setDateFrom] = useState(initialDateFrom);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSearch(query.trim(), dateFrom);
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
            placeholder="Search papers (authors, keywords, or in your own words)…"
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
