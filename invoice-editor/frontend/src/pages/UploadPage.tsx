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

  const handleDemo = () => navigate('/demo/demo')

  return (
    <div style={{ minHeight: '100svh', background: 'var(--bg)', fontFamily: 'var(--font)' }}>

      {/* Gradient hero */}
      <div style={{
        background: 'var(--grad)',
        padding: '52px 24px 96px',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Decorative blobs */}
        <div style={{
          position: 'absolute', top: -80, right: -60,
          width: 280, height: 280,
          background: 'rgba(255,255,255,0.07)',
          borderRadius: '50%',
          pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', bottom: -100, left: -50,
          width: 240, height: 240,
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '50%',
          pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', top: '20%', left: '10%',
          width: 120, height: 120,
          background: 'rgba(255,255,255,0.04)',
          borderRadius: '50%',
          pointerEvents: 'none',
        }} />

        {/* Help button */}
        <button
          onClick={() => setShowHelp(true)}
          style={{
            position: 'absolute', top: 20, right: 20,
            width: 34, height: 34,
            borderRadius: 'var(--r)',
            border: '1px solid rgba(255,255,255,0.3)',
            background: 'rgba(255,255,255,0.15)',
            color: 'white',
            fontSize: 14, fontWeight: 700,
            cursor: 'pointer',
            backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
          title="Ayuda"
        >
          ?
        </button>

        {/* Label badge */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 7,
          padding: '5px 14px',
          background: 'rgba(255,255,255,0.15)',
          borderRadius: 99,
          border: '1px solid rgba(255,255,255,0.25)',
          marginBottom: 22,
        }}>
          <span style={{ fontSize: 14 }}>📋</span>
          <span style={{
            color: 'rgba(255,255,255,0.95)',
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}>
            Editor de Facturas PDF
          </span>
        </div>

        <h1 style={{
          color: 'white',
          fontSize: 38,
          fontWeight: 700,
          letterSpacing: '-0.03em',
          lineHeight: 1.12,
          marginBottom: 16,
          textShadow: '0 2px 12px rgba(0,0,0,0.15)',
        }}>
          Edita tus facturas<br />con precisión
        </h1>

        <p style={{
          color: 'rgba(255,255,255,0.82)',
          fontSize: 15,
          lineHeight: 1.65,
          maxWidth: 400,
          margin: '0 auto',
        }}>
          Carga un PDF, edita los campos de texto y exporta<br />
          un documento idéntico al original con los nuevos valores.
        </p>
      </div>

      {/* Cards overlapping the gradient */}
      <div style={{ maxWidth: 600, margin: '-56px auto 0', padding: '0 24px 48px' }}>

        {/* Dropzone grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <FileDropzone
            label="Factura Regular"
            description="Facturas de cualquier proveedor"
            icon="📄"
            onFile={f => handleFile(f, 'regular')}
            disabled={loading}
          />
          <FileDropzone
            label="Factura Fiscal (DGI)"
            description="Con código QR electrónico"
            icon="🏛️"
            onFile={f => handleFile(f, 'fiscal')}
            disabled={loading}
          />
        </div>

        {/* Status messages */}
        <div style={{ marginTop: 14 }}>
          {loading && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '12px 16px',
              background: 'var(--info-bg)',
              border: '1px solid var(--info-border)',
              borderRadius: 'var(--r)',
              fontSize: 13,
              color: 'var(--info)',
            }}>
              <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⟳</span>
              Procesando PDF…
            </div>
          )}
          {scannedNotice && !loading && (
            <div style={{
              padding: '12px 16px',
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
              padding: '12px 16px',
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

        {/* Demo divider */}
        <div style={{ marginTop: 22 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
            <span style={{ fontSize: 12, color: 'var(--fg-subtle)' }}>o</span>
            <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          </div>
          <button
            onClick={handleDemo}
            disabled={loading}
            style={{
              marginTop: 14,
              width: '100%',
              padding: '11px 16px',
              borderRadius: 'var(--r)',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
              color: 'var(--fg-muted)',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all var(--t)',
              boxShadow: 'var(--shadow-sm)',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'var(--bg-subtle)'
              e.currentTarget.style.borderColor = 'var(--accent)'
              e.currentTarget.style.color = 'var(--accent)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'var(--bg)'
              e.currentTarget.style.borderColor = 'var(--border)'
              e.currentTarget.style.color = 'var(--fg-muted)'
            }}
          >
            ✨ Cargar demo con datos de prueba
          </button>
        </div>

        <p style={{ marginTop: 24, fontSize: 11, color: 'var(--fg-subtle)', textAlign: 'center' }}>
          Máximo 20 MB · Solo archivos PDF · Los datos no se almacenan permanentemente
        </p>
      </div>

      {showHelp && <HelpModal onClose={() => setShowHelp(false)} context="upload" />}

      <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
