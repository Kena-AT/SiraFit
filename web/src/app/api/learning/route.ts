import { NextResponse } from 'next/server';
import { generateLearningPlan } from '@/lib/sirafit-engine';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { candidateSkills = [], jobRequirements = [] } = body;
    const plan = generateLearningPlan(candidateSkills, jobRequirements);
    return NextResponse.json({ ok: true, plan });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  }
}
