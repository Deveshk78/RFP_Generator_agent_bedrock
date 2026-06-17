import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND =
  process.env.API_BACKEND_URL ?? "http://127.0.0.1:8000";

/** Proxy Word document downloads from FastAPI. */
export async function GET(
  _request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const res = await fetch(`${BACKEND}/api/rfps/${params.id}/download`, {
      cache: "no-store",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      return NextResponse.json(err, { status: res.status });
    }

    const blob = await res.blob();
    const disposition = res.headers.get("content-disposition") ?? "";
    return new NextResponse(blob, {
      status: 200,
      headers: {
        "Content-Type":
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "Content-Disposition": disposition || `attachment; filename="RFP.docx"`,
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Cannot reach the API server. Run ./start-api.sh" },
      { status: 503 }
    );
  }
}
