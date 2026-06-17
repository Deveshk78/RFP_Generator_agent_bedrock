"use client";

import { useEffect, useId, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function MermaidDiagram({ chart }: { chart: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const id = useId().replace(/:/g, "");

  useEffect(() => {
    let cancelled = false;
    import("mermaid").then((mermaid) => {
      if (cancelled || !containerRef.current) return;
      mermaid.default.initialize({
        startOnLoad: false,
        theme: "neutral",
        securityLevel: "loose",
      });
      mermaid.default
        .render(`mmd-${id}`, chart.trim())
        .then(({ svg }) => {
          if (!cancelled && containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        })
        .catch(() => {
          if (containerRef.current) {
            containerRef.current.innerHTML = `<pre class="text-xs p-2 bg-muted rounded">${chart}</pre>`;
          }
        });
    });
    return () => {
      cancelled = true;
    };
  }, [chart, id]);

  return (
    <div
      ref={containerRef}
      className="my-3 overflow-x-auto rounded-lg border bg-white p-3 [&_svg]:max-w-full"
    />
  );
}

const proseClass =
  "prose prose-slate max-w-none prose-headings:scroll-mt-20 prose-p:leading-relaxed prose-li:my-0.5 prose-table:text-sm prose-th:bg-muted prose-th:px-3 prose-th:py-2 prose-td:px-3 prose-td:py-2 text-sm sm:text-base";

export function MarkdownView({ content }: { content: string }) {
  return (
    <div className={proseClass}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}

export function ChatMarkdownView({ content }: { content: string }) {
  return (
    <div className={`${proseClass} prose-sm`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const lang = match?.[1];
            const code = String(children).replace(/\n$/, "");
            if (lang === "mermaid") {
              return <MermaidDiagram chart={code} />;
            }
            if (className) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className="rounded bg-black/10 px-1 py-0.5 text-xs" {...props}>
                {children}
              </code>
            );
          },
          img({ src, alt }) {
            return (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={src}
                alt={alt ?? "Diagram"}
                className="my-3 max-w-full rounded-lg border"
              />
            );
          },
          table({ children }) {
            return (
              <div className="my-3 overflow-x-auto rounded-lg border">
                <table className="min-w-full">{children}</table>
              </div>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
