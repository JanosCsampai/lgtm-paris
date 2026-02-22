"use client";

import { useState } from "react";
import { MapPin, Star } from "lucide-react";
import type { ProviderWithPrices } from "@/lib/types";
import { CATEGORY_SWATCHES } from "@/lib/constants";
import { BookingModal } from "@/components/booking-modal";

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
  const [showModal, setShowModal] = useState(false);
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
                  <svg width="13" height="13" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
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
            <button
              onClick={() => setShowModal(true)}
              className="rounded-md px-4 py-2 text-[13px] font-semibold text-white transition-opacity hover:opacity-90"
              style={{ background: "#5C2553" }}
            >
              Book now
            </button>
          </div>
        </div>
      </div>
      {showModal && (
        <BookingModal provider={provider} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
