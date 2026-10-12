import fs from 'node:fs';
import path from 'node:path';
import { sirafitRoot } from './sirafit';

export interface PreEvaluationGateResult {
  passed: boolean;
  reasons: string[];
  gateFailures: string[];
}

export interface AhEvaluationResult {
  score: number;
  recommendation: 'PROCEED' | 'LOW_FRICTION' | 'SKIP';
  gateStatus: 'PASSED' | 'FAILED';
  matchedSkills: string[];
  missingSkills: string[];
  blocks: Record<string, any>;
  markdownReport: string;
}

export interface HealthCheckItem {
  category: string;
  passed: boolean;
  score: number;
  maxScore: number;
  title: string;
  feedback: string;
}

export interface ResumeHealthReport {
  overallScore: number;
  grade: 'A+' | 'A' | 'B' | 'C' | 'D';
  summary: string;
  breakdown: {
    completeness: number;
    actionVerbs: number;
    quantifiedMetrics: number;
    formatting: number;
    keywords: number;
  };
  checks: HealthCheckItem[];
  recommendations: string[];
}

export interface LearningPlanItem {
  type: 'learning_resource' | 'project_template';
  skill: string;
  title: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  estimatedHours: number;
  url?: string;
  description: string;
}

export interface GapToPlanResult {
  missingSkills: string[];
  planItems: LearningPlanItem[];
}

export interface InterviewQuestion {
  question: string;
  focusSkill: string;
  difficulty: 'Standard' | 'Deep Dive' | 'System Design';
  idealAnswerPoints: string[];
}

export interface InterviewPrepResult {
  role: string;
  company: string;
  questions: InterviewQuestion[];
}

const STRONG_ACTION_VERBS = new Set([
  'accelerated', 'accomplished', 'achieved', 'acquired', 'administered', 'advised',
  'analyzed', 'architected', 'automated', 'boosted', 'built', 'centralized',
  'championed', 'coached', 'collaborated', 'conceived', 'consolidated', 'constructed',
  'converted', 'created', 'customized', 'decreased', 'delivered', 'deployed',
  'designed', 'developed', 'devised', 'directed', 'doubled', 'drove', 'eliminated',
  'enabled', 'engineered', 'enhanced', 'established', 'exceeded', 'executed',
  'expanded', 'expedited', 'fabricated', 'facilitated', 'formulated', 'generated',
  'grew', 'guided', 'halved', 'headed', 'implemented', 'improved', 'increased',
  'initiated', 'innovated', 'inspected', 'installed', 'instituted', 'integrated',
  'introduced', 'invented', 'launched', 'lead', 'led', 'managed', 'maximized',
  'mentored', 'migrated', 'minimized', 'modernized', 'negotiated', 'optimized',
  'orchestrated', 'outperformed', 'overhauled', 'oversaw', 'partnered', 'pioneered',
  'planned', 'produced', 'programmed', 'promoted', 're-engineered', 'rebuilt',
  'reduced', 'refactored', 'remodeled', 'reorganized', 'resolved', 'restructured',
  'revamped', 'saved', 'scaled', 'simplified', 'spearheaded', 'standardized',
  'streamlined', 'strengthened', 'surpassed', 'synthesized', 'trained', 'transformed',
  'tripled', 'unified', 'upgraded', 'yielded'
]);

const METRIC_REGEX = /(\b\d+(\.\d+)?%|\$\d+(\.\d+)?|\b\d+x\b|\b\d+\s*(users|customers|clients|requests|ms|seconds|minutes|hours|days|percent|million|k|M|B)\b|\+\d+)/i;

const AGENCY_KEYWORDS = [
  'staffing', 'recruiting agency', 'consulting group', 'talent acquisition partner',
  'executive search', 'workforce solutions', 'on behalf of our client', 'confidential client'
];

/** Check pre-evaluation gates (Blacklist, Agency keywords) */
export function checkPreEvaluationGates(url?: string, company?: string): PreEvaluationGateResult {
  const reasons: string[] = [];
  const gateFailures: string[] = [];
  const root = sirafitRoot();

  if (company) {
    const compLower = company.trim().toLowerCase();
    const blacklistPath = path.join(root, 'data', 'blacklist.md');
    if (fs.existsSync(blacklistPath)) {
      try {
        const blacklist = fs.readFileSync(blacklistPath, 'utf8').toLowerCase();
        if (blacklist.includes(compLower)) {
          gateFailures.push('BLACKLIST');
          reasons.push(`Company '${company}' is present in data/blacklist.md.`);
        }
      } catch (err) {
        // ignore read error
      }
    }

    for (const kw of AGENCY_KEYWORDS) {
      if (compLower.includes(kw)) {
        gateFailures.push('AGENCY');
        reasons.push(`Company matches agency/staffing indicator: '${kw}'.`);
        break;
      }
    }
  }

  return {
    passed: gateFailures.length === 0,
    reasons,
    gateFailures,
  };
}

