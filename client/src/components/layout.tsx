import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Package,
  Truck,
  Plus,
  RotateCcw,
  Menu,
  X,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/returns", label: "Returns", icon: Package },
  { href: "/track", label: "Track", icon: Truck },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            <Link href="/">
              <div className="flex items-center gap-2.5 cursor-pointer" data-testid="link-logo">
                <div className="p-1.5 rounded-lg bg-primary">
                  <RotateCcw className="h-4.5 w-4.5 text-primary-foreground" />
                </div>
                <span className="font-bold text-lg tracking-tight">
                  Return<span className="text-primary">Kart</span>
                </span>
              </div>
            </Link>

            <nav className="hidden sm:flex items-center gap-1" data-testid="nav-desktop">
              {navItems.map((item) => {
                const isActive = location === item.href || (item.href !== "/" && location.startsWith(item.href));
                return (
                  <Link key={item.href} href={item.href}>
                    <Button
                      variant={isActive ? "secondary" : "ghost"}
                      size="sm"
                      className={`gap-2 text-sm ${isActive ? "font-medium" : "text-muted-foreground"}`}
                      data-testid={`nav-${item.label.toLowerCase()}`}
                    >
                      <item.icon className="h-4 w-4" />
                      {item.label}
                    </Button>
                  </Link>
                );
              })}
            </nav>

            <div className="flex items-center gap-2">
              <Link href="/returns/new">
                <Button size="sm" className="hidden sm:flex gap-1.5" data-testid="button-header-new">
                  <Plus className="h-3.5 w-3.5" />
                  New Return
                </Button>
              </Link>
              <Button
                variant="ghost"
                size="icon"
                className="sm:hidden h-9 w-9"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                data-testid="button-mobile-menu"
              >
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </Button>
            </div>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="sm:hidden border-t border-border bg-background" data-testid="nav-mobile">
            <div className="px-4 py-3 space-y-1">
              {navItems.map((item) => {
                const isActive = location === item.href || (item.href !== "/" && location.startsWith(item.href));
                return (
                  <Link key={item.href} href={item.href}>
                    <Button
                      variant={isActive ? "secondary" : "ghost"}
                      className={`w-full justify-start gap-2.5 ${isActive ? "font-medium" : "text-muted-foreground"}`}
                      onClick={() => setMobileMenuOpen(false)}
                      data-testid={`nav-mobile-${item.label.toLowerCase()}`}
                    >
                      <item.icon className="h-4 w-4" />
                      {item.label}
                    </Button>
                  </Link>
                );
              })}
              <Link href="/returns/new">
                <Button
                  className="w-full gap-2 mt-2"
                  onClick={() => setMobileMenuOpen(false)}
                  data-testid="button-mobile-new"
                >
                  <Plus className="h-4 w-4" />
                  New Return
                </Button>
              </Link>
            </div>
          </div>
        )}
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {children}
      </main>
    </div>
  );
}
