import { NextResponse } from 'next/server';
import { calculateAhEvaluation, readCandidateCv } from '@/lib/sirafit-engine';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const {
      jobTitle = 'Software Engineer',
      jobDescription = '',
      company = 'Company',
      url = '',
      skills = [],
      experienceYears = 3.5,
    } = body;

    let candidateSkills = skills;
    if (!candidateSkills || candidateSkills.length === 0) {
      const cvText = readCandidateCv();
      const extracted = ['typescript', 'python', 'react', 'next.js', 'node.js', 'postgresql', 'docker', 'tailwind', 'git', 'ci/cd', 'linux', 'rest'];
      const cvLower = cvText.toLowerCase();
      candidateSkills = extracted.filter((s) => cvLower.includes(s));
    }

    const result = calculateAhEvaluation(
      candidateSkills,
      Number(experienceYears) || 3.0,
      jobTitle,
      jobDescription,
      company,
      url
    );

    return NextResponse.json({ ok: true, result });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  }
}
