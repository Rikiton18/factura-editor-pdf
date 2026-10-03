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
}

export function Toolbar({ state, onReset, onExport, onPreviewPdf, exportError, showPreview, onTogglePreview, onChangeFile, onGoHome }: ToolbarProps) {
  const editCount = state.edits.size
  const isFiscal = state.docType === 'fiscal'

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '8px 16px',
        borderBottom: exportError ? 'none' : '1px solid #e5e7eb',
        backgroundColor: '#f9fafb',
      }}>
        <button
          onClick={onGoHome}
          style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #d1d5db', backgroundColor: 'white', cursor: 'pointer', fontSize: 13 }}
        >
          ← Inicio
        </button>

        <button
          onClick={onChangeFile}
          style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #d1d5db', backgroundColor: 'white', cursor: 'pointer', fontSize: 13 }}
        >
          Cambiar factura
        </button>

        <span style={{ fontWeight: 600, flex: 1 }}>
          {isFiscal ? 'Factura Fiscal' : 'Factura Regular'}
          {editCount > 0 && (
            <span style={{ color: '#16a34a', fontSize: 13, marginLeft: 8 }}>
              {editCount} campo{editCount !== 1 ? 's' : ''} editado{editCount !== 1 ? 's' : ''}
            </span>
          )}
        </span>

        <button
          onClick={onTogglePreview}
          style={{
            padding: '6px 12px', borderRadius: 6, fontSize: 13, cursor: 'pointer',
            border: '1px solid #d1d5db',
            backgroundColor: showPreview ? '#1d4ed8' : 'white',
            color: showPreview ? 'white' : 'inherit',
          }}
        >
          {showPreview ? 'Ocultar vista previa' : 'Mostrar vista previa'}
        </button>

        <button
          onClick={onReset}
          disabled={editCount === 0}
          style={{
            padding: '6px 14px',
            borderRadius: 6,
            border: '1px solid #d1d5db',
            backgroundColor: 'white',
            cursor: editCount === 0 ? 'not-allowed' : 'pointer',
            opacity: editCount === 0 ? 0.5 : 1,
          }}
        >
          Resetear cambios
        </button>

        <button
          onClick={onPreviewPdf}
          disabled={state.isExporting}
          style={{
            padding: '6px 14px', borderRadius: 6, fontSize: 13, cursor: state.isExporting ? 'not-allowed' : 'pointer',
            border: '1px solid #059669', backgroundColor: '#ecfdf5', color: '#065f46',
            opacity: state.isExporting ? 0.5 : 1,
          }}
        >
          {state.isExporting ? 'Procesando…' : '🔍 Ver PDF'}
        </button>

        {isFiscal ? (
          <>
            <button
              onClick={() => onExport(false)}
              disabled={state.isExporting}
              style={{ padding: '6px 14px', borderRadius: 6, border: '1px solid #d1d5db', backgroundColor: 'white', cursor: 'pointer' }}
            >
              {state.isExporting ? 'Exportando…' : 'Exportar PDF'}
            </button>
            <button
              onClick={() => onExport(true)}
              disabled={state.isExporting}
              style={{ padding: '6px 14px', borderRadius: 6, border: 'none', backgroundColor: '#1d4ed8', color: 'white', cursor: 'pointer' }}
            >
              {state.isExporting ? 'Exportando…' : 'Exportar + Regenerar QR'}
            </button>
          </>
        ) : (
          <button
            onClick={() => onExport(false)}
            disabled={state.isExporting}
            style={{ padding: '6px 14px', borderRadius: 6, border: 'none', backgroundColor: '#1d4ed8', color: 'white', cursor: 'pointer' }}
          >
            {state.isExporting ? 'Exportando…' : 'Exportar PDF'}
          </button>
        )}
      </div>

      {exportError && (
        <p style={{
          margin: 0,
          padding: '4px 16px 6px',
          color: '#dc2626',
          fontSize: 13,
          backgroundColor: '#f9fafb',
          borderBottom: '1px solid #e5e7eb',
        }}>
          {exportError}
        </p>
      )}
    </div>
  )
}
