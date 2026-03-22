# Documentation Standards

## 1) Scope and non-scope

- Every net-new doc must declare what it covers and what it intentionally excludes.
- If content is exploratory or future-facing, mark it as non-shipping guidance.

## 2) Audience and prerequisites

- Every page must name the primary audience (for example: contributor, operator, reviewer).
- Every page must list prerequisites before procedural steps.

## 3) Canonical-source policy

- Each topic has one canonical source file.
- Summary or duplicate pages must link back to the canonical source and avoid drift.
- Update canonical source first, then synchronize derivative pages.

## 4) IA depth and cross-linking

- Keep docs navigation depth to 3 levels or fewer.
- Every page should include at least one inbound or outbound related-doc link.
- Use `check_orphan_docs` to prevent stranded pages.

## 5) Docs-as-code ownership and review

- Treat docs changes like code changes: open PR, request review, and run checks.
- Required checks: `check_language_structure`, `check_docs_links`, and docs build.
- Block merge when docs updates change behavior but omit source-of-truth updates.
