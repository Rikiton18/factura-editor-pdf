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
  pdfUrl: 'blob:http://localhost/abc',
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

test('setFont marks the block as modified and keeps its original text', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.init(initPayload))
  act(() => result.current.setFont('b1', 'Courier-Bold'))
  expect(result.current.state.fonts.get('b1')).toBe('Courier-Bold')
  expect(result.current.state.edits.get('b1')).toBe('Original')
})

test('setFont keeps the text already typed', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.init(initPayload))
  act(() => result.current.edit('b1', 'Nuevo'))
  act(() => result.current.setFont('b1', 'Courier'))
  expect(result.current.state.edits.get('b1')).toBe('Nuevo')
})

test('choosing the detected font again clears the override and the edit', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.init(initPayload))
  act(() => result.current.setFont('b1', 'Courier'))
  act(() => result.current.setFont('b1', 'Helvetica'))
  expect(result.current.state.fonts.has('b1')).toBe(false)
  expect(result.current.state.edits.has('b1')).toBe(false)
})

test('choosing the detected font again keeps a text edit', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.init(initPayload))
  act(() => result.current.edit('b1', 'Nuevo'))
  act(() => result.current.setFont('b1', 'Courier'))
  act(() => result.current.setFont('b1', 'Helvetica'))
  expect(result.current.state.fonts.has('b1')).toBe(false)
  expect(result.current.state.edits.get('b1')).toBe('Nuevo')
})

test('typing the original text back keeps a block that has a font override', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.init(initPayload))
  act(() => result.current.edit('b1', 'Nuevo'))
  act(() => result.current.setFont('b1', 'Courier'))
  act(() => result.current.edit('b1', 'Original'))
  expect(result.current.state.edits.get('b1')).toBe('Original')
  expect(result.current.state.fonts.get('b1')).toBe('Courier')
})

test('reset clears font overrides too', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.init(initPayload))
  act(() => result.current.setFont('b1', 'Courier'))
  act(() => result.current.reset())
  expect(result.current.state.fonts.size).toBe(0)
  expect(result.current.state.edits.size).toBe(0)
})

test('setExporting updates flag', () => {
  const { result } = renderHook(() => useEditorState())
  act(() => result.current.setExporting(true))
  expect(result.current.state.isExporting).toBe(true)
})
