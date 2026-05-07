import { render, screen, act, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { ChatApp } from '../ChatApp'
import { FakeWebSocket } from './fakeWebSocket'

beforeEach(() => FakeWebSocket.install())
afterEach(() => FakeWebSocket.uninstall())

describe('ChatApp', () => {
  it('renders a message input and send button', () => {
    render(<ChatApp serverUrl="ws://localhost/ws/chat" />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('displays the user message after sending', async () => {
    const user = userEvent.setup()
    render(<ChatApp serverUrl="ws://localhost/ws/chat" />)

    await user.type(screen.getByRole('textbox'), 'hello world')
    await user.click(screen.getByRole('button', { name: /send/i }))

    expect(screen.getByText('hello world')).toBeInTheDocument()
  })

  it('accumulates token frames into a single AI message', async () => {
    render(<ChatApp serverUrl="ws://localhost/ws/chat" />)
    const ws = FakeWebSocket.latest()

    await act(async () => {
      ws.simulateMessage({ type: 'token', content: 'Hel' })
      ws.simulateMessage({ type: 'token', content: 'lo' })
      ws.simulateMessage({ type: 'token', content: '!' })
    })

    expect(screen.getByText('Hello!')).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(1)
  })

  it('clears the streaming indicator after turn_end', async () => {
    render(<ChatApp serverUrl="ws://localhost/ws/chat" />)
    const ws = FakeWebSocket.latest()

    await act(async () => {
      ws.simulateMessage({ type: 'token', content: 'Done' })
      ws.simulateMessage({ type: 'turn_end' })
    })

    const item = screen.getByRole('listitem')
    expect(item).not.toHaveAttribute('data-streaming')
    expect(item).toHaveTextContent('Done')
  })

  it('shows a confirmation dialog when confirmation_request is received', async () => {
    render(<ChatApp serverUrl="ws://localhost/ws/chat" />)
    const ws = FakeWebSocket.latest()

    await act(async () => {
      ws.simulateMessage({
        type: 'confirmation_request',
        tool: 'search_history',
        args: { query: 'test' },
      })
    })

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/search_history/i)).toBeInTheDocument()
  })

  it('sends approved:true and closes dialog when Confirm is clicked', async () => {
    const user = userEvent.setup()
    render(<ChatApp serverUrl="ws://localhost/ws/chat" />)
    const ws = FakeWebSocket.latest()

    await act(async () => {
      ws.simulateMessage({
        type: 'confirmation_request',
        tool: 'search_history',
        args: { query: 'test' },
      })
    })

    await user.click(screen.getByRole('button', { name: /confirm/i }))

    expect(ws.sent).toContain(JSON.stringify({ type: 'confirmation_response', approved: true }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('sends approved:false and closes dialog when Cancel is clicked', async () => {
    const user = userEvent.setup()
    render(<ChatApp serverUrl="ws://localhost/ws/chat" />)
    const ws = FakeWebSocket.latest()

    await act(async () => {
      ws.simulateMessage({
        type: 'confirmation_request',
        tool: 'search_history',
        args: { query: 'test' },
      })
    })

    await user.click(screen.getByRole('button', { name: /cancel/i }))

    expect(ws.sent).toContain(JSON.stringify({ type: 'confirmation_response', approved: false }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
