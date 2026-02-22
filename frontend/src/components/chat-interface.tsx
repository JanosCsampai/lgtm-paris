"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ChevronLeft, Search } from "lucide-react";
import { sendChatMessage } from "@/lib/api";
import { DistanceSlider } from "@/components/distance-slider";
import type { ChatMessage } from "@/lib/types";

interface ChatInterfaceProps {
  initialQuery: string;
  lat: number;
  lng: number;
  distance: number;
  onDistanceChange: (d: number) => void;
  onReset: () => void;
}

export function ChatInterface({
  initialQuery,
  lat,
  lng,
  distance,
  onDistanceChange,
  onReset,
}: ChatInterfaceProps) {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isNavigating, setIsNavigating] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const hasStarted = useRef(false);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  useEffect(() => {
    if (!isLoading && !isNavigating) {
      inputRef.current?.focus();
    }
  }, [isLoading, isNavigating, messages]);

  const navigateToSearch = useCallback(
    (query: string) => {
      setIsNavigating(true);
      const params = new URLSearchParams({
        q: query,
        lat: String(lat),
        lng: String(lng),
        radius: String(distance * 1000),
      });
      router.push(`/results?${params.toString()}`);
    },
    [lat, lng, distance, router]
  );

  const sendMessage = useCallback(
    async (allMessages: ChatMessage[]) => {
      setIsLoading(true);
      try {
        const response = await sendChatMessage(allMessages);

        if (response.status === "ready" && response.search_query) {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: response.message },
          ]);
          setTimeout(() => navigateToSearch(response.search_query!), 800);
        } else {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: response.message },
          ]);
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Something went wrong. Let me search with what I have.",
          },
        ]);
        const lastUserMsg = allMessages.findLast((m) => m.role === "user");
        if (lastUserMsg) {
          setTimeout(() => navigateToSearch(lastUserMsg.content), 1000);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [navigateToSearch]
  );

  useEffect(() => {
    if (hasStarted.current || !initialQuery) return;
    hasStarted.current = true;
    const firstMessages: ChatMessage[] = [
      { role: "user", content: initialQuery },
    ];
    setMessages(firstMessages);
    sendMessage(firstMessages);
  }, [initialQuery, sendMessage]);

  const handleSubmit = useCallback(() => {
    const text = input.trim();
    if (!text || isLoading) return;
    const newMessages: ChatMessage[] = [
      ...messages,
      { role: "user", content: text },
    ];
    setMessages(newMessages);
    setInput("");
    sendMessage(newMessages);
  }, [input, isLoading, messages, sendMessage]);

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Top bar */}
      <div className="flex shrink-0 items-center justify-between border-b border-border/50 px-5 py-3">
        <button
          onClick={onReset}
          className="flex items-center gap-1 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </button>
        <span className="text-[13px] font-medium text-muted-foreground">
          Let&apos;s find your service
        </span>
        <div className="w-12" />
      </div>

      {/* Messages — scrollable, centred column */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto scroll-smooth">
        <div className="mx-auto flex max-w-xl flex-col gap-3 px-5 py-8">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={[
                  "max-w-[78%] rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed",
                  "animate-in fade-in slide-in-from-bottom-2 duration-200",
                  msg.role === "user"
                    ? "rounded-br-sm bg-primary text-primary-foreground"
                    : "rounded-bl-sm bg-muted text-foreground",
                ].join(" ")}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2 duration-200">
              <div className="flex items-center gap-1 rounded-2xl rounded-bl-sm bg-muted px-4 py-3">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:0ms]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:160ms]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:320ms]" />
              </div>
            </div>
          )}

          {/* Navigating state */}
          {isNavigating && (
            <div className="flex justify-center pt-1 animate-in fade-in duration-300">
              <div className="flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-[13px] font-medium text-primary">
                <Search className="h-3.5 w-3.5 animate-pulse" />
                Searching providers near you…
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input bar — pinned to bottom */}
      <div className="shrink-0 border-t border-border/50 bg-background">
        <div className="mx-auto max-w-xl px-5 py-4">
          <div className="flex items-center gap-3 rounded-full border border-border bg-white px-5 py-3 shadow-[0_2px_12px_rgba(0,0,0,0.06)] transition-shadow focus-within:border-primary/25 focus-within:shadow-[0_4px_20px_rgba(0,0,0,0.10)]">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && input.trim()) handleSubmit();
              }}
              placeholder="Type your answer…"
              disabled={isLoading || isNavigating}
              className="flex-1 bg-transparent text-[15px] text-foreground placeholder:text-muted-foreground/50 focus:outline-none disabled:opacity-40"
            />
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || isLoading || isNavigating}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-all hover:scale-105 hover:bg-primary/90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:scale-100"
            >
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-3 flex justify-center">
            <DistanceSlider value={distance} onChange={onDistanceChange} />
          </div>
        </div>
      </div>
    </div>
  );
}
