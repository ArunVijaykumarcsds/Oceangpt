"use client";

import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { ChatMessage, SourceRef } from "@/lib/types";
import { SourceList } from "./SourceList";

interface DisplayMessage extends ChatMessage {
  sources?: SourceRef[];
  isError?: boolean;
}

const SUGGESTED_PROMPTS = [
  "Where has the green sea turtle been observed recently?",
  "What's the current tide at San Francisco (station 9414290)?",
  "What is ocean acidification?",
  "Give me the wave forecast near 25.46, -80.12",
];

export function ChatPanel() {
  const [messages, setMessages] = useState<DisplayMessage[]>([
    {
      role: "assistant",
      content:
        "I'm OceanGPT. Ask me about marine species, taxonomy, or current ocean conditions — I can pull live data from OBIS, WoRMS, NOAA, and Open-Meteo Marine, or draw on my own reference knowledge.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isLoading]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await api.chat(trimmed, history);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.reply, sources: res.sources },
      ]);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? `Something went wrong reaching the backend: ${err.message}`
          : "Couldn't reach the OceanGPT backend. Is it running on port 8000?";
      setMessages((prev) => [...prev, { role: "assistant", content: message, isError: true }]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full bg-abyss-900/60 border border-line-soft rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-line-soft flex items-center justify-between">
        <span className="font-display text-sm font-semibold text-text-primary">Research Assistant</span>
        <span className="font-mono text-[10px] text-text-tertiary">RAG + LIVE TOOLS</span>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        {isLoading && <TypingIndicator />}
      </div>

      {messages.length <= 1 && (
        <div className="px-4 pb-2 flex flex-wrap gap-1.5">
          {SUGGESTED_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => sendMessage(prompt)}
              className="font-mono text-[11px] text-text-secondary border border-line rounded-full px-3 py-1.5 hover:border-bio-500 hover:text-bio-400 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage(input);
        }}
        className="p-3 border-t border-line-soft flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about species, tides, or ocean conditions..."
          className="flex-1 bg-abyss-800 border border-line rounded-lg px-3 py-2.5 text-sm text-text-primary placeholder:text-text-tertiary focus:border-bio-500 outline-none transition-colors"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="font-mono text-xs font-medium bg-bio-500 text-abyss-950 rounded-lg px-4 py-2.5 hover:bg-bio-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}

function MessageBubble({ message }: { message: DisplayMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        <div
          className={`rounded-xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-bio-500 text-abyss-950 font-medium"
              : message.isError
              ? "bg-coral-500/10 border border-coral-500/30 text-coral-400"
              : "bg-abyss-800 border border-line-soft text-text-primary"
          }`}
        >
          {message.content}
        </div>
        {message.sources && <SourceList sources={message.sources} />}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-abyss-800 border border-line-soft rounded-xl px-4 py-3 flex gap-1.5 items-center">
        <span className="w-1.5 h-1.5 rounded-full bg-bio-500 animate-pulse-glow" style={{ animationDelay: "0ms" }} />
        <span className="w-1.5 h-1.5 rounded-full bg-bio-500 animate-pulse-glow" style={{ animationDelay: "200ms" }} />
        <span className="w-1.5 h-1.5 rounded-full bg-bio-500 animate-pulse-glow" style={{ animationDelay: "400ms" }} />
      </div>
    </div>
  );
}
