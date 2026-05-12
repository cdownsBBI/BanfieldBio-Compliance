# Security policy

## What this repo contains

This repository hosts publicly-viewable compliance documents for BanfieldBio
research shipments — manufacturer SDSs, EPA labels, DOT shipping paperwork,
per-shipment landing PDFs — and a small Python library that constructs URLs
and renders the per-item HTML pages and QR codes that link to them.

It does **not** host:

- Recipient names, addresses, phone numbers, or email addresses.
- Project, grant, or accounting metadata.
- Lab inventory counts, physical storage locations, or internal pricing.
- Sequential shipment numbers in URLs (per-shipment PDFs use opaque UUID
  tokens so URLs are unguessable from the outside).
- Credentials, API keys, or any authentication material.

The private ORS tool (separate repo) holds all of that.

## Reporting a vulnerability

If you find a security issue in the code or discover that a commit has
accidentally leaked data that should not be public, please open a private
security advisory via GitHub
(`Security` tab → `Report a vulnerability`) rather than a public issue.
We'll acknowledge within a few business days.

## Accidental data in git history

Because this repo is public, the commit history is permanently visible
even after a file is removed. If a PDF or metadata entry that should not
be public has been committed, report it via the security advisory route
above and expect a `git filter-repo` rewrite followed by a force-push —
downstream clones will need to be re-cloned.

## Third-party PDFs

Mirrored SDS documents retain the copyright of their original
manufacturers. The repo is a safety-information reference, not a
redistribution clearinghouse. Manufacturers or rights holders who want a
mirrored SDS removed can open a public issue or use the security advisory
route, and it will come down.
