"use client";

import { useState } from "react";
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

export function BookingModal({ provider, onClose }: BookingModalProps) {
  const [firstname, setFirstname] = useState("");
  const [lastname, setLastname] = useState("");
  const [email, setEmail] = useState("");
  const [device, setDevice] = useState(DEVICES[0]);
  const [date, setDate] = useState("");
  const [time, setTime] = useState(TIMES[0].value);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    try {
      const res = await fetch(`${API_URL}/api/book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ firstname, lastname, email, device, date, time }),
      });
      if (!res.ok) throw new Error("Request failed");
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-md rounded-xl border border-border bg-background p-6 shadow-2xl">
        {/* Header */}
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">Book at {provider.name}</h2>
            <p className="text-[13px] text-muted-foreground">{provider.address}</p>
          </div>
          <button
            onClick={onClose}
            className="ml-4 text-muted-foreground hover:text-foreground transition-colors text-xl leading-none"
          >
            ×
          </button>
        </div>

        {status === "success" ? (
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
  );
}
