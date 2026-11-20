# forms
> Surveys and their answers: a form written as a versioned spec, applied in one call. Provider leaf: `gforms`.

```bash
core/run tools/forms/gforms new       --account personal --folder <drive_folder_id> spec.json
core/run tools/forms/gforms read      --account personal <form_id>     # outline + responder link
core/run tools/forms/gforms apply     --account personal <form_id> requests.json
core/run tools/forms/gforms responses --account personal <form_id>     # answers as text
```

The spec format, the two auth grants, why `SERVICE_DISABLED` is not a permission bug, and what `responses` returns: [`SPECS.md`](SPECS.md). The specs Lucas actually applies live with the course material, one copy per discipline — [`academy/teaching/classes/ai4good/`](../../../academy/teaching/classes/ai4good/CONTEXT.md)
and [`academy/teaching/classes/techedu/`](../../../academy/teaching/classes/techedu/CONTEXT.md) —
because the answers are read per turma, never pooled.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | The spec format a form is written in, the two grants it authenticates with, and the failure that reads like a permission bug and is not one. |
| [`forms_core.py`](forms_core.py) | [`forms_core.pyi`](forms_core.pyi) | `get_service`, `get_drive`, `edit_url`, `create`, `get_form` | forms_core.py — Google Forms read+write boundary (account-agnostic) for Core/tools/forms/gforms |
| [`forms_spec.py`](forms_spec.py) | [`forms_spec.pyi`](forms_spec.pyi) | `requests` | forms_spec.py — a form written as JSON: compact spec → Forms API batchUpdate requests |
| [`gforms`](gforms) | — | — | Google Forms CLI: auth, new, read, apply, responses |
<!-- routing:end -->
