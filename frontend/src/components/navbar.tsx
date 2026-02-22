"use client";

import Link from "next/link";
import { User } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b-2 border-[#003888] bg-white">
      <div className="flex h-14 items-center justify-between px-5 sm:px-6 lg:px-8">
        <Link href="/">
          <img
            src="/navbar-logo.svg"
            alt="Plumline"
            className="h-12 w-auto shrink-0"
          />
        </Link>

        <nav className="flex items-center gap-1">
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
