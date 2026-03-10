import { useQuery } from "@tanstack/react-query";
import { useRoute, Link } from "wouter";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import type { ReturnRequest, StatusHistory } from "@shared/schema";
import {
  ArrowLeft,
  Package,
  Calendar,
  IndianRupee,
  MapPin,
  FileText,
  CheckCircle2,
  Circle,
  Clock,
} from "lucide-react";
import {
  getStatusColor,
  getStatusLabel,
  getPlatformIcon,
  getPlatformLabel,
  getReasonLabel,
  formatCurrency,
  formatDate,
  formatDateTime,
  STATUS_FLOW,
} from "@/lib/helpers";

function StatusTimeline({
  currentStatus,
  history,
}: {
  currentStatus: string;
  history: StatusHistory[];
}) {
  const currentIdx = STATUS_FLOW.indexOf(currentStatus as any);
  const isRejected = currentStatus === "rejected";

  return (
    <div className="space-y-0">
      {STATUS_FLOW.map((step, idx) => {
        const isCompleted = idx <= currentIdx && !isRejected;
        const isCurrent = idx === currentIdx && !isRejected;
        const historyEntry = history.find((h) => h.status === step);

        return (
          <div key={step} className="flex gap-3" data-testid={`status-step-${step}`}>
            <div className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  isCompleted
                    ? isCurrent
                      ? "bg-primary text-primary-foreground ring-4 ring-primary/20"
                      : "bg-primary/80 text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {isCompleted && !isCurrent ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : isCurrent ? (
                  <Clock className="h-4 w-4" />
                ) : (
                  <Circle className="h-3 w-3" />
                )}
              </div>
              {idx < STATUS_FLOW.length - 1 && (
                <div
                  className={`w-0.5 h-10 ${
                    idx < currentIdx && !isRejected ? "bg-primary/60" : "bg-muted"
                  }`}
                />
              )}
            </div>
            <div className="pt-1 pb-4">
              <p
                className={`text-sm font-medium ${
                  isCompleted ? "text-foreground" : "text-muted-foreground"
                }`}
              >
                {getStatusLabel(step)}
              </p>
              {historyEntry && (
                <p className="text-xs text-muted-foreground mt-0.5">
                  {formatDateTime(historyEntry.createdAt)}
                  {historyEntry.note && ` · ${historyEntry.note}`}
                </p>
              )}
            </div>
          </div>
        );
      })}

      {isRejected && (
        <div className="flex gap-3" data-testid="status-step-rejected">
          <div className="flex flex-col items-center">
            <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-red-500 text-white ring-4 ring-red-500/20">
              <span className="text-sm font-bold">✕</span>
            </div>
          </div>
          <div className="pt-1">
            <p className="text-sm font-medium text-red-600">Rejected</p>
            {history.find((h) => h.status === "rejected") && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatDateTime(history.find((h) => h.status === "rejected")!.createdAt)}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReturnDetail() {
  const [, params] = useRoute("/returns/:id");
  const returnId = params?.id;

  const { data: returnRequest, isLoading, isError } = useQuery<ReturnRequest>({
    queryKey: ["/api/returns", returnId],
    enabled: !!returnId,
  });

  const { data: history, isLoading: historyLoading } = useQuery<StatusHistory[]>({
    queryKey: ["/api/returns", returnId, "history"],
    enabled: !!returnId,
  });

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="p-4 rounded-full bg-destructive/10 mb-4">
          <Package className="h-8 w-8 text-destructive" />
        </div>
        <h2 className="text-lg font-semibold">Something went wrong</h2>
        <p className="text-sm text-muted-foreground mt-1 max-w-[300px]">
          Unable to load this return request. Please try again.
        </p>
        <Link href="/returns">
          <Button variant="outline" className="mt-4" data-testid="button-error-back">
            Back to Returns
          </Button>
        </Link>
      </div>
    );
  }

  if (isLoading || historyLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Skeleton className="h-9 w-9" />
          <Skeleton className="h-8 w-48" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="h-48 w-full rounded-lg" />
            <Skeleton className="h-64 w-full rounded-lg" />
          </div>
          <Skeleton className="h-96 w-full rounded-lg" />
        </div>
      </div>
    );
  }

  if (!returnRequest) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Package className="h-12 w-12 text-muted-foreground mb-4" />
        <h2 className="text-lg font-semibold">Return not found</h2>
        <p className="text-sm text-muted-foreground mt-1">
          The return request you're looking for doesn't exist.
        </p>
        <Link href="/returns">
          <Button variant="outline" className="mt-4" data-testid="button-back-to-returns">
            Back to Returns
          </Button>
        </Link>
      </div>
    );
  }

  const PlatformIcon = getPlatformIcon(returnRequest.platform);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/returns">
          <Button variant="ghost" size="icon" className="h-9 w-9" data-testid="button-back">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold tracking-tight truncate" data-testid="text-return-title">
            {returnRequest.productName}
          </h1>
          <p className="text-sm text-muted-foreground">
            Order #{returnRequest.orderId}
          </p>
        </div>
        <Badge
          variant="secondary"
          className={`text-xs ${getStatusColor(returnRequest.status)}`}
          data-testid="badge-current-status"
        >
          {getStatusLabel(returnRequest.status)}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="border border-border">
            <CardContent className="p-5">
              <h2 className="font-semibold text-base mb-4">Return Details</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-md bg-accent flex-shrink-0">
                    <PlatformIcon className="h-4 w-4 text-accent-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Platform</p>
                    <p className="text-sm font-medium" data-testid="text-platform">
                      {getPlatformLabel(returnRequest.platform)}
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-md bg-accent flex-shrink-0">
                    <IndianRupee className="h-4 w-4 text-accent-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Amount</p>
                    <p className="text-sm font-bold" data-testid="text-amount">
                      {formatCurrency(returnRequest.amount)}
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-md bg-accent flex-shrink-0">
                    <FileText className="h-4 w-4 text-accent-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Reason</p>
                    <p className="text-sm font-medium" data-testid="text-reason">
                      {getReasonLabel(returnRequest.reason)}
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-md bg-accent flex-shrink-0">
                    <Calendar className="h-4 w-4 text-accent-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Filed On</p>
                    <p className="text-sm font-medium" data-testid="text-filed-date">
                      {formatDate(returnRequest.createdAt)}
                    </p>
                  </div>
                </div>
                {returnRequest.trackingId && (
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-md bg-accent flex-shrink-0">
                      <MapPin className="h-4 w-4 text-accent-foreground" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Tracking ID</p>
                      <p className="text-sm font-medium font-mono" data-testid="text-tracking-id">
                        {returnRequest.trackingId}
                      </p>
                    </div>
                  </div>
                )}
                {returnRequest.pickupDate && (
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-md bg-accent flex-shrink-0">
                      <Calendar className="h-4 w-4 text-accent-foreground" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Pickup Date</p>
                      <p className="text-sm font-medium" data-testid="text-pickup-date">
                        {formatDate(returnRequest.pickupDate)}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {returnRequest.description && (
                <>
                  <Separator className="my-4" />
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Description</p>
                    <p className="text-sm leading-relaxed" data-testid="text-description">
                      {returnRequest.description}
                    </p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="border border-border h-fit">
          <CardContent className="p-5">
            <h2 className="font-semibold text-base mb-5">Status Timeline</h2>
            <StatusTimeline
              currentStatus={returnRequest.status}
              history={history ?? []}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
