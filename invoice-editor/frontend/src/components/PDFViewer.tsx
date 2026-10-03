import { useState, useRef, useEffect } from 'react'
import { Document, Page } from 'react-pdf'
import 'react-pdf/dist/Page/TextLayer.css'
import 'react-pdf/dist/Page/AnnotationLayer.css'

interface PDFViewerProps {
  pdfBase64: string
  pageCount: number
  // Render overlays for each page. Receives page index (0-based) and the
  // computed scale factor (rendered_width / pdf_page_width_in_points).
  renderOverlays?: (pageIndex: number, scale: number) => React.ReactNode
}

export function PDFViewer({ pdfBase64, pageCount, renderOverlays }: PDFViewerProps) {
  const [pageWidths, setPageWidths] = useState<number[]>([])
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerWidth, setContainerWidth] = useState(600)

  useEffect(() => {
    if (!containerRef.current) return
    const observer = new ResizeObserver(entries => {
      setContainerWidth(entries[0].contentRect.width || 600)
    })
    observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  const file = `data:application/pdf;base64,${pdfBase64}`

  return (
    <div ref={containerRef} style={{ width: '100%' }}>
      <Document file={file}>
        {Array.from({ length: pageCount }, (_, i) => {
          const naturalWidth = pageWidths[i] ?? 612
          const scale = containerWidth / naturalWidth
          return (
            <div key={i} style={{ position: 'relative', marginBottom: 16 }}>
              <Page
                pageNumber={i + 1}
                width={containerWidth}
                renderTextLayer={false}
                renderAnnotationLayer={false}
                onLoadSuccess={(p) => {
                  setPageWidths(prev => {
                    const next = [...prev]
                    next[i] = p.originalWidth
                    return next
                  })
                }}
              />
              {renderOverlays?.(i, scale)}
            </div>
          )
        })}
      </Document>
    </div>
  )
}
