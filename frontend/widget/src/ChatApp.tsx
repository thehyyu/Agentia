import { useState, useRef, useEffect } from 'react'
import type { WSMessage } from './types'

interface Message {
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
}

interface PendingConfirm {
  tool: string
  args: Record<string, unknown>
}

interface Props {
  serverUrl: string
}

export function ChatApp({ serverUrl }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [pendingConfirm, setPendingConfirm] = useState<PendingConfirm | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(serverUrl)
    wsRef.current = ws

    ws.onmessage = (e: MessageEvent) => {
      const msg: WSMessage = JSON.parse(e.data)

      if (msg.type === 'token') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.role === 'assistant') {
            return [...prev.slice(0, -1), { ...last, content: last.content + msg.content, streaming: true }]
          }
          return [...prev, { role: 'assistant', content: msg.content, streaming: true }]
        })
      } else if (msg.type === 'turn_end') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.role === 'assistant') {
            return [...prev.slice(0, -1), { ...last, streaming: false }]
          }
          return prev
        })
      } else if (msg.type === 'confirmation_request') {
        setPendingConfirm({ tool: msg.tool, args: msg.args })
      }
    }

    return () => ws.close()
  }, [serverUrl])

  function handleSend() {
    if (!input.trim()) return
    setMessages(prev => [...prev, { role: 'user', content: input }])
    wsRef.current?.send(input)
    setInput('')
  }

  function handleConfirm(approved: boolean) {
    wsRef.current?.send(JSON.stringify({ type: 'confirmation_response', approved }))
    setPendingConfirm(null)
  }

  return (
    <div>
      <ul>
        {messages.map((m, i) => (
          <li key={i} data-role={m.role} {...(m.streaming ? { 'data-streaming': 'true' } : {})}>
            {m.content}
          </li>
        ))}
      </ul>

      {pendingConfirm && (
        <div role="dialog" aria-label="Tool confirmation">
          <p>Allow tool: <strong>{pendingConfirm.tool}</strong>?</p>
          <pre>{JSON.stringify(pendingConfirm.args, null, 2)}</pre>
          <button onClick={() => handleConfirm(true)}>Confirm</button>
          <button onClick={() => handleConfirm(false)}>Cancel</button>
        </div>
      )}

      <input
        type="text"
        value={input}
        onChange={e => setInput(e.target.value)}
        placeholder="Type a message..."
        onKeyDown={e => e.key === 'Enter' && handleSend()}
      />
      <button onClick={handleSend}>Send</button>
    </div>
  )
}
