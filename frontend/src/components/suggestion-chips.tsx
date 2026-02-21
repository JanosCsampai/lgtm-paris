"use client";

import { SUGGESTION_CHIPS } from "@/lib/constants";

interface SuggestionChipsProps {
  onSelect: (query: string) => void;
}

export function SuggestionChips({ onSelect }: SuggestionChipsProps) {
  return (
    <div className="flex flex-wrap justify-center gap-1.5">
      {SUGGESTION_CHIPS.map((chip) => (
        <button
          key={chip}
          onClick={() => onSelect(chip)}
          className="rounded-full border border-border bg-white px-3.5 py-1.5 text-[13px] text-foreground/75 transition-all hover:border-primary/30 hover:text-primary hover:shadow-sm active:scale-[0.97]"
        >
          {chip}
        </button>
      ))}
    </div>
  );
}
