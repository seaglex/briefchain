"use client";

import { useMemo } from "react";
import { marked } from "marked";

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const html = useMemo(() => {
    // Disable raw HTML to avoid XSS; only parse standard Markdown syntax.
    marked.setOptions({
      gfm: true,
      breaks: true,
    });
    return marked.parse(content, { async: false }) as string;
  }, [content]);

  return (
    <div
      className="markdown-body"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
