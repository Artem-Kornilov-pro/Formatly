import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the Formatly heading', () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('no backend in tests'))))

    render(<App />)

    expect(screen.getByRole('heading', { name: 'Formatly' })).toBeInTheDocument()
  })
})
