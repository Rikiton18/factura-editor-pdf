import { useState } from 'react'
import type { TextBlock } from '../types'

// The exported PDF draws edits in Helvetica, so the page and the edit field use
// the same face. Bold blocks are the ones the OCR measured as bold.
const FONT_FAMILY = 'Helvetica, Arial, "Liberation Sans", sans-serif'
const BOLD_FONT_NAME = 'Helvetica-Bold'

// The original OCR box is often too small to read or type in, so the edit field
// is a little larger than it, centred on it.
const MIN_EDIT_HEIGHT_PX = 24
const MIN_EDIT_WIDTH_PX = 80
const EDIT_PADDING_PX = 6
const EDIT_LINE_HEIGHT = 1.6 // field height as a multiple of the font size
const AVG_CHAR_WIDTH_EM = 0.6 // generous average advance so typed text never clips

const fontWeightOf = (block: TextBlock): 400 | 700 => (block.font === BOLD_FONT_NAME ? 700 : 400)

function editFieldBox(block: TextBlock, text: string, scale: number) {
  const fontPx = block.size * scale
  const boxWidth = (block.x1 - block.x0) * scale
  const boxHeight = (block.y1 - block.y0) * scale
  const textWidth = text.length * fontPx * AVG_CHAR_WIDTH_EM
  const width = Math.max(boxWidth, textWidth + 2 * EDIT_PADDING_PX, MIN_EDIT_WIDTH_PX)
  const height = Math.max(boxHeight, fontPx * EDIT_LINE_HEIGHT, MIN_EDIT_HEIGHT_PX)
  return {
    left: block.x0 * scale,
    top: block.y0 * scale - (height - boxHeight) / 2,
    width,
    height,
  }
}

interface EditableOverlayProps {
  block: TextBlock
  editedText?: string
  onEdit: (blockId: string, text: string) => void
  scale: number
}

export function EditableOverlay({ block, editedText, onEdit, scale }: EditableOverlayProps) {
  const [active, setActive] = useState(false)
  const [hovered, setHovered] = useState(false)
  const isEdited = editedText !== undefined
  const displayed = editedText ?? block.text

  const base: React.CSSProperties = {
    position: 'absolute',
    left: block.x0 * scale,
    top: block.y0 * scale,
    width: (block.x1 - block.x0) * scale,
    height: (block.y1 - block.y0) * scale,
    fontSize: block.size * scale,
    lineHeight: `${(block.y1 - block.y0) * scale}px`,
    boxSizing: 'border-box',
    padding: 0,
    margin: 0,
    overflow: 'hidden',
    fontFamily: FONT_FAMILY,
    fontWeight: fontWeightOf(block),
  }

  if (active) {
    return (
      <input
        autoFocus
        style={{
          ...base,
          ...editFieldBox(block, displayed, scale),
          lineHeight: 'normal',
          padding: `0 ${EDIT_PADDING_PX}px`,
          overflow: 'visible',
          border: '1.5px solid #2563eb',
          backgroundColor: '#fff',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          outline: 'none',
          zIndex: 20,
        }}
        value={displayed}
        onChange={e => onEdit(block.block_id, e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') setActive(false) }}
        onBlur={() => setActive(false)}
      />
    )
  }

  return (
    <div
      style={{
        ...base,
        border: isEdited
          ? '1px dashed #16a34a'
          : hovered
          ? '1px solid rgba(37,99,235,0.6)'
          : '1px dashed rgba(37,99,235,0.25)',
        backgroundColor: isEdited
          ? 'rgba(255,255,255,0.9)'
          : hovered
          ? 'rgba(37,99,235,0.08)'
          : 'rgba(37,99,235,0.03)',
        color: isEdited ? 'inherit' : 'transparent',
        cursor: 'text',
        userSelect: 'none',
        transition: 'border-color 0.15s, background-color 0.15s',
      }}
      onClick={() => setActive(true)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {displayed}
    </div>
  )
}

interface PreviewOverlayProps {
  block: TextBlock
  editedText: string
  scale: number
}

export function PreviewOverlay({ block, editedText, scale }: PreviewOverlayProps) {
  return (
    <div
      style={{
        position: 'absolute',
        left: block.x0 * scale,
        top: block.y0 * scale,
        width: (block.x1 - block.x0) * scale,
        height: (block.y1 - block.y0) * scale,
        backgroundColor: 'white',
        fontFamily: FONT_FAMILY,
        fontWeight: fontWeightOf(block),
        fontSize: block.size * scale,
        lineHeight: `${(block.y1 - block.y0) * scale}px`,
        overflow: 'hidden',
        boxSizing: 'border-box',
        padding: 0,
        pointerEvents: 'none',
      }}
    >
      {editedText}
    </div>
  )
}
