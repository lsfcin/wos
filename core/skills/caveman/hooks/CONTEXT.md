# hooks
> Claude Code lifecycle hooks for the caveman suite — activation, mode tracking, stats, statusline.

These are **standalone scripts run by node/bash**, not an importable module: `~/.claude/settings.json`
names four of them by absolute path (through the symlinks `core/tools/wos/sync-global-skills` creates).
That is why there is no facade here — nothing outside this directory imports it.

[`ENTRYPOINTS`](ENTRYPOINTS) declares which files get linked into `~/.claude/hooks`. Add a helper
module and it stays internal; add an entrypoint and it must be listed there **and** wired in
`settings.json`.

**Four entrypoints, each named by the lifecycle event that fires it** — SessionStart,
UserPromptSubmit, statusLine, and the `/caveman stats` CLI. Everything else here is a helper they
import: the flag API, its symlink-safe file I/O, and the three modules `stats` splits into. Which
file is which is the routing table's job; its descriptions come from their own first lines.

Attribution: [`../CONTEXT.md`](../CONTEXT.md). Wiring, and the local adaptations a re-sync has to
reconcile: [`../SPECS.md`](../SPECS.md).

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`activate.js`](activate.js) | [`activate.d.ts`](activate.d.ts) | — | caveman — Claude Code SessionStart activation hook |
| [`config.js`](config.js) | [`config.d.ts`](config.d.ts) | `getConfigDir`, `getConfigPath`, `featureOff`, `getDefaultMode`, `readFlag` | caveman — shared configuration resolver, and the façade the hooks import |
| [`flagfile.js`](flagfile.js) | [`flagfile.d.ts`](flagfile.d.ts) | `safeWriteFlag`, `readFlag`, `appendFlag`, `readHistory` | caveman — reads and writes of the mode flag and the lifetime history log |
| [`jsconfig.json`](jsconfig.json) | — | — | Type-checking settings for the caveman hooks — tells tsc these are CommonJS Node scripts, so the generated .d.ts stubs are correct. |
| [`mode-tracker.js`](mode-tracker.js) | [`mode-tracker.d.ts`](mode-tracker.d.ts) | — | caveman — UserPromptSubmit hook to track which caveman mode is active |
| [`safepath.js`](safepath.js) | [`safepath.d.ts`](safepath.d.ts) | `debugLog`, `resolveSafeDir`, `isWritableTarget`, `prepareTarget`, `withFd` | caveman — symlink-safe path resolution shared by every flag-file writer |
| [`stats-data.js`](stats-data.js) | [`stats-data.d.ts`](stats-data.d.ts) | `findRecentSession`, `parseSession`, `findCompressedPairs`, `summarizeCompressed`, `aggregateHistory` | caveman — collection: read session transcripts, the history log, and compressed |
| [`stats-format.js`](stats-format.js) | [`stats-format.d.ts`](stats-format.d.ts) | `formatHistory`, `formatShare`, `savingsBlock`, `formatStats` | caveman — rendering: turn collected numbers into the three printed views. |
| [`stats-pricing.js`](stats-pricing.js) | [`stats-pricing.d.ts`](stats-pricing.d.ts) | `priceForModel`, `formatUsd`, `deriveSavings`, `parseDuration`, `humanizeTokens` | caveman — savings math: compression ratios, model pricing, derived estimates |
| [`stats.js`](stats.js) | [`stats.d.ts`](stats.d.ts) | `reportLifetime`, `recordSnapshot`, `main` | caveman stats — read the active Claude Code session log, print real token usage |
| [`statusline.sh`](statusline.sh) | — | — | caveman — statusline badge script for Claude Code Reads the caveman mode flag file and outputs a colored badge. |
<!-- routing:end -->
