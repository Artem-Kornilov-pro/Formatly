import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Testing Library's automatic afterEach(cleanup) only registers when it
// detects a *global* afterEach, which requires `test.globals: true` in the
// Vite/Vitest config. This project imports `afterEach` explicitly instead of
// using globals, so without this, rendered DOM from one test silently leaks
// into the next test in the same file.
afterEach(() => {
  cleanup()
})
