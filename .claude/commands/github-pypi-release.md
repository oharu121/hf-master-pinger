# /github-pypi-release

Create a GitHub issue, run release checks, bump version, and create a GitHub release for Python projects.

This command combines issue documentation with automated release workflow: remote sync, checks (typecheck/lint/test), version bump, build verification, commit, push, and GitHub release creation.

**Requires:** `pyproject.toml` (modern Python project structure)

## Instructions

You have access to the full conversation context. Use it to understand what was implemented.

---

## Phase 1: Issue Creation (Steps 1-9)

### Step 1: Gather Context

From the session, identify:
- What feature/fix was implemented
- Which files were modified
- What the key changes were
- Any breaking changes or deprecations

### Step 2: Ask for Title

Use AskUserQuestion with:
- 3 suggested titles based on the work done (concise, action-oriented)
- "Other" option allows free input

Example titles:
- "Add async support for HTTP client"
- "Fix configuration validation for nested paths"
- "Refactor CLI argument parsing"

### Step 3: Ask for Labels

Use AskUserQuestion with multiSelect=true:
- Options: enhancement, bug, documentation, refactor
- "Other" option allows custom labels (comma-separated)

### Step 4: Ask for Version/Milestone

Read `pyproject.toml` to get current version (detected in Step 11), then use AskUserQuestion:
- patch: v1.0.1
- minor: v1.1.0
- major: v2.0.0
- Skip (no milestone)

Note: Always prefix versions with "v" (e.g., "v1.1.0" not "1.1.0") for milestone names.

**Store the selected version type** (patch/minor/major/skip) for use in Step 15.

### Step 5: Create Plan File

Create `.plans/<slugified-title>.md` with this structure:

```markdown
# Plan: <Title>

**Status:** Completed
**Date:** <YYYY-MM-DD>

## Goal

<Brief description of what was implemented>

## Summary of Changes

<Bullet list of key changes>

## Files Modified

- [file1.py](path/to/file1.py) - <what changed>
- [file2.py](path/to/file2.py) - <what changed>

## Breaking Changes

<List any breaking changes, or "None">

## Deprecations

<List any deprecations, or "None">
```

### Step 6: Update CHANGELOG.md

If CHANGELOG.md exists in the project root:

1. If version was selected:
   - Find or create `## [version]` section
   - Add entry with today's date

2. If version was skipped:
   - Find or create `## [Unreleased]` section
   - Add entry without date

Use appropriate subsections:
- `### Added` - for new features
- `### Changed` - for changes in existing functionality
- `### Deprecated` - for soon-to-be removed features
- `### Fixed` - for bug fixes
- `### Removed` - for removed features

### Step 7: Update README.md (if needed)

Check if implementation affects any documented features:
- Configuration options
- CLI arguments
- API/programmatic usage
- Installation instructions

If so, update the relevant sections to match the implementation.

### Step 8: Create GitHub Issue

#### 8a: Handle Milestone (if version was selected)

If user selected a version (not "Skip"), first check if the milestone exists and create it if needed:

```bash
# Check if milestone exists
gh api repos/{owner}/{repo}/milestones --jq '.[] | select(.title == "<version>") | .title'
```

If the milestone does NOT exist (empty output), create it:

```bash
gh api repos/{owner}/{repo}/milestones -f title="<version>" -f state="open"
```

#### 8b: Create the Issue

Use gh CLI to create the issue:

```bash
gh issue create \
  --title "<title>" \
  --label "<label1>,<label2>" \
  --assignee "@me" \
  --milestone "<version>" \
  --body "<body>"
```

Notes:
- Always include `--assignee "@me"` to assign the issue to the current user
- Omit `--milestone` if user selected "Skip"

Issue body format - Include the FULL plan file content followed by acceptance criteria:

```markdown
<Full content of the plan file from .plans/<filename>.md>

---

## Acceptance Criteria

### AC-1: <First criterion name>

| Criteria | Description |
|----------|-------------|
| Given | <precondition> |
| When | <action> |
| Then | <expected result> |
| Evidence | |

### AC-2: <Second criterion name>

| Criteria | Description |
|----------|-------------|
| Given | <precondition> |
| When | <action> |
| Then | <expected result> |
| Evidence | |

---

Plan file: [.plans/<filename>.md](.plans/<filename>.md)
```

