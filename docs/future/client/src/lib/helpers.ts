import {
  Package,
  ShoppingBag,
  Shirt,
  Store,
  Sparkles,
  Heart,
  Box,
} from "lucide-react";

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    initiated: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    pickup_scheduled: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    picked_up: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400",
    in_transit: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400",
    received: "bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400",
    inspecting: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
    refund_initiated: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
    refund_completed: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    rejected: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  };
  return colors[status] ?? "bg-gray-100 text-gray-800";
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    initiated: "Initiated",
    pickup_scheduled: "Pickup Scheduled",
    picked_up: "Picked Up",
    in_transit: "In Transit",
    received: "Received",
    inspecting: "Inspecting",
    refund_initiated: "Refund Initiated",
    refund_completed: "Refund Completed",
    rejected: "Rejected",
  };
  return labels[status] ?? status;
}

export function getPlatformIcon(platform: string) {
  const icons: Record<string, any> = {
    amazon: Package,
    flipkart: ShoppingBag,
    myntra: Shirt,
    meesho: Store,
    ajio: Sparkles,
    nykaa: Heart,
    other: Box,
  };
  return icons[platform] ?? Box;
}

export function getPlatformLabel(platform: string): string {
  const labels: Record<string, string> = {
    amazon: "Amazon",
    flipkart: "Flipkart",
    myntra: "Myntra",
    meesho: "Meesho",
    ajio: "AJIO",
    nykaa: "Nykaa",
    other: "Other",
  };
  return labels[platform] ?? platform;
}

export function getReasonLabel(reason: string): string {
  const labels: Record<string, string> = {
    wrong_item: "Wrong Item Received",
    damaged: "Damaged Product",
    defective: "Defective Product",
    size_issue: "Size Issue",
    quality_issue: "Quality Issue",
    not_as_described: "Not As Described",
    changed_mind: "Changed Mind",
    other: "Other",
  };
  return labels[reason] ?? reason;
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(date: string | Date | null): string {
  if (!date) return "—";
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(date));
}

export function formatDateTime(date: string | Date | null): string {
  if (!date) return "—";
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

export const STATUS_FLOW = [
  "initiated",
  "pickup_scheduled",
  "picked_up",
  "in_transit",
  "received",
  "inspecting",
  "refund_initiated",
  "refund_completed",
] as const;
