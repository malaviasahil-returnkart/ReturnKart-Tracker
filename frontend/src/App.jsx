import { useState, useEffect } from 'react'
import { api } from './lib/api'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'

export default function App() {
  const [userId, setUserId] = useState(() => localStorage.getItem('rk_user_id'))
  const [gmailConnected, setGmailConnected] = useState(false)
  const [checking, setChecking] = useState(true)
  const [page, setPage] = useState('dashboard')
  const [accounts, setAccounts] = useState([])
  const [userProfile, setUserProfile] = useState(() => {
    try {
      const stored = localStorage.getItem('rk_user_profile')
      return stored ? JSON.parse(stored) : null
    } catch { return null }
  })

  // Check URL params after OAuth redirect
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('gmail') === 'connected') {
      setGmailConnected(true)

      // Store/update Google profile from callback
      const name = params.get('user_name')
      const email = params.get('user_email')
      const picture = params.get('user_picture')
      if (name || email || picture) {
        const profile = { name: name || '', email: email || '', picture: picture || '' }
        localStorage.setItem('rk_user_profile', JSON.stringify(profile))
        setUserProfile(profile)
      }

      window.history.replaceState({}, '', '/')

      // Refresh accounts list after adding a new one
      if (userId) {
        api.getAccounts(userId).then(data => setAccounts(data.accounts || [])).catch(() => {})
      }
    }
    if (params.get('error')) {
      console.error('OAuth error:', params.get('error'))
      window.history.replaceState({}, '', '/')
    }
  }, [])

  // Check Gmail connection status + load accounts
  useEffect(() => {
    if (!userId) { setChecking(false); return }
    Promise.all([
      api.authStatus(userId),
      api.getAccounts(userId),
    ])
      .then(([status, accts]) => {
        setGmailConnected(status.connected)
        setAccounts(accts.accounts || [])
        // Set profile from first account if not already set
        if (!localStorage.getItem('rk_user_profile') && accts.accounts?.length > 0) {
          const first = accts.accounts[0]
          const profile = { name: first.name, email: first.email, picture: first.picture }
          localStorage.setItem('rk_user_profile', JSON.stringify(profile))
          setUserProfile(profile)
        }
      })
      .catch(() => {})
      .finally(() => setChecking(false))
  }, [userId])

  function handleConnect(uid) {
    localStorage.setItem('rk_user_id', uid)
    setUserId(uid)
    window.location.href = api.gmailOAuthUrl(uid)
  }

  function handleAddAccount() {
    if (userId) {
      window.location.href = api.gmailOAuthUrl(userId)
    }
  }

  function handleDisconnectAccount(email) {
    if (!userId) return
    api.authRevoke(userId, email)
      .then(() => api.getAccounts(userId))
      .then(data => {
        const accts = data.accounts || []
        setAccounts(accts)
        if (accts.length === 0) {
          // No accounts left — full logout
          localStorage.removeItem('rk_user_id')
          localStorage.removeItem('rk_user_profile')
          setUserId(null)
          setUserProfile(null)
          setGmailConnected(false)
          setPage('dashboard')
        } else {
          // Update profile to first remaining account
          const first = accts[0]
          const profile = { name: first.name, email: first.email, picture: first.picture }
          localStorage.setItem('rk_user_profile', JSON.stringify(profile))
          setUserProfile(profile)
        }
      })
      .catch(console.error)
  }

  function handleDisconnectAll() {
    if (userId) api.authRevoke(userId).catch(() => {})
    localStorage.removeItem('rk_user_id')
    localStorage.removeItem('rk_user_profile')
    setUserId(null)
    setUserProfile(null)
    setAccounts([])
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
        userProfile={userProfile}
        accounts={accounts}
        onBack={() => setPage('dashboard')}
        onDisconnect={handleDisconnectAll}
        onDisconnectAccount={handleDisconnectAccount}
        onAddAccount={handleAddAccount}
      />
    )
  }

  return (
    <Dashboard
      userId={userId}
      userProfile={userProfile}
      accounts={accounts}
      onDisconnect={handleDisconnectAll}
      onOpenSettings={() => setPage('settings')}
      onAddAccount={handleAddAccount}
    />
  )
}
