"use client";

import React, { useEffect, useState } from "react";
import { api } from "../../lib/api";

type NeedsItem = { rfp_id: string; title: string; review_reason?: string; updated_at?: string };

export default function NeedsReviewPage() {
  const [items, setItems] = useState<NeedsItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem("apiToken") : null;

  useEffect(() => {
    if (!token) {
      setError("No API token found in localStorage (key: apiToken). Only reviewers may use this page.");
      setLoading(false);
      return;
    }

    api
      .needsReview()
      .then((res) => {
        setItems(res);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

  async function handleApprove(rfp_id: string) {
    setError(null);
    try {
      const approver = localStorage.getItem("approverName") || undefined;
      await api.approveRfp(rfp_id, approver);
      setItems((prev) => (prev ? prev.filter((i) => i.rfp_id !== rfp_id) : prev));
    } catch (err: any) {
      setError(err?.message || String(err));
    }
  }

  if (loading) return <div>Loading…</div>;
  if (error) return <div style={{ color: "red" }}>{error}</div>;

  if (!items || items.length === 0) return <div>No RFPs need review.</div>;

  return (
    <div>
      <h1>RFPs Needing Review</h1>
      <ul>
        {items.map((it) => (
          <li key={it.rfp_id} style={{ marginBottom: 12 }}>
            <strong>{it.title}</strong>
            <div>Reason: {it.review_reason || "(unspecified)"}</div>
            <div>Updated: {it.updated_at}</div>
            <button onClick={() => handleApprove(it.rfp_id)}>Approve</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
