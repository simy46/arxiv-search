import { useState } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";
import type { GeneratedQuery } from "@/lib/api";

interface Props {
  queries: GeneratedQuery[];
}

export default function GeneratedQueries({ queries }: Props) {
  const [open, setOpen] = useState(false);

  if (!queries.length) return null;

  return (
    <div className="border-b px-4 py-2 text-xs">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-muted-foreground transition-colors hover:text-foreground"
      >
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <span>Generated queries</span>
        <span className="ml-0.5 text-muted-foreground/60">({queries.length})</span>
      </button>
      {open && (
        <div className="mt-1.5 space-y-1 pl-4">
          {queries.map((q, i) => (
            <div key={i} className="rounded border bg-surface-raised px-2.5 py-1.5 font-mono text-[11px] text-foreground/80">
              {q.query}
              {q.categories.length > 0 && (
                <span className="ml-2 text-muted-foreground">[{q.categories.join(", ")}]</span>
              )}
              {q.date_from && (
                <span className="ml-2 text-muted-foreground">from {q.date_from}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}