import { useEffect, useState } from 'react';
import { getAuthUrl, syncEmails, getOrders, getOrderStats } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Package, Clock, CheckCircle2, IndianRupee, Mail, RefreshCw, LogIn } from 'lucide-react';

function StatCard({ title, value, icon: Icon, color, subtitle }: {
  title: string; value: string | number; icon: any; color: string; subtitle?: string;
}) {
  return (
    <Card className="border border-border">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground font-medium">{title}</p>
            <p className="text-2xl font-bold tracking-tight">{value}</p>
            {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
          </div>
          <div className={`p-2.5 rounded-lg ${color}`}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function getStatusColor(status: string) {
  if (status === 'active') return 'bg-blue-100 text-blue-700';
  if (status === 'expiring_soon') return 'bg-orange-100 text-orange-700';
  if (status === 'expired') return 'bg-red-100 text-red-700';
  if (status === 'returned' || status === 'return_initiated') return 'bg-green-100 text-green-700';
  return 'bg-gray-100 text-gray-700';
}

function getStatusLabel(status: string) {
  if (status === 'active') return 'Active';
  if (status === 'expiring_soon') return 'Expiring Soon';
  if (status === 'expired') return 'Expired';
  if (status === 'returned') return 'Returned';
  if (status === 'return_initiated') return 'Return Initiated';
  return status;
}

export default function Dashboard() {
  const [orders, setOrders] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [tokens, setTokens] = useState<any>(null);
  const [syncMessage, setSyncMessage] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tokensParam = params.get('tokens');
    if (tokensParam) {
      try {
        const parsedTokens = JSON.parse(decodeURIComponent(tokensParam));
        setTokens(parsedTokens);
        localStorage.setItem('rk_tokens', JSON.stringify(parsedTokens));
        window.history.replaceState({}, '', '/');
      } catch (e) {}
    } else {
      const stored = localStorage.getItem('rk_tokens');
      if (stored) setTokens(JSON.parse(stored));
    }
  }, []);

  useEffect(() => { loadOrders(); }, []);

  async function loadOrders() {
    setLoading(true);
    try {
      const [ordersData, statsData] = await Promise.all([getOrders(), getOrderStats()]);
      setOrders(Array.isArray(ordersData) ? ordersData : []);
      setStats(statsData);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function handleConnectGmail() {
    try {
      const url = await getAuthUrl();
      window.location.href = url;
    } catch (e) {
      alert('Could not connect to backend. Make sure your backend is running.');
    }
  }

  async function handleSync() {
    if (!tokens) { await handleConnectGmail(); return; }
    setSyncing(true);
    setSyncMessage('');
    try {
      const result = await syncEmails(tokens);
      setSyncMessage(`✅ Synced ${result.synced} orders from your Gmail!`);
      await loadOrders();
    } catch (e) {
      setSyncMessage('❌ Sync failed. Try reconnecting Gmail.');
    }
    setSyncing(false);
  }

  function handleDisconnect() {
    localStorage.removeItem('rk_tokens');
    setTokens(null);
    setSyncMessage('');
  }

  const daysLeft = (deadline: string) =>
    Math.ceil((new Date(deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">ReturnKart Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">Track your ecommerce return windows automatically</p>
        </div>
        <div className="flex gap-2">
          {tokens ? (
            <>
              <Button onClick={handleSync} disabled={syncing} className="gap-2">
                <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Sync Gmail'}
              </Button>
              <Button variant="outline" onClick={handleDisconnect}>Disconnect</Button>
            </>
          ) : (
            <Button onClick={handleConnectGmail} className="gap-2">
              <Mail className="h-4 w-4" /> Connect Gmail
            </Button>
          )}
        </div>
      </div>

      {syncMessage && <div className="p-3 rounded-lg bg-muted text-sm">{syncMessage}</div>}

      {!tokens && (
        <Card className="border-2 border-dashed border-primary/30">
          <CardContent className="p-8 flex flex-col items-center text-center gap-4">
            <div className="p-4 rounded-full bg-primary/10">
              <Mail className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Connect your Gmail to get started</h2>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                ReturnKart will scan your emails from Amazon, Flipkart, Myntra, and more to automatically track your return windows.
              </p>
            </div>
            <Button onClick={handleConnectGmail} size="lg" className="gap-2">
              <LogIn className="h-4 w-4" /> Connect Gmail
            </Button>
          </CardContent>
        </Card>
      )}

      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Total Orders" value={stats.total} icon={Package} color="bg-primary/10 text-primary" subtitle="Tracked" />
          <StatCard title="Active" value={stats.active} icon={Clock} color="bg-blue-500/10 text-blue-600" subtitle="Return window open" />
          <StatCard title="Expiring Soon" value={stats.expiring_soon} icon={IndianRupee} color="bg-orange-500/10 text-orange-600" subtitle="Within 2 days" />
          <StatCard title="Returned" value={stats.returned} icon={CheckCircle2} color="bg-green-500/10 text-green-600" subtitle="Completed" />
        </div>
      )}

      <Card className="border border-border">
        <CardContent className="p-5">
          <h2 className="font-semibold text-base mb-4">Your Orders</h2>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : orders.length === 0 ? (
            <div className="text-center py-12">
              <Package className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm font-medium">No orders found</p>
              <p className="text-xs text-muted-foreground mt-1">Connect Gmail and sync to see your orders</p>
            </div>
          ) : (
            <div className="space-y-2">
              {orders.map((order: any) => (
                <div key={order.id} className="flex items-center gap-4 p-3.5 rounded-lg border border-border">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{order.product_name}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {order.platform?.toUpperCase()} · {order.order_id}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {order.return_deadline && (
                      <p className="text-xs text-muted-foreground whitespace-nowrap">
                        {daysLeft(order.return_deadline) > 0 ? `${daysLeft(order.return_deadline)} days left` : 'Expired'}
                      </p>
                    )}
                    <Badge className={`text-xs ${getStatusColor(order.status)}`}>
                      {getStatusLabel(order.status)}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
