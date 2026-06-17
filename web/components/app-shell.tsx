"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Menu, PlusCircle, Sparkles, X } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/generate", label: "Generate", icon: PlusCircle },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const NavLinks = ({ onNavigate }: { onNavigate?: () => void }) => (
    <>
      {navItems.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          onClick={onNavigate}
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors min-h-11",
            pathname === href
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          )}
        >
          <Icon className="h-5 w-5 shrink-0" />
          {label}
        </Link>
      ))}
    </>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Desktop sidebar — Figma laptop frame: 1024px+ */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r bg-white/80 backdrop-blur lg:block">
        <div className="flex h-16 items-center gap-2 border-b px-6">
          <Sparkles className="h-6 w-6 text-primary" />
          <div>
            <p className="font-semibold leading-tight">RFP Generator</p>
            <p className="text-xs text-muted-foreground">Bedrock Agent</p>
          </div>
        </div>
        <nav className="space-y-1 p-4">
          <NavLinks />
        </nav>
      </aside>

      {/* Mobile header — iPhone/Android safe areas */}
      <header className="sticky top-0 z-30 border-b bg-white/90 backdrop-blur safe-top lg:hidden">
        <div className="flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <span className="font-semibold">RFP Generator</span>
          </div>
          <Button variant="ghost" size="icon" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </Button>
        </div>
      </header>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <div className="absolute right-0 top-0 h-full w-[min(100%,320px)] bg-white shadow-xl safe-top safe-bottom">
            <div className="flex items-center justify-between border-b p-4">
              <span className="font-semibold">Menu</span>
              <Button variant="ghost" size="icon" onClick={() => setMobileOpen(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>
            <nav className="space-y-1 p-4">
              <NavLinks onNavigate={() => setMobileOpen(false)} />
            </nav>
          </div>
        </div>
      )}

      {/* Main content — responsive max-width for laptop/desktop Figma frames */}
      <main className="lg:pl-64">
        <div className="mx-auto max-w-content px-4 py-6 sm:px-6 lg:px-8 lg:py-8 pb-24 lg:pb-8">
          {children}
        </div>
      </main>

      {/* Mobile bottom nav — thumb-friendly 375–430px screens */}
      <nav className="fixed bottom-0 left-0 right-0 z-30 border-t bg-white/95 backdrop-blur safe-bottom lg:hidden">
        <div className="mx-auto flex max-w-lg items-stretch justify-around px-2 py-1">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-1 flex-col items-center justify-center gap-1 py-2 text-xs font-medium min-h-[56px]",
                pathname === href ? "text-primary" : "text-muted-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {label}
            </Link>
          ))}
        </div>
      </nav>
    </div>
  );
}
