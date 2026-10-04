import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileDropzone } from '../components/FileDropzone'
import { HelpModal } from '../components/HelpModal'
import { uploadPDF } from '../api/client'

export function UploadPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [scannedNotice, setScannedNotice] = useState(false)
  const [showHelp, setShowHelp] = useState(false)

  const handleFile = async (file: File, docType: 'regular' | 'fiscal') => {
    setLoading(true)
    setError(null)
    setScannedNotice(false)
    try {
      const { data } = await uploadPDF(file, docType)
      if (data.scanned) {
        setScannedNotice(true)
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
      setError('Error al procesar el PDF. Verifica que el archivo sea válido y no supere los 20 MB.')
    } finally {
      setLoading(false)
    }
  }

  const handleDemo = () => {
    navigate('/demo/demo')
  }

  return (
    <div style={{
      minHeight: '100svh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      background: 'var(--bg)',
    }}>
      {/* Header */}
      <div style={{ width: '100%', maxWidth: 560, marginBottom: 40 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
              <div style={{
                width: 32,
                height: 32,
                background: 'var(--accent)',
                borderRadius: 'var(--r)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 15,
                color: 'var(--accent-fg)',
                flexShrink: 0,
              }}>
                📋
              </div>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--fg)', letterSpacing: '-0.01em' }}>
                Editor de Facturas PDF
              </span>
            </div>
            <h1 style={{ fontSize: 28, fontWeight: 600, letterSpacing: '-0.03em', lineHeight: 1.15, color: 'var(--fg)' }}>
              Edita tus facturas<br />con precisión
            </h1>
            <p style={{ marginTop: 10, fontSize: 14, color: 'var(--fg-muted)', lineHeight: 1.6 }}>
              Carga una factura PDF, edita los campos de texto y exporta<br />
              un documento idéntico al original con los nuevos valores.
            </p>
          </div>
          <button
            onClick={() => setShowHelp(true)}
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--r)',
              border: '1px solid var(--border)',
              background: 'var(--bg-subtle)',
              color: 'var(--fg-muted)',
              fontSize: 13,
              fontWeight: 600,
              flexShrink: 0,
              marginTop: 2,
              cursor: 'pointer',
            }}
            title="Ayuda (? para abrir)"
          >
            ?
          </button>
        </div>
      </div>

      {/* Dropzones */}
      <div style={{ width: '100%', maxWidth: 560, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <FileDropzone
          label="Factura Regular"
          description="Facturas estándar de cualquier proveedor"
          icon="📄"
          onFile={f => handleFile(f, 'regular')}
          disabled={loading}
        />
        <FileDropzone
          label="Factura Fiscal (DGI)"
          description="Facturas electrónicas con código QR"
          icon="🏛️"
          onFile={f => handleFile(f, 'fiscal')}
          disabled={loading}
        />
      </div>

      {/* Status messages */}
      <div style={{ width: '100%', maxWidth: 560, marginTop: 12 }}>
        {loading && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 14px',
            background: 'var(--bg-subtle)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--r)',
            fontSize: 13,
            color: 'var(--fg-muted)',
          }}>
            <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⟳</span>
            Procesando PDF…
          </div>
        )}
        {scannedNotice && !loading && (
          <div style={{
            padding: '10px 14px',
            background: 'var(--info-bg)',
            border: '1px solid var(--info-border)',
            borderRadius: 'var(--r)',
            fontSize: 13,
            color: 'var(--info)',
          }}>
            PDF escaneado detectado — se aplicará OCR al texto.
          </div>
        )}
        {error && (
          <div style={{
            padding: '10px 14px',
            background: 'var(--error-bg)',
            border: '1px solid var(--error-border)',
            borderRadius: 'var(--r)',
            fontSize: 13,
            color: 'var(--error)',
          }}>
            {error}
          </div>
        )}
      </div>

      {/* Demo button */}
      <div style={{ width: '100%', maxWidth: 560, marginTop: 16 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          <span style={{ fontSize: 12, color: 'var(--fg-subtle)' }}>o</span>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        </div>
        <button
          onClick={handleDemo}
          disabled={loading}
          style={{
            marginTop: 12,
            width: '100%',
            padding: '9px 16px',
            borderRadius: 'var(--r)',
            border: '1px solid var(--border)',
            background: 'var(--bg-subtle)',
            color: 'var(--fg-muted)',
            fontSize: 13,
            fontWeight: 500,
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'background var(--t), color var(--t)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'var(--bg-muted)'
            e.currentTarget.style.color = 'var(--fg)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'var(--bg-subtle)'
            e.currentTarget.style.color = 'var(--fg-muted)'
          }}
        >
          Cargar demo con datos de prueba
        </button>
      </div>

      {/* Footer */}
      <p style={{ marginTop: 32, fontSize: 11, color: 'var(--fg-subtle)', textAlign: 'center' }}>
        Máximo 20 MB · Solo archivos PDF · Los datos no se almacenan permanentemente
      </p>

      {showHelp && (
        <HelpModal onClose={() => setShowHelp(false)} context="upload" />
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
      `}</style>
    </div>
  )
}
