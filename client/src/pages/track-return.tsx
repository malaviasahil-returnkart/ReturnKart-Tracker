import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "wouter";
import type { ReturnRequest } from "@shared/schema";
import {
  Search,
  Package,
  Truck,
  ArrowRight,
} from "lucide-react";
import {
  getStatusColor,
  getStatusLabel,
  getPlatformIcon,
  getPlatformLabel,
  formatCurrency,
  formatDate,
} from "@/lib/helpers";

export default function TrackReturn() {
  const [orderId, setOrderId] = useState("");
  const [searchTriggered, setSearchTriggered] = useState(false);

  const { data: results, isLoading, isError } = useQuery<ReturnRequest[]>({
    queryKey: ["/api/returns/track", orderId],
    enabled: searchTriggered && orderId.length > 0,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (orderId.trim()) {
      setSearchTriggered(true);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <div className="inline-flex items-center justify-center p-3 rounded-full bg-primary/10 mb-2">
          <Truck className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight" data-testid="text-track-title">
          Track Your Return
        </h1>
        <p className="text-muted-foreground text-sm max-w-md mx-auto">
          Enter your order ID to find and track your return request status
        </p>
      </div>

      <Card className="border border-border">
        <CardContent className="p-6">
          <form onSubmit={handleSearch} className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Enter Order ID (e.g., OD12345678)"
                value={orderId}
                onChange={(e) => {
                  setOrderId(e.target.value);
                  setSearchTriggered(false);
                }}
                className="pl-9"
                data-testid="input-track-order-id"
              />
            </div>
            <Button type="submit" disabled={!orderId.trim()} data-testid="button-track-search">
              Track
            </Button>
          </form>
        </CardContent>
      </Card>

      {isLoading && (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full rounded-lg" />
        </div>
      )}

      {isError && searchTriggered && (
        <Card className="border border-border">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-4 rounded-full bg-destructive/10 mb-4">
              <Package className="h-8 w-8 text-destructive" />
            </div>
            <h3 className="font-medium">Search failed</h3>
            <p className="text-sm text-muted-foreground mt-1 max-w-[300px]">
              Something went wrong while searching. Please try again.
            </p>
          </CardContent>
        </Card>
      )}

      {searchTriggered && !isLoading && !isError && results && results.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Found {results.length} return{results.length !== 1 ? "s" : ""} for order{" "}
            <span className="font-medium text-foreground">{orderId}</span>
          </p>
          {results.map((request) => {
            const PlatformIcon = getPlatformIcon(request.platform);
            return (
              <Link key={request.id} href={`/returns/${request.id}`}>
                <Card
                  className="border border-border hover:border-primary/30 transition-colors cursor-pointer group"
                  data-testid={`card-track-result-${request.id}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-4">
                      <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-accent flex items-center justify-center">
                        <PlatformIcon className="h-6 w-6 text-accent-foreground" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-sm truncate">{request.productName}</h3>
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                          <span className="text-xs text-muted-foreground">
                            {getPlatformLabel(request.platform)}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(request.createdAt)}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <Badge variant="secondary" className={`text-xs ${getStatusColor(request.status)}`}>
                          {getStatusLabel(request.status)}
                        </Badge>
                        <span className="text-sm font-bold">{formatCurrency(request.amount)}</span>
                        <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      )}

      {searchTriggered && !isLoading && !isError && results && results.length === 0 && (
        <Card className="border border-border">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-4 rounded-full bg-muted mb-4">
              <Package className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="font-medium">No returns found</h3>
            <p className="text-sm text-muted-foreground mt-1 max-w-[300px]">
              No return requests found for order ID "{orderId}". Double-check and try again.
            </p>
          </CardContent>
        </Card>
      )}

      {!searchTriggered && (
        <Card className="border border-border">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-4 rounded-full bg-muted mb-4">
              <Search className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="font-medium">Enter your order ID</h3>
            <p className="text-sm text-muted-foreground mt-1 max-w-[300px]">
              Search by your order ID from any e-commerce platform to track your return status
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
