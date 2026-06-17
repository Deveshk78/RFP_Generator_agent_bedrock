"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Mic, MicOff, Send } from "lucide-react";
import { ChatMarkdownView } from "@/components/markdown-view";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type ChatMessage = { role: string; content: string };

type SpeechRecognitionCtor = new () => SpeechRecognitionInstance;

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
}

interface SpeechRecognitionEvent {
  results: { [index: number]: { [index: number]: { transcript: string } } };
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  }
}

export function RfpChatPanel({
  rfpId,
  initialMessages,
  onError,
}: {
  rfpId: string;
  initialMessages: ChatMessage[];
  onError: (msg: string) => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const transcriptRef = useRef("");

  useEffect(() => {
    setMessages(initialMessages);
  }, [initialMessages]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatLoading]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    setSpeechSupported(!!SpeechRecognition);
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = "en-US";
      recognitionRef.current = rec;
    }
    return () => {
      recognitionRef.current?.stop();
    };
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const userMsg = text.trim();
      if (!userMsg || chatLoading) return;

      setChatInput("");
      setMessages((m) => [...m, { role: "user", content: userMsg }]);
      setChatLoading(true);
      onError("");

      try {
        const { reply } = await api.sendChat(rfpId, userMsg);
        setMessages((m) => [...m, { role: "assistant", content: reply }]);
      } catch (err) {
        onError(err instanceof Error ? err.message : "Chat failed");
      } finally {
        setChatLoading(false);
      }
    },
    [chatLoading, onError, rfpId]
  );

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    sendMessage(chatInput);
  }

  function toggleVoice() {
    const rec = recognitionRef.current;
    if (!rec) {
      onError("Voice input is not supported in this browser. Try Chrome or Safari.");
      return;
    }

    if (listening) {
      rec.stop();
      setListening(false);
      return;
    }

    rec.onresult = (event) => {
      const transcript = Array.from({ length: event.results.length })
        .map((_, i) => event.results[i][0].transcript)
        .join("");
      transcriptRef.current = transcript;
      setChatInput(transcript);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => {
      setListening(false);
      const text = transcriptRef.current.trim();
      transcriptRef.current = "";
      if (text) sendMessage(text);
    };

    setListening(true);
    rec.start();
  }

  return (
    <div className="space-y-4">
      <ScrollArea className="h-[min(55vh,480px)] rounded-lg border bg-slate-50/50 p-4">
        <div className="space-y-4 pr-2">
          {messages.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Ask about requirements, compliance, deadlines, or proposal strategy. Use the mic for
              voice input.
            </p>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={cn(
                "flex",
                msg.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              <div
                className={cn(
                  "max-w-[92%] rounded-xl px-4 py-3 shadow-sm",
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-white border"
                )}
              >
                {msg.role === "user" ? (
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <ChatMarkdownView content={msg.content} />
                )}
              </div>
            </div>
          ))}
          {chatLoading && (
            <div className="flex items-center gap-2 text-muted-foreground text-sm pl-1">
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing and formatting response...
            </div>
          )}
          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      <form onSubmit={handleSubmit} className="flex gap-2">
        {speechSupported && (
          <Button
            type="button"
            size="icon"
            variant={listening ? "destructive" : "outline"}
            onClick={toggleVoice}
            disabled={chatLoading}
            title={listening ? "Stop listening" : "Voice input"}
            className="shrink-0"
          >
            {listening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </Button>
        )}
        <Input
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          placeholder={listening ? "Listening..." : "Ask a question or use the mic..."}
          disabled={chatLoading || listening}
          className="flex-1"
        />
        <Button type="submit" size="icon" disabled={chatLoading || !chatInput.trim()} className="shrink-0">
          <Send className="h-4 w-4" />
        </Button>
      </form>
      {listening && (
        <p className="text-xs text-primary animate-pulse">Listening — speak your question...</p>
      )}
    </div>
  );
}
