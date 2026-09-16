#!/usr/bin/env node
// caveman stats — read the active Claude Code session log, print real token usage
// plus an estimated savings figure from the benchmark in benchmarks/.
//
// Run directly:    node core/skills/caveman/hooks/stats.js
// Inside Claude:   /caveman stats triggers this via the UserPromptSubmit hook.
// Hook integration passes --session-file <transcript_path> so we always read the
// active session, not whichever JSONL was modified most recently.
//
// This file is the CLI only. Collection is in stats-data.js, the savings math in
// stats-pricing.js, and the printed views in stats-format.js.

const path = require('path');
const os = require('os');
const { readFlag, appendFlag, safeWriteFlag } = require('./config');
const { deriveSavings, parseDuration, humanizeTokens } = require('./stats-pricing');
const {
  findRecentSession, parseSession, findCompressedPairs, summarizeCompressed, aggregateHistory,
} = require('./stats-data');
const { formatHistory, formatShare, formatStats } = require('./stats-format');

// Lifetime views need no live session, so they answer and exit early.
function reportLifetime(historyPath, sinceArg) {
  const sinceMs = parseDuration(sinceArg);
  if (sinceArg && sinceMs === null) {
    process.stderr.write(`caveman stats: --since takes Nh or Nd (e.g. 7d, 24h), got: ${sinceArg}\n`);
    process.exit(2);
  }
  const agg = aggregateHistory(historyPath, sinceMs);
  process.stdout.write(formatHistory({ ...agg, since: sinceArg || null }));
}

// Append a snapshot of this session's totals to the lifetime log. Multiple
// /caveman stats calls in one session emit multiple lines for the same
// session_id; aggregateHistory keeps only the latest per session_id.
function recordSnapshot({ claudeDir, historyPath, sessionFile, parsed, mode }) {
  const { estSavedTokens, estSavedUsd } = deriveSavings({ ...parsed, mode });
  appendFlag(historyPath, JSON.stringify({
    ts: Date.now(),
    session_id: path.basename(sessionFile, '.jsonl'),
    mode: mode || null,
    model: parsed.model || null,
    output_tokens: parsed.outputTokens,
    est_saved_tokens: estSavedTokens,
    est_saved_usd: estSavedUsd,
  }));

  // Statusline suffix: tiny pre-rendered string the shell statusline can cat
  // without parsing JSONL. Routed through safeWriteFlag — the suffix path is
  // predictable and user-owned, same symlink-clobber surface as the flag.
  const agg = aggregateHistory(historyPath, null);
  const suffix = agg.estSavedTokens > 0 ? `⛏ ${humanizeTokens(agg.estSavedTokens)}` : '';
  safeWriteFlag(path.join(claudeDir, '.caveman-statusline-suffix'), suffix);
}

function main() {
  const args = process.argv.slice(2);
  const fileIdx = args.indexOf('--session-file');
  const sinceIdx = args.indexOf('--since');
  const sessionFileArg = fileIdx !== -1 ? args[fileIdx + 1] : null;
  const sinceArg = sinceIdx !== -1 ? args[sinceIdx + 1] : null;

  const claudeDir = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
  const historyPath = path.join(claudeDir, '.caveman-history.jsonl');

  if (args.includes('--all') || sinceArg) {
    reportLifetime(historyPath, sinceArg);
    return;
  }

  const sessionFile = sessionFileArg || findRecentSession(claudeDir);
  if (!sessionFile) {
    process.stderr.write('caveman stats: no Claude Code session found.\n');
    process.exit(1);
  }

  const parsed = parseSession(sessionFile);
  const mode = readFlag(path.join(claudeDir, '.caveman-active'));

  if (parsed.turns > 0) {
    recordSnapshot({ claudeDir, historyPath, sessionFile, parsed, mode });
  }

  if (args.includes('--share')) {
    process.stdout.write(formatShare({ ...parsed, mode }) + '\n');
    return;
  }

  const scanDirs = [claudeDir, process.cwd()].filter((d, i, a) => a.indexOf(d) === i);
  const compressed = summarizeCompressed(findCompressedPairs(scanDirs));
  process.stdout.write(formatStats({ ...parsed, mode, sessionPath: sessionFile, compressed }));
}

if (require.main === module) main();

// Re-exported so the split stays invisible to anything that imported stats.js.
module.exports = {
  ...require('./stats-pricing'),
  ...require('./stats-data'),
  ...require('./stats-format'),
};
