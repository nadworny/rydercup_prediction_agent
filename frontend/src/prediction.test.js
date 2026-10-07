import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { applyEvent, buildPrompt, readSse, runPrediction } from './prediction.js'

const sample = {
  europe: 'Justin Rose',
  usa: 'Cameron Young',
  europeScore: '11.5',
  usaScore: '4.5',
  context: 'Windy conditions',
}

function stream(...chunks) {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      chunks.forEach((chunk) => controller.enqueue(encoder.encode(chunk)))
      controller.close()
    },
  })
}

beforeEach(() => {
  vi.stubGlobal('crypto', { randomUUID: () => 'fixed-id' })
})

afterEach(() => vi.unstubAllGlobals())

describe('ADK transport', () => {
  it('sends the sample prompt to a fresh session and yields streamed ADK events', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'session-1' }) })
      .mockResolvedValueOnce({
        ok: true,
        body: stream(
          'data: {"author":"PlayerProfilerAgent","partial":true,"content":{"parts":[{"text":"First"}]}}\n\n',
          'data: {"author":"PlayerProfilerAgent","partial":false,"content":{"parts":[{"text":"First result"}]}}\n\n',
        ),
      })
    vi.stubGlobal('fetch', fetchMock)
    const signal = new AbortController().signal
    const events = []
    for await (const event of runPrediction(sample, signal)) events.push(event)

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[0]).toEqual([
      '/apps/ryder_cup_prediction/users/local-fixed-id/sessions',
      expect.objectContaining({ method: 'POST', body: '{}', signal }),
    ])
    const [url, options] = fetchMock.mock.calls[1]
    expect(url).toBe('/run_sse')
    expect(options.signal).toBe(signal)
    expect(options.headers.Accept).toBe('text/event-stream')
    expect(JSON.parse(options.body)).toMatchObject({
      appName: 'ryder_cup_prediction',
      userId: 'local-fixed-id',
      sessionId: 'session-1',
      streaming: true,
      newMessage: { role: 'user', parts: [{ text: expect.stringContaining('Justin Rose (Europe) vs Cameron Young (USA)') }] },
    })
    expect(events).toHaveLength(2)
    expect(buildPrompt(sample)).toContain('Additional context:\nWindy conditions')
  })

  it('parses split UTF-8, CRLF, multi-line data and an unterminated last event', async () => {
    const encoder = new TextEncoder()
    const bytes = encoder.encode('data: {"author":"Rory","content":{"parts":[{"text":"Å"}]}}\r\n\r\ndata: {"author":\ndata: "Rose"}')
    const events = []
    for await (const event of readSse(new ReadableStream({
      start(controller) {
        for (const byte of bytes) controller.enqueue(Uint8Array.of(byte))
        controller.close()
      },
    }))) events.push(event)
    expect(events).toEqual([
      { author: 'Rory', content: { parts: [{ text: 'Å' }] } },
      { author: 'Rose' },
    ])
  })

  it('replaces partial chunks with the aggregated text without duplication', () => {
    const first = applyEvent([], { author: 'PlayerProfilerAgent', partial: true, content: { parts: [{ text: 'Hello' }] } })
    const second = applyEvent(first, { author: 'PlayerProfilerAgent', partial: true, content: { parts: [{ text: ' world' }] } })
    const final = applyEvent(second, { author: 'PlayerProfilerAgent', partial: false, content: { parts: [{ text: 'Hello world' }] } })
    expect(final).toEqual([{ author: 'PlayerProfilerAgent', text: 'Hello world', draft: false }])
    expect(applyEvent(final, { author: 'RecentFormAnalyst', content: { parts: [{ text: 'Form' }] } })).toHaveLength(2)
    expect(applyEvent(final, { author: 'PlayerProfilerAgent', content: { parts: [{ functionCall: {} }, { text: 'Private', thought: true }] } })).toEqual(final)
  })

  it('fails on session errors and streamed errors rather than reporting success', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }))
    await expect(async () => {
      for await (const event of runPrediction(sample)) void event
    }).rejects.toThrow('Session creation failed (HTTP 503)')

    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'session-1' }) })
      .mockResolvedValueOnce({ ok: true, body: stream('data: {"error":"Model unavailable"}\n\n') }))
    await expect(async () => {
      for await (const event of runPrediction(sample)) void event
    }).rejects.toThrow('Model unavailable')
  })
})
