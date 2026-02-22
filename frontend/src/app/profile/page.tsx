"use client";

import { useState, useEffect } from "react";
import { User } from "lucide-react";

const STORAGE_KEY = "plumline_profile";

export default function ProfilePage() {
  const [firstname, setFirstname] = useState("");
  const [lastname, setLastname] = useState("");
  const [email, setEmail] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const p = JSON.parse(raw);
      if (p.firstname) setFirstname(p.firstname);
      if (p.lastname) setLastname(p.lastname);
      if (p.email) setEmail(p.email);
    } catch {}
  }, []);

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ firstname, lastname, email }));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
            <User className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">Your Profile</h1>
            <p className="text-[13px] text-muted-foreground">
              Saved details are pre-filled when you book a repair.
            </p>
          </div>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
                First Name
              </label>
              <input
                required
                value={firstname}
                onChange={(e) => setFirstname(e.target.value)}
                placeholder="John"
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
                placeholder="Doe"
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
              placeholder="john@example.com"
              className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-[14px] focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
          >
            {saved ? "Saved ✓" : "Save Profile"}
          </button>
        </form>
      </div>
    </div>
  );
}
