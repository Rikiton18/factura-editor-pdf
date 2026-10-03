import { useEffect, useState } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { useEditorState } from '../hooks/useEditorState'
import { useExport } from '../hooks/useExport'
import { PDFViewer } from '../components/PDFViewer'
import { EditableOverlay, PreviewOverlay } from '../components/TextOverlay'
import { Toolbar } from '../components/Toolbar'
import type { TextBlock } from '../types'

export function EditorPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const { state, init, edit, reset, setExporting } = useEditorState()
  const { doExport, exportError } = useExport(state, setExporting)
  const [showPreview, setShowPreview] = useState(true)

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

  if (!state.pdfBase64) return <p style={{ padding: 24 }}>Cargando...</p>

  const blocksByPage = (pageIndex: number): TextBlock[] =>
    state.blocks.filter(b => b.page === pageIndex)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Toolbar
        state={state}
        onReset={reset}
        onExport={doExport}
        exportError={exportError}
        showPreview={showPreview}
        onTogglePreview={() => setShowPreview(v => !v)}
        onChangeFile={() => navigate('/', { state: { docType: state.docType } })}
        onGoHome={() => navigate('/')}
      />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Left panel: editable */}
        <div style={{ flex: 1, overflow: 'auto', borderRight: '1px solid #e5e7eb', padding: 16 }}>
          <p style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>
            Haz clic en cualquier texto para editarlo
          </p>
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

        {/* Right panel: preview */}
        {showPreview && <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
          <p style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>
            Vista previa en tiempo real
          </p>
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
    </div>
  )
}
