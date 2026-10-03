import { useReducer } from 'react'
import type { EditorState, TextBlock } from '../types'

type InitPayload = {
  sessionId: string
  docType: 'regular' | 'fiscal'
  pdfBase64: string
  blocks: TextBlock[]
  pageCount: number
}

type Action =
  | { type: 'INIT'; payload: InitPayload }
  | { type: 'EDIT'; blockId: string; text: string }
  | { type: 'RESET' }
  | { type: 'SET_EXPORTING'; value: boolean }

const initial: EditorState = {
  sessionId: '',
  docType: 'regular',
  pdfBase64: '',
  blocks: [],
  edits: new Map(),
  isExporting: false,
  pageCount: 0,
}

function reducer(state: EditorState, action: Action): EditorState {
  switch (action.type) {
    case 'INIT':
      return { ...initial, ...action.payload, edits: new Map() }
    case 'EDIT': {
      const newEdits = new Map(state.edits)
      const block = state.blocks.find(b => b.block_id === action.blockId)
      if (block && action.text === block.text) {
        newEdits.delete(action.blockId)
      } else {
        newEdits.set(action.blockId, action.text)
      }
      return { ...state, edits: newEdits }
    }
    case 'RESET':
      return { ...state, edits: new Map() }
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
    reset: () => dispatch({ type: 'RESET' }),
    setExporting: (value: boolean) => dispatch({ type: 'SET_EXPORTING', value }),
  }
}
