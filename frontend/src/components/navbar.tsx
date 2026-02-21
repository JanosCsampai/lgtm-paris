"use client";

import Link from "next/link";
import { CalendarDays, User } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b-2 border-[#003888] bg-white">
      <div className="flex h-14 items-center justify-between px-5 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2.5">
          {/* TfL roundel-inspired logo */}
          <div className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-[#003888]">
            <div className="absolute h-2.25 w-full bg-primary" />
            <span className="relative z-10 text-[9px] font-black tracking-tight text-white">TL</span>
          </div>
          <span className="text-[15px] font-bold tracking-tight text-foreground">
            TrustLocal
          </span>
        </Link>

        <nav className="flex items-center gap-1">
          <Link
            href="/bookings"
            className="flex items-center gap-1.5 rounded-full px-3.5 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <CalendarDays className="h-4 w-4" />
            <span className="hidden sm:inline">Bookings</span>
          </Link>
          <Link
            href="/profile"
            className="flex items-center gap-1.5 rounded-full px-3.5 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <User className="h-4 w-4" />
            <span className="hidden sm:inline">Profile</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
