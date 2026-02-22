"use client";

import type { PriceStats, ProviderWithPrices } from "@/lib/types";
import { ResultCard } from "@/components/result-card";
import { Skeleton } from "@/components/ui/skeleton";
import { SearchX } from "lucide-react";

interface ResultsListProps {
  results: ProviderWithPrices[];
  priceStats: PriceStats | null;
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

function formatStatPrice(price: number, currency: string): string {
  const symbols: Record<string, string> = { GBP: "\u00a3", EUR: "\u20ac", USD: "$" };
  return `${symbols[currency] ?? currency + " "}${Math.round(price)}`;
}

function PriceSummaryBar({ stats }: { stats: PriceStats }) {
  return (
    <div className="mb-4 rounded-lg border border-border/60 bg-muted/30 px-4 py-3">
      <div className="flex items-center justify-between text-[13px]">
        <span className="font-medium text-foreground/70">
          Local price range
        </span>
        <span className="text-muted-foreground">
          Based on {stats.sample_size} provider{stats.sample_size !== 1 ? "s" : ""}
        </span>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <span className="text-[13px] font-semibold text-emerald-600">
          {formatStatPrice(stats.min_price, stats.currency)}
        </span>
        <div className="relative flex-1 h-1.5 rounded-full bg-border/60 overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-linear-to-r from-emerald-400 via-amber-300 to-rose-400"
            style={{ width: "100%" }}
          />
          {stats.max_price > stats.min_price && (
            <div
              className="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-foreground border-2 border-background shadow-sm"
              style={{
                left: `${((stats.avg_price - stats.min_price) / (stats.max_price - stats.min_price)) * 100}%`,
              }}
              title={`Average: ${formatStatPrice(stats.avg_price, stats.currency)}`}
            />
          )}
        </div>
        <span className="text-[13px] font-semibold text-rose-500">
          {formatStatPrice(stats.max_price, stats.currency)}
        </span>
      </div>
      <div className="mt-1.5 text-center text-[11px] text-muted-foreground">
        Avg {formatStatPrice(stats.avg_price, stats.currency)} · Median{" "}
        {formatStatPrice(stats.median_price, stats.currency)}
      </div>
    </div>
  );
}

export function ResultsList({
  results,
  priceStats,
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

  const sorted = [...results].sort((a, b) => {
    const aPrice = a.observations.filter((o) => o.price > 0).sort((x, y) => x.price - y.price)[0]?.price ?? Infinity;
    const bPrice = b.observations.filter((o) => o.price > 0).sort((x, y) => x.price - y.price)[0]?.price ?? Infinity;
    return aPrice - bPrice;
  });

  return (
    <div>
      {priceStats && priceStats.sample_size >= 2 && (
        <PriceSummaryBar stats={priceStats} />
      )}
      <div className="divide-y divide-border">
        {sorted.map((provider) => (
          <ResultCard
            key={provider.id}
            provider={provider}
            priceStats={priceStats}
          />
        ))}
      </div>
    </div>
  );
}
