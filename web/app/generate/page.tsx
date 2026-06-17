"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, Sparkles } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api, type Domain } from "@/lib/api";
import { groupDomainsByCategory, STATIC_DOMAINS } from "@/lib/domains";

function GenerateForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselected = searchParams.get("domain") ?? "";

  const [domains, setDomains] = useState<Domain[]>(STATIC_DOMAINS);
  const [domainsLoading, setDomainsLoading] = useState(true);
  const [domainId, setDomainId] = useState<string | undefined>(
    preselected || undefined
  );
  const [title, setTitle] = useState("");
  const [organization, setOrganization] = useState("");
  const [projectSummary, setProjectSummary] = useState("");
  const [budgetRange, setBudgetRange] = useState("$500K – $2M");
  const [timeline, setTimeline] = useState("6-12 months");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .domains()
      .then((data) => {
        if (data.length > 0) setDomains(data);
      })
      .catch(() => {
        /* keep STATIC_DOMAINS fallback */
      })
      .finally(() => setDomainsLoading(false));
  }, []);

  useEffect(() => {
    if (preselected && domains.some((d) => d.id === preselected)) {
      setDomainId(preselected);
    }
  }, [preselected, domains]);

  const grouped = groupDomainsByCategory(domains);
  const selected = domains.find((d) => d.id === domainId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await api.generateRfp({
        title,
        domain_id: domainId!,
        organization,
        project_summary: projectSummary,
        budget_range: budgetRange,
        timeline,
      });

      if (result.has_docx) {
        const link = document.createElement("a");
        link.href = api.downloadUrl(result.rfp_id);
        link.download = `${title.replace(/\s+/g, "_")}.docx`;
        document.body.appendChild(link);
        link.click();
        link.remove();
      }

      router.push(`/rfp/${result.rfp_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 space-y-2">
          <h1 className="text-2xl font-bold sm:text-3xl">Generate RFP</h1>
          <p className="text-muted-foreground">
            Choose an industry domain and describe your software engineering program. Bedrock will
            draft a detailed RFP and export it as a Word (.docx) document.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>1. Industry domain</CardTitle>
              <CardDescription>Select the sector for your software program</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="domain">Domain</Label>
                <Select
                  value={domainId}
                  onValueChange={setDomainId}
                  disabled={domainsLoading && domains.length === 0}
                >
                  <SelectTrigger id="domain" aria-label="Select industry domain">
                    <SelectValue placeholder="Select industry domain" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(grouped).map(([category, items]) => (
                      <SelectGroup key={category}>
                        <SelectLabel>{category}</SelectLabel>
                        {items.map((d) => (
                          <SelectItem key={d.id} value={d.id}>
                            {d.label}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selected && (
                <div className="rounded-lg border bg-muted/40 p-4 space-y-2 text-sm">
                  <p>{selected.description}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selected.compliance.map((c) => (
                      <Badge key={c} variant="outline" className="text-xs">
                        {c}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>2. Project details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="title">Project title</Label>
                  <Input
                    id="title"
                    placeholder="e.g. Hospital EHR Modernization Platform"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="org">Organization name</Label>
                  <Input
                    id="org"
                    placeholder="e.g. Metro Health Systems"
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="budget">Budget range</Label>
                  <Input
                    id="budget"
                    value={budgetRange}
                    onChange={(e) => setBudgetRange(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="timeline">Timeline</Label>
                  <Input
                    id="timeline"
                    value={timeline}
                    onChange={(e) => setTimeline(e.target.value)}
                  />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="summary">Project summary</Label>
                  <Textarea
                    id="summary"
                    placeholder="Describe goals, users, integrations, compliance needs, and success criteria..."
                    value={projectSummary}
                    onChange={(e) => setProjectSummary(e.target.value)}
                    rows={6}
                    required
                    minLength={20}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {error && (
            <p className="text-sm text-destructive rounded-md border border-destructive/30 bg-destructive/5 p-3">
              {error}
            </p>
          )}

          <Button type="submit" size="lg" className="w-full sm:w-auto" disabled={loading || !domainId}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generating detailed RFP + Word doc (1–3 min)...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Generate RFP (Word Document)
              </>
            )}
          </Button>
        </form>
      </div>
    </AppShell>
  );
}

export default function GeneratePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-muted-foreground">Loading...</div>}>
      <GenerateForm />
    </Suspense>
  );
}
