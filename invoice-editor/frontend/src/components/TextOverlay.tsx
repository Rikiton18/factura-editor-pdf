import { useState } from 'react'
import type { TextBlock } from '../types'

interface EditableOverlayProps {
  block: TextBlock
  editedText?: string
  onEdit: (blockId: string, text: string) => void
  scale: number
}

export function EditableOverlay({ block, editedText, onEdit, scale }: EditableOverlayProps) {
  const [active, setActive] = useState(false)
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
    fontFamily: 'inherit',
  }

  if (active) {
    return (
      <input
        autoFocus
        style={{
          ...base,
          border: '1.5px solid #2563eb',
          backgroundColor: 'rgba(255,255,255,0.95)',
          outline: 'none',
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
        border: isEdited ? '1px dashed #16a34a' : '1px solid transparent',
        backgroundColor: isEdited ? 'rgba(255,255,255,0.9)' : 'transparent',
        color: isEdited ? 'inherit' : 'transparent',
        cursor: 'text',
        userSelect: 'none',
      }}
      onClick={() => setActive(true)}
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
