import React, { useState } from 'react';
import {
  BookOpen,
  Copy,
  Check,
  RefreshCw,
  List,
  Code2,
  CheckCircle2,
  AlertTriangle,
  Info,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

/**
 * Intelligent Markdown Parser into structured Study Guide sections
 */
function parseSummaryMarkdown(markdownText = '') {
  if (!markdownText) return { overview: '', sections: [] };

  const lines = markdownText.split('\n');
  let overview = '';
  const sections = [];
  let currentSection = null;
  let currentSubsection = null;
  let inCodeBlock = false;
  let codeBuffer = [];
  let codeLang = '';

  let tableBuffer = [];
  let inTable = false;

  lines.forEach((line) => {
    const trimmed = line.trim();

    // Code Block Toggles
    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        // Close code block
        const codeText = codeBuffer.join('\n');
        const block = { type: 'code', lang: codeLang || 'text', code: codeText };
        if (currentSubsection) currentSubsection.blocks.push(block);
        else if (currentSection) currentSection.blocks.push(block);
        codeBuffer = [];
        codeLang = '';
        inCodeBlock = false;
      } else {
        // Open code block
        inCodeBlock = true;
        codeLang = trimmed.replace('```', '').trim();
      }
      return;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      return;
    }

    // Markdown Table Detection
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      inTable = true;
      tableBuffer.push(trimmed);
      return;
    } else if (inTable) {
      // Flush table
      const parsedTable = parseMarkdownTable(tableBuffer);
      if (parsedTable) {
        const block = { type: 'table', headers: parsedTable.headers, rows: parsedTable.rows };
        if (currentSubsection) currentSubsection.blocks.push(block);
        else if (currentSection) currentSection.blocks.push(block);
      }
      tableBuffer = [];
      inTable = false;
    }

    // Section H1 / H2 Headers (# or ##)
    if (/^#{1,2}\s+/.test(trimmed)) {
      const title = trimmed.replace(/^#{1,2}\s+/, '').replace(/^[\d.]+\s*/, '').trim();
      if (title.toLowerCase().includes('overview') || title.toLowerCase().includes('introduction') && !overview) {
        // Section header
      }
      currentSection = {
        id: `section-${sections.length + 1}`,
        number: String(sections.length + 1).padStart(2, '0'),
        title,
        subsections: [],
        blocks: [],
      };
      sections.push(currentSection);
      currentSubsection = null;
      return;
    }

    // Subsection H3 Headers (###)
    if (/^#{3,4}\s+/.test(trimmed)) {
      const title = trimmed.replace(/^#{3,4}\s+/, '').trim();
      currentSubsection = {
        title,
        blocks: [],
      };
      if (currentSection) {
        currentSection.subsections.push(currentSubsection);
      }
      return;
    }

    // Horizontal Rules
    if (trimmed === '---' || trimmed === '***') {
      return;
    }

    if (!trimmed) return;

    // Bullet Points
    if (/^[\*\-\+]\s+/.test(trimmed) || /^\d+\.\s+/.test(trimmed)) {
      const text = trimmed.replace(/^[\*\-\+]\s+/, '').replace(/^\d+\.\s+/, '');
      const block = { type: 'bullet', text };

      if (currentSubsection) currentSubsection.blocks.push(block);
      else if (currentSection) currentSection.blocks.push(block);
      else if (!overview) overview = text;
      return;
    }

    // Regular Paragraph
    const block = { type: 'text', text: trimmed };
    if (currentSubsection) {
      currentSubsection.blocks.push(block);
    } else if (currentSection) {
      currentSection.blocks.push(block);
    } else {
      if (!overview) overview = trimmed;
      else overview += ' ' + trimmed;
    }
  });

  // Flush trailing table if any
  if (inTable && tableBuffer.length > 0) {
    const parsedTable = parseMarkdownTable(tableBuffer);
    if (parsedTable && currentSection) {
      currentSection.blocks.push({ type: 'table', headers: parsedTable.headers, rows: parsedTable.rows });
    }
  }

  return { overview, sections };
}

