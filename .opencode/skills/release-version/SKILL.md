---
name: release-version
description: Update the application release version across all version files and regenerate the changelog. Use when the user wants to set a new release version.
license: MIT
metadata:
  author: amaurycarvalho
  version: "1.0"
---

Update the application release version across the codebase and regenerate all changelog-related files.

**Input**: Version string (e.g., `1.0.1`). Must be provided by the user in the command or message. If omitted, show an error message and STOP.

**Steps**

1. **Extract the version**

   Parse the version string from the user's message or command. The version should match the pattern `X.Y.Z` (three numeric segments separated by dots). Examples: `1.0.1`, `2.0.0`.

   **If no version is provided** (the user did not include a version string in their message):
   - Display the following error message and STOP:
     ```
     ERROR: No version provided.
     Usage: /release-version <version>
     Example: /release-version 1.0.1
     ```
   - Do NOT proceed with any of the steps below.

2. **Update app_version and release date in **init**.py**

   Read `src/b3_selic_pre/__init__.py` and find the lines containing `__version__ =` and `__release_date__ =`.

   Replace the version value with the new version string and the release date with the current date in ISO format (`YYYY-MM-DD`):

   ```
   __version__ = "<new-version>"
   __release_date__ = "<current-date>"
   ```

   Obtain the current date from the system (for example, `date +%F`); do not guess it.

3. **Update b3-selic-pre.spec**

3.1. Read `b3-selic-pre.spec` and find the `'CFBundleShortVersionString':` field.

Replace the current version:

```
'CFBundleShortVersionString': '<new-version>',
```

3.2. Read `b3-selic-pre.spec` and find the `'CFBundleVersion':` field.

Replace the current version:

```
'CFBundleVersion': '<new-version>',
```

4. **Update version in pyproject.toml**

   Read `pyproject.toml` and find the line containing `version = `.

   Replace the current value with the new version string:

   ```
   version = "<new-version>"
   ```

5. **Update the editable package metadata**

   The project is installed in editable mode. After changing the version in `pyproject.toml`, refresh the package metadata in the virtualenv so `pip show b3-selic-pre` reflects the new version and the declared dependencies.

   Use the project's virtualenv Python:

   Linux/macOS:
   ```
   .venv/bin/python3 -m pip install -e .
   ```

   Windows:
   ```
   .venv\Scripts\python.exe -m pip install -e .
   ```

   If the project does not have `.venv`, use `python3 -m pip install -e .` (or `python -m pip install -e .` on Windows).

   Verify with:

   ```
   .venv/bin/python3 -m pip show b3-selic-pre
   ```

   The output must contain `Version: <new-version>`.

6. **Verify consistency**

   Read back the modified files and confirm:
   - `src/b3_selic_pre/__init__.py` has `__version__ = "<new-version>"`
   - `src/b3_selic_pre/__init__.py` has `__release_date__` set to the current date in `YYYY-MM-DD`
   - `b3-selic-pre.spec` has the correct `'CFBundleShortVersionString':` and `'CFBundleVersion':` fields
   - `pyproject.toml` has `version = "<new-version>"`
   - `pip show b3-selic-pre` reports `Version: <new-version>`

**Output On Success**

```
Release version updated to <version>

Files updated:
- src/b3_selic_pre/__init__.py (__version__, __release_date__)
- b3-selic-pre.spec
- pyproject.toml
- editable package metadata (pip show b3-selic-pre)

Commentary: changelog skill can now be used manually to update the changelog files.
```

**Output On Error**

```
ERROR: No version provided.
Usage: /release-version <version>
Example: /release-version 1.0.1
```

**Guardrails**

- Always validate that a version string was provided before making any changes
- Do NOT guess or auto-generate a version — the user must supply it explicitly
- The version format should follow `X.Y.Z` (e.g., `1.0.1`)
- Always refresh the editable package metadata after changing `pyproject.toml`; do not consider the release complete until `pip show b3-selic-pre` reports the new version