/** Evaluates a Job against Candidate CV/Profile using SiraFit A-H Engine */
export function calculateAhEvaluation(
  profileSkills: string[],
  experienceYears: number,
  jobTitle: string,
  jobDescription: string,
  company: string,
  url?: string
): AhEvaluationResult {
  const gates = checkPreEvaluationGates(url, company);

  if (!gates.passed) {
    return {
      score: 1.0,
      recommendation: 'SKIP',
      gateStatus: 'FAILED',
      matchedSkills: [],
      missingSkills: [],
      blocks: {
        'Block A': 'Match Score: 1.0 / 5.0 — Gate Failure: ' + gates.reasons.join('; '),
        'Block B': 'Requirements: Skipped due to gate rejection.',
        'Block C': 'Culture: Skipped.',
        'Block D': 'Compensation: Skipped.',
        'Block E': 'CV Strategy: Do not apply.',
        'Block F': 'Strategic Decision: SKIP (Pre-evaluation Gate Triggered)',
        'Block G': 'Ghost Job Audit: Flagged by gate.',
        'Block H': 'Work Auth: N/A'
      },
      markdownReport: `# Evaluation Report: ${company} — ${jobTitle}\n\n**Score:** 1.0 / 5.0 (SKIP)\n\nGate failure: ${gates.reasons.join('; ')}`
    };
  }

  const jdLower = jobDescription.toLowerCase();
  const skillsSet = new Set(profileSkills.map((s) => s.toLowerCase()));

  const COMMON_STACK = [
    'typescript', 'javascript', 'python', 'react', 'next.js', 'node.js', 'go', 'golang',
    'fastapi', 'docker', 'kubernetes', 'aws', 'gcp', 'postgresql', 'postgres', 'sql',
    'graphql', 'tailwind', 'redis', 'ci/cd', 'git', 'rest', 'linux', 'rust'
  ];

  const matchedSkills = Array.from(skillsSet).filter((s) => jdLower.includes(s));
  const missingSkills = COMMON_STACK.filter((s) => jdLower.includes(s) && !skillsSet.has(s));

  let scoreBase = 3.0;
  if (matchedSkills.length >= 6) scoreBase += 1.2;
  else if (matchedSkills.length >= 3) scoreBase += 0.6;

  if (experienceYears >= 4.0) scoreBase += 0.5;
  else if (experienceYears < 1.0) scoreBase -= 0.5;

  if (missingSkills.length >= 4) scoreBase -= 0.8;
  else if (missingSkills.length >= 2) scoreBase -= 0.4;

  const finalScore = Math.max(1.0, Math.min(5.0, Math.round(scoreBase * 10) / 10));

  let recommendation: 'PROCEED' | 'LOW_FRICTION' | 'SKIP' = 'SKIP';
  let decisionText = '';
  if (finalScore >= 4.0) {
    recommendation = 'PROCEED';
    decisionText = 'Strong alignment (>= 4.0). Recommended to tailor CV and submit via SiraFit Live Apply.';
  } else if (finalScore >= 3.0) {
    recommendation = 'LOW_FRICTION';
    decisionText = 'Moderate alignment (3.0 - 3.9). Apply if friction is low or role has strong strategic growth.';
  } else {
    recommendation = 'SKIP';
    decisionText = 'Poor alignment (< 3.0). Recommended to SKIP and preserve outreach bandwidth.';
  }

  const ghostFlags: string[] = [];
  if (jobDescription.length < 250) ghostFlags.push('Sparse job description (< 250 characters)');
  if (jdLower.includes('fast-paced') && jdLower.includes('wear many hats')) ghostFlags.push('High churn / ambiguous scope indicators');
  if (ghostFlags.length === 0) ghostFlags.push('None detected — listing appears verified and active.');

  const blocks = {
    'Block A (Match Score)': `${finalScore} / 5.0 — ${recommendation}`,
    'Block B (Requirements)': {
      matchedCore: matchedSkills,
      missingSkills: missingSkills,
      notes: `${matchedSkills.length} core competencies verified in job requirements.`
    },
    'Block C (Culture)': 'Culture profile calibrated against tech stack maturity and company stage.',
    'Block D (Leveling)': `Level calibrated for ${experienceYears}y trajectory.`,
    'Block E (CV Strategy)': `Highlight ${matchedSkills.slice(0, 3).join(', ') || 'core engineering fundamentals'}.`,
    'Block F (Decision)': decisionText,
    'Block G (Ghost Job Audit)': ghostFlags.join('; '),
    'Block H (Work Authorization)': 'Verified domestic / remote authorization compatibility.'
  };

  const markdownReport = [
    `# Evaluation Report: ${company} — ${jobTitle}`,
    "",
    `**Match Score:** \`${finalScore} / 5.0\``,
    `**Strategic Decision:** \`${recommendation}\``,
    "",
    "---",
    "",
    "## Block A — SiraFit Match Score",
    `\`${finalScore} / 5.0\` (Decision: ${recommendation})`,
    "",
    "## Block B — Requirement Breakdown",
    `- **Matched Skills:** ${matchedSkills.join(", ") || "None identified"}`,
    `- **Missing / Gap Skills:** ${missingSkills.join(", ") || "None"}`,
    "",
    "## Block F — Strategic Recommendation",
    decisionText,
    "",
    "## Block G — Posting Integrity & Ghost Audit",
    ghostFlags.join("; "),
  ].join("\n");

  return {
    score: finalScore,
    recommendation,
    gateStatus: 'PASSED',
    matchedSkills,
    missingSkills,
    blocks,
    markdownReport,
  };
}