IMPORTANT: The issue body should contain the COMPLETE plan file content (Goal, Summary of Changes, Files Modified, etc.), NOT a summary.

### Step 9: Generate Commit Message

After the issue is created successfully, parse the issue URL to get the issue number, then generate and **store** the commit message:

```
feat(<scope>): <description> (#<issue-number>)
```

Where:
- `<scope>` is the main area changed (e.g., api, cli, core, utils)
- `<description>` is a concise summary in lowercase
- `<issue-number>` is extracted from the created issue URL

For bug fixes, use `fix(<scope>)` instead of `feat(<scope>)`.
For documentation only, use `docs(<scope>)`.
For refactoring, use `refactor(<scope>)`.

Output to the user:
```
Issue created: <full-url>

Proceeding with release automation...
```

---

## Phase 2: Release Automation (Steps 10-19)

### Step 10: Check Remote Status

Check if there are commits on the remote that you don't have locally:

```bash
git fetch
```

```bash
git rev-list --count HEAD..@{u}
```

If the count is greater than 0:

1. Inform the user: "Remote has X commit(s) you don't have locally"

2. Check for uncommitted changes:
   ```bash
   git status --porcelain
   ```

3. If uncommitted changes exist, use AskUserQuestion:
   - "You have uncommitted changes. Commit them before pulling?"
   - Options: Yes (commit with WIP message), No (cancel)

4. If user says Yes, commit changes:
   ```bash
   git add .
   git commit -m "WIP: save changes before pulling remote updates"
   ```

5. Ask user to confirm pull:
   - "Pull latest changes before continuing?"
   - Options: Yes, No (cancel)

6. If user says Yes:
   ```bash
   git pull --rebase
   ```

If pull fails due to conflicts, stop and instruct user to resolve conflicts manually.

### Step 11: Detect Project Configuration and Available Tools

**Step 11a: Verify Python Project Structure**

Check for `pyproject.toml`:

```bash
test -f pyproject.toml && echo "exists" || echo "not found"
```

If `pyproject.toml` does not exist, stop with error:
```
Error: No pyproject.toml found.
This command requires a modern Python project with pyproject.toml.
```

**Step 11b: Read Current Version**

Try multiple methods to extract version:

Method 1 - Standard [project] section (Python 3.11+ tomllib):
```bash
python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null
```

Method 2 - Poetry [tool.poetry] section:
```bash
python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['tool']['poetry']['version'])" 2>/dev/null
```

Method 3 - Regex fallback (works without Python 3.11):
```bash
grep -E '^version\s*=' pyproject.toml | head -1 | sed 's/.*=\s*["'\'']\([^"'\'']*\)["'\''].*/\1/'
```

Store the current version for use in Steps 4 and 15.

**Step 11c: Detect Build Backend**

Read the build backend:

```bash
python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb')).get('build-system', {}).get('build-backend', 'unknown'))" 2>/dev/null
```

Also check for `poetry.lock` to confirm Poetry project:
```bash
test -f poetry.lock && echo "poetry"
```

Determine build command based on backend:

| Build Backend | Build Command |
|--------------|---------------|
| `poetry.core.masonry.api` | `poetry build` |
| `hatchling.build` | `python -m build` |
| `setuptools.build_meta` | `python -m build` |
| `flit_core.buildapi` | `flit build` |
| `pdm.backend` | `pdm build` |
| Other/unknown | `python -m build` |

**Step 11d: Detect Type Checking Tools**

Check for type checker configuration (use first found):

1. **mypy**:
   ```bash
   python -c "import tomllib; 'mypy' in tomllib.load(open('pyproject.toml', 'rb')).get('tool', {}) and print('configured')" 2>/dev/null
   ```
   Also check: `test -f mypy.ini || test -f .mypy.ini`

   Command: `mypy .` (or `mypy src/` if src/ exists)

2. **pyright**:
   ```bash
   python -c "import tomllib; 'pyright' in tomllib.load(open('pyproject.toml', 'rb')).get('tool', {}) and print('configured')" 2>/dev/null
   ```
   Also check: `test -f pyrightconfig.json`

   Command: `pyright`

