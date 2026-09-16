# notes — Specs
> Notion API gotchas and the auth mechanics specific to this tool.

## Auth: Lucas mints the secret, the agent does everything else

Notion has no headless consent flow: the secret is minted inside Lucas's account at
[my-integrations](https://www.notion.so/my-integrations) and a page is connected to it one at a
time — his only two clicks. Everything with a command form is the agent's, including storing the
secret through the builtin pipe (`printf … | notion auth <alias>`); the family-wide protocol
(auth-failure relay, argv-safe storage) lives in [`../SPECS.md`](../SPECS.md).

## A 404 is a sharing failure until proven otherwise

Notion returns the same code for "not connected to this integration" and "no such id," and the
first is by far the more common cause: content stays invisible to an integration it hasn't been
shared with. `not_shared_text` leads with that reading on purpose.

## No read/write token split

Capabilities are chosen when the integration is created (AD-11's exception, see
[`../../SPECS.md`](../../SPECS.md) § AD-11) — unlike Slides or Drive, one secret with
Read + Update + Insert already carries the strongest grant, so there is no second token to
request.

## `VERSION` pins the API contract

`notion_core.py`'s `VERSION` header is mandatory on every request. Notion breaks by version, not
by date, so a bump can silently change the shape of a database response.
