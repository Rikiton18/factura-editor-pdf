import { useRef, useState } from 'react'

interface FileDropzoneProps {
  label: string
  onFile: (file: File) => void
  disabled?: boolean
}

export function FileDropzone({ label, onFile, disabled = false }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const handleFile = (file: File) => {
    if (file.type === 'application/pdf') onFile(file)
  }

  return (
    <div
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => {
        e.preventDefault()
        setDragging(false)
        const file = e.dataTransfer.files[0]
        if (file) handleFile(file)
      }}
      style={{
        border: `2px dashed ${dragging ? '#2563eb' : '#9ca3af'}`,
        borderRadius: 8,
        padding: '32px 24px',
        textAlign: 'center',
        cursor: disabled ? 'not-allowed' : 'pointer',
        backgroundColor: dragging ? '#eff6ff' : '#f9fafb',
        opacity: disabled ? 0.6 : 1,
        marginBottom: 16,
      }}
    >
      <p style={{ margin: 0, fontWeight: 600 }}>{label}</p>
      <p style={{ margin: '8px 0 0', color: '#6b7280', fontSize: 14 }}>
        Arrastra un PDF aquí o haz clic para seleccionar
      </p>
      <input
        ref={inputRef}
        data-testid="file-input"
        type="file"
        accept=".pdf,application/pdf"
        style={{ display: 'none' }}
        onChange={e => {
          const file = e.target.files?.[0]
          if (file) handleFile(file)
          e.target.value = ''
        }}
      />
    </div>
  )
}
