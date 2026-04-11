import { useEffect, useState } from "react";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { fetchHistory, type HistoryListItem } from "@/lib/api";

interface Props {
  open: boolean;
  onClose: () => void;
  onRestore: (historyId: string) => void;
  onError: (error: unknown) => void;
}

export default function HistoryPanel({ open, onClose, onRestore, onError }: Props) {
  const [items, setItems] = useState<HistoryListItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;

    let isCurrent = true;
    setLoading(true);

    void fetchHistory(page)
      .then((res) => {
        if (!isCurrent) return;
        setItems(res.items);
        setHasNext(res.has_next);
      })
      .catch((error: unknown) => {
        if (!isCurrent) return;
        onError(error);
      })
      .finally(() => {
        if (!isCurrent) return;
        setLoading(false);
      });

    return () => {
      isCurrent = false;
    };
  }, [open, page, onError]);

  if (!open) return null;

  return (
    <>
      {/* backdrop */}
      <div className="fixed inset-0 z-40 bg-background/40" onClick={onClose} />
      {/* panel */}
      <div className="fixed inset-y-0 right-0 z-50 flex w-72 flex-col border-l bg-card shadow-lg">
        <div className="flex items-center justify-between border-b px-3 py-2.5">
          <span className="text-xs font-semibold tracking-tight text-foreground">Search History</span>
          <button
            onClick={onClose}
            className="rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <X size={13} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {loading && <div className="px-3 py-6 text-center text-xs text-muted-foreground">Loading…</div>}
          {!loading && items.map((item) => (
            <button
              key={item.history_id}
              onClick={() => onRestore(item.history_id)}
              className="block w-full border-b border-border/50 px-3 py-2.5 text-left transition-colors hover:bg-accent"
            >
              <div className="truncate text-xs text-foreground">{item.query}</div>
              <div className="mt-0.5 flex items-center gap-2 text-[10px] text-muted-foreground">
                <span>{new Date(item.created_at).toLocaleDateString()}</span>
                <span>{new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                <span className="ml-auto font-mono">n={item.result_count}</span>
              </div>
            </button>
          ))}
          {!loading && items.length === 0 && (
            <div className="px-3 py-6 text-center text-xs text-muted-foreground">No history yet.</div>
          )}
        </div>
        <div className="flex items-center justify-between border-t px-3 py-2 text-xs text-muted-foreground">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="flex items-center gap-0.5 rounded p-1 transition-colors hover:bg-accent hover:text-foreground disabled:opacity-30"
          >
            <ChevronLeft size={12} /> Prev
          </button>
          <span className="text-[10px]">{page}</span>
          <button
            disabled={!hasNext}
            onClick={() => setPage((p) => p + 1)}
            className="flex items-center gap-0.5 rounded p-1 transition-colors hover:bg-accent hover:text-foreground disabled:opacity-30"
          >
            Next <ChevronRight size={12} />
          </button>
        </div>
      </div>
    </>
  );
}
