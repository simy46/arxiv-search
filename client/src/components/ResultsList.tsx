import type { Paper } from "@/lib/api";
import PaperRow from "./PaperRow";

interface Props {
  results: Paper[];
  totalCandidates: number | null;
  historyId: string;
  onDownload: (paperId: string) => void;
  onSummarize: (paperId: string) => void;
  summaries: Record<string, { summary: string; highlights: string[] }>;
  summarizingIds: Set<string>;
  downloadingIds: Set<string>;
}

export default function ResultsList({
  results,
  totalCandidates,
  historyId,
  onDownload,
  onSummarize,
  summaries,
  summarizingIds,
  downloadingIds,
}: Props) {
  if (!results.length) return null;

  return (
    <div>
      <div className="border-b px-4 py-1.5 text-[11px] text-muted-foreground">
        Showing {results.length} result{results.length !== 1 && "s"}
        {totalCandidates != null && <span> of {totalCandidates} candidates</span>}
      </div>
      {results.map((paper) => (
        <PaperRow
          key={paper.paper_id}
          paper={paper}
          onDownload={onDownload}
          onSummarize={onSummarize}
          summary={summaries[paper.paper_id] ?? null}
          summarizing={summarizingIds.has(paper.paper_id)}
          downloading={downloadingIds.has(paper.paper_id)}
        />
      ))}
    </div>
  );
}