"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { MapPin } from "lucide-react";
import { SearchInput } from "@/components/search-input";
import { SuggestionChips } from "@/components/suggestion-chips";
import { DistanceSlider } from "@/components/distance-slider";
import { TrustBadges } from "@/components/trust-badges";
import { ChatInterface } from "@/components/chat-interface";
import { useGeolocation } from "@/hooks/use-geolocation";
import { sendChatMessage } from "@/lib/api";
import { DISTANCE_DEFAULT_KM } from "@/lib/constants";

type Mode = "search" | "loading" | "chat";

export default function HomePage() {
  const router = useRouter();
  const geo = useGeolocation();
  const inputRef = useRef<HTMLInputElement>(null);

  const [query, setQuery] = useState("");
  const [distance, setDistance] = useState(DISTANCE_DEFAULT_KM);
  const [mode, setMode] = useState<Mode>("search");
  const [chatQuery, setChatQuery] = useState("");
  const [chatKey, setChatKey] = useState(0);

  const navigateToSearch = useCallback(
    (q: string) => {
      const params = new URLSearchParams({
        q,
        lat: String(geo.lat),
        lng: String(geo.lng),
        radius: String(distance * 1000),
      });
      router.push(`/results?${params.toString()}`);
    },
    [geo.lat, geo.lng, distance, router]
  );

  const handleSearch = useCallback(
    async (q?: string) => {
      const searchQuery = (q ?? query).trim();
      if (!searchQuery) return;

      setMode("loading");

      try {
        const response = await sendChatMessage([
          { role: "user", content: searchQuery },
        ]);

        if (response.status === "ready" && response.search_query) {
          navigateToSearch(response.search_query);
        } else {
          setChatQuery(searchQuery);
          setChatKey((k) => k + 1);
          setMode("chat");
        }
      } catch {
        navigateToSearch(searchQuery);
      }
    },
    [query, navigateToSearch]
  );

  const handleChipSelect = useCallback(
    (chip: string) => {
      setQuery(chip);
      handleSearch(chip);
    },
    [handleSearch]
  );

  const handleReset = useCallback(() => {
    setMode("search");
    setQuery("");
    setChatQuery("");
  }, []);

  const isChat = mode === "chat";

  return (
    /*
     * Fixed-height container so the absolute-positioned chat overlay
     * always fills the exact same area as the hero.
     */
    <div className="relative h-[calc(100vh-4rem)] overflow-hidden">

      {/* ── HERO ─────────────────────────────────────────────────────── */}
      <div
        className={[
          "flex h-full items-center justify-center px-5",
          "transition-all duration-500 ease-in-out",
          isChat
            ? "opacity-0 -translate-y-10 pointer-events-none select-none"
            : "opacity-100 translate-y-0",
        ].join(" ")}
      >
        <div className="w-full max-w-xl space-y-7 text-center">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-1.5 rounded border border-border bg-muted px-3 py-1 text-[12px] font-semibold uppercase tracking-widest text-muted-foreground">
              <MapPin className="h-3 w-3" />
              London local services
            </div>

            <h1 className="text-[2.5rem] font-bold leading-[1.1] tracking-tight sm:text-5xl">
              Compare prices from
              <br />
              <span className="gradient-text">locals near you</span>
            </h1>

            <p className="mx-auto max-w-md text-[15px] leading-relaxed text-muted-foreground">
              Search any service and see real prices in your area
            </p>
          </div>

          <div className="space-y-3">
            <SearchInput
              ref={inputRef}
              value={query}
              onChange={setQuery}
              onSubmit={() => handleSearch()}
              isLoading={mode === "loading"}
            />
            <div
              className={[
                "transition-opacity duration-300",
                mode === "loading" ? "opacity-0 pointer-events-none" : "opacity-100",
              ].join(" ")}
            >
              <SuggestionChips onSelect={handleChipSelect} />
            </div>
          </div>

          <div className="flex justify-center pt-1">
            <DistanceSlider value={distance} onChange={setDistance} />
          </div>

          <TrustBadges />
        </div>
      </div>

      {/* ── CHAT OVERLAY ─────────────────────────────────────────────── */}
      <div
        className={[
          "absolute inset-0",
          "transition-all duration-500 ease-in-out delay-75",
          isChat
            ? "opacity-100 translate-y-0 pointer-events-auto"
            : "opacity-0 translate-y-10 pointer-events-none select-none",
        ].join(" ")}
      >
        <ChatInterface
          key={chatKey}
          initialQuery={chatQuery}
          lat={geo.lat}
          lng={geo.lng}
          distance={distance}
          onDistanceChange={setDistance}
          onReset={handleReset}
        />
      </div>

    </div>
  );
}
