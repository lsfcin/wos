// opencode config facade — public surface consumed by plugins/workspace-policy.js.
// Re-exports the workspace-policy translation helpers (spawning, schema mapping,
// warning surfacing). See ./wp-helpers.js for implementations and ./CONTEXT.md
// for the full event -> script mapping.
export * from "./wp-helpers.js"
