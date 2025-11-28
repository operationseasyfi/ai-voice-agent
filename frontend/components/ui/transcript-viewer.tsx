"use client"

import { useMemo } from "react"

// Keyword categories for highlighting
const KEYWORD_PATTERNS = {
  money: {
    pattern: /\$[\d,]+(?:\.\d{2})?|\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|thousand|k|grand)/gi,
    className: "bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 px-0.5 rounded font-medium",
    label: "Money"
  },
  debt: {
    pattern: /\b(?:debt|owe|owing|creditor|collection|balance|outstanding|delinquent|past due|charged off|default)\b/gi,
    className: "bg-purple-500/20 text-purple-700 dark:text-purple-300 px-0.5 rounded",
    label: "Debt"
  },
  income: {
    pattern: /\b(?:income|salary|wage|earn|make|paycheck|monthly|weekly|hourly|job|work|employed|employment|unemployed)\b/gi,
    className: "bg-blue-500/20 text-blue-700 dark:text-blue-300 px-0.5 rounded",
    label: "Income"
  },
  hardship: {
    pattern: /\b(?:hardship|struggle|struggling|difficult|trouble|behind|late|can't pay|cannot pay|missed|medical|hospital|surgery|lost job|laid off|divorce|death)\b/gi,
    className: "bg-orange-500/20 text-orange-700 dark:text-orange-300 px-0.5 rounded",
    label: "Hardship"
  },
  objection: {
    pattern: /\b(?:not interested|no thank|hang up|stop calling|busy|bad time|call back|later|too much|expensive|scam|fraud|not real|legitimate)\b/gi,
    className: "bg-red-500/20 text-red-700 dark:text-red-300 px-0.5 rounded",
    label: "Objection"
  },
  dnc: {
    pattern: /\b(?:do not call|don't call|stop calling|remove|take me off|no more calls|never call|attorney|lawyer|sue|harassment|report|ftc|fcc|complaint)\b/gi,
    className: "bg-red-600/30 text-red-800 dark:text-red-200 px-0.5 rounded font-semibold border border-red-500/50",
    label: "DNC"
  },
  positive: {
    pattern: /\b(?:yes|interested|help|need|want|agree|okay|transfer|connect|speak|talk to|qualify|eligible)\b/gi,
    className: "bg-green-500/20 text-green-700 dark:text-green-300 px-0.5 rounded",
    label: "Positive"
  }
}

interface TranscriptViewerProps {
  transcript: string | null | undefined
  showLegend?: boolean
  className?: string
}

export function TranscriptViewer({ transcript, showLegend = true, className = "" }: TranscriptViewerProps) {
  const highlightedTranscript = useMemo(() => {
    if (!transcript) return null
    
    // Split transcript into segments and highlight keywords
    let result = transcript
    const highlights: Array<{ start: number; end: number; type: string; text: string }> = []
    
    // Find all matches for each pattern
    Object.entries(KEYWORD_PATTERNS).forEach(([type, { pattern }]) => {
      const regex = new RegExp(pattern.source, pattern.flags)
      let match
      while ((match = regex.exec(transcript)) !== null) {
        highlights.push({
          start: match.index,
          end: match.index + match[0].length,
          type,
          text: match[0]
        })
      }
    })
    
    // Sort by position (reverse to process from end to start)
    highlights.sort((a, b) => b.start - a.start)
    
    // Apply highlights (processing from end to not mess up indices)
    highlights.forEach(({ start, end, type, text }) => {
      const before = result.slice(0, start)
      const after = result.slice(end)
      const className = KEYWORD_PATTERNS[type as keyof typeof KEYWORD_PATTERNS].className
      result = `${before}<span class="${className}">${text}</span>${after}`
    })
    
    return result
  }, [transcript])

  if (!transcript) {
    return (
      <div className={`p-4 text-center text-muted-foreground bg-muted/50 rounded-lg ${className}`}>
        No transcript available
      </div>
    )
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {showLegend && (
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="text-muted-foreground">Keywords:</span>
          {Object.entries(KEYWORD_PATTERNS).map(([key, { className: colorClass, label }]) => (
            <span key={key} className={`${colorClass} px-1.5 py-0.5`}>
              {label}
            </span>
          ))}
        </div>
      )}
      <div 
        className="p-4 bg-muted/30 rounded-lg text-sm leading-relaxed whitespace-pre-wrap font-mono"
        dangerouslySetInnerHTML={{ __html: highlightedTranscript || transcript }}
      />
    </div>
  )
}

// Export keyword patterns for use elsewhere
export { KEYWORD_PATTERNS }

