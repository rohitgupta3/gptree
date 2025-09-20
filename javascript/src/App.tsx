import { useState } from 'react'
import './App.css'

interface StatusResponse {
  success: boolean;
  message?: string;
}

function App() {
  const [count, setCount] = useState(0)
  const [status, setStatus] = useState<string>('Not tested')
  const [loading, setLoading] = useState(false)

  const testBackendConnection = async () => {
    setLoading(true)
    setStatus('Testing...')

    try {
      // Use relative URL - will work both locally and on Heroku
      const response = await fetch('/api/test')

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: StatusResponse = await response.json()

      if (data.success) {
        setStatus(`✅ Connected! ${data.message || ''}`)
      } else {
        setStatus('❌ Backend returned error')
      }
    } catch (error) {
      console.error('Connection test failed:', error)
      setStatus(`❌ Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <h1>GPTree</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count tester ({count})
        </button>

        <div style={{ marginTop: '20px' }}>
          <button
            onClick={testBackendConnection}
            disabled={loading}
            style={{
              padding: '10px 20px',
              marginBottom: '10px',
              backgroundColor: loading ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Testing...' : 'Test Backend Connection'}
          </button>

          <div style={{
            padding: '10px',
            marginTop: '10px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '4px',
            fontFamily: 'monospace'
          }}>
            Status: {status}
          </div>
        </div>
      </div>
    </>
  )
}

export default App