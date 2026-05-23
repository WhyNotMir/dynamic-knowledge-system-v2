'use client'

import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'

interface ConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  confirmLabel?: string
  confirmVariant?: 'primary' | 'danger'
  onConfirm: () => void
  loading?: boolean
}

export function ConfirmDialog({
  open, onOpenChange, title, description,
  confirmLabel = 'Confirm', confirmVariant = 'primary',
  onConfirm, loading,
}: ConfirmDialogProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay style={{
          position: 'fixed', inset: 0,
          background: 'oklch(0.2 0.015 260 / 0.35)',
          zIndex: 100,
        }} />
        <Dialog.Content style={{
          position: 'fixed',
          top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          background: 'var(--surface)',
          border: '1px solid var(--rule-strong)',
          borderRadius: '4px',
          padding: '24px',
          zIndex: 101,
          width: '400px',
          maxWidth: 'calc(100vw - 32px)',
          boxShadow: '0 20px 60px oklch(0.2 0.02 260 / 0.2)',
        }}>
          <Dialog.Title style={{ fontSize: '17px', fontWeight: 500, margin: '0 0 8px', color: 'var(--ink)' }}>
            {title}
          </Dialog.Title>
          {description && (
            <Dialog.Description style={{ fontSize: '13.5px', color: 'var(--ink-2)', margin: '0 0 20px', lineHeight: 1.55 }}>
              {description}
            </Dialog.Description>
          )}
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <Dialog.Close asChild>
              <button className="btn">Cancel</button>
            </Dialog.Close>
            <button
              className={`btn ${confirmVariant === 'danger' ? 'btn--rust' : 'btn--primary'}`}
              onClick={onConfirm}
              disabled={loading}
            >
              {loading ? 'Working…' : confirmLabel}
            </button>
          </div>
          <Dialog.Close asChild>
            <button className="btn btn--ghost btn--icon" style={{ position: 'absolute', top: '12px', right: '12px' }}>
              <X size={14} />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
