const APP_NAME = 'ryder_cup_prediction'

export function buildPrompt({ europe, usa, europeScore, usaScore, context }) {
  return `Analyze the Sunday singles match for the 2025 Ryder Cup.

Current Score (after Saturday):
- USA: ${usaScore}
- Europe: ${europeScore}

Sunday Singles Pairing (Europe player listed first):
Match 1: ${europe.trim()} (Europe) vs ${usa.trim()} (USA)

${context.trim() ? `Additional context:\n${context.trim()}\n\n` : ''}Your task:
1. Use the sequential pipeline to analyze this match: profile both players, analyze recent form and baseline skill, synthesize probabilities, and generate an outcome.
2. Report the result for this match and explain the key factors.
3. Show how the pipeline stages communicate via session.state.

Begin your analysis now.`
}

async function assertOk(response, action) {
  if (!response.ok) {
    throw new Error(`${action} failed (HTTP ${response.status}). Check the ADK server terminal for details.`)
  }
}

export async function* readSse(stream) {
  if (!stream) throw new Error('The ADK server returned an empty stream.')

  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let pending = ''
  let data = []

  function parseLine(line) {
    if (line === '') {
      if (!data.length) return null
      const payload = data.join('\n')
      data = []
      if (payload === '[DONE]') return null
      try {
        return JSON.parse(payload)
      } catch {
        throw new Error('The ADK server sent an invalid stream event.')
      }
    }
    if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''))
    return null
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      pending += done ? decoder.decode() : decoder.decode(value, { stream: true })
      let newline
      while ((newline = pending.indexOf('\n')) !== -1) {
        const line = pending.slice(0, newline).replace(/\r$/, '')
        pending = pending.slice(newline + 1)
        const event = parseLine(line)
        if (event !== null) yield event
      }
      if (done) {
        if (pending) {
          const event = parseLine(pending.replace(/\r$/, ''))
          if (event !== null) yield event
        }
        const event = parseLine('')
        if (event !== null) yield event
        break
      }
    }
  } finally {
    reader.releaseLock()
  }
}

export async function* runPrediction(input, signal) {
  const userId = `local-${crypto.randomUUID()}`
  const sessionResponse = await fetch(
    `/apps/${APP_NAME}/users/${userId}/sessions`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', signal },
  )
  await assertOk(sessionResponse, 'Session creation')
  const session = await sessionResponse.json()
  if (typeof session.id !== 'string' || !session.id) {
    throw new Error('The ADK server did not return a session ID.')
  }

  const response = await fetch('/run_sse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({
      appName: APP_NAME,
      userId,
      sessionId: session.id,
      newMessage: { role: 'user', parts: [{ text: buildPrompt(input) }] },
      streaming: true,
    }),
    signal,
  })
  await assertOk(response, 'Prediction')
  for await (const event of readSse(response.body)) {
    if (event?.error || event?.error_code || event?.errorCode) {
      throw new Error(
        typeof event.error === 'string'
          ? event.error
          : event.error_message || event.errorMessage || 'The agent reported an error.',
      )
    }
    if (event?.interrupted) throw new Error('The agent stopped before completing the prediction.')
    yield event
  }
}

export function applyEvent(entries, event) {
  const author = typeof event?.author === 'string' ? event.author : ''
  const text = event?.content?.parts
    ?.filter((part) => typeof part.text === 'string' && !part.thought)
    .map((part) => part.text)
    .join('') || ''
  if (!author || !text) return entries

  const next = [...entries]
  const last = next.at(-1)
  if (last?.author === author && last.draft) {
    next[next.length - 1] = {
      author,
      text: event.partial ? last.text + text : text,
      draft: Boolean(event.partial),
    }
  } else {
    next.push({ author, text, draft: Boolean(event.partial) })
  }
  return next
}