function parseMarkdownTable(lines) {
  if (lines.length < 2) return null;
  const rows = lines.map((l) => l.split('|').map((cell) => cell.trim()).filter((_, idx, arr) => idx > 0 && idx < arr.length - 1));
  const headers = rows[0];
  const dataRows = rows.slice(2); // skip header separator line
  return { headers, rows: dataRows };
}

export function StructuredSummaryViewer({
  summaryData,
  resourceTitle,
  onRegenerate,
  isRegenerating,
}) {
  const [copied, setCopied] = useState(false);
  const [copiedCodeIdx, setCopiedCodeIdx] = useState(null);

  const summaryText = summaryData?.summary || summaryData?.summary_text || '';
  const isCached = summaryData?.cached ?? true;
  const createdAt = summaryData?.created_at ? new Date(summaryData.created_at).toLocaleDateString() : 'Recently';

  const { overview, sections } = parseSummaryMarkdown(summaryText);
  const wordCount = summaryText ? summaryText.trim().split(/\s+/).filter(Boolean).length : 0;

  const handleCopyFullSummary = () => {
    if (!summaryText) return;
    navigator.clipboard.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyCode = (code, idx) => {
    navigator.clipboard.writeText(code);
    setCopiedCodeIdx(idx);
    setTimeout(() => setCopiedCodeIdx(null), 2000);
  };

  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header Card & Control Actions */}
      <div className="bg-[#0d1420] rounded-2xl p-6 border border-white/[0.07] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3 className="text-xl font-bold text-[#f5f7fa]">
              {resourceTitle || 'Material Study Guide'}
            </h3>
            <Badge variant="primary">
              AI Summary Guide
            </Badge>
          </div>
          <p className="text-xs text-[#9ca8ba]">
            Generated {createdAt} &bull; ~{wordCount} words &bull; {sections.length} core sections
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" icon={copied ? Check : Copy} onClick={handleCopyFullSummary}>
            {copied ? 'Copied' : 'Copy Guide'}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={RefreshCw}
            onClick={() => onRegenerate && onRegenerate(true)}
            isLoading={isRegenerating}
          >
            Regenerate Fresh
          </Button>
        </div>
      </div>

      {/* 2. "At a Glance" Executive Overview Card */}
      {overview && (
        <div className="relative overflow-hidden rounded-2xl bg-[#101827] border border-blue-500/30 p-6 text-[#f5f7fa] shadow-md">
          <div className="relative z-10">
            <div className="flex items-center gap-2 text-blue-400 font-bold text-xs uppercase tracking-wider mb-2">
              <Sparkles className="w-4 h-4" />
              <span>At a Glance Overview</span>
            </div>
            <p className="text-sm md:text-base leading-relaxed text-[#f5f7fa] font-medium">
              {overview}
            </p>
          </div>
        </div>
      )}

      {/* 3. Compact Table of Contents Navigation Bar */}
      {sections.length > 0 && (
        <div className="bg-[#0a0f18] p-4 rounded-xl border border-white/[0.07]">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
            <List className="w-3.5 h-3.5" />
            <span>Table of Contents</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {sections.map((sec) => (
              <button
                key={sec.id}
                onClick={() => scrollToSection(sec.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0d1420] border border-white/[0.08] text-xs text-[#9ca8ba] font-medium hover:border-blue-500/40 hover:text-[#f5f7fa] transition-colors"
              >
                <span className="font-mono text-[11px] font-bold text-blue-400">
                  {sec.number}
                </span>
                <span className="truncate max-w-[180px]">{sec.title}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 4. Structured Sections List */}
      <div className="space-y-8">
        {sections.map((sec) => (
          <div
            key={sec.id}
            id={sec.id}
            className="bg-[#0d1420] rounded-2xl p-6 md:p-8 border border-white/[0.07] shadow-sm scroll-mt-6"
          >
            {/* Section Header */}
            <div className="flex items-center gap-3 pb-4 border-b border-white/[0.07] mb-6">
              <span className="w-9 h-9 rounded-xl bg-blue-600/10 text-blue-400 font-mono font-extrabold text-sm flex items-center justify-center shrink-0 border border-blue-500/20">
                {sec.number}
              </span>
              <h3 className="text-lg font-bold text-[#f5f7fa]">
                {sec.title}
              </h3>
            </div>

            {/* Direct Section Blocks */}
            <RenderBlocks blocks={sec.blocks} onCopyCode={handleCopyCode} copiedCodeIdx={copiedCodeIdx} />

            {/* Subsections */}
            {sec.subsections.map((sub, sIdx) => (
              <div key={sIdx} className="mt-6 pt-4 border-t border-white/[0.05]">
                <h4 className="text-sm font-bold text-[#f5f7fa] mb-3 flex items-center gap-2">
                  <ChevronRight className="w-4 h-4 text-blue-400 shrink-0" />
                  <span>{sub.title}</span>
                </h4>
                <RenderBlocks blocks={sub.blocks} onCopyCode={handleCopyCode} copiedCodeIdx={copiedCodeIdx} />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Block Renderer for Text, Bullets, Code Blocks, Callouts, and Tables
 */
function RenderBlocks({ blocks = [], onCopyCode, copiedCodeIdx }) {
  if (!blocks || blocks.length === 0) return null;

  return (
    <div className="space-y-4">
      {blocks.map((block, idx) => {
        if (block.type === 'bullet') {
          // Identify semantic callouts (Key Concept, Note, Warning)
          const lower = block.text.toLowerCase();
          if (lower.startsWith('key concept:') || lower.startsWith('important:')) {
            return (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-blue-50/60 dark:bg-blue-950/40 border-l-4 border-l-blue-500 text-xs text-slate-800 dark:text-slate-200 flex items-start gap-2.5"
              >
                <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed font-medium">{block.text}</span>
              </div>
            );
          }

          if (lower.startsWith('best practice:') || lower.startsWith('recommendation:')) {
            return (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-green-50/60 dark:bg-green-950/40 border-l-4 border-l-green-500 text-xs text-slate-800 dark:text-slate-200 flex items-start gap-2.5"
              >
                <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed font-medium">{block.text}</span>
              </div>
            );
          }

          if (lower.startsWith('warning:') || lower.startsWith('common mistake:')) {
            return (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-amber-50/60 dark:bg-amber-950/40 border-l-4 border-l-amber-500 text-xs text-slate-800 dark:text-slate-200 flex items-start gap-2.5"
              >
                <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed font-medium">{block.text}</span>
              </div>
            );
          }

          return (
            <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0 mt-1.5" />
              <span>{block.text}</span>
            </div>
          );
        }

        if (block.type === 'code') {
          const codeKey = `${idx}-${block.code.slice(0, 10)}`;
          return (
            <div
              key={idx}
              className="rounded-xl bg-slate-900 text-slate-100 border border-slate-800 overflow-hidden font-mono text-xs shadow-inner"
            >
              <div className="px-4 py-2 bg-slate-950 border-b border-slate-800/80 flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Code2 className="w-3.5 h-3.5 text-blue-400" />
                  <span>{block.lang || 'code'}</span>
                </span>
                <button
                  onClick={() => onCopyCode(block.code, codeKey)}
                  className="p-1 rounded text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1 text-[11px]"
                >
                  {copiedCodeIdx === codeKey ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-green-400" />
                      <span className="text-green-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="p-4 overflow-x-auto text-xs leading-relaxed whitespace-pre font-mono selection:bg-blue-500 selection:text-white">
                <code>{block.code}</code>
              </pre>
            </div>
          );
        }

        if (block.type === 'table') {
          return (
            <div key={idx} className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 my-4">
              <table className="w-full text-xs text-left text-slate-800 dark:text-slate-200">
                <thead className="bg-slate-50 dark:bg-slate-900/60 uppercase font-bold text-[11px] text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    {block.headers.map((h, hIdx) => (
                      <th key={hIdx} className="px-4 py-3">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                  {block.rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-50/50 dark:hover:bg-slate-700/30">
                      {row.map((cell, cIdx) => (
                        <td key={cIdx} className="px-4 py-3">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }

        return (
          <p key={idx} className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
            {block.text}
          </p>
        );
      })}
    </div>
  );
}
