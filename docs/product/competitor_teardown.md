# Competitor teardown: pharma QMS / eBR software (for positioning BatchGuard-style features)

> Written from public product pages, documentation and reviews as of 2026-09. Treat feature details as claims to verify in a demo;
> nothing here comes from private sources.

## Landscape
| Type | Examples | Strength | Typical weakness customers mention |
|---|---|---|---|
| Enterprise QMS suites | Veeva Vault Quality, MasterControl, Honeywell TrackWise | Breadth (documents, CAPA, training, audits), regulator familiarity | Long implementations, heavy configuration, validation effort per release |
| MES / eBR platforms | Siemens Opcenter, Werum PAS-X, Emerson Syncade | Deep shop-floor integration, recipe control | Cost and complexity; slow for small changes |
| Modern no-code GxP platforms | Leucine and similar newer vendors | Faster rollout, configurable workflows, AI assistance | Must prove validation rigor to conservative QA teams |
| Paper + Excel | Most small/mid sites | Familiar, cheap | Missing entries, illegible records, late reviews: the ALCOA+ problems |

## Where the buying decision is actually made
1. **Will QA trust it?** Audit trail, e-signatures, Part 11 evidence, the vendor's validation package.
2. **How much validation work lands on the customer?** Vendors that ship executed IQ/OQ/PQ evidence per release win.
3. **Time to first batch** on the new system.
4. **Review-by-exception:** does QA only look at what went wrong (deviations, OOS) instead of every page?

## Implications for product (what BatchGuard demonstrates)
| Buyer concern | BatchGuard answer |
|---|---|
| Validation burden | Traceability matrix and executed IQ/OQ/PQ generated per release in minutes |
| Review by exception | Release blockers list only what needs QA attention; ALCOA+ report summarises the rest |
| Data integrity | Hash-chained audit trail that shows tampering; corrections never overwrite |
| Spec quality | SpecCheck stops untestable requirements before development |

## Open questions to research next
Pricing models (per site vs per user); how competitors handle validation of AI-assisted features; which ones offer customer-facing validation accelerators.
