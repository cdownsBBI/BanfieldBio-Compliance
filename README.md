# BanfieldBio-Compliance

Public compliance documentation library for the Outbound Research Shipping
(ORS) tool. When a research shipment leaves BanfieldBio, the box carries a
QR code. Scanning that QR lands the receiving lab on a per-shipment PDF
hosted here, with links to every safety / regulatory document for the items
in that shipment — manufacturer SDSs, EPA labels, DOT paperwork, and (when
applicable) lot certificates.

## What this repo is, and isn't

This repository exists to make safety and regulatory information available
at the point of delivery. SDS documents are mandated-to-be-accessible
references under OSHA HCS and equivalent international rules; EPA labels
ride along with regulated products; DOT paperwork accompanies hazmat
shipments. Documents hosted here are either:

1. **Mirrored copies** of manufacturer-provided documents (SDS PDFs in
   `docs/sds/`, EPA labels in `docs/epa/`, etc.), served via GitHub Pages.
   Each mirrored PDF is credited to its original manufacturer in
   `data/index.json` and should be refreshed when the manufacturer
   publishes a newer version.
2. **Outbound links** to the manufacturer's own hosted document, used when
   we do not mirror a local copy.

This is not a commercial document clearinghouse and makes no warranty about
currency or completeness of the safety information. Receiving labs should
always confirm the document matches the label on the container they received.

## How it fits with the ORS tool

```
 [ORS private tool]                         [This public repo]
  intake.xlsx                                data/index.json
      |                                          ^
      v                                          |
  process --> pack list PDF (in box) --> QR --+  |
                                              |  |
                                              +-> https://cdownsBBI.github.io/BanfieldBio-Compliance/shipment/<uuid>.pdf
                                                 |
  publish ---------------------------------------+
          writes per-shipment PDF here, keyed by opaque UUID token.
          The token <-> shipment-number mapping stays in the private ORS DB.
```

The ORS tool handles everything private (inventory, recipients, the
shipment database, the sequential `S20260512-001` shipment number). This
repo holds only:

- the document PDFs we've mirrored (`docs/sds/`, future `docs/epa/`, etc.)
- the index of which Inv# maps to which PDF / manufacturer link
- per-item HTML landing pages (one folder per Inv#) used as the
  SDS-link indirection layer — when a manufacturer URL changes, we update
  one entry in `data/index.json`, redeploy Pages, and every previously-
  shipped PDF still resolves correctly via the per-item page redirect
- per-shipment PDFs at opaque UUID-token paths
- the small Python library that constructs URLs and renders the per-item
  HTML pages and per-shipment PDFs

No recipient addresses, no project/grant numbers, no internal SKUs beyond
the Inv# already stamped on every lab container, no sequential shipment
numbers in any URL.

## Layout

```
BanfieldBio-Compliance/
├── config.toml                 # github_user + repo_name + custom_domain
├── data/
│   └── index.json              # Inv# → {mirror_path?, source_url?, cas, mfr, ...}
├── docs/                       # GitHub Pages source (Pages serves from /docs)
│   ├── index.html              # library home
│   ├── sds/                    # mirrored SDS PDFs (C1174.pdf, ...)
│   ├── epa/                    # mirrored EPA labels (future)
│   ├── item/                   # per-item landing pages (generated)
│   ├── shipment/               # per-shipment PDFs (generated, opaque names)
│   ├── robots.txt              # blocks /shipment/ from search-engine indexing
│   └── assets/style.css
├── scripts/
│   └── build_index.py          # rebuild data/index.json from docs/sds/
├── src/banfieldbio_compliance/ # Python package
│   ├── config.py
│   ├── index.py
│   ├── urls.py
│   ├── qr.py
│   └── landing.py
└── tests/
```

## Setup (first time)

1. Repo lives at https://github.com/cdownsBBI/BanfieldBio-Compliance
2. Clone it locally.
3. In the repo's **Settings → Pages**, set the source to branch `main`,
   folder `/docs`. First deploy takes a minute or two.
4. Install the package for local work: `pip install -e .[dev]`
5. From the ORS private tool, set `[sds].repo_path` in `ors_config.toml` to
   the local clone path so `ors process <intake>` writes new shipment PDFs
   into this checkout's `docs/shipment/` folder.

## Adding an SDS

Two ways:

**Mirror a local copy.** Drop the manufacturer's PDF into `docs/sds/` with
filename matching the Inv#, e.g., `docs/sds/C1174.pdf`. Then run:

```
python scripts/build_index.py
```

This rescans `docs/sds/` and updates `data/index.json` with the new entry.
Edit the entry by hand afterward to fill in `cas_num`, `manufacturer`,
`source_url`, and `sds_version`.

**Link out only.** Add an entry to `data/index.json` manually with
`source_url` set and `mirror_path` omitted. The library will resolve to the
manufacturer's URL at QR-scan time. Use this when a chemical's SDS is big,
volatile, or legally safer to link.

## URL scheme

- Library home: `/BanfieldBio-Compliance/`
- Per-item page (info + SDS link): `/BanfieldBio-Compliance/item/<Inv#>/`
- Per-shipment PDF: `/BanfieldBio-Compliance/shipment/<uuid>.pdf`
- Mirrored SDS PDF: `/BanfieldBio-Compliance/sds/<Inv#>.pdf`

Once a custom domain is configured (planned: `compliance.banfieldbio.com`),
these path shapes stay the same under the new root. Do not change path
shape — already-printed QR codes depend on it.

## Privacy posture

`/shipment/` URLs use unguessable UUID4 tokens, are blocked from
search-engine indexing via `robots.txt`, and are intended to be discovered
only by the receiving lab via the QR code on their delivered box. There
is no sequential or enumerable shipment URL surface. Recipient identity,
project, grant, and internal storage location never appear on any public
artifact.

## License

Code: Proprietary — Copyright Chris Downs. All rights reserved. See
`LICENSE` for the full text. Public viewability of this repository does
not constitute a grant of license to copy, modify, or redistribute the
source code.

PDFs: each mirrored document remains the copyright of its original
manufacturer and is hosted here for compliance-reference purposes only.
Attribution is preserved in `data/index.json`.
