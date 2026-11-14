# Public-readiness audit (P14)

The audit scanned all 403 Git blobs, 101 trees and 14 commits reachable to `git cat-file --batch-all-objects`, plus the current tracked worktree, ignored files and local Git configuration. It checked credential-like filenames, common provider token formats, private-key markers, credential assignments and URLs, environment files, private home paths and local account names. Pattern scanning cannot prove that an arbitrary string is safe.

## Sensitive material

- **Tracked content and Git object history:** no tokens, private keys, `.env` or credential files, or private home paths were detected. The only credential-shaped match is the literal `your-client-secret` in a saved ORNL API example (`data/raw/p13/ornl_ui.html`); it is a placeholder, not a usable secret.
- **Commit metadata:** all existing commits have one personal author/committer identity with a non-noreply email. The identity will be visible if this history is published. History was not rewritten.
- **Ignored local files:** Python bytecode and the installed `.venv` contain local user and absolute path strings. They are not tracked. A third-party `.env` example inside `.venv` and package code containing credential examples are likewise not tracked. Do not add the environment directory to Git.
- **Local Git settings:** no credential-bearing URL or token was found in this repo's `.git/config` or `.git/info/exclude`.

## Size and ignore policy

The working directory occupies approximately 648 MiB on disk, of which `.venv` accounts for 629 MiB. Current tracked files total 12,960,657 bytes (12.96 MB decimal); Git loose objects occupy approximately 5.39 MiB. The largest tracked files are `data/raw/p2_evidence/p2_evidence.json` (1,343,924 bytes), `data/raw/p2_evidence/kenya_power.json` (508,213 bytes), and `data/processed/climate_us_high_plains_b.parquet` (359,821 bytes). No tracked file or historical blob exceeds 10 MB.

**All worktree files over 10 MB (all ignored `.venv` dependencies):**

| File | Bytes |
|---|---:|
| `.venv/lib/python3.14/site-packages/pyarrow/libarrow.2600.dylib` | 39,062,432 |
| `.venv/lib/python3.14/site-packages/pyarrow/libarrow_flight.2600.dylib` | 24,632,984 |
| `.venv/share/jupyter/nbextensions/pydeck/index.js.map` | 19,408,921 |
| `.venv/lib/python3.14/site-packages/pydeck/nbextension/static/index.js.map` | 19,408,921 |
| `.venv/lib/python3.14/site-packages/pyarrow/libarrow_compute.2600.dylib` | 15,615,896 |

`.gitignore` excludes virtual environments, bytecode, test and lint caches, local environment/secrets files, generated `data/cache/` and newly created `data/raw/` files. Previously committed small raw evidence remains tracked for provenance and offline verification. Review and force-add any future raw fixture deliberately. Processed runtime files remain committed; see [portability](portability.md).

## Links and screenshots

The README and `docs/` initially contained 57 relative Markdown links/images; every target existed. All nine committed screenshots opened as valid PNG files. An unauthenticated public GET check of 54 distinct external Markdown URLs returned 2xx for 48. The USDA Soil Data Access endpoint returns 400 to GET but its documented **POST** was verified in [P13's audit](citation_audit.md). The University of Minnesota Extension page returned 403 to this request client, although its indexed text was read and supports the cited table. The USGS legacy decommission notice returned 403, two original KALRO bitstream URLs timed out, and the ORNL live subset example timed out on this check. Those four live links were replaced with literal URLs and, for ORNL, a link to the archived successful response in [API status](api_status.md). The KALRO originals remain documented as historical/unreachable in the [citation audit](citation_audit.md). The current Markdown has 50 distinct external links; 48 returned 2xx, and the two exceptions are the POST-only USDA endpoint and access-restricted Minnesota page. The app and offline tests do not depend on either URL.
