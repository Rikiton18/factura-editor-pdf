import axios from 'axios'
import type { TextBlock, DemoData } from '../types'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? '/api' })

export interface UploadResponse {
  session_id: string
  pdf_base64: string
  blocks: TextBlock[]
  page_count: number
  scanned: boolean
}

export interface ExportRequest {
  edits: { block_id: string; new_text: string }[]
  regenerate_qr: boolean
}

export interface ExportResponse {
  pdf_base64: string
}

export const uploadPDF = (file: File, doc_type: 'regular' | 'fiscal') => {
  const form = new FormData()
  form.append('file', file)
  form.append('doc_type', doc_type)
  return api.post<UploadResponse>('/upload', form)
}

export const exportPDF = (session_id: string, req: ExportRequest) =>
  api.post<ExportResponse>(`/export/${session_id}`, req)

export const getDemoData = (session_id: string) =>
  api.get<DemoData>(`/demo/${session_id}`)
