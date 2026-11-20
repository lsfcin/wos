# Forms — Specs
> The spec format a form is written in, the two grants it authenticates with, and the failure
> that reads like a permission bug and is not one.

Companion to [`CONTEXT.md`](CONTEXT.md), which says what this directory is and how to call it.

## The spec is the form

`new` creates, fills and files in one call, so a survey is authored as a JSON file in the workspace and pushed — never clicked together in the browser and then lost. The questions therefore diff, review and get reused across terms; Google holds a copy, not the original.

`{"title", "documentTitle", "description", "items": [...]}`, one entry per item:

| `type` | Fields it reads |
|--------|-----------------|
| `section` | `title`, `description` — a page break, not a question |
| `note` | `title`, `description` — text block, nothing to answer |
| `text` | `paragraph` (long answer) |
| `radio` / `checkbox` / `dropdown` | `options[]`, `other`, `shuffle` |
| `scale` | `low`, `high`, `lowLabel`, `highLabel` |
| `time` | `duration` |
| `date` | `includeTime`, `includeYear` |

Every question type also takes `title`, `description` and `required`. An unknown type raises before anything reaches Google, because the API's own error for a malformed request does not name the typo.

**The description is a `updateFormInfo`, not part of creation.** `forms.create` accepts a title and nothing else, so the builder emits the description first and the items after — order is load-bearing and [`../test/test_forms.py`](../test/test_forms.py) holds it.

## Two grants, not one

Same split as [`../files/`](../files/CONTEXT.md). Reads use the `forms` token (`forms.body.readonly` + `forms.responses.readonly`); `new` and `apply` use `forms-write` (`forms.body` + `drive.file`). `drive.file` rides along because filing a new form into a Drive folder is a Drive write — and it reaches only files this tool itself created, which is why it is acceptable to carry here at all.

A read re-consent leaves the write token dead: `gforms auth <alias> --write --reauth` is a different command, and the recovery message says so.

## A disabled API looks like a permission bug and is not one

`SERVICE_DISABLED` comes back from every call until Google Forms API is switched on in the GCP project that owns the OAuth client. No scope fixes it, and re-consenting looks like it should but does not — the consent screen and the API library are different pages. That switch is a click in Google's console, so it is Lucas's: [SETUP-accounts.md](../../../SETUP-accounts.md) § Google Forms API. Live since 2026-08-19 on project `workspace-os-506016`, created by him and carrying gmail, calendar, docs, slides and sheets too — the successor to `workspace-gmail-499605` for anything needing the console.
One project serves every account: the project owns the *app*, an account only consents to it, so a second account needs a row under *Audience → Test users* rather than a second project.

## `apply` is the general boundary

The Forms API is itself a list of typed requests, so the CLI wraps that list rather than inventing a DSL that goes stale the moment Google adds a request type. `new` is the convenience over it, and `read --json` gives the input side of the same shape.

## Responses come back as text

`responses` joins `questionId` to the question title and prints the answers. That is the whole payload for an anonymous form — there is no identity column a spreadsheet would add, so a CSV export would be a second format carrying the same thing.
