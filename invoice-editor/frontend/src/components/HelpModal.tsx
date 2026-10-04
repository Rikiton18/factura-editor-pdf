import { useEffect } from 'react'

interface HelpModalProps {
  onClose: () => void
  context?: 'upload' | 'editor'
  docType?: 'regular' | 'fiscal'
}

const S = {
  backdrop: {
    position: 'fixed' as const,
    inset: 0,
    background: 'rgba(0,0,0,0.5)',
    backdropFilter: 'blur(4px)',
    WebkitBackdropFilter: 'blur(4px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '24px',
  },
  panel: {
    background: 'var(--bg)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--r-lg)',
    width: '100%',
    maxWidth: 640,
    maxHeight: '85vh',
    display: 'flex',
    flexDirection: 'column' as const,
    boxShadow: 'var(--shadow-md)',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '20px 24px',
    background: 'var(--grad)',
    flexShrink: 0,
  },
  title: {
    fontSize: 16,
    fontWeight: 600,
    letterSpacing: '-0.01em',
    color: 'white',
  },
  closeBtn: {
    width: 28,
    height: 28,
    borderRadius: 'var(--r-sm)',
    border: '1px solid rgba(255,255,255,0.3)',
    background: 'rgba(255,255,255,0.15)',
    color: 'white',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 14,
    transition: 'background var(--t)',
  },
  body: {
    overflowY: 'auto' as const,
    padding: '0 24px 24px',
    flex: 1,
  },
  section: {
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: '0.06em',
    textTransform: 'uppercase' as const,
    color: 'var(--accent)',
    marginBottom: 12,
  },
  grid: {
    display: 'grid' as const,
    gap: 8,
  },
  item: {
    display: 'flex' as const,
    gap: 12,
    padding: '12px 14px',
    background: 'var(--bg-subtle)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--r)',
  },
  itemIcon: {
    width: 32,
    height: 32,
    background: 'var(--bg-muted)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--r-sm)',
    display: 'flex' as const,
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 14,
    flexShrink: 0,
  },
  itemContent: {
    flex: 1,
    minWidth: 0,
  },
  itemLabel: {
    fontSize: 13,
    fontWeight: 500,
    color: 'var(--fg)',
    marginBottom: 2,
  },
  itemDesc: {
    fontSize: 12,
    color: 'var(--fg-muted)',
    lineHeight: 1.5,
  },
  kbd: {
    display: 'inline-flex' as const,
    alignItems: 'center',
    padding: '1px 5px',
    background: 'var(--bg-muted)',
    border: '1px solid var(--border-strong)',
    borderRadius: 4,
    fontSize: 11,
    fontFamily: 'var(--font-mono)',
    color: 'var(--fg-muted)',
    marginLeft: 4,
  },
  tip: {
    marginTop: 16,
    padding: '12px 14px',
    background: 'var(--info-bg)',
    border: '1px solid var(--info-border)',
    borderRadius: 'var(--r)',
    fontSize: 13,
    color: 'var(--info)',
    lineHeight: 1.5,
  },
}

