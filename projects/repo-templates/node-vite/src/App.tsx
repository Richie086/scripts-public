import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="container">
      <header className="header">
        <h1>Welcome to Your New Project</h1>
        <p className="subtitle">Scaffolded with standard 4-folder blueprint</p>
      </header>

      <main className="main-content">
        <div className="card">
          <h2>Interactive State Check</h2>
          <p>Click the button below to verify React state transitions are active:</p>
          <button className="btn" onClick={() => setCount((c) => c + 1)}>
            Count is {count}
          </button>
        </div>

        <div className="card">
          <h2>Workspace Design System</h2>
          <ul className="folder-list">
            <li><strong>📂 docs/</strong> — Specifications and guides</li>
            <li><strong>📂 scripts/</strong> — DevOps and helpers</li>
            <li><strong>📂 frontend/</strong> — UI client code (Vite + React)</li>
            <li><strong>📂 backend/</strong> — API servers and databases</li>
          </ul>
        </div>
      </main>

      <footer className="footer">
        <p>Built with ❤️ and Antigravity</p>
      </footer>
    </div>
  )
}

export default App
