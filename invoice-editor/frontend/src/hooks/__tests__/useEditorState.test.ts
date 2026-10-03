import { renderHook, act } from '@testing-library/react'
import { useEditorState } from '../useEditorState'
import type { TextBlock } from '../../types'

const block: TextBlock = {
  block_id: 'b1',
  page: 0,
  x0: 10, y0: 20, x1: 100, y1: 30,
  text: 'Original',
  font: 'Helvetica',
  size: 12,
  color: [0, 0, 0],
  flags: 0,
  editable: true,
}

const initPayload = {
  sessionId: 'sess1',
  docType: 'regular' as const,
  pdfBase64: 'abc',
  blocks: [block],
  pageCount: 1,
}

test('init populates state', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.init(initPayload))
  expect(result.current.state.sessionId).toBe('sess1')
  expect(result.current.state.blocks).toHaveLength(1)
  expect(result.current.state.edits.size).toBe(0)
})

test('edit stores new text', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.init(initPayload))
  act(() => result.current.edit('b1', 'Nuevo'))
  expect(result.current.state.edits.get('b1')).toBe('Nuevo')
})

test('reset clears edits', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.init(initPayload))
  act(() => result.current.edit('b1', 'Nuevo'))
  act(() => result.current.reset())
  expect(result.current.state.edits.size).toBe(0)
})

test('setExporting updates flag', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.setExporting(true))
  expect(result.current.state.isExporting).toBe(true)
})
