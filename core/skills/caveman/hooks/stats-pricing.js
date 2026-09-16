// caveman — savings math: compression ratios, model pricing, derived estimates
//
// Everything here is an estimate and is labelled as one wherever it surfaces.
// Kept separate from collection (stats-data.js) and rendering (stats-format.js)
// so the numbers can be checked without reading either.

// Mean per-task savings from benchmarks/results/*.json (avg_savings: 65 across
// 10 tasks, sonnet-4-20250514). Only 'full' has measured data; lite / ultra /
// wenyan modes show no estimate until benchmarked. Add an entry here when a new
// run is committed.
const COMPRESSION = { 'full': 0.65 };

// Approximate Anthropic public output-token pricing, USD per million.
// Match by model id prefix so this stays correct across point releases
// (e.g. claude-sonnet-4-20250514, claude-sonnet-4-7). Update from
// https://www.anthropic.com/pricing if a release changes the level.
const MODEL_OUTPUT_PRICE_PER_M = [
  ['claude-opus-4',     75.00],
  ['claude-sonnet-4',   15.00],
  ['claude-haiku-4',     4.00],
  ['claude-3-5-sonnet', 15.00],
  ['claude-3-5-haiku',   4.00],
  ['claude-3-opus',     75.00],
];

function priceForModel(model) {
  if (!model) return null;
  for (const [prefix, price] of MODEL_OUTPUT_PRICE_PER_M) {
    if (model.startsWith(prefix)) return price;
  }
  return null;
}

function formatUsd(amount) {
  if (amount >= 1) return `$${amount.toFixed(2)}`;
  if (amount >= 0.01) return `$${amount.toFixed(3)}`;
  return `$${amount.toFixed(4)}`;
}

// The one place the savings estimate is computed. `ratio` and `price` come back
// with it so callers can render "no benchmark for this mode" without recomputing.
// A null ratio means: no measured data, claim nothing.
function deriveSavings({ outputTokens, mode, model }) {
  const ratio = COMPRESSION[mode] != null ? COMPRESSION[mode] : null;
  const price = priceForModel(model);
  if (ratio === null) {
    return { ratio: null, price, estNormal: null, estSavedTokens: 0, estSavedUsd: 0 };
  }
  const estNormal = Math.round(outputTokens / (1 - ratio));
  const estSavedTokens = estNormal - outputTokens;
  const estSavedUsd = price !== null ? (estSavedTokens / 1_000_000) * price : 0;
  return { ratio, price, estNormal, estSavedTokens, estSavedUsd };
}

// Parse "7d", "12h" etc. to milliseconds. Returns null on invalid input.
function parseDuration(spec) {
  if (!spec) return null;
  const m = /^(\d+)([dh])$/.exec(spec.trim());
  if (!m) return null;
  const n = parseInt(m[1], 10);
  return m[2] === 'd' ? n * 86_400_000 : n * 3_600_000;
}

function humanizeTokens(n) {
  if (!Number.isFinite(n) || n <= 0) return '0';
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'k';
  return String(Math.round(n));
}

module.exports = {
  COMPRESSION, MODEL_OUTPUT_PRICE_PER_M,
  priceForModel, formatUsd, deriveSavings, parseDuration, humanizeTokens,
};
