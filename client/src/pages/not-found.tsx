import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";
import { Link } from "wouter";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="p-4 rounded-full bg-muted mb-4">
        <AlertCircle className="h-8 w-8 text-muted-foreground" />
      </div>
      <h2 className="text-lg font-semibold" data-testid="text-404-title">Page Not Found</h2>
      <p className="text-sm text-muted-foreground mt-1 max-w-[300px]">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link href="/">
        <Button variant="outline" className="mt-4" data-testid="button-go-home">
          Go to Dashboard
        </Button>
      </Link>
    </div>
  );
}
