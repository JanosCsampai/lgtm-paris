"use client";

import { useState } from "react";
import {
  MapPin,
  Star,
  Mail,
  Loader2,
  CheckCircle2,
  Clock,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  Trophy,
} from "lucide-react";
import type { PriceStats, ProviderWithPrices } from "@/lib/types";
import { CATEGORY_LABELS, CATEGORY_SWATCHES } from "@/lib/constants";
import { BookingModal } from "@/components/booking-modal";
import { sendInquiry } from "@/lib/api";

interface ResultCardProps {
  provider: ProviderWithPrices;
  priceStats?: PriceStats | null;
  scrapingInProgress?: boolean;
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
  const withPrice = provider.observations.filter((o) => o.price > 0);
  if (withPrice.length === 0) return null;
  const sorted = [...withPrice].sort((a, b) => a.price - b.price);
  return { price: sorted[0].price, currency: sorted[0].currency };
}

function formatPrice(price: number, currency: string): string {
  const symbols: Record<string, string> = { GBP: "£", EUR: "€", USD: "$" };
  return `${symbols[currency] ?? currency + " "}${Math.round(price)}`;
}

type PriceCallout =
  | { kind: "best"; label: string }
  | { kind: "below_avg"; label: string; pctBelow: number }
  | { kind: "above_avg"; label: string; ratio: number }
  | { kind: "near_avg"; label: string }
  | null;

function getPriceCallout(
  price: number,
  stats: PriceStats
): PriceCallout {
  if (stats.sample_size < 2) return null;

  const avg = stats.avg_price;
  const ratio = price / avg;

  if (price <= stats.min_price) {
    return { kind: "best", label: "Best price locally" };
  }
  if (ratio <= 0.7) {
    const pctBelow = Math.round((1 - ratio) * 100);
    return {
      kind: "below_avg",
      label: `${pctBelow}% below local avg`,
      pctBelow,
    };
  }
  if (ratio >= 2) {
    const r = Math.round(ratio * 10) / 10;
    return {
      kind: "above_avg",
      label: `${r}x the local average`,
      ratio: r,
    };
  }
  if (ratio > 1.3) {
    const pctAbove = Math.round((ratio - 1) * 100);
    return {
      kind: "above_avg",
      label: `${pctAbove}% above local avg`,
      ratio,
    };
  }
  if (ratio >= 0.7 && ratio <= 1.3) {
    return { kind: "near_avg", label: "Near local average" };
  }

  return null;
}

function PriceCalloutBadge({ callout, avgFormatted }: { callout: NonNullable<PriceCallout>; avgFormatted: string }) {
  switch (callout.kind) {
    case "best":
      return (
        <div className="mt-1 flex items-center gap-1 rounded-md bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 px-2 py-1">
          <Trophy className="h-3 w-3 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-300">
            {callout.label}
          </span>
        </div>
      );
    case "below_avg":
      return (
        <div className="mt-1 flex items-center gap-1 rounded-md bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 px-2 py-1">
          <TrendingDown className="h-3 w-3 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span className="text-[11px] font-medium text-emerald-700 dark:text-emerald-300">
            {callout.label}
          </span>
        </div>
      );
    case "above_avg":
      return (
        <div className="mt-1 flex items-center gap-1 rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 px-2 py-1">
          {callout.ratio >= 2 ? (
            <AlertTriangle className="h-3 w-3 text-amber-600 dark:text-amber-400 shrink-0" />
          ) : (
            <TrendingUp className="h-3 w-3 text-amber-600 dark:text-amber-400 shrink-0" />
          )}
          <span className="text-[11px] font-medium text-amber-700 dark:text-amber-300">
            {callout.label}
          </span>
          <span className="text-[10px] text-amber-500 dark:text-amber-500">
            (avg {avgFormatted})
          </span>
        </div>
      );
    case "near_avg":
      return (
        <div className="mt-1 flex items-center gap-1 rounded-md bg-muted/50 border border-border/60 px-2 py-1">
          <span className="text-[11px] text-muted-foreground">
            ~ {callout.label}
          </span>
        </div>
      );
  }
}

