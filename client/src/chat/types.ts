export type MessageRole = 'user' | 'assistant'

export interface Source {
  source_id: string
  file: string
  title: string
  url?: string | null
}

export interface Step {
  id: string
  tool: string
  args: Record<string, unknown>
  result: string
}

export interface Message {
  id: string
  role: MessageRole
  content: string
  sources?: Source[]
  steps?: Step[]
}
