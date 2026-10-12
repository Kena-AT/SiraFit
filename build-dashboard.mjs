#!/usr/bin/env node
// build-dashboard.mjs â€” cross-platform build for the Go TUI dashboard.
//
// `go build -o sirafit-dashboard .` writes an extension-less binary on Windows
// (Go only auto-appends .exe when -o is omitted), which breaks bare-name/PATH
// lookup there. This wrapper picks the platform-correct output name instead:
// dashboard/sirafit-dashboard on Unix, dashboard/sirafit-dashboard.exe on Windows.

import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const out = process.platform === 'win32' ? 'sirafit-dashboard.exe' : 'sirafit-dashboard';

const result = spawnSync('go', ['build', '-o', out, '.'], {
  cwd: join(root, 'dashboard'),
  stdio: 'inherit',
});

if (result.error) {
  if (result.error.code === 'ENOENT') {
    console.error('Go toolchain not found. Install Go 1.24+ from https://go.dev/dl/ and retry.');
  } else {
    console.error(`Build failed to start: ${result.error.message}`);
  }
  process.exit(1);
}

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}

console.log(`Built dashboard/${out} â€” run it with: npm run serve:dashboard (or dashboard/${out} --path .)`);

