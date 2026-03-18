import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Link } from "wouter";
import type { ReturnRequest } from "@shared/schema";
import {
  Search,
  Plus,
  ArrowRight,
  RotateCcw,
  Filter,
} from "lucide-react";
import {
  getStatusColor,
  getStatusLabel,
  getPlatformIcon,
  getPlatformLabel,
  getReasonLabel,
  formatCurrency,
  formatDate,
} from "@/lib/helpers";

export default function ReturnsList() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [platformFilter, setPlatformFilter] = useState("all");

  const { data: returns, isLoading, isError } = useQuery<ReturnRequest[]>({
    queryKey: ["/api/returns"],
  });

  const filtered = returns?.filter((r) => {
    const matchesSearch =
      !search ||
      r.productName.toLowerCase().includes(search.toLowerCase()) ||
      r.orderId.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || r.status === statusFilter;
    const matchesPlatform = platformFilter === "all" || r.platform === platformFilter;
    return matchesSearch && matchesStatus && matchesPlatform;
  }) ?? [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-40" />
          <Skeleton className="h-10 w-36" />
        </div>
        <div className="flex gap-3">
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 w-40" />
          <Skeleton className="h-10 w-40" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="p-4 rounded-full bg-destructive/10 mb-4">
          <RotateCcw className="h-8 w-8 text-destructive" />
        </div>
        <h2 className="text-lg font-semibold">Failed to load returns</h2>
        <p className="text-sm text-muted-foreground mt-1 max-w-[300px]">
          Something went wrong. Please try refreshing the page.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" data-testid="text-returns-title">
            All Returns
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            {returns?.length ?? 0} return request{(returns?.length ?? 0) !== 1 ? "s" : ""}
          </p>
        </div>
        <Link href="/returns/new">
          <Button className="gap-2" data-testid="button-new-return-list">
            <Plus className="h-4 w-4" />
            New Return
          </Button>
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by product or order ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            data-testid="input-search-returns"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[180px]" data-testid="select-status-filter">
            <Filter className="h-4 w-4 mr-2 text-muted-foreground" />
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="initiated">Initiated</SelectItem>
            <SelectItem value="pickup_scheduled">Pickup Scheduled</SelectItem>
            <SelectItem value="picked_up">Picked Up</SelectItem>
            <SelectItem value="in_transit">In Transit</SelectItem>
            <SelectItem value="received">Received</SelectItem>
            <SelectItem value="inspecting">Inspecting</SelectItem>
            <SelectItem value="refund_initiated">Refund Initiated</SelectItem>
            <SelectItem value="refund_completed">Refund Completed</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
        <Select value={platformFilter} onValueChange={setPlatformFilter}>
          <SelectTrigger className="w-full sm:w-[160px]" data-testid="select-platform-filter">
            <SelectValue placeholder="Platform" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Platforms</SelectItem>
            <SelectItem value="amazon">Amazon</SelectItem>
            <SelectItem value="flipkart">Flipkart</SelectItem>
            <SelectItem value="myntra">Myntra</SelectItem>
            <SelectItem value="meesho">Meesho</SelectItem>
            <SelectItem value="ajio">AJIO</SelectItem>
            <SelectItem value="nykaa">Nykaa</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {filtered.length === 0 ? (
        <Card className="border border-border">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="p-4 rounded-full bg-muted mb-4">
              <RotateCcw className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="font-medium">No returns found</h3>
            <p className="text-sm text-muted-foreground mt-1 max-w-[300px]">
              {search || statusFilter !== "all" || platformFilter !== "all"
                ? "Try adjusting your filters or search term"
                : "Start tracking your returns by creating a new return request"}
            </p>
            {!search && statusFilter === "all" && platformFilter === "all" && (
              <Link href="/returns/new">
                <Button variant="outline" size="sm" className="mt-4 gap-1.5" data-testid="button-empty-create">
                  <Plus className="h-3.5 w-3.5" /> Create Return
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((request) => {
            const PlatformIcon = getPlatformIcon(request.platform);
            return (
              <Link key={request.id} href={`/returns/${request.id}`}>
                <Card
                  className="border border-border hover:border-primary/30 transition-colors cursor-pointer group"
                  data-testid={`card-return-${request.id}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-4">
                      <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-accent flex items-center justify-center">
                        <PlatformIcon className="h-6 w-6 text-accent-foreground" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <h3 className="font-medium text-sm truncate">
                              {request.productName}
                            </h3>
                            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                              <span className="text-xs text-muted-foreground">
                                Order: {request.orderId}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {getPlatformLabel(request.platform)}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {formatDate(request.createdAt)}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-3 flex-shrink-0">
                            <Badge
                              variant="secondary"
                              className={`text-xs ${getStatusColor(request.status)}`}
                            >
                              {getStatusLabel(request.status)}
                            </Badge>
                            <span className="text-sm font-bold whitespace-nowrap">
                              {formatCurrency(request.amount)}
                            </span>
                            <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity hidden sm:block" />
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {getReasonLabel(request.reason)}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
