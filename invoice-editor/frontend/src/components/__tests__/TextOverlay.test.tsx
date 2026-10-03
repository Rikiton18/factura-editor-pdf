import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { EditableOverlay } from '../TextOverlay'
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
