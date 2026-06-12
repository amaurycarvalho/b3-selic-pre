## Context

The current project is a compact Python script that builds a B3 reference-rate request, calls the public B3 endpoint, parses JSON, and prints `day252`, `day360`, and `rate` values to stdout. The UI change should keep the implementation lightweight and local-first, because the repository does not currently define a package structure, dependency manager, frontend build tool, or web framework.

## Goals / Non-Goals

**Goals:**

- Provide a simple browser UI for choosing a reference date and viewing B3 SELIC pré rates.
- Refactor B3 fetching into reusable functions that both CLI and UI code can call.
- Keep the first implementation small enough for the current repository shape.
- Present clear loading, empty, and error states around B3 requests.

**Non-Goals:**

- Deploy a hosted production service.
- Add authentication, persistence, background jobs, or caching.
- Build a complex frontend toolchain.
- Guarantee B3 endpoint availability or validate financial correctness beyond displaying returned data.

## Decisions

- Use Python's standard-library HTTP server for the first UI service. This avoids adding dependencies while the project is still a single-file script. Alternative considered: Flask or FastAPI, which would be more ergonomic but adds packaging and installation decisions that are not yet present.
- Serve a static HTML page with vanilla JavaScript. The UI only needs date input, fetch submission, and table rendering, so React/Vue or a bundler would be unnecessary at this stage. Alternative considered: server-rendered HTML only, but JavaScript provides a cleaner interactive loading/error experience.
- Expose a local JSON endpoint for rate queries. The browser should call the local Python server, and the Python code should perform the B3 request to avoid browser CORS issues and centralize request encoding. Alternative considered: direct browser requests to B3, which is more fragile because remote headers and CORS policy are outside this project.
- Preserve CLI behavior where practical by moving side-effectful top-level code behind a main entry point and reusable functions. This keeps existing command-line usage available while adding a UI entry mode. Alternative considered: replacing the script entirely with a web app, which would be a larger breaking change.
- Validate dates at the local boundary using ISO `YYYY-MM-DD` format before calling B3. This keeps error messages predictable and prevents malformed request payloads. Alternative considered: passing all input to B3 and surfacing remote failures, which would produce less useful local feedback.

## Risks / Trade-offs

- B3 endpoint changes or downtime → Surface fetch failures clearly in the UI and keep request construction isolated for future updates.
- Standard-library server has limited production features → Document the UI as local development/use only, not a hardened public service.
- Vanilla JavaScript can become hard to maintain if the UI grows → Keep the first UI small; revisit framework choices only after requirements expand.
- Refactoring a single script may accidentally alter CLI output → Add or run focused checks for request encoding, response normalization, and CLI formatting during implementation.

## Migration Plan

- Refactor `b3_selic_pre.py` into reusable functions plus a guarded CLI entry point.
- Add local UI serving and API routing without requiring external dependencies.
- Add static UI assets or inline HTML/JS in a structure appropriate for the repository.
- Roll back by removing the UI server path and keeping the reusable fetch function if it remains beneficial.

## Open Questions

- Should the CLI accept a date argument as part of this change, or remain hard-coded until a separate CLI improvement?
- Should rate values be displayed exactly as returned by B3, or normalized/formatted for locale-specific presentation?