**Step 11e: Detect Linting Tools**

Check for linting configuration (run ALL that are configured):

1. **ruff**:
   ```bash
   python -c "import tomllib; 'ruff' in tomllib.load(open('pyproject.toml', 'rb')).get('tool', {}) and print('configured')" 2>/dev/null
   ```
   Also check: `test -f ruff.toml`

   Command: `ruff check .`
   Fix suggestion: `ruff check . --fix`

2. **black** (formatting check):
   ```bash
   python -c "import tomllib; 'black' in tomllib.load(open('pyproject.toml', 'rb')).get('tool', {}) and print('configured')" 2>/dev/null
   ```

   Command: `black --check .`
   Fix suggestion: `black .`

3. **pylint**:
   ```bash
   python -c "import tomllib; 'pylint' in tomllib.load(open('pyproject.toml', 'rb')).get('tool', {}) and print('configured')" 2>/dev/null
   ```
   Also check: `test -f .pylintrc || test -f pylintrc`

   Command: `pylint src/` or `pylint <package_name>/`

**Step 11f: Detect Testing Tools**

Check for test configuration (use first found):

1. **pytest**:
   ```bash
   python -c "import tomllib; 'pytest' in tomllib.load(open('pyproject.toml', 'rb')).get('tool', {}) and print('configured')" 2>/dev/null
   ```
   Also check: `test -f pytest.ini || test -f conftest.py`

   Command: `pytest`

2. **unittest** (fallback):
   Check if `tests/` directory exists with test files:
   ```bash
   test -d tests && ls tests/test_*.py 2>/dev/null
   ```

   Command: `python -m unittest discover`

**Step 11g: Detect Version Bump Tool**

Check for version management tools (use first found):

1. **Poetry** (if Poetry project):
   Command: `poetry version <patch|minor|major>`

2. **bump2version**:
   ```bash
   test -f .bumpversion.cfg || test -f .bumpversion.toml
   ```
   Command: `bump2version <patch|minor|major>`

3. **Hatch**:
   If build backend is `hatchling.build`
   Command: `hatch version <patch|minor|major>`

4. **Manual** (fallback):
   Use Python to update version in pyproject.toml + create git tag

**Step 11h: Report Detected Tools**

Inform the user which checks will run:

```
Detected Python project configuration:
- Build backend: <backend> (command: <build-command>)
- Type checker: <mypy|pyright|none>
- Linters: <ruff, black, pylint|none>
- Test runner: <pytest|unittest|none>
- Version management: <poetry|bump2version|hatch|manual>

Will run: typecheck (mypy), lint (ruff, black), test (pytest)
```

If no checks are configured:
```
Warning: No typecheck, lint, or test tools detected in pyproject.toml.
Proceeding with build and release only.
```

### Step 12: Run Checks

Run each available check in order. Stop on first failure.

**Type Check** (if detected):

For mypy:
```bash
mypy . 2>&1
```
Or if `src/` directory exists:
```bash
mypy src/ 2>&1
```

For pyright:
```bash
pyright 2>&1
```

If fails: Stop, show error, output "Fix the type errors and re-run /github-pypi-release"

**Lint** (if detected - run all configured tools):

For ruff:
```bash
ruff check . 2>&1
```
If fails: Stop, show error, output "Fix the lint errors (try: ruff check . --fix) and re-run /github-pypi-release"

For black:
```bash
black --check . 2>&1
```
If fails: Stop, show error, output "Fix the formatting errors (try: black .) and re-run /github-pypi-release"

For pylint:
```bash
pylint src/ 2>&1
```
If fails: Stop, show error, output "Fix the lint errors and re-run /github-pypi-release"

**Test** (if detected):

For pytest:
```bash
pytest 2>&1
```

For unittest:
```bash
python -m unittest discover 2>&1
```

If fails: Stop, show error, output "Fix the failing tests and re-run /github-pypi-release"

If all checks pass (or no checks configured), continue to next step.

### Step 13: Pre-Commit Verification

Verify the working directory state:

```bash
git status --porcelain
```

