import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 300;
export const dynamic = "force-dynamic";

const BACKEND = process.env.API_BACKEND_URL ?? "http://127.0.0.1:8000";

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const body = await request.text();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 300_000);

  try {
    const res = await fetch(`${BACKEND}/api/rfps/${params.id}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      signal: controller.signal,
      cache: "no-store",
    });
    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    const message =
      err instanceof Error && err.name === "AbortError"
        ? "Chat timed out. Please try again."
        : "Cannot reach the API server. Run ./start-api.sh";
    return NextResponse.json({ detail: message }, { status: 503 });
  } finally {
    clearTimeout(timer);
  }
}
