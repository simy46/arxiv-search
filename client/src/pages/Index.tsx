import { useState, useCallback } from "react";
import TopBar from "@/components/TopBar";
import SearchBar from "@/components/SearchBar";
import GeneratedQueries from "@/components/GeneratedQueries";
import ResultsList from "@/components/ResultsList";
import HistoryPanel from "@/components/HistoryPanel";
import {
  search,
  downloadPaper,
  summarizePaper,
  fetchHistoryDetail,
  getApiErrorMessage,
  type Paper,
  type GeneratedQuery,
} from "@/lib/api";
import { toast } from "@/hooks/use-toast";

export default function Index() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Paper[]>([]);
  const [generatedQueries, setGeneratedQueries] = useState<GeneratedQuery[]>([]);
  const [historyId, setHistoryId] = useState("");
  const [totalCandidates, setTotalCandidates] = useState<number | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  const [summarizingIds, setSummarizingIds] = useState<Set<string>>(new Set());
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());

  // key to remount SearchBar on history restore
  const [searchKey, setSearchKey] = useState(0);
  const [restoredSearch, setRestoredSearch] = useState<{ query: string; dateFrom: string } | null>(null);

  const showApiErrorToast = useCallback((error: unknown) => {
    toast({
      title: "Request failed",
      description: getApiErrorMessage(error),
      variant: "destructive",
      duration: 4500,
    });
  }, []);

  const handleSearch = useCallback(async (query: string, dateFrom: string) => {
    setLoading(true);
    try {
      const res = await search({ query, date_from: dateFrom || null });
      setResults(res.results);
      setGeneratedQueries(res.generated_queries);
      setHistoryId(res.history_id);
      setTotalCandidates(res.total_candidates);
    } catch (error: unknown) {
      showApiErrorToast(error);
    } finally {
      setLoading(false);
    }
  }, [showApiErrorToast]);

  const handleDownload = useCallback(async (paperId: string) => {
    setDownloadingIds((s) => new Set(s).add(paperId));
    try {
      const response = await downloadPaper(paperId);
      setResults((prev) => prev.map((p) => (
        p.paper_id === paperId ? { ...p, downloaded: response.downloaded } : p
      )));
    } catch (error: unknown) {
      showApiErrorToast(error);
    } finally {
      setDownloadingIds((s) => { const n = new Set(s); n.delete(paperId); return n; });
    }
  }, [showApiErrorToast]);

  const handleSummarize = useCallback(async (paperId: string) => {
    const existingPaper = results.find((paper) => paper.paper_id === paperId);
    if (!historyId || existingPaper?.summary) return;

    setSummarizingIds((s) => new Set(s).add(paperId));
    try {
      const response = await summarizePaper({
        history_id: historyId,
        paper_id: paperId,
        style: "brief",
      });
      setResults((prev) => prev.map((paper) => (
        paper.paper_id === paperId
          ? { ...paper, summary: response.summary, highlights: response.highlights }
          : paper
      )));
    } catch (error: unknown) {
      showApiErrorToast(error);
    } finally {
      setSummarizingIds((s) => { const n = new Set(s); n.delete(paperId); return n; });
    }
  }, [historyId, results, showApiErrorToast]);

  const handleRestoreHistory = useCallback(async (hId: string) => {
    setHistoryOpen(false);
    setLoading(true);
    try {
      const detail = await fetchHistoryDetail(hId);
      setRestoredSearch({ query: detail.query, dateFrom: detail.date_from ?? "" });
      setSearchKey((k) => k + 1);
      setResults(detail.results);
      setGeneratedQueries(detail.generated_queries);
      setHistoryId(detail.history_id);
      setTotalCandidates(null);
    } catch (error: unknown) {
      showApiErrorToast(error);
    } finally {
      setLoading(false);
    }
  }, [showApiErrorToast]);

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
      <GeneratedQueries queries={generatedQueries} />
      <ResultsList
        results={results}
        totalCandidates={totalCandidates}
        onDownload={handleDownload}
        onSummarize={handleSummarize}
        summarizingIds={summarizingIds}
        downloadingIds={downloadingIds}
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
      />
    </div>
  );
}
