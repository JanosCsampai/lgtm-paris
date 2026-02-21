"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { MapPin } from "lucide-react";
import { SearchInput } from "@/components/search-input";
import { SuggestionChips } from "@/components/suggestion-chips";
import { DistanceSlider } from "@/components/distance-slider";
import { TrustBadges } from "@/components/trust-badges";
import { useGeolocation } from "@/hooks/use-geolocation";
import { DISTANCE_DEFAULT_KM } from "@/lib/constants";

export default function HomePage() {
  const router = useRouter();
  const geo = useGeolocation();
  const inputRef = useRef<HTMLInputElement>(null);

  const [query, setQuery] = useState("");
  const [distance, setDistance] = useState(DISTANCE_DEFAULT_KM);

  const handleSearch = useCallback(
    (q?: string) => {
      const searchQuery = (q ?? query).trim();
      if (!searchQuery) return;

      const params = new URLSearchParams({
        q: searchQuery,
        lat: String(geo.lat),
        lng: String(geo.lng),
        radius: String(distance * 1000),
      });
      router.push(`/results?${params.toString()}`);
    },
    [query, geo.lat, geo.lng, distance, router]
  );

  const handleChipSelect = useCallback(
    (chip: string) => {
      setQuery(chip);
      handleSearch(chip);
    },
    [handleSearch]
  );

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center px-5">
      <div className="w-full max-w-xl space-y-7 text-center">
        <div className="space-y-3">
          <div className="inline-flex items-center gap-1.5 rounded border border-border bg-muted px-3 py-1 text-[12px] font-semibold uppercase tracking-widest text-muted-foreground">
            <MapPin className="h-3 w-3" />
            London local services
          </div>

          <h1 className="text-[2.5rem] font-bold leading-[1.1] tracking-tight sm:text-5xl">
            What service are you
            <br />
            <span className="gradient-text">looking for today?</span>
          </h1>

          <p className="mx-auto max-w-md text-[15px] leading-relaxed text-muted-foreground">
            Describe what you need — we&apos;ll find trusted professionals near
            you in seconds.
          </p>
        </div>

        <div className="space-y-3">
          <SearchInput
            ref={inputRef}
            value={query}
            onChange={setQuery}
            onSubmit={() => handleSearch()}
          />
          <SuggestionChips onSelect={handleChipSelect} />
        </div>

        <div className="flex justify-center pt-1">
          <DistanceSlider value={distance} onChange={setDistance} />
        </div>

        <TrustBadges />
      </div>
    </div>
  );
}
