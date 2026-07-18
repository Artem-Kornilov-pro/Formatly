import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

type BackendStatus = 'checking' | 'online' | 'offline'

function App() {
  const [status, setStatus] = useState<BackendStatus>('checking')

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => setStatus(res.ok ? 'online' : 'offline'))
      .catch(() => setStatus('offline'))
  }, [])

  return (
    <main className="app">
      <h1>Formatly</h1>
      <p className="tagline">
        Turn a raw .docx into a document that matches your style guide — automatically.
      </p>
      <p className={`status status--${status}`}>Backend: {status}</p>
    </main>
  )
}

export default App