export function HelpModal({ onClose, context = 'editor', docType }: HelpModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div style={S.backdrop} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={S.panel}>
        <header style={S.header}>
          <span style={S.title}>
            {context === 'upload' ? 'Cómo usar el editor' : 'Guía del editor'}
          </span>
          <button
            style={S.closeBtn}
            onClick={onClose}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.25)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.15)')}
            aria-label="Cerrar ayuda"
          >
            ✕
          </button>
        </header>

        <div style={S.body}>
          {context === 'upload' && (
            <>
              <div style={S.section}>
                <p style={S.sectionTitle}>Pantalla de inicio</p>
                <div style={S.grid}>
                  <div style={S.item}>
                    <div style={S.itemIcon}>📄</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Factura Regular</p>
                      <p style={S.itemDesc}>Sube una factura PDF estándar (sin validación DGI). Funciona con cualquier factura generada por software de contabilidad.</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>🏛️</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Factura Fiscal (DGI)</p>
                      <p style={S.itemDesc}>Sube una factura fiscal panameña que contiene código QR de la DGI. Al exportar, puedes regenerar el QR con un enlace al portal demo.</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>🔎</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Arrastrar y soltar</p>
                      <p style={S.itemDesc}>Arrastra un archivo PDF directamente sobre cualquiera de las zonas, o haz clic para abrir el selector de archivos. Solo se aceptan archivos .pdf (máximo 20 MB).</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>🎯</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Demo con datos de prueba</p>
                      <p style={S.itemDesc}>Botón "Cargar demo" — abre una sesión con datos pre-cargados sin necesidad de subir ningún archivo. Ideal para explorar el editor.</p>
                    </div>
                  </div>
                </div>
              </div>
              <div style={S.tip}>
                💡 El sistema detecta automáticamente si el PDF fue escaneado (imagen) y usará reconocimiento óptico de caracteres (OCR) para extraer los bloques de texto.
              </div>
            </>
          )}

          {context === 'editor' && (
            <>
              <div style={S.section}>
                <p style={S.sectionTitle}>Barra de herramientas</p>
                <div style={S.grid}>
                  <div style={S.item}>
                    <div style={S.itemIcon}>←</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Inicio</p>
                      <p style={S.itemDesc}>Vuelve a la pantalla de carga. Los cambios no guardados se perderán.</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>🔄</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Cambiar factura</p>
                      <p style={S.itemDesc}>Sube una nueva factura del mismo tipo ({docType === 'fiscal' ? 'fiscal' : 'regular'}) sin volver a la pantalla de inicio.</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>↩️</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Resetear cambios</p>
                      <p style={S.itemDesc}>Deshace todos los campos editados y regresa al texto original. Se activa solo cuando hay cambios pendientes.</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>👁</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Vista previa / Ocultar</p>
                      <p style={S.itemDesc}>Muestra u oculta el panel derecho con la vista previa en tiempo real. Útil en pantallas pequeñas para tener más espacio de edición.</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>🔍</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Ver PDF</p>
                      <p style={S.itemDesc}>Genera y abre el PDF con todos los cambios aplicados en una pestaña nueva. Útil para revisar antes de descargar.</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>⬇️</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Exportar PDF</p>
                      <p style={S.itemDesc}>Descarga el PDF final con todos los cambios incorporados. El archivo es visualmente idéntico al original, solo con los textos reemplazados.</p>
                    </div>
                  </div>
                  {docType === 'fiscal' && (
                    <div style={S.item}>
                      <div style={S.itemIcon}>QR</div>
                      <div style={S.itemContent}>
                        <p style={S.itemLabel}>Exportar + Regenerar QR</p>
                        <p style={S.itemDesc}>Exporta el PDF y además reemplaza el código QR original con uno nuevo que apunta al portal demo de la DGI. Útil para practicar la verificación de facturas electrónicas.</p>
                      </div>
                    </div>
                  )}
                  <div style={S.item}>
                    <div style={S.itemIcon}>?</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Ayuda</p>
                      <p style={S.itemDesc}>Abre esta guía. También puedes usar <kbd style={S.kbd}>?</kbd> en cualquier momento.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div style={S.section}>
                <p style={S.sectionTitle}>Panel izquierdo — Editor</p>
                <div style={S.grid}>
                  <div style={S.item}>
                    <div style={S.itemIcon}>📝</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Hacer clic sobre el texto</p>
                      <p style={S.itemDesc}>Cada bloque de texto del PDF es clickeable. Al hacer clic, aparece un campo de texto editable en su posición exacta dentro del documento.</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>✏️</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Editar el texto</p>
                      <p style={S.itemDesc}>Escribe el nuevo valor. Los bloques editados se resaltan con borde verde punteado. Presiona <kbd style={S.kbd}>Enter</kbd> o haz clic fuera para confirmar.</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>🟢</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Indicador de cambios</p>
                      <p style={S.itemDesc}>El borde verde punteado indica que ese bloque fue modificado. El contador en la barra de herramientas muestra el total de campos editados.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div style={S.section}>
                <p style={S.sectionTitle}>Panel derecho — Vista previa</p>
                <div style={S.grid}>
                  <div style={S.item}>
                    <div style={S.itemIcon}>⚡</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Actualización en tiempo real</p>
                      <p style={S.itemDesc}>Cada edición aparece instantáneamente en el panel de vista previa. Los bloques editados muestran el nuevo texto sobre fondo blanco.</p>
                    </div>
                  </div>
                  <div style={S.item}>
                    <div style={S.itemIcon}>🎯</div>
                    <div style={S.itemContent}>
                      <p style={S.itemLabel}>Posición exacta</p>
                      <p style={S.itemDesc}>El texto se posiciona en las coordenadas exactas del bloque original, garantizando fidelidad visual al exportar.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div style={S.tip}>
                💡 El PDF exportado es visualmente idéntico al original: solo reemplaza los textos seleccionados usando PyMuPDF. El resto del documento (imágenes, gráficos, formato) permanece intacto.
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
