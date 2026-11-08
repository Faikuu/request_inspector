import type { CapturedRequest } from '@/api/types'

export type SnippetId = 'curl' | 'fetch' | 'python' | 'httpie'

export interface SendSnippet {
  id: SnippetId
  label: string
  code: string
}

/** Wrap a value in single quotes for a POSIX shell, escaping embedded quotes as '\''. */
function sh(value: string): string {
  return "'" + value.split("'").join("'\\''") + "'"
}

/** The request path followed by its query string, e.g. "/orders/42?expand=1". */
export function pathWithQuery(req: Pick<CapturedRequest, 'path' | 'query'>): string {
  const parts: string[] = []
  for (const [key, values] of Object.entries(req.query)) {
    for (const value of values) {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    }
  }
  return parts.length ? `${req.path}?${parts.join('&')}` : req.path
}

const SAMPLE_BODY = { event: 'order.created', id: 42 }

/** Snippets that send a sample JSON POST to the capture URL. */
export function sendSnippets(url: string): SendSnippet[] {
  const json = JSON.stringify(SAMPLE_BODY)
  return [
    {
      id: 'curl',
      label: 'curl',
      code: [
        `curl -X POST ${sh(url)} \\`,
        `  -H ${sh('Content-Type: application/json')} \\`,
        `  -d ${sh(json)}`,
      ].join('\n'),
    },
    {
      id: 'fetch',
      label: 'fetch',
      code: [
        `await fetch(${JSON.stringify(url)}, {`,
        `  method: 'POST',`,
        `  headers: { 'Content-Type': 'application/json' },`,
        `  body: JSON.stringify(${json}),`,
        `})`,
      ].join('\n'),
    },
    {
      id: 'python',
      label: 'Python',
      code: [
        `import requests`,
        ``,
        `requests.post(`,
        `    ${JSON.stringify(url)},`,
        `    json=${json},`,
        `)`,
      ].join('\n'),
    },
    {
      id: 'httpie',
      label: 'HTTPie',
      code: `http POST ${sh(url)} event=order.created id:=42`,
    },
  ]
}

/** Headers that describe the original connection rather than the payload. */
const SKIPPED_HEADERS = new Set(['host', 'content-length', 'connection', 'accept-encoding'])

/** Reproduce a captured request as a runnable curl command aimed at `url` (the capture URL). */
export function toCurl(req: CapturedRequest, url: string): string {
  const pq = pathWithQuery(req)
  const full = url + (pq === '/' ? '' : pq)
  const lines = [`curl -X ${req.method} ${sh(full)}`]

  for (const [name, value] of Object.entries(req.headers)) {
    const lower = name.toLowerCase()
    if (SKIPPED_HEADERS.has(lower) || lower.startsWith('x-forwarded-')) continue
    lines.push(`  -H ${sh(`${name}: ${value}`)}`)
  }

  let comment = ''
  if (req.body_base64) {
    comment = '# Binary body: decode the captured payload into body.bin, then send it.\n'
    lines.push('  --data-binary @body.bin')
  } else if (req.body) {
    lines.push(`  --data-raw ${sh(req.body)}`)
  }

  return comment + lines.join(' \\\n')
}
