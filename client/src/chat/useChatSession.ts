import { useCallback, useRef, useState } from 'react'
import { sendMessageToAI } from './chatService'
import type { Message } from './types'

// Generated once per page load (component mount) and never persisted, so a
// refresh always starts a brand new conversation on the backend.
function createSessionId(): string {
  return crypto.randomUUID()
}

export function useChatSession() {
  const sessionIdRef = useRef(createSessionId())
  const [messages, setMessages] = useState<Message[]>([])
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return

    setError(null)
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', content: trimmed }])
    setIsSending(true)

    try {
      const { reply, sources, steps } = await sendMessageToAI(sessionIdRef.current, trimmed)
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: 'assistant', content: reply, sources, steps },
      ])
    } catch {
      setError("Impossible de contacter l'assistant. Réessayez dans un instant.")
    } finally {
      setIsSending(false)
    }
  }, [])

  return { messages, isSending, error, sendMessage }
}
