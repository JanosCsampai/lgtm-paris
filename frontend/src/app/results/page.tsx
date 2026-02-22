"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ResultsHeader } from "@/components/results-header";
import { ResultsList } from "@/components/results-list";
import { useSearch } from "@/hooks/use-search";
import dynamic from "next/dynamic";

const ResultsMap = dynamic(() => import("@/components/results-map"), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-muted animate-pulse" />,
});

function ResultsContent() {
  const searchParams = useSearchParams();

  const q = searchParams.get("q") ?? "";
  const lat = parseFloat(searchParams.get("lat") ?? "0");
  const lng = parseFloat(searchParams.get("lng") ?? "0");
  const radiusMeters = parseFloat(searchParams.get("radius") ?? "5000");

  const params =
    q.length > 0 ? { q, lat, lng, radius_meters: radiusMeters } : null;

  const { data, isLoading, error, refetch } = useSearch(params);

  const results = data?.results ?? [];
  const priceStats = data?.price_stats ?? null;
  const scrapingInProgress = data?.scraping_in_progress ?? false;
  const distanceKm = Math.round(radiusMeters / 1000);

  return (
    <>
      {/* Mobile: stacked layout */}
      <div className="lg:hidden">
        <div className="px-5 pt-4 pb-3">
          <ResultsHeader
            count={results.length}
            distanceKm={distanceKm}
            isLoading={isLoading}
            onRepliesChecked={() => refetch()}
          />
        </div>
        <div className="h-52 w-full">
          <ResultsMap
            results={results}
            userLat={lat}
            userLng={lng}
            isLoading={isLoading}
          />
        </div>
        <div className="px-5 py-4">
          <ResultsList
            results={results}
            priceStats={priceStats}
            isLoading={isLoading}
            error={error}
            onRetry={() => refetch()}
            scrapingInProgress={scrapingInProgress}
          />
        </div>
      </div>

      {/* Desktop: Airbnb-style split — list (scrollable) | map (fixed, edge-to-edge) */}
      <div className="hidden lg:flex h-[calc(100vh-4rem)]">
        <div className="w-[55%] shrink-0 overflow-y-auto border-r border-border">
          <div className="px-6 xl:px-10 pt-5 pb-2">
            <ResultsHeader
              count={results.length}
              distanceKm={distanceKm}
              isLoading={isLoading}
              onRepliesChecked={() => refetch()}
            />
          </div>
          <div className="px-6 xl:px-10 pb-8">
            <ResultsList
              results={results}
              priceStats={priceStats}
              isLoading={isLoading}
              error={error}
              onRetry={() => refetch()}
              scrapingInProgress={scrapingInProgress}
            />
          </div>
        </div>
        <div className="flex-1 relative">
          <ResultsMap
            results={results}
            userLat={lat}
            userLng={lng}
            isLoading={isLoading}
          />
        </div>
      </div>
    </>
  );
}

export default function ResultsPage() {
  return (
    <Suspense
      fallback={
        <div className="hidden lg:flex h-[calc(100vh-4rem)]">
          <div className="w-[55%] shrink-0 px-6 xl:px-10 pt-5 space-y-4">
            <div className="h-7 w-48 animate-pulse rounded-md bg-muted" />
            <div className="h-4 w-32 animate-pulse rounded-md bg-muted" />
            <div className="space-y-0 divide-y divide-border">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="py-5">
                  <div className="flex gap-4">
                    <div className="h-11 w-11 shrink-0 animate-pulse rounded-lg bg-muted" />
                    <div className="flex-1 space-y-2">
                      <div className="h-5 w-52 animate-pulse rounded bg-muted" />
                      <div className="h-4 w-full animate-pulse rounded bg-muted" />
                      <div className="h-4 w-32 animate-pulse rounded bg-muted" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="flex-1 bg-muted animate-pulse" />
        </div>
      }
    >
      <ResultsContent />
    </Suspense>
  );
}
