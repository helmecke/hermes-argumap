---
name: argumap-review
description: Use when creating a durable, snapshot-bound review of a claim.
---

Create a case, add only supported typed nodes and same-case relations, then call
`analyze_case` or `create_verdict`. Report the returned case, graph version, and
snapshot identifiers. Do not bypass snapshot creation or edit curated sources.