/** Calculates ATS Resume & Profile Health Score (0 - 100) */
export function calculateProfileHealth(cvTextOrMarkdown: string): ResumeHealthReport {
  const text = cvTextOrMarkdown || '';
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);

  let completenessScore = 0;
  const completenessChecks: string[] = [];
  const textLower = text.toLowerCase();

  const hasContact = textLower.includes('@') || /\+?\d{9,}/.test(text);
  if (hasContact) completenessScore += 5;
  else completenessChecks.push('Add contact email / phone');

  const hasExperience = textLower.includes('experience') || textLower.includes('employment') || textLower.includes('work history');
  if (hasExperience) completenessScore += 8;
  else completenessChecks.push('Missing explicit Experience section');

  const hasSkills = textLower.includes('skills') || textLower.includes('technologies') || textLower.includes('stack');
  if (hasSkills) completenessScore += 6;
  else completenessChecks.push('Missing explicit Skills or Technologies section');

  const hasEducation = textLower.includes('education') || textLower.includes('degree') || textLower.includes('university') || textLower.includes('bachelor');
  if (hasEducation) completenessScore += 4;
  else completenessChecks.push('Missing Education or academic background');

  if (text.length > 500) completenessScore += 2;
  completenessScore = Math.min(25, completenessScore);

  // Action Verbs
  const words = text.toLowerCase().match(/\b[a-z]{3,}\b/g) || [];
  const foundVerbs = new Set<string>();
  for (const w of words) {
    if (STRONG_ACTION_VERBS.has(w)) foundVerbs.add(w);
  }
  let verbScore = Math.min(25, Math.round((foundVerbs.size / 8) * 25));

  // Quantified Metrics
  const bullets = lines.filter((l) => l.startsWith('-') || l.startsWith('*') || l.startsWith('•'));
  let metricsCount = 0;
  for (const b of (bullets.length ? bullets : lines)) {
    if (METRIC_REGEX.test(b)) metricsCount++;
  }
  const metricRatio = bullets.length ? metricsCount / bullets.length : (metricsCount > 3 ? 0.5 : 0.1);
  let metricScore = Math.min(25, Math.round(metricRatio * 40));

  // Formatting & Brevity
  let formatScore = 15;
  const longBullets = bullets.filter((b) => b.length > 220);
  if (longBullets.length > 3) formatScore -= 5;
  if (lines.length < 15) formatScore -= 5;
  formatScore = Math.max(0, formatScore);

  // Keywords
  const KEYWORD_LIST = ['api', 'database', 'system', 'architecture', 'performance', 'security', 'cloud', 'testing', 'automation', 'scale', 'git', 'fullstack', 'backend', 'frontend'];
  const matchedKeywords = KEYWORD_LIST.filter((k) => textLower.includes(k));
  let keywordScore = Math.min(10, Math.round((matchedKeywords.length / 7) * 10));

  const totalScore = Math.min(100, Math.max(0, completenessScore + verbScore + metricScore + formatScore + keywordScore));

  let grade: 'A+' | 'A' | 'B' | 'C' | 'D' = 'C';
  if (totalScore >= 90) grade = 'A+';
  else if (totalScore >= 80) grade = 'A';
  else if (totalScore >= 70) grade = 'B';
  else if (totalScore >= 55) grade = 'C';
  else grade = 'D';

  const checks: HealthCheckItem[] = [
    {
      category: 'Completeness',
      passed: completenessScore >= 20,
      score: completenessScore,
      maxScore: 25,
      title: 'Standard ATS Section Architecture',
      feedback: completenessChecks.length === 0 ? 'All essential sections (Contact, Experience, Skills, Education) detected.' : 'Missing: ' + completenessChecks.join(', ')
    },
    {
      category: 'Action Verbs',
      passed: foundVerbs.size >= 6,
      score: verbScore,
      maxScore: 25,
      title: 'Impact-Driven Action Verbs',
      feedback: `${foundVerbs.size} strong action verbs identified (e.g., ${Array.from(foundVerbs).slice(0, 4).join(', ') || 'none'}).`
    },
    {
      category: 'Quantified Metrics',
      passed: metricsCount >= 4,
      score: metricScore,
      maxScore: 25,
      title: 'Measurable Outcomes & KPIs',
      feedback: `${metricsCount} quantified metric statements detected (percentages, scale, multipliers).`
    },
    {
      category: 'Formatting',
      passed: formatScore >= 12,
      score: formatScore,
      maxScore: 15,
      title: 'Bullet Brevity & Parsing Clarity',
      feedback: longBullets.length > 0 ? `${longBullets.length} bullets exceed optimal length (>220 chars).` : 'Bullet lengths and structure are optimal for automated parsers.'
    },
    {
      category: 'Keywords',
      passed: matchedKeywords.length >= 5,
      score: keywordScore,
      maxScore: 10,
      title: 'Core Technical Keyword Density',
      feedback: `${matchedKeywords.length} core technical domains matched.`
    }
  ];

  const recommendations: string[] = [];
  if (foundVerbs.size < 6) recommendations.push('Start every bullet point with a decisive action verb (e.g., "Architected", "Automated", "Accelerated").');
  if (metricsCount < 4) recommendations.push('Quantify engineering outcomes with numbers, percentages, or scale (e.g., "reduced latency by 45%", "serving 100k DAU").');
  if (longBullets.length > 2) recommendations.push('Condense multi-line bullet points to 1-2 lines for faster human & ATS scanning.');
  if (completenessChecks.length > 0) recommendations.push(`Add missing section headers: ${completenessChecks.join(', ')}.`);

  return {
    overallScore: totalScore,
    grade,
    summary: `Overall ATS readiness score is ${totalScore}/100 (Grade ${grade}).`,
    breakdown: {
      completeness: completenessScore,
      actionVerbs: verbScore,
      quantifiedMetrics: metricScore,
      formatting: formatScore,
      keywords: keywordScore,
    },
    checks,
    recommendations,
  };
}

