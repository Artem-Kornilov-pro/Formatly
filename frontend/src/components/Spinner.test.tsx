import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Spinner } from './Spinner'

describe('Spinner', () => {
  it('announces the default loading label to assistive tech', () => {
    render(<Spinner />)

    expect(screen.getByRole('status', { name: 'Loading…' })).toBeInTheDocument()
  })

  it('accepts a custom label', () => {
    render(<Spinner label="Saving settings…" />)

    expect(screen.getByRole('status', { name: 'Saving settings…' })).toBeInTheDocument()
  })
})
