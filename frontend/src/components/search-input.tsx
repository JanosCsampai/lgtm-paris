"use client";

import { MapPin, ArrowRight, Loader2 } from "lucide-react";
import { forwardRef } from "react";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  isLoading?: boolean;
}

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  function SearchInput({ value, onChange, onSubmit, placeholder, isLoading }, ref) {
    return (
      <div className="flex w-full items-center gap-3 rounded-full border border-border bg-white px-5 py-3 shadow-[0_2px_12px_rgba(0,0,0,0.06)] transition-shadow focus-within:shadow-[0_4px_20px_rgba(0,0,0,0.10)] focus-within:border-primary/25">
        <MapPin className="h-[18px] w-[18px] shrink-0 text-muted-foreground/70" />
        <input
          ref={ref}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && value.trim() && !isLoading) onSubmit();
          }}
          placeholder={placeholder ?? "e.g. Screen repair under £100 near me"}
          disabled={isLoading}
          className="flex-1 bg-transparent text-[15px] text-foreground placeholder:text-muted-foreground/50 focus:outline-none disabled:opacity-60"
        />
        <button
          onClick={onSubmit}
          disabled={!value.trim() || isLoading}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-all hover:bg-primary/90 hover:scale-105 active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <ArrowRight className="h-4 w-4" />
          )}
        </button>
      </div>
    );
  }
);