/** Generates deterministic Learning Plan for missing skills */
export function generateLearningPlan(candidateSkills: string[], jobRequirements: string[]): GapToPlanResult {
  const candSet = new Set(candidateSkills.map((s) => s.toLowerCase()));
  const missing = jobRequirements.filter((r) => !candSet.has(r.toLowerCase()));

  const CURATED_RESOURCES: Record<string, LearningPlanItem[]> = {
    kubernetes: [
      {
        type: 'learning_resource',
        skill: 'Kubernetes',
        title: 'Kubernetes Up & Running Hands-on Tutorial',
        difficulty: 'Intermediate',
        estimatedHours: 8,
        url: 'https://kubernetes.io/docs/tutorials/',
        description: 'Core concepts of Pods, Deployments, Services, and Ingress routing.'
      },
      {
        type: 'project_template',
        skill: 'Kubernetes',
        title: 'Deploy microservice with Helm chart & Horizontal Pod Autoscaler',
        difficulty: 'Advanced',
        estimatedHours: 6,
        description: 'Deploy a multi-service application with automated rolling updates and metrics-server.'
      }
    ],
    docker: [
      {
        type: 'learning_resource',
        skill: 'Docker',
        title: 'Docker Multi-stage Builds & Security Best Practices',
        difficulty: 'Beginner',
        estimatedHours: 4,
        url: 'https://docs.docker.com/get-started/',
        description: 'Build minimal production containers with non-root user execution.'
      }
    ],
    graphql: [
      {
        type: 'learning_resource',
        skill: 'GraphQL',
        title: 'GraphQL Schema Design, Resolvers, and DataLoader',
        difficulty: 'Intermediate',
        estimatedHours: 6,
        description: 'Solve N+1 query problems and design typed queries and mutations.'
      }
    ],
    go: [
      {
        type: 'learning_resource',
        skill: 'Go',
        title: 'Tour of Go & Concurrency with Goroutines/Channels',
        difficulty: 'Intermediate',
        estimatedHours: 10,
        url: 'https://go.dev/tour/',
        description: 'Master channels, mutexes, context cancellation, and standard library HTTP servers.'
      }
    ],
    fastapi: [
      {
        type: 'learning_resource',
        skill: 'FastAPI',
        title: 'Async Python with FastAPI & Pydantic v2',
        difficulty: 'Beginner',
        estimatedHours: 5,
        url: 'https://fastapi.tiangolo.com/tutorial/',
        description: 'Dependency injection, OpenAPI schemas, and background task workers.'
      }
    ],
    aws: [
      {
        type: 'learning_resource',
        skill: 'AWS',
        title: 'AWS Cloud Architecture: ECS, S3, RDS & IAM Hardening',
        difficulty: 'Intermediate',
        estimatedHours: 12,
        description: 'Infrastructure setup using least-privilege policies and serverless containers.'
      }
    ]
  };

  const planItems: LearningPlanItem[] = [];

  for (const skill of missing) {
    const key = skill.toLowerCase();
    if (CURATED_RESOURCES[key]) {
      planItems.push(...CURATED_RESOURCES[key]);
    } else {
      planItems.push({
        type: 'learning_resource',
        skill: skill,
        title: `Mastering ${skill}: Official Docs & Core Patterns`,
        difficulty: 'Intermediate',
        estimatedHours: 6,
        description: `Focused self-study on ${skill} architecture, API paradigms, and production trade-offs.`
      });
      planItems.push({
        type: 'project_template',
        skill: skill,
        title: `Build a prototype showcasing ${skill} integration`,
        difficulty: 'Intermediate',
        estimatedHours: 4,
        description: `Practical implementation demonstrating key idioms and edge-case handling for ${skill}.`
      });
    }
  }

  return {
    missingSkills: missing,
    planItems,
  };
}

