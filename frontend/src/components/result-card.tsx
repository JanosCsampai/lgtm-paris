"use client";

import { MapPin, Star } from "lucide-react";
import type { ProviderWithPrices } from "@/lib/types";
import { CATEGORY_SWATCHES } from "@/lib/constants";

interface ResultCardProps {
  provider: ProviderWithPrices;
}

function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toFixed(1)} km`;
}

function getLowestPrice(provider: ProviderWithPrices): {
  price: number;
  currency: string;
} | null {
  if (provider.observations.length === 0) return null;
  const sorted = [...provider.observations].sort((a, b) => a.price - b.price);
  return { price: sorted[0].price, currency: sorted[0].currency };
}

function formatPrice(price: number, currency: string): string {
  const symbols: Record<string, string> = { GBP: "£", EUR: "€", USD: "$" };
  return `${symbols[currency] ?? currency + " "}${Math.round(price)}`;
}

export function ResultCard({ provider }: ResultCardProps) {
  const lowest = getLowestPrice(provider);
  const categoryLabel = provider.category_label || provider.category;
  const swatch = CATEGORY_SWATCHES[provider.category] ?? "#6b7280";

  return (
    <div className="group py-5 cursor-pointer transition-colors hover:bg-muted/40 -mx-3 px-3 rounded-sm">
      <div className="min-w-0">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="text-[15px] font-semibold leading-snug text-foreground group-hover:text-primary transition-colors">
              {provider.name}
            </h3>
            {/* Tube-line indicator badge */}
            <div className="mt-1 flex items-center gap-2">
              <span className="flex items-center gap-1.5">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-[2px]"
                  style={{ background: swatch }}
                />
                <span className="text-[11px] font-semibold uppercase tracking-widest text-foreground/55">
                  {categoryLabel}
                </span>
              </span>
              {provider.rating != null && (
                <span className="flex items-center gap-0.5 text-[13px]">
                  <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                  <span className="font-medium">{provider.rating}</span>
                  {provider.review_count != null && (
                    <span className="text-muted-foreground">
                      ({provider.review_count})
                    </span>
                  )}
                </span>
              )}
            </div>
          </div>

          {lowest && (
            <div className="shrink-0 text-right">
              <span className="text-base font-bold text-foreground">
                {formatPrice(lowest.price, lowest.currency)}
              </span>
            </div>
          )}
        </div>

        {provider.description && (
          <p className="mt-1.5 line-clamp-2 text-[13px] leading-relaxed text-muted-foreground">
            {provider.description}
          </p>
        )}

        <div className="mt-2.5 flex items-center justify-between">
          <div className="flex items-center gap-1 text-[13px] text-muted-foreground">
            <MapPin className="h-3.5 w-3.5" />
            {formatDistance(provider.distance_meters)}
          </div>

          <div className="flex items-center gap-4">
            <button className="text-[12px] text-muted-foreground/60 hover:text-foreground transition-colors">
              Why recommended?
            </button>
            <button className="rounded-sm border border-border px-3.5 py-1.5 text-[13px] font-medium text-foreground/70 transition-colors hover:border-foreground/30 hover:text-foreground">
              Book now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
