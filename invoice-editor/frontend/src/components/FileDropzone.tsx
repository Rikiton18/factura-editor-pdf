import { useRef, useState } from 'react'

interface FileDropzoneProps {
  label: string
  description: string
  icon: string
  onFile: (file: File) => void
  disabled?: boolean
}

export function FileDropzone({ label, description, icon, onFile, disabled = false }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const handleFile = (file: File) => {
    if (file.type === 'application/pdf') onFile(file)
  }

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label={`Subir ${label}`}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={e => { if ((e.key === 'Enter' || e.key === ' ') && !disabled) inputRef.current?.click() }}
      onDragOver={e => { e.preventDefault(); if (!disabled) setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => {
        e.preventDefault()
        setDragging(false)
        if (disabled) return
        const file = e.dataTransfer.files[0]
        if (file) handleFile(file)
      }}
      style={{
        border: `1.5px dashed ${dragging ? 'var(--accent)' : 'var(--border-strong)'}`,
        borderRadius: 'var(--r-lg)',
        padding: '28px 24px',
        textAlign: 'center',
        cursor: disabled ? 'not-allowed' : 'pointer',
        backgroundColor: dragging ? 'var(--bg-muted)' : 'var(--bg-subtle)',
        opacity: disabled ? 0.5 : 1,
        transition: 'border-color var(--t), background-color var(--t)',
        outline: 'none',
      }}
      onFocus={e => !disabled && (e.currentTarget.style.boxShadow = '0 0 0 2px var(--accent)')}
      onBlur={e => (e.currentTarget.style.boxShadow = 'none')}
    >
      <div style={{ fontSize: 28, marginBottom: 10, lineHeight: 1 }}>{icon}</div>
      <p style={{ fontWeight: 600, fontSize: 14, color: 'var(--fg)', marginBottom: 4 }}>{label}</p>
      <p style={{ fontSize: 12, color: 'var(--fg-muted)' }}>{description}</p>
      <p style={{ fontSize: 11, color: 'var(--fg-subtle)', marginTop: 8 }}>
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
