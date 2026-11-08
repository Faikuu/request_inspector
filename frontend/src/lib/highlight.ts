import type { CapturedRequest } from '@/api/types'

export type JsonTokenType = 'key' | 'string' | 'number' | 'boolean' | 'null' | 'punct' | 'ws'
export interface JsonToken {
  t: JsonTokenType
  v: string
}
export type BodyKind = 'json' | 'text' | 'form' | 'binary' | 'empty'

// Sticky patterns, tested at the current position. Tokens always concatenate back to the input,
// and any character no rule matches becomes a one-character punct token, so the scan cannot stall.
const RULES: [JsonTokenType, RegExp][] = [
  ['ws', /\s+/y],
  ['key', /"(?:[^"\\\n]|\\.)*"(?=\s*:)/y],
  ['string', /"(?:[^"\\\n]|\\.)*"/y],
  ['number', /-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/y],
  ['boolean', /(?:true|false)/y],
  ['null', /null/y],
  ['punct', /[{}[\],:]/y],
]

/**
 * Lexes already pretty-printed JSON into tokens for colouring. Output is rendered as text
 * nodes in a template; never feed it to v-html, since payloads are attacker-controlled.
 */
export function tokenizeJson(text: string): JsonToken[] {
  const out: JsonToken[] = []
  let pos = 0
  while (pos < text.length) {
    let matched: JsonToken | null = null
    for (const [t, re] of RULES) {
      re.lastIndex = pos
      const m = re.exec(text)
      if (m) {
        matched = { t, v: m[0] }
        break
      }
    }
    const tok: JsonToken = matched ?? { t: 'punct', v: text.charAt(pos) }
    out.push(tok)
    pos += tok.v.length
  }
  return out
}

/** Readable text for a captured body, plus how it should be displayed. */
export function prettyBody(req: CapturedRequest): { kind: BodyKind; text: string } {
  if (req.body_base64) {
    return {
      kind: 'binary',
      text: `Binary body, ${req.size} bytes (base64 shown)\n\n${req.body_base64}`,
    }
  }
  const body = req.body ?? ''
  if (!body) return { kind: 'empty', text: '' }

  const ct = (req.content_type ?? req.headers['content-type'] ?? '').toLowerCase()
  const looksJson = ct.includes('json') || (!ct && /^\s*[[{]/.test(body))
  if (looksJson) {
    try {
      return { kind: 'json', text: JSON.stringify(JSON.parse(body), null, 2) }
    } catch {
      // Not valid JSON after all; show it as text.
    }
  }

  if (ct.startsWith('application/x-www-form-urlencoded')) {
    const lines: string[] = []
    new URLSearchParams(body).forEach((value, key) => lines.push(`${key} = ${value}`))
    return { kind: 'form', text: lines.join('\n') }
  }

  return { kind: 'text', text: body }
}
