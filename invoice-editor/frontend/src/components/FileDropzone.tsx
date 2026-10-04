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
  const [focused, setFocused] = useState(false)

  const handleFile = (file: File) => {
    if (file.type === 'application/pdf') onFile(file)
  }

  const highlighted = dragging || focused

  return (
    <div style={{
      background: highlighted ? 'var(--grad)' : 'var(--border)',
      padding: highlighted ? 2 : 1.5,
      borderRadius: 'var(--r-lg)',
      transition: 'all var(--t)',
      boxShadow: highlighted ? 'var(--shadow-md)' : 'var(--shadow-sm)',
    }}>
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
        onFocus={() => !disabled && setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          borderRadius: 'calc(var(--r-lg) - 2px)',
          padding: '26px 18px',
          textAlign: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          background: highlighted ? 'var(--bg-subtle)' : 'var(--bg)',
          opacity: disabled ? 0.5 : 1,
          transition: 'background var(--t)',
          outline: 'none',
          userSelect: 'none',
        }}
      >
        <div style={{
          width: 48,
          height: 48,
          borderRadius: 'var(--r)',
          background: highlighted ? 'var(--grad)' : 'var(--bg-muted)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 22,
          margin: '0 auto 14px',
          transition: 'all var(--t)',
          boxShadow: highlighted ? 'var(--shadow-sm)' : 'none',
        }}>
          {icon}
        </div>
        <p style={{
          fontWeight: 600,
          fontSize: 14,
          color: highlighted ? 'var(--accent)' : 'var(--fg)',
          marginBottom: 5,
          transition: 'color var(--t)',
        }}>
          {label}
        </p>
        <p style={{ fontSize: 12, color: 'var(--fg-muted)', marginBottom: 8, lineHeight: 1.4 }}>
          {description}
        </p>
        <p style={{ fontSize: 11, color: 'var(--fg-subtle)' }}>
          Arrastra o haz clic para seleccionar
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
    </div>
  )
}
