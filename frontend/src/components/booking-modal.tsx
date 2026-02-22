"use client";

import { useState, useEffect } from "react";
import { MapPin, X } from "lucide-react";
import type { ProviderWithPrices } from "@/lib/types";

const DEVICES = [
  "iPhone 14",
  "iPhone 13",
  "Samsung Galaxy S23",
  "Samsung Galaxy S22",
  "Google Pixel 7",
  "OnePlus 11",
];

const TIMES = [
  { value: "10:00", label: "10:00 AM" },
  { value: "12:00", label: "12:00 PM" },
  { value: "14:00", label: "2:00 PM" },
  { value: "16:00", label: "4:00 PM" },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface BookingModalProps {
  provider: ProviderWithPrices;
  onClose: () => void;
}

const AGENT_STEPS = [
  "Opening browser...",
  "Filling in your details...",
  "Selecting device & time...",
  "Processing payment...",
  "Confirming booking...",
];

export function BookingModal({ provider, onClose }: BookingModalProps) {
  const [firstname, setFirstname] = useState("");
  const [lastname, setLastname] = useState("");
  const [email, setEmail] = useState("");
  const [device, setDevice] = useState(DEVICES[0]);
  const [date, setDate] = useState("");
  const [time, setTime] = useState(TIMES[0].value);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [stepIndex, setStepIndex] = useState(0);

  // Pre-fill from saved profile
  useEffect(() => {
    try {
      const raw = localStorage.getItem("plumline_profile");
      if (!raw) return;
      const p = JSON.parse(raw);
      if (p.firstname) setFirstname(p.firstname);
      if (p.lastname) setLastname(p.lastname);
      if (p.email) setEmail(p.email);
    } catch {}
  }, []);

  // Cycle through agent steps while loading
  useEffect(() => {
    if (status !== "loading") return;
    const interval = setInterval(() => {
      setStepIndex((i) => (i + 1) % AGENT_STEPS.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [status]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setStepIndex(0);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120_000);
    try {
      const res = await fetch(`${API_URL}/api/book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ firstname, lastname, email, device, date, time }),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error("Request failed");
      setStatus("success");
    } catch {
      setStatus("error");
    } finally {
      clearTimeout(timeout);
    }
  }

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="relative w-full max-w-md rounded-xl border border-border bg-background shadow-2xl overflow-hidden">
        {/* Close button — hidden while agent is running */}
        {status !== "loading" && (
          <button
            onClick={onClose}
            className="absolute right-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-muted/80 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}

        {/* Header */}
        <div className="border-b border-border bg-muted/40 px-6 py-4 pr-12">
          <h2 className="text-base font-semibold leading-snug">
            Book at {provider.name}
          </h2>
          <p className="mt-1 flex items-start gap-1 text-[13px] leading-snug text-muted-foreground">
            <MapPin className="mt-0.5 h-3 w-3 shrink-0" />
            <span>{provider.address}</span>
          </p>
        </div>

        <div className="px-6 py-5">
          {status === "loading" ? (
            <div className="flex flex-col items-center py-6 text-center">
              {/* Spinning robot icon */}
              <div className="relative mb-5 flex h-16 w-16 items-center justify-center">
                <div className="absolute inset-0 rounded-full border-4 border-primary/20" />
                <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-primary" />
                <span className="text-2xl">🤖</span>
              </div>
              <p className="text-base font-semibold">Agent is booking your repair</p>
              <p className="mt-1 text-[13px] text-muted-foreground">
                Watch the browser window — it&apos;s filling the form for you.
              </p>
              {/* Animated step indicator */}
              <div className="mt-5 w-full rounded-lg border border-border bg-muted/40 px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary" />
                  <span className="text-[13px] text-muted-foreground transition-all duration-500">
                    {AGENT_STEPS[stepIndex]}
                  </span>
                </div>
                {/* Progress dots */}
                <div className="mt-3 flex gap-1.5 justify-center">
                  {AGENT_STEPS.map((_, i) => (
                    <div
                      key={i}
                      className={`h-1.5 rounded-full transition-all duration-500 ${
                        i === stepIndex ? "w-4 bg-primary" : "w-1.5 bg-muted-foreground/30"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          ) : status === "success" ? (
            <div className="rounded-lg bg-green-500/10 border border-green-500/30 px-4 py-5 text-center">
              <p className="text-2xl mb-2">🎉</p>
              <p className="font-semibold text-green-400">Booking confirmed!</p>
              <p className="mt-1 text-[13px] text-muted-foreground">
                Watch the agent fill out the form automatically.
              </p>
              <button
                onClick={onClose}
                className="mt-4 rounded-lg bg-green-500 px-4 py-2 text-sm font-medium text-white hover:bg-green-400 transition-colors"
              >
                Close
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
                    First Name
                  </label>
                  <input
                    required
                    value={firstname}
                    onChange={(e) => setFirstname(e.target.value)}
                    className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-[14px] focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
                    Last Name
                  </label>
                  <input
                    required
                    value={lastname}
                    onChange={(e) => setLastname(e.target.value)}
                    className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-[14px] focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
                  Email
                </label>
                <input
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-[14px] focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
                  Device
                </label>
                <select
                  value={device}
                  onChange={(e) => setDevice(e.target.value)}
                  className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-[14px] focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {DEVICES.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
                    Date
                  </label>
                  <input
                    required
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-[14px] focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
                    Time
                  </label>
                  <select
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                    className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-[14px] focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    {TIMES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {status === "error" && (
                <p className="text-[13px] text-red-400">
                  Something went wrong. Is the backend running on port 8000?
                </p>
              )}

              <button
                type="submit"
                disabled={status === "loading"}
                className="mt-1 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {status === "loading" ? "Processing…" : "Confirm Booking"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
