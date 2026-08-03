"use client"

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

export function Markdown({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className="prose prose-sm dark:prose-invert max-w-none
        prose-headings:font-semibold prose-headings:tracking-tight
        prose-h1:text-lg prose-h2:text-base prose-h3:text-sm
        prose-p:leading-relaxed prose-p:my-1.5
        prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5
        prose-table:text-xs prose-th:py-1.5 prose-td:py-1.5
        prose-pre:bg-muted prose-pre:text-foreground prose-pre:text-xs
        prose-code:text-xs prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded
        prose-a:text-primary prose-a:no-underline hover:prose-a:underline
        prose-strong:text-foreground
        prose-blockquote:border-primary/30 prose-blockquote:text-muted-foreground"
      components={{
        table: ({ children }) => (
          <div className="overflow-x-auto my-2">
            <table className="w-full">{children}</table>
          </div>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}
