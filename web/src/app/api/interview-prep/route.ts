import { NextResponse } from 'next/server';
import { generateInterviewPrepQuestions } from '@/lib/sirafit-engine';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const {
      candidateSkills = [],
      jobRequirements = [],
      company = 'Target Company',
      role = 'Senior Engineer',
    } = body;

    const prep = generateInterviewPrepQuestions(candidateSkills, jobRequirements, company, role);
    return NextResponse.json({ ok: true, prep });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  }
}
