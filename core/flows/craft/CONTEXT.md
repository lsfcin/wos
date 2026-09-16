# Craft Flows
> The engineering cluster owned by the `craft` skill — build work in file-relayed loops. Invoked as `/craft`.

Entry point: the `craft` skill ([`core/skills/craft.md`](../../skills/craft.md)) — it loads the
shared discipline before any file here is read directly.

Why `craft.md` stays one file instead of splitting further: [`SPECS.md`](SPECS.md).

<!-- routing:start -->
## Routing

| File | Description |
|------|-------------|
| [`SPECS.md`](SPECS.md) | How `craft.md` is split, and the axis both of its splits followed. |
| [`architect.md`](architect.md) | Architecture-decision folder of the craft tree — turn a design/technology choice into a recorded decision (problem → options → trade-offs → decision → ADR). Produces a durable decision record, not code. |
| [`craft-build.md`](craft-build.md) | Loops 3-4b of the craft flow — architecture, contract layout, tests first, then code until green. |
| [`craft-plan.md`](craft-plan.md) | Loops 0-2 of the craft flow — clarify the ask, plan it adversarially, ground it in the code that exists. |
| [`craft-ship.md`](craft-ship.md) | Loops 5-6.5 of the craft flow — user test, ship the branch, and extract any skill the run earned. |
| [`craft.md`](craft.md) | Looped engineering flow — development in file-relayed loops with model autorouting; each loop runs in a fresh, cheap session that reads exactly one file. |
| [`prior-art.md`](prior-art.md) | Where this flow comes from, what evidence backs its routing decisions, and one worked failure it caught. **Nothing here is needed to run the flow** — load it when changing the flow, defending it, or writing about it. |
| [`route.md`](route.md) | Loop router — classify a /craft task by TYPE and dispatch to the right folder flow (padaria · feature/SDD · research · architecture). Thin: it classifies and hands off, it does not do the work. |
| [`routing.md`](routing.md) | Which concrete model fills each level, per provider; the availability check; the delegation direction; and how to refresh the table. **VOLATILE** — model ids and prices go stale. |
| [`runtimes.md`](runtimes.md) | How the orchestrator actually spawns a loop, per runtime. Verbatim recipes; no improvisation. |
| [`tree.md`](tree.md) | Canonical map of `/craft`: a router classifies each task and dispatches to a folder whose step-sequence fits the work. Goals: [craft-flows](../../../brain/goals/craft-flows.md), [spec-driven-development](../../../brain/goals/spec-driven-development.md). |
<!-- routing:end -->