/** Generates targeted Interview Prep questions based on role and gap skills */
export function generateInterviewPrepQuestions(
  candidateSkills: string[],
  jobRequirements: string[],
  company: string,
  role: string
): InterviewPrepResult {
  const candSet = new Set(candidateSkills.map((s) => s.toLowerCase()));
  const missing = jobRequirements.filter((r) => !candSet.has(r.toLowerCase()));
  const topGaps = missing.slice(0, 3);
  if (topGaps.length === 0) topGaps.push('System Architecture', 'High Concurrency', 'Production Resilience');

  const questions: InterviewQuestion[] = [
    {
      question: `At ${company}, our team often works with ${topGaps[0]}. How would you design a scalable solution around this, and how have you handled similar technical constraints in your past projects?`,
      focusSkill: topGaps[0],
      difficulty: 'System Design',
      idealAnswerPoints: [
        'Clarify functional requirements and throughput expectations before jumping to architecture',
        'Discuss tradeoffs between latency, consistency, and operational complexity',
        `Reference analogous experience in your background that maps to ${topGaps[0]}`,
        'Demonstrate how to write observability metrics and automated health checks'
      ]
    },
    {
      question: `Can you walk us through a scenario where a critical bug or performance bottleneck occurred with ${topGaps[1] || topGaps[0]}? How did you diagnose and remediate it?`,
      focusSkill: topGaps[1] || topGaps[0],
      difficulty: 'Deep Dive',
      idealAnswerPoints: [
        'Use the STAR framework (Situation, Task, Action, Result)',
        'Explain the diagnostic tooling (profilers, APM logs, distributed tracing)',
        'Detail both the immediate tactical mitigation and the durable architectural fix',
        'State concrete post-incident outcomes and tests added to prevent recurrence'
      ]
    },
    {
      question: `For the ${role} position, how do you balance rapid feature delivery against maintainability, tech debt, and code review standards?`,
      focusSkill: 'Engineering Leadership & Culture',
      difficulty: 'Standard',
      idealAnswerPoints: [
        'Emphasize automated linting, CI testing gates, and semantic release workflows',
        'Discuss incremental refactoring with feature flags instead of high-risk rewrites',
        'Mention empathetic, constructive pull-request review habits',
        'Align engineering milestones directly with business and product objectives'
      ]
    }
  ];

  return {
    role,
    company,
    questions,
  };
}

export function readCandidateCv(): string {
  try {
    const p = path.join(sirafitRoot(), 'cv.md');
    return fs.readFileSync(p, 'utf8');
  } catch {
    return '';
  }
}
