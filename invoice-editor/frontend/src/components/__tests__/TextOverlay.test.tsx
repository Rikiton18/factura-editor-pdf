import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { EditableOverlay, PreviewOverlay } from '../TextOverlay'
import type { TextBlock } from '../../types'

const block: TextBlock = {
  block_id: 'b1', page: 0,
  x0: 10, y0: 20, x1: 200, y1: 35,
  text: 'Texto original', font: 'helv', size: 12,
  color: [0, 0, 0], flags: 0, editable: true,
}

test('renders original text', () => {
  render(<EditableOverlay block={block} onEdit={vi.fn()} scale={1} />)
  expect(screen.getByText('Texto original')).toBeInTheDocument()
})

test('renders edited text when provided', () => {
  render(<EditableOverlay block={block} editedText="Nuevo" onEdit={vi.fn()} scale={1} />)
  expect(screen.getByText('Nuevo')).toBeInTheDocument()
})

test('activates input on click', () => {
  render(<EditableOverlay block={block} onEdit={vi.fn()} scale={1} />)
  fireEvent.click(screen.getByText('Texto original'))
  expect(screen.getByRole('textbox')).toBeInTheDocument()
})

test('calls onEdit when typing', () => {
  const onEdit = vi.fn()
  render(<EditableOverlay block={block} onEdit={onEdit} scale={1} />)
  fireEvent.click(screen.getByText('Texto original'))
  fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Cambiado' } })
  expect(onEdit).toHaveBeenCalledWith('b1', 'Cambiado')
})

// ── editing must look like the exported PDF and stay readable ────────────────

const boldBlock: TextBlock = { ...block, font: 'Helvetica-Bold' }

function openEditor(target: TextBlock, scale = 1) {
  render(<EditableOverlay block={target} onEdit={vi.fn()} scale={scale} />)
  fireEvent.click(screen.getByText(target.text))
  return screen.getByRole('textbox') as HTMLInputElement
}

test('edit field uses Helvetica, the font the PDF is exported with', () => {
  expect(openEditor(block).style.fontFamily).toMatch(/Helvetica/)
})

test('edit field keeps the block font size at the current zoom', () => {
  expect(openEditor(block, 2).style.fontSize).toBe('24px')
})

test('regular blocks are edited in normal weight', () => {
  expect(openEditor(block).style.fontWeight).toBe('400')
})

test('bold blocks are edited in bold', () => {
  expect(openEditor(boldBlock).style.fontWeight).toBe('700')
})

test('edit field is at least 24px tall even when the text is small', () => {
  const small: TextBlock = { ...block, size: 6, y0: 20, y1: 26 }

  expect(parseFloat(openEditor(small).style.height)).toBeGreaterThanOrEqual(24)
})

test('edit field is centred vertically on the block', () => {
  const small: TextBlock = { ...block, size: 6, y0: 20, y1: 26 }
  const input = openEditor(small)

  expect(parseFloat(input.style.top) + parseFloat(input.style.height) / 2).toBeCloseTo(23, 0)
})

test('edit field is never narrower than the block and keeps its left edge', () => {
  const input = openEditor(block)

  expect(parseFloat(input.style.width)).toBeGreaterThanOrEqual(190)
  expect(input.style.left).toBe('10px')
})

test('edit field widens when the text is longer than the block', () => {
  const long: TextBlock = { ...block, text: 'x'.repeat(80) }

  expect(parseFloat(openEditor(long).style.width)).toBeGreaterThan(190)
})

test('edit field has a minimum width for very short text', () => {
  const tiny: TextBlock = { ...block, text: '1', x1: 20 }

  expect(parseFloat(openEditor(tiny).style.width)).toBeGreaterThanOrEqual(80)
})

test('edited text shown on the page keeps the font and weight', () => {
  render(<EditableOverlay block={boldBlock} editedText="Nuevo" onEdit={vi.fn()} scale={1} />)
  const shown = screen.getByText('Nuevo')

  expect(shown.style.fontFamily).toMatch(/Helvetica/)
  expect(shown.style.fontWeight).toBe('700')
})

// ── choosing a font while editing ────────────────────────────────────────────

function openEditorWithFonts(props: { font?: string; onFontChange?: (id: string, font: string) => void }) {
  render(<EditableOverlay block={block} onEdit={vi.fn()} scale={1} {...props} />)
  fireEvent.click(screen.getByText(block.text))
}

test('shows the four font choices while editing', () => {
  openEditorWithFonts({ onFontChange: vi.fn() })

  for (const name of ['Helvetica', 'Helvetica negrita', 'Courier', 'Courier negrita']) {
    expect(screen.getByRole('button', { name })).toBeInTheDocument()
  }
})

test('choosing a font reports it and keeps the editor open', () => {
  const onFontChange = vi.fn()
  openEditorWithFonts({ onFontChange })

  fireEvent.click(screen.getByRole('button', { name: 'Courier negrita' }))

  expect(onFontChange).toHaveBeenCalledWith('b1', 'Courier-Bold')
  expect(screen.getByRole('textbox')).toBeInTheDocument()
})

test('font buttons do not take focus away from the edit field', () => {
  openEditorWithFonts({ onFontChange: vi.fn() })

  // fireEvent returns false when the event's default was prevented
  expect(fireEvent.mouseDown(screen.getByRole('button', { name: 'Courier' }))).toBe(false)
})

test('the font in use is marked as pressed', () => {
  openEditorWithFonts({ font: 'Courier', onFontChange: vi.fn() })

  expect(screen.getByRole('button', { name: 'Courier' })).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getByRole('button', { name: 'Helvetica' })).toHaveAttribute('aria-pressed', 'false')
})

test('no font choices are shown when nothing handles the change', () => {
  openEditorWithFonts({})

  expect(screen.queryByRole('button', { name: 'Courier' })).not.toBeInTheDocument()
})

test('the chosen font changes the edit field typeface and weight', () => {
  openEditorWithFonts({ font: 'Courier-Bold', onFontChange: vi.fn() })
  const input = screen.getByRole('textbox') as HTMLInputElement

  expect(input.style.fontFamily).toMatch(/Courier/)
  expect(input.style.fontWeight).toBe('700')
})

test('edited text on the page uses the chosen font', () => {
  render(<EditableOverlay block={block} editedText="Nuevo" font="Courier" onEdit={vi.fn()} scale={1} />)
  const shown = screen.getByText('Nuevo')

  expect(shown.style.fontFamily).toMatch(/Courier/)
  expect(shown.style.fontWeight).toBe('400')
})

test('preview overlay uses the chosen font', () => {
  render(<PreviewOverlay block={block} editedText="Listo" font="Courier-Bold" scale={1} />)
  const shown = screen.getByText('Listo')

  expect(shown.style.fontFamily).toMatch(/Courier/)
  expect(shown.style.fontWeight).toBe('700')
})

test('preview overlay keeps the font and weight', () => {
  render(<PreviewOverlay block={boldBlock} editedText="Listo" scale={1} />)
  const shown = screen.getByText('Listo')

  expect(shown.style.fontFamily).toMatch(/Helvetica/)
  expect(shown.style.fontWeight).toBe('700')
})
