import type { Meeting } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.detail ?? `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export function analyzeMeeting(title: string, transcript: string) {
  return request<Meeting>('/api/meetings', {
    method: 'POST',
    body: JSON.stringify({ title, transcript }),
  })
}

export function answerClarifications(id: string, answers: Record<string, string>) {
  return request<Meeting>(`/api/meetings/${id}/clarifications`, {
    method: 'POST',
    body: JSON.stringify({ answers }),
  })
}

export function addContext(title: string, text: string) {
  return request<{ status: string; title: string }>('/api/context', {
    method: 'POST',
    body: JSON.stringify({ title, text }),
  })
}
