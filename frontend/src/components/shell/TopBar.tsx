'use client'

import Link from 'next/link'
import { Search } from 'lucide-react'
import { useState } from 'react'
import type { Project } from '@/lib/types'

interface TopBarProps {
  project: Project
  breadcrumbs?: { label: string; href?: string }[]
}

export function TopBar({ project, breadcrumbs }: TopBarProps) {
  const [searchFocused, setSearchFocused] = useState(false)

  return (
    <div style={{
      height: 'var(--shell-topbar)',
      flexShrink: 0,
      display: 'grid',
      gridTemplateColumns: '1fr minmax(280px, 480px) 1fr',
      alignItems: 'center',
      padding: '0 18px',
      borderBottom: '1px solid var(--rule)',
      background: 'var(--paper)',
      gap: '14px',
    }}>
      {/* Breadcrumbs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--graphite)' }}>
        <Link href={`/${project.id}/`} style={{ letterSpacing: '0.005em' }}>
          {project.name}
        </Link>
        {breadcrumbs?.map((crumb, i) => (
          <span key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--whisper)', fontSize: '11px' }}>›</span>
            {crumb.href
              ? <Link href={crumb.href} style={{ letterSpacing: '0.005em' }}>{crumb.label}</Link>
              : <span style={{ color: 'var(--ink)', fontWeight: 500 }}>{crumb.label}</span>
            }
          </span>
        ))}
      </div>

      {/* Search */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '14px 1fr auto',
        gap: '9px',
        alignItems: 'center',
        padding: '5px 9px',
        border: `1px solid ${searchFocused ? 'var(--ink-2)' : 'var(--rule)'}`,
        borderRadius: '3px',
        background: 'var(--surface)',
        color: 'var(--graphite)',
        transition: 'border-color 0.12s',
      }}>
        <Search size={13} />
        <input
          placeholder="Search articles, fragments…"
          style={{
            border: 0, outline: 0, background: 'transparent',
            font: 'inherit', color: 'var(--ink)', width: '100%',
            fontSize: '12.5px',
          }}
          onFocus={() => setSearchFocused(true)}
          onBlur={() => setSearchFocused(false)}
        />
        <span className="kbd">⌘K</span>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'flex-end' }}>
        <div style={{
          width: 26, height: 26, borderRadius: '50%',
          background: 'oklch(0.55 0.06 145)',
          color: 'var(--paper)',
          display: 'grid', placeItems: 'center',
          fontSize: '10.5px', fontWeight: 500, letterSpacing: '0.02em',
        }}>
          M
        </div>
      </div>
    </div>
  )
}
