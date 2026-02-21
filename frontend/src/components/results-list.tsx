"use client";

import type { ProviderWithPrices } from "@/lib/types";
import { ResultCard } from "@/components/result-card";
import { Skeleton } from "@/components/ui/skeleton";
import { SearchX } from "lucide-react";

interface ResultsListProps {
  results: ProviderWithPrices[];
  isLoading: boolean;
  error: Error | null;
  onRetry?: () => void;
}

function ResultSkeleton() {
  return (
    <div className="py-5 space-y-2.5">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4.5 w-48" />
          <Skeleton className="h-3.5 w-24" />
        </div>
        <Skeleton className="h-6 w-10 shrink-0" />
      </div>
      <Skeleton className="h-3.5 w-full max-w-sm" />
      <Skeleton className="h-3.5 w-20" />
    </div>
  );
}

export function ResultsList({
  results,
  isLoading,
  error,
  onRetry,
}: ResultsListProps) {
  if (isLoading) {
    return (
      <div className="divide-y divide-border">
        {Array.from({ length: 5 }).map((_, i) => (
          <ResultSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 py-20 text-center">
        <div className="rounded-full bg-destructive/10 p-4">
          <SearchX className="h-7 w-7 text-destructive" />
        </div>
        <div className="space-y-1">
          <h3 className="text-[15px] font-semibold">Something went wrong</h3>
          <p className="text-[13px] text-muted-foreground">
            We couldn&apos;t load results. Please try again.
          </p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="rounded-full bg-foreground px-5 py-2 text-[13px] font-medium text-background hover:bg-foreground/90 transition-colors"
          >
            Try again
          </button>
        )}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="flex flex-col items-center gap-4 py-20 text-center">
        <div className="rounded-full bg-muted p-4">
          <SearchX className="h-7 w-7 text-muted-foreground" />
        </div>
        <div className="space-y-1">
          <h3 className="text-[15px] font-semibold">No results found</h3>
          <p className="text-[13px] text-muted-foreground">
            Try a different search or increase the distance.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="divide-y divide-border">
      {results.map((provider) => (
        <ResultCard key={provider.id} provider={provider} />
      ))}
    </div>
  );
}
