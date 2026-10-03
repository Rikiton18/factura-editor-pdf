export interface TextBlock {
  block_id: string
  page: number
  x0: number
  y0: number
  x1: number
  y1: number
  text: string
  font: string
  size: number
  color: [number, number, number]
  flags: number
  editable: boolean
}

export interface EditorState {
  sessionId: string
  docType: 'regular' | 'fiscal'
  pdfBase64: string
  blocks: TextBlock[]
  edits: Map<string, string>
  isExporting: boolean
  pageCount: number
}

export interface DemoBlock {
  block_id: string
  page: number
  text: string
  x0: number
  y0: number
  x1: number
  y1: number
}

export interface DemoData {
  session_id: string
  doc_type: string
  blocks: DemoBlock[]
}
