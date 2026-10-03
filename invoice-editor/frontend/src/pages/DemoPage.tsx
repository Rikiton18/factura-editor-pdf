// invoice-editor/frontend/src/pages/DemoPage.tsx
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getDemoData } from '../api/client'
import type { DemoData, DemoBlock } from '../types'
import '../styles/demo.css'

function findBlock(blocks: DemoBlock[], keywords: string[]): string {
  for (const b of blocks) {
    if (keywords.some(k => b.text.toLowerCase().includes(k.toLowerCase()))) {
      return b.text
    }
  }
  return '—'
}

export function DemoPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [data, setData] = useState<DemoData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    document.body.classList.add('dgi-demo')
    return () => document.body.classList.remove('dgi-demo')
  }, [])

  useEffect(() => {
    if (!sessionId) return
    getDemoData(sessionId)
      .then(r => setData(r.data))
      .catch(() => setError('Sesión no encontrada o expirada.'))
  }, [sessionId])

  if (error) return (
    <>
      <div className="sim-banner">⚠ SIMULACIÓN — Esta página es una demostración educativa del sistema DGI de Panamá</div>
      <div style={{ padding: 24 }}>{error}</div>
    </>
  )

  if (!data) return (
    <>
      <div className="sim-banner">⚠ SIMULACIÓN — Esta página es una demostración educativa del sistema DGI de Panamá</div>
      <div style={{ padding: 24 }}>Cargando...</div>
    </>
  )

  const blocks = data.blocks

  const cufe = findBlock(blocks, ['CUFE', 'FE01', 'FE02', 'FE03'])
  const protocolo = findBlock(blocks, ['Protocolo', 'Autorización', 'protocolo'])
  const fecha = findBlock(blocks, ['Fecha', 'fecha', 'Emisión', 'emisión'])
  const pageBlocks = blocks.filter(b => b.page === 0)

  return (
    <>
      <div className="sim-banner">
        ⚠ SIMULACIÓN — Esta página es una demostración educativa del sistema DGI de Panamá
      </div>

      <div className="dgi-header">
        <div>
          <p className="subtitle">REPÚBLICA DE PANAMÁ</p>
          <h1>Sistema de Factura Electrónica — DGI</h1>
          <p className="subtitle">Ministerio de Economía y Finanzas</p>
        </div>
      </div>

      <link
        rel="stylesheet"
        href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"
        crossOrigin="anonymous"
      />

      <div className="container-fluid" style={{ padding: '16px 24px' }}>
        <div className="row">

          <div className="col-sm-3">
            <div className="panel panel-default">
              <div className="panel-heading">
                Comprobante Auxiliar de Factura Electrónica
              </div>
              <div className="panel-body" style={{ padding: '12px' }}>
                <hr style={{ margin: '8px 0' }} />
                <p style={{ fontWeight: 600, marginBottom: 4, fontSize: 13 }}>Criterio de Búsqueda</p>
                <label style={{ fontSize: 12, color: '#555' }}>* CUFE</label>
                <div className="cufe-input">{cufe}</div>
                <div style={{ marginTop: 12, display: 'flex', gap: 6 }}>
                  <button
                    className="btn btn-primary btn-sm"
                    style={{ backgroundColor: '#003366', borderColor: '#003366', fontSize: 12 }}
                    disabled
                  >
                    Consultar
                  </button>
                  <button className="btn btn-default btn-sm" style={{ fontSize: 12 }} disabled>
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="col-sm-9">
            <div className="alert-dgi">
              Esta es una simulación con fines didácticos. El documento mostrado no tiene validez fiscal.
            </div>

            <div className="panel panel-default" style={{ marginBottom: 12 }}>
              <div className="section-title">COMPROBANTE AUXILIAR DE FACTURA ELECTRÓNICA</div>
              <div className="panel-body" style={{ padding: '12px 16px' }}>
                <table className="dgi-table">
                  <tbody>
                    <tr>
                      <td style={{ width: '30%', fontWeight: 600 }}>Tipo de Comprobante</td>
                      <td>{findBlock(blocks, ['Factura de Operación', 'Interna', 'CAFE'])}</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600 }}>CUFE</td>
                      <td style={{ fontSize: 11, wordBreak: 'break-all' }}>{cufe}</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600 }}>Protocolo de Autorización</td>
                      <td style={{ fontSize: 11 }}>{protocolo}</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600 }}>Fecha y Hora de Emisión</td>
                      <td>{fecha}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="panel panel-default" style={{ marginBottom: 12 }}>
              <div className="section-title">DATOS DEL DOCUMENTO</div>
              <div className="panel-body" style={{ padding: 0 }}>
                <table className="dgi-table">
                  <thead>
                    <tr>
                      <th style={{ width: '40%' }}>Campo</th>
                      <th>Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pageBlocks.map(b => (
                      <tr key={b.block_id}>
                        <td style={{ color: '#6b7280', fontSize: 11 }}>
                          {Math.round(b.y0)},{Math.round(b.x0)}
                        </td>
                        <td>{b.text}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ fontSize: 11, color: '#6b7280', borderTop: '1px solid #e5e7eb', paddingTop: 8 }}>
              {findBlock(blocks, ['Soluciones', 'R.U.C', 'Punto de Venta', 'Impresor'])}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
