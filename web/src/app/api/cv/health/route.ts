import { NextResponse } from 'next/server';
import { calculateProfileHealth, readCandidateCv } from '@/lib/sirafit-engine';

export async function GET() {
  try {
    const cvText = readCandidateCv();
    const report = calculateProfileHealth(cvText);
    return NextResponse.json({ ok: true, report });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const cvContent = body.content || readCandidateCv();
    const report = calculateProfileHealth(cvContent);
    return NextResponse.json({ ok: true, report });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  }
}
