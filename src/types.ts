export type Decision = { description: string; evidence: string }
export type ActionItem = {
  description: string
  owner: string | null
  due_date: string | null
  evidence: string
  needs_clarification: boolean
}
export type Clarification = {
  id: string
  action_item_index: number
  field: string
  question: string
  evidence: string
}
export type Meeting = {
  id: string
  title: string
  status: string
  summary: string
  decisions: Decision[]
  action_items: ActionItem[]
  clarifications: Clarification[]
}
