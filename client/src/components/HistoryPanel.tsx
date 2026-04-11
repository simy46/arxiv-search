import { useEffect, useRef, useState } from "react";
import { X, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import {
  fetchHistory,
  type HistoryListItem,
  type HistoryListResponse,
} from "@/lib/api";

interface Props {
  open: boolean;
  onClose: () => void;
  onRestore: (historyId: string) => void;
  onError: (error: unknown) => void;
  refreshKey: number;
}

export default function HistoryPanel({
  open,
  onClose,
  onRestore,
  onError,
  refreshKey,
}: Props) {
  const [items, setItems] = useState<HistoryListItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(false);
  const pageCache = useRef<Record<number, HistoryListResponse>>({});
  const lastRefreshKey = useRef(refreshKey);

  const getStatusClassName = (status: HistoryListItem["status"]): string => {
    if (status === "failed") return "border-destructive/30 text-destructive";
    if (status === "running") return "border-amber-500/30 text-amber-600";
    return "border-emerald-500/30 text-emerald-700";
  };

  useEffect(() => {
    const hasRefreshSignal = refreshKey !== lastRefreshKey.current;
    if (hasRefreshSignal) {
      pageCache.current = {};
      lastRefreshKey.current = refreshKey;
    }

    if (!open) return;

    let isCurrent = true;
    const cachedPage = hasRefreshSignal ? undefined : pageCache.current[page];
    if (cachedPage) {
      setItems(cachedPage.items);
      setHasNext(cachedPage.has_next);
      return;
    }

    setLoading(true);
    void fetchHistory(page)
      .then((res) => {
        if (!isCurrent) return;
        pageCache.current[page] = res;
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
  }, [open, page, onError, refreshKey]);

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
              <div className="flex items-center gap-2">
                <div className="truncate text-xs text-foreground">{item.query}</div>
                {item.status === "running" && (
                  <Loader2
                    size={11}
                    className="ml-auto shrink-0 animate-spin text-amber-600"
                    aria-label="Running"
                  />
                )}
                <span
                  className={`rounded border px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide ${getStatusClassName(item.status)}`}
                >
                  {item.status}
                </span>
              </div>
              <div className="mt-0.5 flex items-center gap-2 text-[10px] text-muted-foreground">
                <span>{new Date(item.created_at).toLocaleDateString()}</span>
                <span>{new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                <span className="ml-auto font-mono">n={item.result_count}</span>
              </div>
              {item.status === "failed" && item.error_message && (
                <div className="mt-1 truncate text-[10px] text-destructive/90">
                  {item.error_message}
                </div>
              )}
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
