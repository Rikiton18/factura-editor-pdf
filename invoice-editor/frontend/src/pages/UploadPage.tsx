import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileDropzone } from '../components/FileDropzone'
import { uploadPDF } from '../api/client'

export function UploadPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [scannedNotice, setScannedNotice] = useState(false)

  const handleFile = async (file: File, docType: 'regular' | 'fiscal') => {
    setLoading(true)
    setError(null)
    setScannedNotice(false)
    try {
      const { data } = await uploadPDF(file, docType)
      if (data.scanned) {
        setScannedNotice(true)
        // Brief pause so the OCR notice is visible before navigation
        await new Promise(resolve => setTimeout(resolve, 1500))
      }
      navigate(`/editor/${data.session_id}`, {
        state: {
          pdfBase64: data.pdf_base64,
          blocks: data.blocks,
          pageCount: data.page_count,
          docType,
          scanned: data.scanned ?? false,
        },
      })
    } catch {
      setError('Error al procesar el PDF. Verifique que el archivo es válido.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 640, margin: '80px auto', padding: '0 24px' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 32 }}>
        Editor de Facturas PDF
      </h1>

      <FileDropzone
        label="Factura Regular"
        onFile={f => handleFile(f, 'regular')}
        disabled={loading}
      />

      <FileDropzone
        label="Factura Fiscal (DGI)"
        onFile={f => handleFile(f, 'fiscal')}
        disabled={loading}
      />

      {loading && (
        <p style={{ color: '#6b7280' }}>Procesando PDF...</p>
      )}
      {scannedNotice && (
        <p style={{ color: '#2563eb', background: '#eff6ff', border: '1px solid #93c5fd', borderRadius: 6, padding: '8px 12px' }}>
          PDF escaneado detectado. Se utilizará reconocimiento de texto (OCR) cuando esté habilitado.
        </p>
      )}
      {error && (
        <p style={{ color: '#dc2626' }}>{error}</p>
      )}
    </div>
  )
}
