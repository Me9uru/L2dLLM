// OpenAI-compatible client for the L2dLLM backend.
//
// Two entry points:
//   listModels()  — GET  /v1/models       → string[]
//   streamChat()  — POST /v1/chat/completions (stream:true)
//                 → async iterable of text deltas
//
// SSE parsing is hand-rolled because EventSource can't issue POSTs. The chunk
// boundary handling is the easy place to break this — keep the line buffer.

import type { ChatMessage } from '../types'

export async function listModels(): Promise<string[]> {
  const res = await fetch('/v1/models')
  if (!res.ok) throw new Error(`listModels: HTTP ${res.status}`)
  const json = (await res.json()) as { data: Array<{ id: string }> }
  return json.data.map((m) => m.id)
}

interface ChatChunk {
  choices: Array<{
    delta?: { content?: string; audio?: string }
    finish_reason?: string | null
  }>
}

export interface StreamResult {
  text: string
  audio?: string
}

/**
 * Stream assistant text deltas from the backend.
 *
 * The generator yields raw text fragments — the caller is responsible for
 * appending them to the live assistant message. Tool calls are invisible:
 * the backend resolves them internally and only streams final assistant text.
 *
 * Also captures audio data if tts is enabled.
 */
export async function* streamChat(
  model: string,
  messages: ChatMessage[],
  signal?: AbortSignal,
  tts: boolean = true,
): AsyncIterable<{ type: 'text' | 'audio'; data: string }> {
  const res = await fetch('/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, messages, stream: true, tts }),
    signal,
  })
  if (!res.ok || !res.body) {
    throw new Error(`streamChat: HTTP ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buf = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })

    // SSE events are separated by blank lines. We may receive partial events
    // (mid-JSON) or several events in one chunk — drain whatever is complete
    // and keep the tail in `buf` for the next iteration.
    let sep: number
    while ((sep = buf.indexOf('\n\n')) !== -1) {
      const rawEvent = buf.slice(0, sep)
      buf = buf.slice(sep + 2)

      // An event can contain multiple `data:` lines; OpenAI's SSE always uses
      // a single line, but be permissive.
      const dataLines = rawEvent
        .split('\n')
        .filter((l) => l.startsWith('data:'))
        .map((l) => l.slice(5).trimStart())
      if (dataLines.length === 0) continue

      const payload = dataLines.join('\n')
      if (payload === '[DONE]') return

      try {
        const chunk = JSON.parse(payload) as ChatChunk
        const delta = chunk.choices?.[0]?.delta
        if (delta?.content) {
          yield { type: 'text', data: delta.content }
        }
        if (delta?.audio) {
          yield { type: 'audio', data: delta.audio }
        }
      } catch {
        // Malformed JSON — skip the event and keep reading.
      }
    }
  }
}
