import type { Source, Step } from './types'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface ChatApiResponse {
  reply: string
  sources: Source[]
  steps: Step[]
}

export async function sendMessageToAI(
  sessionId: string,
  message: string,
): Promise<ChatApiResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  })

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status} ${response.statusText}`)
  }

  return response.json()
}
