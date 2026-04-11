import { useState, useEffect } from "react";
import { History, Sun, Moon } from "lucide-react";

interface TopBarProps {
  onHistoryClick: () => void;
}

export default function TopBar({ onHistoryClick }: TopBarProps) {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <div className="flex items-center justify-between border-b px-4 py-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold tracking-tight text-foreground">ArXiv Lab Search</span>
        <span className="text-[10px] text-muted-foreground">local</span>
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={() => setDark(!dark)}
          className="rounded p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          title={dark ? "Switch to light mode" : "Switch to dark mode"}
        >
          {dark ? <Sun size={14} /> : <Moon size={14} />}
        </button>
        <button
          onClick={onHistoryClick}
          className="flex items-center gap-1.5 rounded px-2 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          title="Search history"
        >
          <History size={13} />
          History
        </button>
      </div>
    </div>
  );
}