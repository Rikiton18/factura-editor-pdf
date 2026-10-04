import { useEffect, useState } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { useEditorState } from '../hooks/useEditorState'
import { useExport } from '../hooks/useExport'
import { PDFViewer } from '../components/PDFViewer'
import { EditableOverlay, PreviewOverlay } from '../components/TextOverlay'
import { Toolbar } from '../components/Toolbar'
import { HelpModal } from '../components/HelpModal'
import type { TextBlock } from '../types'

export function EditorPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const { state, init, edit, reset, setExporting } = useEditorState()
  const { exportAndDownload, previewPdf, exportError } = useExport(state, setExporting)
  const [showPreview, setShowPreview] = useState(true)
  const [showHelp, setShowHelp] = useState(false)

  useEffect(() => {
    if (!location.state) {
      navigate('/')
      return
    }
    init({
      sessionId: sessionId!,
      docType: location.state.docType,
      pdfBase64: location.state.pdfBase64,
      blocks: location.state.blocks,
      pageCount: location.state.pageCount,
    })
  }, [sessionId])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === '?' && !(e.target instanceof HTMLInputElement)) {
        setShowHelp(v => !v)
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  if (!state.pdfBase64) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100svh',
        color: 'var(--fg-muted)',
        fontSize: 14,
        gap: 8,
      }}>
        <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span>
        Cargando…
        <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`}</style>
      </div>
    )
  }

  const blocksByPage = (pageIndex: number): TextBlock[] =>
    state.blocks.filter(b => b.page === pageIndex)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100svh', overflow: 'hidden', background: 'var(--bg)' }}>
      <Toolbar
        state={state}
        onReset={reset}
        onExport={exportAndDownload}
        onPreviewPdf={() => previewPdf(false)}
        exportError={exportError}
        showPreview={showPreview}
        onTogglePreview={() => setShowPreview(v => !v)}
        onChangeFile={() => navigate('/', { state: { docType: state.docType } })}
        onGoHome={() => navigate('/')}
        onHelp={() => setShowHelp(true)}
      />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Left panel: editable */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          borderRight: showPreview ? '1px solid var(--border)' : 'none',
          background: 'var(--bg-subtle)',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 16px',
            borderBottom: '1px solid var(--border)',
            background: 'var(--bg)',
            position: 'sticky',
            top: 0,
            zIndex: 10,
          }}>
            <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--fg-subtle)' }}>
              Editor
            </span>
            <span style={{ fontSize: 11, color: 'var(--fg-subtle)' }}>
              Clic sobre el texto para editar
            </span>
          </div>
          <div style={{ padding: 16 }}>
            <PDFViewer
              pdfBase64={state.pdfBase64}
              pageCount={state.pageCount}
              renderOverlays={(pageIndex, scale) => (
                <>
                  {blocksByPage(pageIndex).map(b => (
                    <EditableOverlay
                      key={b.block_id}
                      block={b}
                      editedText={state.edits.get(b.block_id)}
                      onEdit={edit}
                      scale={scale}
                    />
                  ))}
                </>
              )}
            />
          </div>
        </div>

        {/* Right panel: preview */}
        {showPreview && (
          <div style={{
            flex: 1,
            overflow: 'auto',
            background: 'var(--bg-subtle)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 16px',
              borderBottom: '1px solid var(--border)',
              background: 'var(--bg)',
              position: 'sticky',
              top: 0,
              zIndex: 10,
            }}>
              <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--fg-subtle)' }}>
                Vista previa
              </span>
              <span style={{ fontSize: 11, color: 'var(--fg-subtle)' }}>
                {state.edits.size === 0 ? 'Edita un campo para ver cambios' : `${state.edits.size} campo${state.edits.size !== 1 ? 's' : ''} modificado${state.edits.size !== 1 ? 's' : ''}`}
              </span>
            </div>
            <div style={{ padding: 16 }}>
              <PDFViewer
                pdfBase64={state.pdfBase64}
                pageCount={state.pageCount}
                renderOverlays={(pageIndex, scale) => (
                  <>
                    {blocksByPage(pageIndex)
                      .filter(b => state.edits.has(b.block_id))
                      .map(b => (
                        <PreviewOverlay
                          key={b.block_id}
                          block={b}
                          editedText={state.edits.get(b.block_id)!}
                          scale={scale}
                        />
                      ))}
                  </>
                )}
              />
            </div>
          </div>
        )}
      </div>

      {showHelp && (
        <HelpModal
          onClose={() => setShowHelp(false)}
          context="editor"
          docType={state.docType}
        />
      )}
    </div>
  )
}
