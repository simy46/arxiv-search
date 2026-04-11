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
  type Paper,
  type GeneratedQuery,
} from "@/lib/api";

export default function Index() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Paper[]>([]);
  const [generatedQueries, setGeneratedQueries] = useState<GeneratedQuery[]>([]);
  const [historyId, setHistoryId] = useState("");
  const [totalCandidates, setTotalCandidates] = useState<number | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  // summaries & downloads
  const [summaries, setSummaries] = useState<Record<string, { summary: string; highlights: string[] }>>({});
  const [summarizingIds, setSummarizingIds] = useState<Set<string>>(new Set());
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());

  // key to remount SearchBar on history restore
  const [searchKey, setSearchKey] = useState(0);
  const [restoredSearch, setRestoredSearch] = useState<{ query: string; pageSize: number; dateFrom: string } | null>(null);

  const handleSearch = useCallback(async (query: string, pageSize: number, dateFrom: string) => {
    setLoading(true);
    setSummaries({});
    try {
      const res = await search({ query, page_size: pageSize, date_from: dateFrom });
      setResults(res.results);
      setGeneratedQueries(res.generated_queries);
      setHistoryId(res.history_id);
      setTotalCandidates(res.total_candidates);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDownload = useCallback(async (paperId: string) => {
    setDownloadingIds((s) => new Set(s).add(paperId));
    try {
      await downloadPaper(paperId);
      setResults((prev) => prev.map((p) => (p.paper_id === paperId ? { ...p, downloaded: true } : p)));
    } catch (e) {
      console.error(e);
    } finally {
      setDownloadingIds((s) => { const n = new Set(s); n.delete(paperId); return n; });
    }
  }, []);

  const handleSummarize = useCallback(async (paperId: string) => {
    if (summaries[paperId]) return;
    setSummarizingIds((s) => new Set(s).add(paperId));
    try {
      const res = await summarizePaper(historyId, paperId);
      setSummaries((prev) => ({ ...prev, [paperId]: { summary: res.summary, highlights: res.highlights } }));
    } catch (e) {
      console.error(e);
    } finally {
      setSummarizingIds((s) => { const n = new Set(s); n.delete(paperId); return n; });
    }
  }, [historyId, summaries]);

  const handleRestoreHistory = useCallback(async (hId: string) => {
    setHistoryOpen(false);
    setLoading(true);
    setSummaries({});
    try {
      const detail = await fetchHistoryDetail(hId);
      setRestoredSearch({ query: detail.query, pageSize: detail.page_size, dateFrom: detail.date_from });
      setSearchKey((k) => k + 1);
      setResults(detail.results);
      setGeneratedQueries(detail.generated_queries);
      setHistoryId(detail.history_id);
      setTotalCandidates(null);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="mx-auto max-w-4xl">
      <TopBar onHistoryClick={() => setHistoryOpen(true)} />
      <SearchBar
        key={searchKey}
        initialQuery={restoredSearch?.query}
        initialPageSize={restoredSearch?.pageSize}
        initialDateFrom={restoredSearch?.dateFrom}
        onSearch={handleSearch}
        loading={loading}
      />
      <GeneratedQueries queries={generatedQueries} />
      <ResultsList
        results={results}
        totalCandidates={totalCandidates}
        historyId={historyId}
        onDownload={handleDownload}
        onSummarize={handleSummarize}
        summaries={summaries}
        summarizingIds={summarizingIds}
        downloadingIds={downloadingIds}
      />
      {!results.length && !loading && (
        <div className="px-4 py-8 text-center text-xs text-muted-foreground">
          Enter a query to search arXiv papers.
        </div>
      )}
      <HistoryPanel open={historyOpen} onClose={() => setHistoryOpen(false)} onRestore={handleRestoreHistory} />
    </div>
  );
}
