# /create-issue

Create a GitHub issue to document completed implementation work from the current session.

## Instructions

You have access to the full conversation context. Use it to understand what was implemented.

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
- "Add typecheck, lint, deploy commands"
- "Fix config loading for nested paths"
- "Refactor step execution flow"

### Step 3: Ask for Labels

Use AskUserQuestion with multiSelect=true:
- Options: enhancement, bug, documentation, refactor
- "Other" option allows custom labels (comma-separated)

### Step 4: Ask for Version/Milestone

Read package.json to get current version (e.g., "1.0.0"), then use AskUserQuestion:
- patch: v1.0.1
- minor: v1.1.0
- major: v2.0.0
- Skip (no milestone)

Note: Always prefix versions with "v" (e.g., "v1.1.0" not "1.1.0") for milestone names.

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

- [file1.ts](path/to/file1.ts) - <what changed>
- [file2.ts](path/to/file2.ts) - <what changed>

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
- Configuration options (commands, steps, git, github sections)
- CLI flags (--skip-*, --dry-run, etc.)
- API/programmatic usage
- Workflow steps

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

IMPORTANT: The issue body should contain the COMPLETE plan file content (Goal, Summary of Changes, Execution Flow, Files Modified, etc.), NOT a summary. This ensures the issue serves as full documentation of what was implemented.

### Step 9: Output Commit Message

After the issue is created successfully, parse the issue URL to get the issue number, then output:

```
Issue created: <full-url>

Suggested commit message:
feat(<scope>): <description> (#<issue-number>)
```

Where:
- `<scope>` is the main area changed (e.g., commands, config, cli, steps)
- `<description>` is a concise summary in lowercase
- `<issue-number>` is extracted from the created issue URL

For bug fixes, use `fix(<scope>)` instead of `feat(<scope>)`.
For documentation only, use `docs(<scope>)`.
For refactoring, use `refactor(<scope>)`.

## Example Session

User runs `/create-issue` after implementing typecheck, lint, deploy commands:

1. **Title prompt** shows:
   - "Add typecheck, lint, deploy commands" (Recommended)
   - "Extend command configuration options"
   - "Add pre-release check commands"

2. **Labels prompt** shows: enhancement, bug, documentation, refactor (multi-select)

3. **Version prompt** shows: v1.0.1 (patch), v1.1.0 (minor), v2.0.0 (major), Skip

4. Creates `.plans/add-typecheck-lint-deploy-commands.md`

5. Updates CHANGELOG.md under selected version

6. Updates README.md config examples and CLI options

7. Creates GitHub issue with acceptance criteria

8. Outputs:
   ```
   Issue created: https://github.com/user/repo/issues/5

   Suggested commit message:
   feat(commands): add typecheck, lint, deploy commands (#5)
   ```