If there are uncommitted changes (plan file, CHANGELOG, README, etc.), this is expected. Continue.

### Step 14: Show Changes & Commit

Display the changes that will be committed:

```bash
git status --short
```

List the files that were modified (plan file, CHANGELOG, README if updated).

Use AskUserQuestion to confirm:
- "Commit these changes?"
- Show the commit message from Step 9
- Options:
  - "Yes, use this message" (proceed with stored commit message)
  - "No, use custom message" (prompt for custom message)
  - "Cancel" (stop execution)

If Yes or custom message provided:
```bash
git add .
git commit -m "<commit-message>"
```

### Step 15: Bump Version

**If user selected "Skip" in Step 4:**

Use AskUserQuestion:
- "You chose to skip version bump earlier. Confirm skipping version bump and GitHub release?"
- Options:
  - "Yes, skip version & release" (proceed to push without version bump, skip GitHub release)
  - "No, select a version now" (re-prompt for version: patch/minor/major)

**If version type is selected (patch/minor/major):**

Calculate new version from current version stored in Step 11b.

**Poetry projects** (detected via `poetry.lock` or `[tool.poetry]`):
```bash
poetry version <patch|minor|major>
```
Extract new version:
```bash
poetry version --short
```
Then commit and tag:
```bash
git add pyproject.toml
git commit -m "Bump version to <new-version>"
git tag v<new-version>
```

**bump2version projects** (detected via `.bumpversion.cfg` or `.bumpversion.toml`):
```bash
bump2version <patch|minor|major>
```
Note: bump2version automatically commits and creates tag if configured.

Extract new version:
```bash
grep -E '^current_version' .bumpversion.cfg | cut -d'=' -f2 | tr -d ' '
```

**Hatch projects** (if hatch is detected):
```bash
hatch version <patch|minor|major>
```
Extract new version:
```bash
hatch version
```
Then commit and tag:
```bash
git add pyproject.toml
git commit -m "Bump version to <new-version>"
git tag v<new-version>
```

**Manual update** (fallback for all other projects):

Calculate new version:
- For patch: 1.0.0 -> 1.0.1
- For minor: 1.0.0 -> 1.1.0
- For major: 1.0.0 -> 2.0.0

Update pyproject.toml using Python:
```bash
python -c "
import re

with open('pyproject.toml', 'r') as f:
    content = f.read()

# Calculate new version
current = '<current-version>'
parts = current.split('.')
if '<version-type>' == 'patch':
    parts[2] = str(int(parts[2]) + 1)
elif '<version-type>' == 'minor':
    parts[1] = str(int(parts[1]) + 1)
    parts[2] = '0'
elif '<version-type>' == 'major':
    parts[0] = str(int(parts[0]) + 1)
    parts[1] = '0'
    parts[2] = '0'
new_version = '.'.join(parts)

# Update version in [project] section
content = re.sub(
    r'^(version\s*=\s*[\"'\''])([^\"'\'']+)([\"'\''])',
    rf'\g<1>{new_version}\g<3>',
    content,
    flags=re.MULTILINE
)

with open('pyproject.toml', 'w') as f:
    f.write(content)

print(new_version)
"
```

Then commit and tag:
```bash
git add pyproject.toml
git commit -m "Bump version to <new-version>"
git tag v<new-version>
```

Capture the new version and store for Step 18.

If version bump fails (tag exists, permissions, etc.), stop and show error with guidance.

### Step 16: Build Package (Verification)

Run the build command detected in Step 11c to verify the package builds correctly:

**Poetry projects**:
```bash
poetry build
```

**Flit projects**:
```bash
flit build
```

**PDM projects**:
```bash
pdm build
```

**Generic/Setuptools/Hatch projects**:
```bash
python -m build
```

If build fails: Stop, show error, output "Fix the build errors and re-run /github-pypi-release"

Note: Build artifacts are created locally for verification only. The actual PyPI publish happens via CI when the GitHub release is published.

### Step 17: Push to Remote

Use AskUserQuestion:
- "Push commits and tags to remote?"
- Options:
  - "Yes, push now"
  - "No, I'll push manually later"
  - "Cancel"

If Yes:
```bash
git push && git push --tags
```

