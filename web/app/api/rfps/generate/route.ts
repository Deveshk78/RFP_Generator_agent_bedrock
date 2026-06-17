import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 300;
export const dynamic = "force-dynamic";

const BACKEND =
  process.env.API_BACKEND_URL ?? "http://127.0.0.1:8000";

/** Proxy generate requests with a 5-minute timeout (Bedrock can take 60–120s). */
export async function POST(request: NextRequest) {
  const body = await request.text();

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 300_000);

  try {
    const res = await fetch(`${BACKEND}/api/rfps/generate`, {
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
        ? "Generation timed out after 5 minutes. Please try again."
        : "Cannot reach the API server. Run ./start-api.sh in a separate terminal.";
    return NextResponse.json({ detail: message }, { status: 503 });
  } finally {
    clearTimeout(timer);
  }
}
