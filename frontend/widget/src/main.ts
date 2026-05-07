import { createElement } from 'react'
import { createRoot } from 'react-dom/client'
import { ChatApp } from './ChatApp'

class AgentiaChat extends HTMLElement {
  connectedCallback() {
    const serverUrl = this.getAttribute('server-url') ?? 'ws://localhost:8000/ws/chat'
    const shadow = this.attachShadow({ mode: 'open' })
    const mount = document.createElement('div')
    shadow.appendChild(mount)
    createRoot(mount).render(createElement(ChatApp, { serverUrl }))
  }
}

customElements.define('agentia-chat', AgentiaChat)
