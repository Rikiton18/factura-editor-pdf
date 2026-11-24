import { renderHook, act } from '@testing-library/react'
import { useExport } from '../useExport'
import { exportPDF } from '../../api/client'
import type { EditorState } from '../../types'

// The request is what matters here. jsdom has no URL.createObjectURL, so the code after
// the call fails and the hook reports an error, which is fine for these tests.
vi.mock('../../api/client', () => ({
  exportPDF: vi.fn().mockResolvedValue({ data: { pdf_base64: '' } }),
}))

const state: EditorState = {
  sessionId: 'sess1',
  docType: 'regular',
  pdfUrl: 'blob:http://localhost/x',
  blocks: [],
  pageCount: 1,
  isExporting: false,
  edits: new Map([['b1', 'Nuevo'], ['b2', 'Mismo texto']]),
  fonts: new Map([['b2', 'Courier-Bold']]),
}

const expectedEdits = [
  { block_id: 'b1', new_text: 'Nuevo', font: undefined },
  { block_id: 'b2', new_text: 'Mismo texto', font: 'Courier-Bold' },
]

beforeEach(() => vi.mocked(exportPDF).mockClear())

test('exporting sends the chosen font with each edit', async () => {
  const { result } = renderHook(() => useExport(state, vi.fn()))

  await act(async () => { await result.current.exportAndDownload(false) })

  expect(exportPDF).toHaveBeenCalledWith('sess1', { edits: expectedEdits, regenerate_qr: false })
})

test('previewing sends the chosen font with each edit', async () => {
  const { result } = renderHook(() => useExport(state, vi.fn()))

  await act(async () => { await result.current.previewPdf(false) })

  expect(exportPDF).toHaveBeenCalledWith('sess1', { edits: expectedEdits, regenerate_qr: false })
})
