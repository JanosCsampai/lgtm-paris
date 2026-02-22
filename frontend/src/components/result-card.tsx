"use client";

import { useState } from "react";
import { MapPin, Star, Mail, Loader2, CheckCircle2, Clock } from "lucide-react";
import type { ProviderWithPrices } from "@/lib/types";
import { CATEGORY_LABELS, CATEGORY_SWATCHES } from "@/lib/constants";
import { BookingModal } from "@/components/booking-modal";
import { sendInquiry } from "@/lib/api";

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
  const withPrice = provider.observations.filter((o) => o.price > 0);
  if (withPrice.length === 0) return null;
  const sorted = [...withPrice].sort((a, b) => a.price - b.price);
  return { price: sorted[0].price, currency: sorted[0].currency };
}

function formatPrice(price: number, currency: string): string {
  const symbols: Record<string, string> = { GBP: "£", EUR: "€", USD: "$" };
  return `${symbols[currency] ?? currency + " "}${Math.round(price)}`;
}

export function ResultCard({ provider }: ResultCardProps) {
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
              {provider.name}
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

          <div className="shrink-0 text-right">
            {hasPrice ? (
              <span className="text-base font-bold text-foreground">
                {formatPrice(lowest.price, lowest.currency)}
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
            <button className="text-[12px] text-muted-foreground/60 hover:text-foreground transition-colors">
              Why recommended?
            </button>

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
                className="rounded-sm border border-border px-3.5 py-1.5 text-[13px] font-medium text-foreground/70 transition-colors hover:border-foreground/30 hover:text-foreground"
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
