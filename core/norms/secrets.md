---
name: secrets
description: A credential or someone else's personal data never enters a versioned file; it lives in a gitignored segredos.env and the text carries the label.
---

**SECRETS STAY OUT OF GIT**: passwords, tokens, CPF/CNPJ go in a gitignored
`<subtree>/segredos.env`; the text keeps the label.
