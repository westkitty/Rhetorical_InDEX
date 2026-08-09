# Donor ledger

| Capability | Source | Disposition | Current destination | Reason |
|---|---|---|---|---|
| Product constitution and phased roadmap | GitHub implementation plan | Govern | existing root plan | Strongest normative source |
| Lens interaction model | GitHub standalone prototype | Reimplemented under parity gate | `apps/web` | Strong runtime QA and interaction maturity |
| Tablet pointer lifecycle | GitHub standalone prototype | Reimplemented | `apps/web/src/app.ts` | Preserves capture/cancel/bounds behavior |
| Reduced Motion / Pattern Mode | GitHub standalone prototype | Reimplemented | web source/CSS | Accessibility behavior already validated conceptually |
| Finding/domain model | Experimental component app | Adapted | `packages/schema` | Useful typed structure; singular mechanism rule retained |
| Alpha-0 taxonomy | Experimental component app | Adapted | `packages/taxonomy` | Detailed definitions, criteria, exclusions, rubrics, neighbors |
| Synthetic SB-802 fixture | Experimental component app | Adapted | `packages/fixtures` | Useful claim/evidence/omission demonstration; reserved URLs retained |
| Framing Switcher | Experimental component app | Reimplemented conceptually | Compare view | Same claim, exact source wording remains core interaction |
| Event Record | Both | Reimplemented | Event view | Forensic ledger rather than synthesized neutral article |
| URL fetcher / SSRF code | Experimental component app | Rejected for Alpha | none | Premature and previously unsafe |
| Express/Gemini server | Experimental component app | Rejected for Alpha | none | Does not match canonical backend architecture or current milestone |
| Detector validation lessons | Experimental audits | Retained as guards | `services/api/detector_contract.py` | Strict enums, criteria, exact spans, occurrence disambiguation |
