import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

import Connections from './Connections'
import Progress from './Progress'
import Settings from './Settings'

describe('Placeholder pages', () => {
  it('renders Connections page with heading', () => {
    render(<Connections />)
    expect(screen.getByText('Connections')).toBeInTheDocument()
    expect(screen.getByText(/Phase 2/)).toBeInTheDocument()
  })

  it('renders Progress page with heading', () => {
    render(<Progress />)
    expect(screen.getByText('Progress')).toBeInTheDocument()
    expect(screen.getByText(/Phase 3/)).toBeInTheDocument()
  })

  it('renders Settings page with heading', () => {
    render(<Settings />)
    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByText(/Phase 2/)).toBeInTheDocument()
  })
})
