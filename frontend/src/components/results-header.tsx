"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, MapPin, RefreshCw } from "lucide-react";
import { checkReplies } from "@/lib/api";

interface ResultsHeaderProps {
  count: number;
  distanceKm: number;
  isLoading: boolean;
  onRepliesChecked?: () => void;
}

export function ResultsHeader({
  count,
  distanceKm,
  isLoading,
  onRepliesChecked,
}: ResultsHeaderProps) {
  const router = useRouter();
  const [checking, setChecking] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);

  async function handleCheckReplies() {
    setChecking(true);
    setFlash(null);
    try {
      const { replies_processed } = await checkReplies();
      if (replies_processed > 0) {
        setFlash(`${replies_processed} new repl${replies_processed === 1 ? "y" : "ies"}`);
        onRepliesChecked?.();
      } else {
        setFlash("No new replies");
      }
    } catch {
      setFlash("Check failed");
    } finally {
      setChecking(false);
      setTimeout(() => setFlash(null), 3000);
    }
  }

  return (
    <div className="flex items-center justify-between gap-4 pb-3 border-b border-border">
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/")}
          className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-white text-foreground transition-colors hover:bg-muted"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div>
          <p className="text-[13px] font-medium text-muted-foreground">
            {isLoading
              ? "Searching near you..."
              : `${count} service${count !== 1 ? "s" : ""} found near you`}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={handleCheckReplies}
          disabled={checking}
          className="flex items-center gap-1.5 rounded-full border border-border bg-white px-3 py-1.5 text-[13px] font-medium text-foreground transition-colors hover:bg-muted disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${checking ? "animate-spin" : ""}`} />
          {checking ? "Checking…" : flash ?? "Check replies"}
        </button>

        <div className="flex items-center gap-1.5 rounded-full border border-border bg-white px-3 py-1.5 text-[13px] font-medium text-foreground">
          <MapPin className="h-3.5 w-3.5 text-primary" />
          {distanceKm} km
        </div>
      </div>
    </div>
  );
}
