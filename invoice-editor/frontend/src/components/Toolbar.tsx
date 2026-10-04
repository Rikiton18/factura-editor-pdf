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

const btn = (variant: 'ghost' | 'outline' | 'primary' | 'success'): React.CSSProperties => {
  const base: React.CSSProperties = {
    height: 30,
    padding: '0 12px',
    borderRadius: 'var(--r)',
    fontSize: 12,
    fontWeight: 500,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    whiteSpace: 'nowrap',
    transition: 'background var(--t), color var(--t), border-color var(--t)',
    flexShrink: 0,
  }
  if (variant === 'ghost') return { ...base, background: 'transparent', border: '1px solid transparent', color: 'var(--fg-muted)' }
  if (variant === 'outline') return { ...base, background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--fg)' }
  if (variant === 'primary') return { ...base, background: 'var(--accent)', border: '1px solid var(--accent)', color: 'var(--accent-fg)' }
  if (variant === 'success') return { ...base, background: 'var(--success-bg)', border: '1px solid var(--success-border)', color: 'var(--success)' }
  return base
}

export function Toolbar({ state, onReset, onExport, onPreviewPdf, exportError, showPreview, onTogglePreview, onChangeFile, onGoHome, onHelp }: ToolbarProps) {
  const editCount = state.edits.size
  const isFiscal = state.docType === 'fiscal'

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '0 12px',
        height: 46,
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg)',
        overflowX: 'auto',
      }}>
        {/* Left group */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <button
            onClick={onGoHome}
            style={btn('ghost')}
            title="Ir al inicio"
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-muted)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            ← Inicio
          </button>

          <div style={{ width: 1, height: 16, background: 'var(--border)' }} />

          <button
            onClick={onChangeFile}
            style={btn('ghost')}
            title="Cambiar factura"
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-muted)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
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
              padding: '1px 8px',
              borderRadius: 99,
              background: 'var(--success-bg)',
              border: '1px solid var(--success-border)',
              color: 'var(--success)',
              fontSize: 11,
              fontWeight: 500,
              whiteSpace: 'nowrap',
            }}>
              {editCount} campo{editCount !== 1 ? 's' : ''} editado{editCount !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Right group */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <button
            onClick={onTogglePreview}
            style={btn('outline')}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-muted)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'var(--bg)')}
          >
            {showPreview ? '⊟ Ocultar' : '⊞ Previa'}
          </button>

          <button
            onClick={onReset}
            disabled={editCount === 0}
            style={btn('outline')}
            title="Deshacer todos los cambios"
            onMouseEnter={e => !state.isExporting && editCount > 0 && (e.currentTarget.style.background = 'var(--bg-muted)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'var(--bg)')}
          >
            ↩ Resetear
          </button>

          <button
            onClick={onPreviewPdf}
            disabled={state.isExporting}
            style={btn('success')}
            title="Ver PDF en nueva pestaña"
            onMouseEnter={e => !state.isExporting && (e.currentTarget.style.opacity = '0.85')}
            onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
          >
            {state.isExporting ? '…' : '🔍 Ver PDF'}
          </button>

          <div style={{ width: 1, height: 16, background: 'var(--border)' }} />

          {isFiscal ? (
            <>
              <button
                onClick={() => onExport(false)}
                disabled={state.isExporting}
                style={btn('outline')}
                onMouseEnter={e => !state.isExporting && (e.currentTarget.style.background = 'var(--bg-muted)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'var(--bg)')}
              >
                {state.isExporting ? 'Exportando…' : '⬇ PDF'}
              </button>
              <button
                onClick={() => onExport(true)}
                disabled={state.isExporting}
                style={btn('primary')}
                title="Exportar y regenerar código QR"
                onMouseEnter={e => !state.isExporting && (e.currentTarget.style.background = 'var(--accent-hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'var(--accent)')}
              >
                {state.isExporting ? 'Exportando…' : '⬇ PDF + QR'}
              </button>
            </>
          ) : (
            <button
              onClick={() => onExport(false)}
              disabled={state.isExporting}
              style={btn('primary')}
              onMouseEnter={e => !state.isExporting && (e.currentTarget.style.background = 'var(--accent-hover)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'var(--accent)')}
            >
              {state.isExporting ? 'Exportando…' : '⬇ Exportar PDF'}
            </button>
          )}

          <div style={{ width: 1, height: 16, background: 'var(--border)' }} />

          <button
            onClick={onHelp}
            style={{
              ...btn('ghost'),
              width: 30,
              padding: 0,
              justifyContent: 'center',
              fontWeight: 600,
              fontSize: 13,
            }}
            title="Ayuda (tecla ?)"
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-muted)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
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
