import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import TopBar from "@/components/TopBar";
import SearchBar from "@/components/SearchBar";
import GeneratedQueries from "@/components/GeneratedQueries";
import ResultsList from "@/components/ResultsList";
import HistoryPanel from "@/components/HistoryPanel";
import {
  search,
  summarizePaper,
  fetchHistoryDetail,
  getApiErrorMessage,
  type HistoryItem,
  type Paper,
  type GeneratedQuery,
} from "@/lib/api";
import { toast } from "@/hooks/use-toast";

export default function Index() {
  const [activeSearchCount, setActiveSearchCount] = useState(0);
  const [results, setResults] = useState<Paper[]>([]);
  const [generatedQueries, setGeneratedQueries] = useState<GeneratedQuery[]>([]);
  const [historyId, setHistoryId] = useState("");
  const [totalCandidates, setTotalCandidates] = useState<number | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);
  const [activeHistoryStatus, setActiveHistoryStatus] =
    useState<HistoryItem["status"] | null>(null);
  const [activeHistoryError, setActiveHistoryError] = useState<string | null>(null);

  const [summarizingIds, setSummarizingIds] = useState<Set<string>>(new Set());

  // key to remount SearchBar on history restore
  const [searchKey, setSearchKey] = useState(0);
  const [restoredSearch, setRestoredSearch] = useState<{ query: string; dateFrom: string } | null>(null);
  const latestRequestIdRef = useRef(0);
  const refreshTimersRef = useRef<number[]>([]);
  const activeHistoryIdRef = useRef("");
  const loading = activeSearchCount > 0;

  const showApiErrorToast = useCallback((error: unknown) => {
    toast({
      title: "Request failed",
      description: getApiErrorMessage(error),
      variant: "destructive",
      duration: 4500,
    });
  }, []);

  const refreshHistory = useCallback(() => {
    setHistoryRefreshKey((key) => key + 1);
  }, []);

  const setActiveHistoryId = useCallback((nextHistoryId: string) => {
    activeHistoryIdRef.current = nextHistoryId;
    setHistoryId(nextHistoryId);
  }, []);

  const refreshHistoryAfterDelay = useCallback((delayMs: number) => {
    const timerId = window.setTimeout(() => {
      refreshHistory();
      refreshTimersRef.current = refreshTimersRef.current.filter((id) => id !== timerId);
    }, delayMs);
    refreshTimersRef.current.push(timerId);
  }, [refreshHistory]);

  useEffect(() => {
    return () => {
      for (const timerId of refreshTimersRef.current) {
        window.clearTimeout(timerId);
      }
      refreshTimersRef.current = [];
    };
  }, []);

  const activeSummarizingIds = useMemo(() => {
    if (!historyId) return new Set<string>();
    const prefix = `${historyId}:`;
    const paperIds = Array.from(summarizingIds)
      .filter((key) => key.startsWith(prefix))
      .map((key) => key.slice(prefix.length));
    return new Set(paperIds);
  }, [historyId, summarizingIds]);

  const handleSearch = useCallback(async (query: string, dateFrom: string) => {
    const requestId = latestRequestIdRef.current + 1;
    latestRequestIdRef.current = requestId;

    // Start each new search from a clean result view.
    setResults([]);
    setGeneratedQueries([]);
    setActiveHistoryId("");
    setTotalCandidates(null);

    setActiveSearchCount((count) => count + 1);
    setActiveHistoryStatus("running");
    setActiveHistoryError(null);
    refreshHistory();
    refreshHistoryAfterDelay(350);
    refreshHistoryAfterDelay(1200);

    try {
      const res = await search({ query, date_from: dateFrom || null });
      if (requestId === latestRequestIdRef.current) {
        setResults(res.results);
        setGeneratedQueries(res.generated_queries);
        setActiveHistoryId(res.history_id);
        setTotalCandidates(res.total_candidates);
        setActiveHistoryStatus("completed");
        setActiveHistoryError(null);
      }
    } catch (error: unknown) {
      if (requestId === latestRequestIdRef.current) {
        setActiveHistoryStatus("failed");
        setActiveHistoryError(getApiErrorMessage(error));
      }
      showApiErrorToast(error);
    } finally {
      setActiveSearchCount((count) => Math.max(0, count - 1));
      refreshHistory();
    }
  }, [refreshHistory, refreshHistoryAfterDelay, setActiveHistoryId, showApiErrorToast]);

  const handleSummarize = useCallback(async (paperId: string) => {
    const existingPaper = results.find((paper) => paper.paper_id === paperId);
    const contextHistoryId = historyId;
    if (!contextHistoryId || existingPaper?.summary) return;

    const summarizeKey = `${contextHistoryId}:${paperId}`;
    setSummarizingIds((s) => new Set(s).add(summarizeKey));
    try {
      const response = await summarizePaper({
        history_id: contextHistoryId,
        paper_id: paperId,
        style: "brief",
      });

      const isActiveContext = activeHistoryIdRef.current === contextHistoryId;
      const isMatchingResponse =
        response.history_id === contextHistoryId &&
        response.paper_id === paperId;

      if (isActiveContext && isMatchingResponse) {
        setResults((prev) => prev.map((paper) => (
          paper.paper_id === paperId
            ? { ...paper, summary: response.summary, highlights: response.highlights }
            : paper
        )));
      }
    } catch (error: unknown) {
      showApiErrorToast(error);
    } finally {
      setSummarizingIds((s) => {
        const n = new Set(s);
        n.delete(summarizeKey);
        return n;
      });
    }
  }, [historyId, results, showApiErrorToast]);

  const handleRestoreHistory = useCallback(async (hId: string) => {
    setHistoryOpen(false);
    setActiveSearchCount((count) => count + 1);
    try {
      const detail = await fetchHistoryDetail(hId);
      setRestoredSearch({ query: detail.query, dateFrom: detail.date_from ?? "" });
      setSearchKey((k) => k + 1);
      setResults(detail.results);
      setGeneratedQueries(detail.generated_queries);
      setActiveHistoryId(detail.history_id);
      setTotalCandidates(null);
      setActiveHistoryStatus(detail.status);
      setActiveHistoryError(detail.error_message);
    } catch (error: unknown) {
      showApiErrorToast(error);
    } finally {
      setActiveSearchCount((count) => Math.max(0, count - 1));
    }
  }, [setActiveHistoryId, showApiErrorToast]);

  return (
    <div className="mx-auto max-w-4xl">
      <TopBar onHistoryClick={() => setHistoryOpen(true)} />
      <SearchBar
        key={searchKey}
        initialQuery={restoredSearch?.query}
        initialDateFrom={restoredSearch?.dateFrom}
        onSearch={handleSearch}
        loading={loading}
      />
      {activeHistoryStatus === "running" && (
        <div className="border-b border-sky-500/30 bg-sky-500/5 px-4 py-2 text-xs text-sky-700">
          <span className="inline-flex items-center gap-1.5">
            <Loader2 size={12} className="animate-spin" />
            Results will appear when processing completes.
          </span>
        </div>
      )}
      {activeHistoryStatus === "failed" && activeHistoryError && (
        <div className="border-b border-destructive/30 bg-destructive/5 px-4 py-2 text-xs text-destructive">
          {activeHistoryError}
        </div>
      )}
      <GeneratedQueries queries={generatedQueries} />
      <ResultsList
        results={results}
        totalCandidates={totalCandidates}
        onSummarize={handleSummarize}
        summarizingIds={activeSummarizingIds}
      />
      {!results.length && !loading && (
        <div className="px-4 py-8 text-center text-xs text-muted-foreground">
          Enter a query to search arXiv papers.
        </div>
      )}
      <HistoryPanel
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onRestore={handleRestoreHistory}
        onError={showApiErrorToast}
        refreshKey={historyRefreshKey}
      />
    </div>
  );
}
