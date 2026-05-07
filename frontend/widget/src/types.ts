export type WSMessage =
  | { type: 'session_init'; thread_id: string }
  | { type: 'token'; content: string }
  | { type: 'turn_end' }
  | { type: 'confirmation_request'; tool: string; args: Record<string, unknown> }

export type ConfirmationResponse = {
  type: 'confirmation_response'
  approved: boolean
}
