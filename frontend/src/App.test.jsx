import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App.jsx'

beforeEach(() => {
  vi.stubGlobal('crypto', { randomUUID: () => 'fixed-id' })
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function adkResponse(events) {
  const encoder = new TextEncoder()
  return {
    ok: true,
    body: new ReadableStream({
      start(controller) {
        events.forEach((event) => controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`)))
        controller.close()
      },
    }),
  }
}

it('shows the sample, accepts context, and renders a completed streamed forecast', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 's-1' }) })
    .mockResolvedValueOnce(adkResponse([
      { author: 'PlayerProfilerAgent', partial: true, content: { parts: [{ text: 'Profile' }] } },
      { author: 'PlayerProfilerAgent', partial: false, content: { parts: [{ text: 'Profile complete' }] } },
      { author: 'RyderCupCoordinator', content: { parts: [{ text: 'Rose wins the match.' }] } },
    ]))
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)
  expect(screen.getByLabelText('Europe player')).toHaveValue('Justin Rose')
  expect(screen.getByLabelText('USA player')).toHaveValue('Cameron Young')
  expect(screen.getByLabelText('Europe score')).toHaveValue(11.5)
  fireEvent.change(screen.getByLabelText('MATCH CONTEXT (OPTIONAL)'), { target: { value: 'Windy' } })
  fireEvent.click(screen.getByRole('button', { name: /Run prediction/ }))
  await waitFor(() => expect(screen.getByText('Rose wins the match.')).toBeInTheDocument())
  expect(screen.getByText(/Analysis complete/)).toBeInTheDocument()
  expect(screen.getByText('Earlier agent output (1)')).toBeInTheDocument()
  expect(JSON.parse(fetchMock.mock.calls[1][1].body).newMessage.parts[0].text).toContain('Additional context:\nWindy')
})

it('shows a server failure and permits another run', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: false, status: 503 })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 's-2' }) })
    .mockResolvedValueOnce(adkResponse([{ author: 'RyderCupCoordinator', content: { parts: [{ text: 'A result' }] } }]))
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)
  fireEvent.click(screen.getByRole('button', { name: /Run prediction/ }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Session creation failed (HTTP 503)')
  fireEvent.click(screen.getByRole('button', { name: /Run prediction/ }))
  expect(await screen.findByText('A result')).toBeInTheDocument()
})

it('lets the user stop a pending run without claiming a completed prediction', async () => {
  vi.stubGlobal('fetch', vi.fn((_, options) => new Promise((_, reject) => {
    options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
  })))
  render(<App />)
  fireEvent.click(screen.getByRole('button', { name: /Run prediction/ }))
  fireEvent.click(screen.getByRole('button', { name: /Stop analysis/ }))
  await waitFor(() => expect(screen.getByText(/Analysis stopped/)).toBeInTheDocument())
  expect(screen.queryByText(/Analysis complete/)).not.toBeInTheDocument()
})