export function ResultCard({ provider, priceStats, scrapingInProgress }: ResultCardProps) {
  const [showModal, setShowModal] = useState(false);
  const [inquiryState, setInquiryState] = useState<
    "idle" | "sending" | "sent" | "error"
  >(provider.inquiry_status === "sent" ? "sent" : "idle");
  const [errorMsg, setErrorMsg] = useState("");

  const lowest = getLowestPrice(provider);
  const categoryLabel = provider.category_label || provider.category;
  const swatch = CATEGORY_SWATCHES[provider.category] ?? "#6b7280";
  const hasPrice = !!lowest;
  const alreadyReplied = provider.inquiry_status === "replied";

  async function handleInquire() {
    setInquiryState("sending");
    setErrorMsg("");
    try {
      await sendInquiry(provider.id, provider.category);
      setInquiryState("sent");
    } catch (err: any) {
      setInquiryState("error");
      setErrorMsg(err.message || "Failed to send inquiry");
    }
  }

  return (
    <div className="group py-5 cursor-pointer transition-colors hover:bg-muted/40 -mx-3 px-3 rounded-sm">
      <div className="min-w-0">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="text-[15px] font-semibold leading-snug text-foreground group-hover:text-primary transition-colors">
              {provider.website ? (
                <a
                  href={provider.website.startsWith("http") ? provider.website : `http://${provider.website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  {provider.name}
                </a>
              ) : (
                provider.name
              )}
            </h3>
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

          <div className="shrink-0 text-right flex flex-col items-end">
            {hasPrice ? (
              <>
                <span className="text-base font-bold text-foreground">
                  {formatPrice(lowest.price, lowest.currency)}
                </span>
                {priceStats && priceStats.sample_size >= 2 && (() => {
                  const callout = getPriceCallout(lowest.price, priceStats);
                  if (!callout) return null;
                  return (
                    <PriceCalloutBadge
                      callout={callout}
                      avgFormatted={formatPrice(priceStats.avg_price, priceStats.currency)}
                    />
                  );
                })()}
              </>
            ) : scrapingInProgress ? (
              <span className="flex items-center gap-1 text-[13px] text-muted-foreground animate-pulse">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Checking&hellip;
              </span>
            ) : alreadyReplied ? (
              <span className="flex items-center gap-1 text-[13px] text-emerald-600">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Reply received
              </span>
            ) : inquiryState === "sent" || provider.inquiry_status === "sent" ? (
              <span className="flex items-center gap-1 text-[13px] text-amber-600">
                <Clock className="h-3.5 w-3.5" />
                Inquiry sent
              </span>
            ) : null}
          </div>
        </div>

        {provider.description && (
          <p className="mt-1.5 line-clamp-2 text-[13px] leading-relaxed text-muted-foreground">
            {provider.description}
          </p>
        )}

        {errorMsg && (
          <p className="mt-1 text-[12px] text-red-500">{errorMsg}</p>
        )}

        <div className="mt-2.5 flex items-center justify-between">
          <div className="flex items-center gap-1 text-[13px] text-muted-foreground">
            <MapPin className="h-3.5 w-3.5" />
            {formatDistance(provider.distance_meters)}
          </div>

          <div className="flex items-center gap-4">

            {!hasPrice && !alreadyReplied && inquiryState !== "sent" && provider.inquiry_status !== "sent" ? (
              <button
                onClick={handleInquire}
                disabled={inquiryState === "sending"}
                className="rounded-sm border border-primary/30 bg-primary/5 px-3.5 py-1.5 text-[13px] font-medium text-primary transition-colors hover:bg-primary/10 hover:border-primary/50 disabled:opacity-50 flex items-center gap-1.5"
              >
                {inquiryState === "sending" ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Sending…
                  </>
                ) : (
                  <>
                    <Mail className="h-3.5 w-3.5" />
                    Inquire price
                  </>
                )}
              </button>
            ) : (
              <button
              onClick={() => setShowModal(true)}
              className="rounded-md px-4 py-2 text-[13px] font-semibold text-white transition-opacity hover:opacity-90"
              style={{ background: "#5C2553" }}
            >
              Book now
            </button>
            )}
          </div>
        </div>
      </div>
      {showModal && (
        <BookingModal provider={provider} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