If push fails, warn user and show manual command:
```
Push failed. Run manually:
  git push && git push --tags
```

If No: Inform user "Remember to push manually: git push && git push --tags"

### Step 18: Create GitHub Release (Draft)

**Skip this step if version was skipped.**

First, check if gh CLI is available and authenticated:

```bash
gh --version
```

```bash
gh auth status
```

If gh is not installed or not authenticated, warn user and provide manual release URL:
```
GitHub CLI not available. Create release manually at:
  https://github.com/<owner>/<repo>/releases/new?tag=v<version>
```

**Create the release:**

Prepare the release body by taking the plan file content and removing the `# Plan: <Title>` header line (keep everything from `**Status:**` onwards).

```bash
gh release create v<version> \
  --title "<version> - <plan-title>" \
  --draft \
  --notes "<plan-content-without-header>"
```

Where:
- `<version>` is the new version (e.g., "1.2.0")
- `<plan-title>` is the title from Step 2
- `<plan-content-without-header>` is the plan file content starting from `**Status:**`

If release creation fails, warn user and provide manual URL.

### Step 19: Output Success

Display final summary:

**If version was bumped:**
```
Release complete!

Issue: <issue-url>
Version: <old-version> -> <new-version>
Tag: v<new-version>
Release (draft): <github-release-url>

The release was created as a draft. When you publish it:
- GitHub Actions will automatically build and publish to PyPI
```

**If version was skipped:**
```
Changes committed and pushed!

Issue: <issue-url>
Commit: <commit-message>

No version bump or GitHub release (skipped as requested).
```

---

## Error Handling Summary

| Scenario | Action |
|----------|--------|
| No pyproject.toml found | Stop: "requires modern Python project with pyproject.toml" |
| Version extraction fails | Stop with guidance to check pyproject.toml format |
| No checks configured | Warn: "No typecheck/lint/test detected" but continue |
| Remote fetch fails | Warn and continue (might be offline) |
| Pull fails (conflicts) | Stop, instruct to resolve conflicts |
| Type check (mypy) fails | Stop, show errors, suggest fixes |
| Type check (pyright) fails | Stop, show errors, suggest fixes |
| Lint (ruff) fails | Stop, show errors, suggest `ruff check . --fix` |
| Lint (black) fails | Stop, show errors, suggest `black .` |
| Lint (pylint) fails | Stop, show errors, suggest fixes |
| Tests fail | Stop, show errors, suggest fixes |
| Build fails | Stop, show error |
| Commit fails | Stop (likely pre-commit hook) |
| Version bump fails | Stop (tag exists? write permissions?) |
| Push fails | Warn, show manual push command |
| gh not installed | Warn, provide manual release URL |
| gh not authenticated | Warn, suggest `gh auth login` |

---

## Example Session

User runs `/github-pypi-release` after implementing a new feature:

1. **Phase 1 - Issue Creation:**
   - Title: "Add async support for HTTP client"
   - Labels: enhancement
   - Version: minor (v1.2.0)
   - Creates `.plans/add-async-support-for-http-client.md`
   - Updates CHANGELOG.md
   - Creates GitHub issue #7
   - Generates commit message: `feat(http): add async support for HTTP client (#7)`

2. **Phase 2 - Release Automation:**
   - Remote check: Up to date
   - Project detection:
     - Build backend: poetry.core.masonry.api (Poetry)
     - Type checker: mypy configured
     - Linters: ruff, black configured
     - Test runner: pytest configured
     - Version management: Poetry
   - Runs mypy... passed
   - Runs ruff check... passed
   - Runs black --check... passed
   - Runs pytest... passed
   - Shows changes, confirms commit
   - Bumps version: poetry version minor (1.1.0 -> 1.2.0)
   - Builds package: poetry build (verification)
   - Pushes to remote
   - Creates draft GitHub release

3. **Final Output:**
   ```
   Release complete!

   Issue: https://github.com/user/repo/issues/7
   Version: 1.1.0 -> 1.2.0
   Tag: v1.2.0
   Release (draft): https://github.com/user/repo/releases/tag/v1.2.0

   The release was created as a draft. When you publish it:
   - GitHub Actions will automatically build and publish to PyPI
   ```
