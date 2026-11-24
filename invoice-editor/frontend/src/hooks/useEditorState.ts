import { useReducer } from 'react'
import type { EditorState, TextBlock } from '../types'

type InitPayload = {
  sessionId: string
  docType: 'regular' | 'fiscal'
  pdfUrl: string
  blocks: TextBlock[]
  pageCount: number
}

type Action =
  | { type: 'INIT'; payload: InitPayload }
  | { type: 'EDIT'; blockId: string; text: string }
  | { type: 'SET_FONT'; blockId: string; font: string }
  | { type: 'RESET' }
  | { type: 'SET_EXPORTING'; value: boolean }

const initial: EditorState = {
  sessionId: '',
  docType: 'regular',
  pdfUrl: '',
  blocks: [],
  edits: new Map(),
  fonts: new Map(),
  isExporting: false,
  pageCount: 0,
}

function reducer(state: EditorState, action: Action): EditorState {
  switch (action.type) {
    case 'INIT':
      return { ...initial, ...action.payload, edits: new Map(), fonts: new Map() }
    case 'EDIT': {
      const newEdits = new Map(state.edits)
      const block = state.blocks.find(b => b.block_id === action.blockId)
      // A block stays modified while it has a font override, even with its original text.
      const unchanged = block && action.text === block.text && !state.fonts.has(action.blockId)
      if (unchanged) {
        newEdits.delete(action.blockId)
      } else {
        newEdits.set(action.blockId, action.text)
      }
      return { ...state, edits: newEdits }
    }
    case 'SET_FONT': {
      const block = state.blocks.find(b => b.block_id === action.blockId)
      if (!block) return state
      const fonts = new Map(state.fonts)
      const edits = new Map(state.edits)
      if (action.font === block.font) {
        fonts.delete(action.blockId)
      } else {
        fonts.set(action.blockId, action.font)
      }
      // The block is redrawn on export, so it needs an edit entry even if its text is unchanged.
      const text = edits.get(action.blockId) ?? block.text
      if (fonts.has(action.blockId) || text !== block.text) {
        edits.set(action.blockId, text)
      } else {
        edits.delete(action.blockId)
      }
      return { ...state, fonts, edits }
    }
    case 'RESET':
      return { ...state, edits: new Map(), fonts: new Map() }
    case 'SET_EXPORTING':
      return { ...state, isExporting: action.value }
  }
}

export function useEditorState() {
  const [state, dispatch] = useReducer(reducer, initial)
  return {
    state,
    init: (payload: InitPayload) => dispatch({ type: 'INIT', payload }),
    edit: (blockId: string, text: string) => dispatch({ type: 'EDIT', blockId, text }),
    setFont: (blockId: string, font: string) => dispatch({ type: 'SET_FONT', blockId, font }),
    reset: () => dispatch({ type: 'RESET' }),
    setExporting: (value: boolean) => dispatch({ type: 'SET_EXPORTING', value }),
  }
}
