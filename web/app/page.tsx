"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Loader2, Sparkles } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type Domain, type RfpSummary } from "@/lib/api";

const categoryColors: Record<string, string> = {
  Energy: "bg-amber-100 text-amber-800 border-amber-200",
  Legal: "bg-violet-100 text-violet-800 border-violet-200",
  Healthcare: "bg-emerald-100 text-emerald-800 border-emerald-200",
  Hospitality: "bg-sky-100 text-sky-800 border-sky-200",
  Finance: "bg-indigo-100 text-indigo-800 border-indigo-200",
};

export default function HomePage() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [rfps, setRfps] = useState<RfpSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.domains(), api.listRfps()])
      .then(([d, r]) => {
        setDomains(d);
        setRfps(r);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const categories = [...new Set(domains.map((d) => d.category))];

  return (
    <AppShell>
      {/* Hero — stacks on mobile, side-by-side on laptop */}
      <section className="mb-8 grid gap-6 lg:grid-cols-2 lg:items-center lg:gap-10">
        <div className="space-y-4">
          <Badge variant="secondary" className="w-fit">
            Amazon Bedrock + DynamoDB
          </Badge>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Generate RFPs for software engineering programs
          </h1>
          <p className="text-base text-muted-foreground sm:text-lg max-w-xl">
            Create professional, domain-tailored Requests for Proposal across energy, healthcare,
            legal, hospitality, and finance — powered by AI.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg" className="w-full sm:w-auto">
              <Link href="/generate">
                <Sparkles className="h-4 w-4" />
                Generate New RFP
              </Link>
            </Button>
          </div>
        </div>

        <Card className="border-primary/20 bg-gradient-to-br from-blue-50 to-white">
          <CardHeader>
            <CardTitle>Supported domains</CardTitle>
            <CardDescription>{domains.length} industry templates ready to use</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {categories.map((cat) => (
                <Badge key={cat} variant="outline" className={categoryColors[cat] ?? ""}>
                  {cat}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Domain grid — 1 col mobile, 2 col tablet, 3 col laptop (Figma breakpoints) */}
      <section className="mb-10">
        <h2 className="mb-4 text-xl font-semibold">Industry domains</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {domains.map((domain) => (
            <Card key={domain.id} className="transition-shadow hover:shadow-md">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base">{domain.label}</CardTitle>
                  <Badge variant="outline" className={`shrink-0 text-[10px] ${categoryColors[domain.category] ?? ""}`}>
                    {domain.category}
                  </Badge>
                </div>
                <CardDescription className="line-clamp-2">{domain.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild variant="outline" size="sm" className="w-full">
                  <Link href={`/generate?domain=${domain.id}`}>
                    Use template
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Recent RFPs */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Recent RFPs</h2>
        </div>
        {loading ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin mr-2" />
            Loading...
          </div>
        ) : rfps.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center text-muted-foreground">
              No RFPs yet. Generate your first one to get started.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {rfps.slice(0, 6).map((rfp) => (
              <Link key={rfp.rfp_id} href={`/rfp/${rfp.rfp_id}`}>
                <Card className="h-full transition-shadow hover:shadow-md hover:border-primary/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base line-clamp-2">{rfp.title}</CardTitle>
                    <CardDescription className="flex flex-wrap gap-2">
                      {rfp.domain_label && <Badge variant="secondary">{rfp.domain_label}</Badge>}
                      <Badge variant="outline">{rfp.status}</Badge>
                    </CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}
