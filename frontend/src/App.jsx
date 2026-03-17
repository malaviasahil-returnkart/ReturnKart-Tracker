import { useState, useEffect } from 'react'
import { api } from './lib/api'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'

export default function App() {
  const [userId, setUserId] = useState(() => localStorage.getItem('rk_user_id'))
  const [gmailConnected, setGmailConnected] = useState(false)
  const [checking, setChecking] = useState(true)
  const [page, setPage] = useState('dashboard') // dashboard | settings

  // Check URL params after OAuth redirect
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('gmail') === 'connected') {
      setGmailConnected(true)
      window.history.replaceState({}, '', '/')
    }
    if (params.get('error')) {
      console.error('OAuth error:', params.get('error'))
      window.history.replaceState({}, '', '/')
    }
  }, [])

  // Check Gmail connection status
  useEffect(() => {
    if (!userId) { setChecking(false); return }
    api.authStatus(userId)
      .then(data => setGmailConnected(data.connected))
      .catch(() => {})
      .finally(() => setChecking(false))
  }, [userId])

  function handleConnect(uid) {
    localStorage.setItem('rk_user_id', uid)
    setUserId(uid)
    window.location.href = api.gmailOAuthUrl(uid)
  }

  function handleDisconnect() {
    if (userId) api.authRevoke(userId).catch(() => {})
    localStorage.removeItem('rk_user_id')
    setUserId(null)
    setGmailConnected(false)
    setPage('dashboard')
  }

  if (checking) {
    return (
      <div className="min-h-screen bg-vault-black flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-vault-gold border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!userId || !gmailConnected) {
    return <Onboarding onConnect={handleConnect} />
  }

  if (page === 'settings') {
    return (
      <Settings
        userId={userId}
        onDisconnect={handleDisconnect}
        onBack={() => setPage('dashboard')}
      />
    )
  }

  return (
    <Dashboard
      userId={userId}
      onDisconnect={handleDisconnect}
      onSettings={() => setPage('settings')}
    />
  )
}
