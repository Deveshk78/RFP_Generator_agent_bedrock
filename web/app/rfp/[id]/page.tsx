"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Loader2, Sparkles, FileDown } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { MarkdownView } from "@/components/markdown-view";
import { RfpChatPanel } from "@/components/rfp-chat-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { api, type RfpDetail } from "@/lib/api";

export default function RfpDetailPage() {
  const params = useParams();
  const rfpId = params.id as string;

  const [rfp, setRfp] = useState<RfpDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [proposing, setProposing] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [companyProfile, setCompanyProfile] = useState("");
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [error, setError] = useState("");

  const loadRfp = useCallback(async () => {
    try {
      const data = await api.getRfp(rfpId);
      setRfp(data);
      const history = await api.getChat(rfpId);
      setChatHistory(history.map((m) => ({ role: m.role, content: m.content })));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load RFP");
    } finally {
      setLoading(false);
    }
  }, [rfpId]);

  useEffect(() => {
    loadRfp();
  }, [loadRfp]);

  async function handleAnalyze() {
    setAnalyzing(true);
    setError("");
    try {
      const { analysis } = await api.analyzeRfp(rfpId);
      setRfp((prev) => (prev ? { ...prev, analysis, status: "analyzed" } : prev));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handlePropose() {
    setProposing(true);
    setError("");
    try {
      const { proposal } = await api.proposeRfp(rfpId, {
        company_name: companyName,
        company_profile: companyProfile,
      });
      setRfp((prev) =>
        prev ? { ...prev, proposal, company_name: companyName, status: "proposal_generated" } : prev
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Proposal failed");
    } finally {
      setProposing(false);
    }
  }

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-20 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          Loading RFP...
        </div>
      </AppShell>
    );
  }

  if (!rfp) {
    return (
      <AppShell>
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground">
            {error || "RFP not found"}
          </CardContent>
        </Card>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header — stacks on mobile */}
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {rfp.domain_label && <Badge>{rfp.domain_label}</Badge>}
            {rfp.category && <Badge variant="outline">{rfp.category}</Badge>}
            <Badge variant="secondary">{rfp.status}</Badge>
          </div>
          <h1 className="text-2xl font-bold sm:text-3xl">{rfp.title}</h1>
          {rfp.organization && (
            <p className="text-muted-foreground">Organization: {rfp.organization}</p>
          )}
          <div className="flex flex-wrap gap-3 pt-1">
            <Button asChild variant="default">
              <a href={api.downloadUrl(rfpId)} download>
                <FileDown className="h-4 w-4" />
                Download Word Document (.docx)
              </a>
            </Button>
          </div>
        </div>

        {error && (
          <p className="text-sm text-destructive rounded-md border border-destructive/30 bg-destructive/5 p-3">
            {error}
          </p>
        )}

        <Tabs defaultValue="document" className="w-full">
          <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4 h-auto">
            <TabsTrigger value="document">Document</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
            <TabsTrigger value="proposal">Proposal</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
          </TabsList>

          <TabsContent value="document">
            <Card>
              <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle>RFP Document</CardTitle>
                  <CardDescription>
                    Full RFP text — also available as a formatted Word document
                  </CardDescription>
                </div>
                <Button asChild variant="outline" className="w-full sm:w-auto">
                  <a href={api.downloadUrl(rfpId)} download>
                    <FileDown className="h-4 w-4" />
                    Download .docx
                  </a>
                </Button>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[min(70vh,600px)] pr-4">
                  {rfp.content ? <MarkdownView content={rfp.content} /> : <p>No content</p>}
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analysis">
            <Card>
              <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle>AI Analysis & Insights</CardTitle>
                  <CardDescription>
                    Requirements, compliance checklist, risk matrix, and response strategy
                  </CardDescription>
                </div>
                <Button onClick={handleAnalyze} disabled={analyzing} className="w-full sm:w-auto">
                  {analyzing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Analyzing (1–2 min)...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      {rfp.analysis ? "Re-analyze" : "Analyze RFP"}
                    </>
                  )}
                </Button>
              </CardHeader>
              <CardContent>
                {analyzing && !rfp.analysis && (
                  <p className="text-sm text-muted-foreground mb-4">
                    Bedrock is extracting requirements, evaluation criteria, compliance items, and
                    risks from your RFP...
                  </p>
                )}
                {rfp.analysis ? (
                  <ScrollArea className="h-[min(60vh,500px)] pr-4">
                    <MarkdownView content={rfp.analysis} />
                  </ScrollArea>
                ) : (
                  <p className="text-muted-foreground text-sm">
                    Run analysis to extract requirements, deadlines, and evaluation criteria.
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="proposal">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Generate Proposal</CardTitle>
                  <CardDescription>Draft a vendor response with Bedrock</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="company">Company name</Label>
                    <Input
                      id="company"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      placeholder="Your company"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="profile">Company profile</Label>
                    <Textarea
                      id="profile"
                      value={companyProfile}
                      onChange={(e) => setCompanyProfile(e.target.value)}
                      placeholder="Capabilities, certifications, experience..."
                      rows={5}
                    />
                  </div>
                  <Button
                    onClick={handlePropose}
                    disabled={proposing || !companyName || !companyProfile}
                    className="w-full"
                  >
                    {proposing ? <Loader2 className="h-4 w-4 animate-spin" /> : "Generate Proposal"}
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Proposal Draft</CardTitle>
                </CardHeader>
                <CardContent>
                  {rfp.proposal ? (
                    <ScrollArea className="h-[min(50vh,400px)] pr-4">
                      <MarkdownView content={rfp.proposal} />
                    </ScrollArea>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Enter your company details and generate a proposal response.
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="chat">
            <Card>
              <CardHeader>
                <CardTitle>Ask about this RFP</CardTitle>
                <CardDescription>
                  Formatted answers with tables and diagrams · Voice input supported
                </CardDescription>
              </CardHeader>
              <CardContent>
                <RfpChatPanel
                  rfpId={rfpId}
                  initialMessages={chatHistory}
                  onError={setError}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}
