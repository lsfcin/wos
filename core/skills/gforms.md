---
name: gforms
description: >
  Google Forms as versioned specs: create, edit and read answers across all configured accounts —
  a form written as JSON, applied in one call.
---

Google Forms across all configured accounts (personal, cin, ufrpe): a form written as a versioned
spec, applied in one call, answers read as text.

Arguments: $ARGUMENTS

## Commands

```
core/run tools/forms/gforms new       --account personal --folder <drive_folder_id> spec.json
core/run tools/forms/gforms read      --account personal <form_id>    # outline + responder link
core/run tools/forms/gforms apply     --account personal <form_id> requests.json
core/run tools/forms/gforms responses --account personal <form_id>    # answers as text
```

## How to work a form

1. Author the spec as JSON (the compact format is documented in `core/tools/forms/SPECS.md`), keep
   it versioned next to the material it belongs to, then `new` from it.
2. Edit through `apply` request lists, the same shape the Forms API itself takes.
3. `responses` prints answers as text — read them per turma, never pooled: the specs Lucas applies
   live keep one form per discipline (`academy/teaching/*`).

## Notes

- Two auth grants per account — on a dead token the CLI names the fix:
  `core/run tools/forms/gforms auth <alias> --reauth` (add `--write` for the write grant)
- `SERVICE_DISABLED` on first use is the Forms API not being enabled for the account yet — it is a
  one-click console toggle, not a permission bug; the SPECS names it
- The responder link comes back from `read`; edit links are account-bound
