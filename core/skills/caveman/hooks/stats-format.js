// caveman — rendering: turn collected numbers into the three printed views.
// Pure functions, so tests can pass synthetic inputs. All estimates route
// through deriveSavings so the math is stated in exactly one place.

const { formatUsd, deriveSavings } = require('./stats-pricing');

const SEP = '──────────────────────────────────';

function formatHistory({ sessions, outputTokens, estSavedTokens, estSavedUsd, since }) {
  const window = since ? ` (last ${since})` : '';
  if (sessions === 0) {
    return `\nCaveman Stats — Lifetime${window}\n${SEP}\n` +
      `No sessions logged yet — run /caveman stats inside any session to start tracking.\n${SEP}\n`;
  }
  const usdLine = estSavedUsd > 0 ? `Est. saved (USD):      ~${formatUsd(estSavedUsd)}\n` : '';
  return `\nCaveman Stats — Lifetime${window}\n${SEP}\n` +
    `Sessions:   ${sessions.toLocaleString()}\n${SEP}\n` +
    `Output tokens:         ${outputTokens.toLocaleString()}\n` +
    `Est. tokens saved:     ${estSavedTokens.toLocaleString()}\n` +
    usdLine + SEP + '\n';
}

// Single-line tweetable summary. Stays human-friendly when no ratio is known.
function formatShare({ outputTokens, turns, mode, model }) {
  if (turns === 0) {
    return '🪨 caveman armed but no turns yet — caveman.sh';
  }
  const { ratio, price, estSavedTokens, estSavedUsd } = deriveSavings({ outputTokens, mode, model });
  if (ratio === null) {
    return `🪨 ${turns} turns, ${outputTokens.toLocaleString()} output tokens this session — caveman.sh`;
  }
  const usd = price !== null ? ` (~${formatUsd(estSavedUsd)})` : '';
  return `🪨 Saved ${estSavedTokens.toLocaleString()} output tokens${usd} across ${turns} turns this session — caveman.sh`;
}

// The savings paragraph of the full report, plus the footer that qualifies it.
function savingsBlock({ outputTokens, mode, model }) {
  const { ratio, price, estNormal, estSavedTokens, estSavedUsd } =
    deriveSavings({ outputTokens, mode, model });

  if (ratio === null) {
    const savings = mode && mode !== 'off'
      ? `No savings estimate for '${mode}' mode — only 'full' has benchmark data.`
      : 'Caveman not active this session.';
    return { savings, footer: '' };
  }

  const usdLine = price !== null ? `Est. saved (USD):      ~${formatUsd(estSavedUsd)}` : '';
  const footer = price !== null
    ? `Savings est. from benchmarks/ (mean per-task). Pricing for ${model}. Actual varies by task.`
    : 'Savings est. from benchmarks/ (mean per-task). Actual varies by task.';
  const savings =
    `Est. without caveman:  ${estNormal.toLocaleString()}\n` +
    `Est. tokens saved:     ${estSavedTokens.toLocaleString()} (~${Math.round(ratio * 100)}%)\n` +
    usdLine;
  return { savings, footer };
}

function formatStats({ outputTokens, cacheReadTokens, turns, mode, model, sessionPath, compressed }) {
  if (turns === 0) {
    return `\nCaveman Stats\n${SEP}\nNo conversation yet — stats available after first response.\n${SEP}\n`;
  }

  const shortPath = sessionPath && sessionPath.length > 45
    ? '...' + sessionPath.slice(-45)
    : (sessionPath || '');
  const { savings, footer } = savingsBlock({ outputTokens, mode, model });

  let memoryLine = '';
  if (compressed && compressed.count > 0) {
    memoryLine = `${SEP}\nMemory compressed:     ${compressed.count} file${compressed.count === 1 ? '' : 's'}, ` +
      `~${compressed.tokensSaved.toLocaleString()} tokens saved per session start (approx)\n`;
  }

  return `\nCaveman Stats\n${SEP}\n` +
    (shortPath ? `Session:  ${shortPath}\n` : '') +
    `Turns:    ${turns}\n${SEP}\n` +
    `Output tokens:         ${outputTokens.toLocaleString()}\n` +
    `Cache-read tokens:     ${cacheReadTokens.toLocaleString()}\n${SEP}\n` +
    `${savings}\n` +
    memoryLine +
    (footer ? footer + '\n' : '');
}

module.exports = { formatHistory, formatShare, formatStats };
