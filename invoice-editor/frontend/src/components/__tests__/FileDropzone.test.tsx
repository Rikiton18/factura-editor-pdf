import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { FileDropzone } from '../FileDropzone'

test('renders label', () => {
  render(<FileDropzone label="Factura Regular" description="Desc" icon="📄" onFile={vi.fn()} />)
  expect(screen.getByText('Factura Regular')).toBeInTheDocument()
})

test('calls onFile when file selected via input', () => {
  const onFile = vi.fn()
  render(<FileDropzone label="Test" description="Desc" icon="📄" onFile={onFile} />)
  const input = screen.getByTestId('file-input')
  const file = new File(['%PDF'], 'test.pdf', { type: 'application/pdf' })
  fireEvent.change(input, { target: { files: [file] } })
  expect(onFile).toHaveBeenCalledWith(file)
})
