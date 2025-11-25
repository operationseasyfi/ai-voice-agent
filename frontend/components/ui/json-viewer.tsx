"use client"

import { cn } from "@/lib/utils"

interface JsonViewerProps {
  data: any
  className?: string
}

export function JsonViewer({ data, className }: JsonViewerProps) {
  const syntaxHighlight = (json: string) => {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

    return json.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      (match) => {
        let cls = 'text-warning' // numbers
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = 'text-primary font-semibold' // keys
          } else {
            cls = 'text-success' // strings
          }
        } else if (/true|false/.test(match)) {
          cls = 'text-destructive' // booleans
        } else if (/null/.test(match)) {
          cls = 'text-muted-foreground' // null
        }
        return '<span class="' + cls + '">' + match + '</span>'
      }
    )
  }

  const formattedJson = JSON.stringify(data, null, 2)
  const highlightedJson = syntaxHighlight(formattedJson)

  return (
    <pre
      className={cn(
        "rounded-md border bg-muted/20 p-4 text-xs overflow-x-auto font-mono",
        className
      )}
    >
      <code
        dangerouslySetInnerHTML={{ __html: highlightedJson }}
        className="block"
      />
    </pre>
  )
}
