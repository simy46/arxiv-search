import { Download, FileText, Check } from "lucide-react";
import type { Paper } from "@/lib/api";

interface Props {
  paper: Paper;
  onDownload: (paperId: string) => void;
  onSummarize: (paperId: string) => void;
  summary: { summary: string; highlights: string[] } | null;
  summarizing: boolean;
  downloading: boolean;
}

export default function PaperRow({ paper, onDownload, onSummarize, summary, summarizing, downloading }: Props) {
  const hasSummary = !!summary;

  return (
    <div className="border-b border-border/60 px-4 py-3 transition-colors hover:bg-surface-raised/50">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <a
            href={paper.abs_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[13px] font-medium leading-snug text-primary hover:underline"
          >
            {paper.title}
          </a>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            <span>{paper.authors.join(", ")}</span>
            <span className="text-border">·</span>
            <span>{paper.published}</span>
            {paper.score != null && (
              <>
                <span className="text-border">·</span>
                <span className="font-mono text-[11px]">{paper.score.toFixed(2)}</span>
              </>
            )}
          </div>
          <div className="mt-1 flex flex-wrap gap-1">
            {paper.categories.map((c) => (
              <span key={c} className="rounded bg-accent px-1.5 py-0.5 text-[10px] font-medium text-accent-foreground">
                {c}
              </span>
            ))}
          </div>
          <p className="mt-1.5 text-xs leading-relaxed text-foreground/70">
            {paper.abstract.length > 280 ? paper.abstract.slice(0, 280) + "…" : paper.abstract}
          </p>
        </div>
        <div className="flex shrink-0 flex-col gap-1.5 pt-0.5">
          <button
            onClick={() => onDownload(paper.paper_id)}
            disabled={paper.downloaded || downloading}
            className="flex items-center gap-1 rounded border px-2 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-35"
          >
            {paper.downloaded ? <Check size={11} /> : <Download size={11} />}
            {paper.downloaded ? "Saved" : downloading ? "…" : "Download"}
          </button>
          {!hasSummary && (
            <button
              onClick={() => onSummarize(paper.paper_id)}
              disabled={summarizing}
              className="flex items-center gap-1 rounded border px-2 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-35"
            >
              <FileText size={11} />
              {summarizing ? "…" : "Summarize"}
            </button>
          )}
        </div>
      </div>

      {summarizing && !hasSummary && (
        <div className="mt-2 text-xs text-muted-foreground">Loading summary…</div>
      )}

      {hasSummary && (
        <div className="mt-2.5 rounded border bg-surface-raised px-3 py-2.5 text-xs">
          <div className="mb-1.5 flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
            <FileText size={10} /> Summary
          </div>
          <p className="leading-relaxed text-foreground/85">{summary.summary}</p>
          {summary.highlights.length > 0 && (
            <ul className="mt-2 space-y-0.5 text-muted-foreground">
              {summary.highlights.map((h, i) => (
                <li key={i} className="flex gap-1.5">
                  <span className="mt-0.5 text-border">•</span>
                  <span>{h}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}