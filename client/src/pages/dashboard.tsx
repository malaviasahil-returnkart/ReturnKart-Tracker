import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "wouter";
import type { ReturnRequest } from "@shared/schema";
import {
  Package,
  TrendingUp,
  Clock,
  CheckCircle2,
  IndianRupee,
  Plus,
  ArrowRight,
  Truck,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";
import { getStatusColor, getStatusLabel, getPlatformIcon, formatCurrency } from "@/lib/helpers";

function StatCard({
  title,
  value,
  icon: Icon,
  color,
  subtitle,
}: {
  title: string;
  value: string | number;
  icon: any;
  color: string;
  subtitle?: string;
}) {
  return (
    <Card className="border border-border" data-testid={`stat-card-${title.toLowerCase().replace(/\s/g, "-")}`}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground font-medium">{title}</p>
            <p className="text-2xl font-bold tracking-tight">{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground">{subtitle}</p>
            )}
          </div>
          <div className={`p-2.5 rounded-lg ${color}`}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function RecentReturnRow({ request }: { request: ReturnRequest }) {
  const statusColor = getStatusColor(request.status);
  const PlatformIcon = getPlatformIcon(request.platform);

  return (
    <Link href={`/returns/${request.id}`}>
      <div
        className="flex items-center gap-4 p-3.5 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer group"
        data-testid={`recent-return-${request.id}`}
      >
        <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-accent flex items-center justify-center">
          <PlatformIcon className="h-5 w-5 text-accent-foreground" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{request.productName}</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {request.orderId} · {request.platform.charAt(0).toUpperCase() + request.platform.slice(1)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className={`text-xs ${statusColor}`}>
            {getStatusLabel(request.status)}
          </Badge>
          <span className="text-sm font-semibold whitespace-nowrap">
            {formatCurrency(request.amount)}
          </span>
          <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </div>
    </Link>
  );
}

export default function Dashboard() {
  const { data: returns, isLoading, isError } = useQuery<ReturnRequest[]>({
    queryKey: ["/api/returns"],
  });

  const stats = returns
    ? {
        total: returns.length,
        active: returns.filter((r) =>
          ["initiated", "pickup_scheduled", "picked_up", "in_transit", "received", "inspecting"].includes(r.status)
        ).length,
        completed: returns.filter((r) =>
          ["refund_completed"].includes(r.status)
        ).length,
        totalRefund: returns
          .filter((r) => r.status === "refund_completed")
          .reduce((sum, r) => sum + r.amount, 0),
      }
    : { total: 0, active: 0, completed: 0, totalRefund: 0 };

  const recentReturns = returns?.slice(0, 5) ?? [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64 mt-2" />
          </div>
          <Skeleton className="h-10 w-36" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="border border-border">
              <CardContent className="p-5">
                <Skeleton className="h-16 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card className="border border-border">
          <CardContent className="p-5">
            <Skeleton className="h-48 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="p-4 rounded-full bg-destructive/10 mb-4">
          <Package className="h-8 w-8 text-destructive" />
        </div>
        <h2 className="text-lg font-semibold">Something went wrong</h2>
        <p className="text-sm text-muted-foreground mt-1 max-w-[300px]">
          Unable to load your returns. Please try refreshing the page.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" data-testid="text-dashboard-title">
            Dashboard
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Track and manage all your e-commerce returns
          </p>
        </div>
        <Link href="/returns/new">
          <Button data-testid="button-new-return" className="gap-2">
            <Plus className="h-4 w-4" />
            New Return
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Returns"
          value={stats.total}
          icon={Package}
          color="bg-primary/10 text-primary"
          subtitle="All time"
        />
        <StatCard
          title="Active Returns"
          value={stats.active}
          icon={Clock}
          color="bg-blue-500/10 text-blue-600"
          subtitle="In progress"
        />
        <StatCard
          title="Completed"
          value={stats.completed}
          icon={CheckCircle2}
          color="bg-green-500/10 text-green-600"
          subtitle="Refund received"
        />
        <StatCard
          title="Total Refunds"
          value={formatCurrency(stats.totalRefund)}
          icon={IndianRupee}
          color="bg-purple-500/10 text-purple-600"
          subtitle="Amount recovered"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 border border-border">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-base" data-testid="text-recent-returns">Recent Returns</h2>
              <Link href="/returns">
                <Button variant="ghost" size="sm" className="text-xs gap-1" data-testid="link-view-all">
                  View All <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
            {recentReturns.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="p-4 rounded-full bg-muted mb-4">
                  <RotateCcw className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="font-medium text-sm">No returns yet</h3>
                <p className="text-xs text-muted-foreground mt-1 max-w-[240px]">
                  Start tracking your returns by creating a new return request
                </p>
                <Link href="/returns/new">
                  <Button variant="outline" size="sm" className="mt-4 gap-1.5" data-testid="button-create-first-return">
                    <Plus className="h-3.5 w-3.5" /> Create Return
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-1">
                {recentReturns.map((ret) => (
                  <RecentReturnRow key={ret.id} request={ret} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardContent className="p-5">
            <h2 className="font-semibold text-base mb-4" data-testid="text-quick-actions">Quick Actions</h2>
            <div className="space-y-2.5">
              <Link href="/returns/new">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-3 h-12"
                  data-testid="button-quick-new-return"
                >
                  <div className="p-1.5 rounded-md bg-primary/10">
                    <Plus className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium">New Return</p>
                    <p className="text-xs text-muted-foreground">File a new return request</p>
                  </div>
                </Button>
              </Link>
              <Link href="/track">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-3 h-12"
                  data-testid="button-quick-track"
                >
                  <div className="p-1.5 rounded-md bg-blue-500/10">
                    <Truck className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium">Track Return</p>
                    <p className="text-xs text-muted-foreground">Track by order ID</p>
                  </div>
                </Button>
              </Link>
              <Link href="/returns">
                <Button
                  variant="outline"
                  className="w-full justify-start gap-3 h-12"
                  data-testid="button-quick-all-returns"
                >
                  <div className="p-1.5 rounded-md bg-green-500/10">
                    <ShieldCheck className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium">All Returns</p>
                    <p className="text-xs text-muted-foreground">View complete history</p>
                  </div>
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
