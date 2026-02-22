"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft, MapPin } from "lucide-react";

interface ResultsHeaderProps {
  count: number;
  distanceKm: number;
  isLoading: boolean;
}

export function ResultsHeader({
  count,
  distanceKm,
  isLoading,
}: ResultsHeaderProps) {
  const router = useRouter();

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

      <div className="flex items-center gap-1.5 rounded-full border border-border bg-white px-3 py-1.5 text-[13px] font-medium text-foreground">
        <MapPin className="h-3.5 w-3.5" style={{ color: "#5C2553" }} />
        {distanceKm} km
      </div>
    </div>
  );
}
