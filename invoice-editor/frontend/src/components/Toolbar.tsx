import { useState } from 'react'
import type { EditorState } from '../types'

interface ToolbarProps {
  state: EditorState
  onReset: () => void
  onExport: (regenerateQr: boolean) => void
  onPreviewPdf: () => void
  exportError?: string | null
  showPreview: boolean
  onTogglePreview: () => void
  onChangeFile: () => void
  onGoHome: () => void
  onHelp: () => void
}

export function Toolbar({ state, onReset, onExport, onPreviewPdf, exportError, showPreview, onTogglePreview, onChangeFile, onGoHome, onHelp }: ToolbarProps) {
  const editCount = state.edits.size
  const isFiscal = state.docType === 'fiscal'
  const [hoveredBtn, setHoveredBtn] = useState<string | null>(null)

  const ghostStyle = (id: string): React.CSSProperties => ({
    height: 30,
    padding: '0 10px',
    borderRadius: 'var(--r)',
    fontSize: 12,
    fontWeight: 500,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    whiteSpace: 'nowrap',
    transition: 'all var(--t)',
    flexShrink: 0,
    background: hoveredBtn === id ? 'var(--bg-muted)' : 'transparent',
    border: '1px solid transparent',
    color: hoveredBtn === id ? 'var(--accent)' : 'var(--fg-muted)',
  })

  const outlineStyle = (id: string): React.CSSProperties => ({
    height: 30,
    padding: '0 10px',
    borderRadius: 'var(--r)',
    fontSize: 12,
    fontWeight: 500,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    whiteSpace: 'nowrap',
    transition: 'all var(--t)',
    flexShrink: 0,
    background: hoveredBtn === id ? 'var(--bg-muted)' : 'var(--bg)',
    border: `1px solid ${hoveredBtn === id ? 'var(--border-strong)' : 'var(--border)'}`,
    color: hoveredBtn === id ? 'var(--accent)' : 'var(--fg)',
  })

  const successStyle = (id: string): React.CSSProperties => ({
    height: 30,
    padding: '0 10px',
    borderRadius: 'var(--r)',
    fontSize: 12,
    fontWeight: 500,
    cursor: state.isExporting ? 'default' : 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    whiteSpace: 'nowrap',
    transition: 'all var(--t)',
    flexShrink: 0,
    background: 'var(--success-bg)',
    border: '1px solid var(--success-border)',
    color: 'var(--success)',
    opacity: hoveredBtn === id && !state.isExporting ? 0.85 : 1,
  })

  const primaryStyle = (id: string): React.CSSProperties => ({
    height: 30,
    padding: '0 12px',
    borderRadius: 'var(--r)',
    fontSize: 12,
    fontWeight: 600,
    cursor: state.isExporting ? 'default' : 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    whiteSpace: 'nowrap',
    transition: 'all var(--t)',
    flexShrink: 0,
    background: hoveredBtn === id && !state.isExporting ? 'var(--grad-hover)' : 'var(--grad)',
    border: 'none',
    color: 'white',
    boxShadow: hoveredBtn === id && !state.isExporting ? 'var(--shadow-md)' : 'var(--shadow-sm)',
  })

  const hover = (id: string) => setHoveredBtn(id)
  const unhover = () => setHoveredBtn(null)

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '0 12px',
        height: 48,
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg)',
        overflowX: 'auto',
      }}>
        {/* Left group */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          <button
            onClick={onGoHome}
            style={ghostStyle('home')}
            title="Ir al inicio"
            onMouseEnter={() => hover('home')}
            onMouseLeave={unhover}
          >
            ← Inicio
          </button>
          <div style={{ width: 1, height: 16, background: 'var(--border)', flexShrink: 0 }} />
          <button
            onClick={onChangeFile}
            style={ghostStyle('change')}
            title="Cambiar factura"
            onMouseEnter={() => hover('change')}
            onMouseLeave={unhover}
          >
            Cambiar factura
          </button>
        </div>

        {/* Center: title + badge */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, justifyContent: 'center' }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--fg)', letterSpacing: '-0.01em', whiteSpace: 'nowrap' }}>
            {isFiscal ? 'Factura Fiscal' : 'Factura Regular'}
          </span>
          {editCount > 0 && (
            <span style={{
              padding: '2px 8px',
              borderRadius: 99,
              background: 'var(--grad)',
              color: 'white',
              fontSize: 11,
              fontWeight: 600,
              whiteSpace: 'nowrap',
              boxShadow: 'var(--shadow-sm)',
            }}>
              {editCount} campo{editCount !== 1 ? 's' : ''} editado{editCount !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Right group */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <button
            onClick={onTogglePreview}
            style={outlineStyle('preview')}
            onMouseEnter={() => hover('preview')}
            onMouseLeave={unhover}
          >
            {showPreview ? '⊟ Ocultar' : '⊞ Previa'}
          </button>

          <button
            onClick={onReset}
            disabled={editCount === 0}
            style={{
              ...outlineStyle('reset'),
              opacity: editCount === 0 ? 0.4 : 1,
              cursor: editCount === 0 ? 'not-allowed' : 'pointer',
            }}
            title="Deshacer todos los cambios"
            onMouseEnter={() => editCount > 0 && hover('reset')}
            onMouseLeave={unhover}
          >
            ↩ Resetear
          </button>

          <button
            onClick={onPreviewPdf}
            disabled={state.isExporting}
            style={successStyle('viewpdf')}
            title="Ver PDF en nueva pestaña"
            onMouseEnter={() => !state.isExporting && hover('viewpdf')}
            onMouseLeave={unhover}
          >
            {state.isExporting ? '…' : '🔍 Ver PDF'}
          </button>

          <div style={{ width: 1, height: 16, background: 'var(--border)', flexShrink: 0 }} />

          {isFiscal ? (
            <>
              <button
                onClick={() => onExport(false)}
                disabled={state.isExporting}
                style={outlineStyle('pdf')}
                onMouseEnter={() => !state.isExporting && hover('pdf')}
                onMouseLeave={unhover}
              >
                {state.isExporting ? 'Exportando…' : '⬇ PDF'}
              </button>
              <button
                onClick={() => onExport(true)}
                disabled={state.isExporting}
                style={primaryStyle('pdfqr')}
                title="Exportar y regenerar código QR"
                onMouseEnter={() => !state.isExporting && hover('pdfqr')}
                onMouseLeave={unhover}
              >
                {state.isExporting ? 'Exportando…' : '⬇ PDF + QR'}
              </button>
            </>
          ) : (
            <button
              onClick={() => onExport(false)}
              disabled={state.isExporting}
              style={primaryStyle('export')}
              onMouseEnter={() => !state.isExporting && hover('export')}
              onMouseLeave={unhover}
            >
              {state.isExporting ? 'Exportando…' : '⬇ Exportar PDF'}
            </button>
          )}

          <div style={{ width: 1, height: 16, background: 'var(--border)', flexShrink: 0 }} />

          <button
            onClick={onHelp}
            style={{
              ...ghostStyle('help'),
              width: 30,
              padding: 0,
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: 14,
            }}
            title="Ayuda (tecla ?)"
            onMouseEnter={() => hover('help')}
            onMouseLeave={unhover}
          >
            ?
          </button>
        </div>
      </div>

      {exportError && (
        <div style={{
          padding: '6px 12px',
          fontSize: 12,
          color: 'var(--error)',
          background: 'var(--error-bg)',
          borderBottom: '1px solid var(--error-border)',
        }}>
          {exportError}
        </div>
      )}
    </div>
  )
}
