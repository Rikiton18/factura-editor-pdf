import { useState } from 'react'
import { exportPDF } from '../api/client'
import type { EditorState } from '../types'

function base64ToBlob(b64: string, mime = 'application/pdf'): Blob {
  const bytes = atob(b64)
  const arr = new Uint8Array(bytes.length)
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
  return new Blob([arr], { type: mime })
}

export function useExport(state: EditorState, setExporting: (v: boolean) => void) {
  const [exportError, setExportError] = useState<string | null>(null)

  const exportAndDownload = async (regenerateQr: boolean) => {
    setExporting(true)
    setExportError(null)
    try {
      const edits = Array.from(state.edits.entries()).map(([block_id, new_text]) => ({
        block_id,
        new_text,
      }))
      const { data } = await exportPDF(state.sessionId, { edits, regenerate_qr: regenerateQr })
      const blob = base64ToBlob(data.pdf_base64)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `factura-editada-${state.sessionId.slice(0, 8)}.pdf`
      a.click()
      setTimeout(() => URL.revokeObjectURL(url), 100)
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 404) {
        setExportError('Sesión expirada — vuelva a cargar el PDF')
      } else {
        setExportError('Error al exportar el PDF.')
      }
    } finally {
      setExporting(false)
    }
  }

  const previewPdf = async (regenerateQr = false) => {
    setExporting(true)
    setExportError(null)
    try {
      const edits = Array.from(state.edits.entries()).map(([block_id, new_text]) => ({
        block_id,
        new_text,
      }))
      const { data } = await exportPDF(state.sessionId, { edits, regenerate_qr: regenerateQr })
      const blob = base64ToBlob(data.pdf_base64)
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
      setTimeout(() => URL.revokeObjectURL(url), 30000)
    } catch (err: unknown) {
      const status = (err as { response?: { response?: { status?: number } } })?.response?.response?.status
      if (status === 404) {
        setExportError('Sesión expirada — vuelva a cargar el PDF')
      } else {
        setExportError('Error al previsualizar el PDF.')
      }
    } finally {
      setExporting(false)
    }
  }

  const clearExportError = () => setExportError(null)

  const doExport = exportAndDownload

  return { exportAndDownload, doExport, previewPdf, exportError, clearExportError }
}
