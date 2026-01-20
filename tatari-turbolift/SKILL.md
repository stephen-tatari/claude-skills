---
name: tatari-turbolift
description: Automate bulk code changes across multiple GitHub repositories using turbolift for campaign management, slam for batch PR review/merge, and gh CLI. Use when making identical or similar changes to many repositories, running bulk refactoring campaigns, or automating mass updates. (project, gitignored)
allowed-tools:
  - Bash(turbolift:*)
  - Bash(slam:*)
  - Bash(gh:*)
  - Bash(rg:*)
---

# Turbolift Campaign Management Skill

This skill guides you through automating bulk code changes across multiple GitHub repositories using `turbolift`, `slam`, and `gh` CLI tools.

## When to Use This Skill

Use this workflow when you need to:

- **Make identical changes across many repositories** (10+ repos)
- **Run organization-wide refactoring campaigns** (e.g., update dependencies, change CI/CD configurations)
- **Bulk update workflow files** (e.g., GitHub Actions, security policies)
- **Migrate settings or configurations** across a repository fleet
- **Apply security patches** to multiple codebases

**DO NOT use for:**

- Single repository changes (use standard git workflow)
- Changes requiring significant per-repo customization
- Exploratory refactoring where the exact changes aren't known upfront

## Tools Overview

### turbolift

**What it is:** Open-source campaign management tool for bulk repository operations by Skyscanner

**Features:**

- Clones multiple repos in a workspace
- Applies changes uniformly via foreach
- Creates PRs across all repos
- Tracks campaign progress

**Documentation & Download:**

- GitHub: <https://github.com/Skyscanner/turbolift>
- Releases: <https://github.com/Skyscanner/turbolift/releases>

**Installation:**

```bash
# macOS (Homebrew)
brew install skyscanner/tap/turbolift

# Or download binary from releases page
# Place in ~/bin/ or /usr/local/bin/

# Verify installation
turbolift --version
```

**Configuration:**

Requires GitHub authentication (uses gh CLI under the hood)

### slam

**What it is:** HPA (Horizontal PR Autoscaler) - batch PR management tool

**Features:**

- Reviews PRs across multiple repos by change ID
- Approves and merges PRs in bulk
- Validates CI status before merging
- Cleans up branches automatically

**Documentation & Download:**

- GitHub: <https://github.com/scottidler/slam>
- Releases: <https://github.com/scottidler/slam/releases>

**Installation:**

```bash
# Install via Rust cargo
cargo install --git https://github.com/scottidler/slam

# Or download binary from releases page
# Place in ~/bin/ or /usr/local/bin/

# Verify installation
slam --version
```

**Configuration:**

- Requires GitHub authentication (uses gh CLI)
- Logs written to: `~/.local/share/slam/slam.log`
- Default organization: `tatari-tv` (configurable with `--org` flag)

**Note:** If slam is not available or you prefer not to use it, see "Alternative: Without slam" section below for gh CLI-only workflows

### gh

**What it is:** Official GitHub CLI for repository operations

**Features:**

- Searches for PRs across organization
- Manages PR states (draft → ready)
- Checks workflow runs and releases
- Validates tags and deployments

**Documentation & Download:**

- Website: <https://cli.github.com/>
- GitHub: <https://github.com/cli/cli>
- Docs: <https://cli.github.com/manual/>

**Installation:**

```bash
# macOS
brew install gh

# Linux
# See: <https://github.com/cli/cli/blob/trunk/docs/install_linux.md>

# Windows
# See: <https://github.com/cli/cli#windows>

# Verify installation
gh --version
```

**Configuration:**

```bash
# Authenticate with GitHub
gh auth login

# Verify authentication
gh auth status
```

## Documentation Structure

This skill includes:

- **SKILL.md** (this file): Complete workflow guide and best practices
- **REFERENCE.md**: Detailed command reference with real examples
- **FUTURE_ENHANCEMENTS.md**: Optional templates and scripts to add

Refer to **REFERENCE.md** for detailed command syntax and real-world usage examples.

## Complete Workflow

### Phase 0: Planning & Preparation

#### 1. Define the Scope

Create a campaign directory and planning documents:

```bash
mkdir SRE-XXXX-campaign-name
cd SRE-XXXX-campaign-name
```

Create an `EXECUTION_PLAN.md` documenting:

- **Objective**: What changes will be made and why
- **Scope**: How many repos, what types
- **Changes**: Detailed description of transformations
- **Safety checks**: How to verify correctness
- **Rollout phases**: Test → small batch → larger batches
- **Rollback plan**: How to undo if things go wrong

#### 2. Identify Target Repositories

Use GitHub CLI to find repositories:

```bash
# Example: Find repos with specific workflow files
gh search repos 'org:tatari-tv' --json name,owner | jq -r '.[] | "\(.owner.login)/\(.name)"' > repos-candidates.txt

# Or search for specific file content
gh api search/code -X GET \
  -f q='org:tatari-tv path:.github/workflows filename:ci.yaml' \
  --jq '.items[].repository.full_name' | sort -u > repos-candidates.txt
```

Create `repos-all.txt` with final list (format: `org/repo`):

```text
tatari-tv/repo-name-1
tatari-tv/repo-name-2
tatari-tv/repo-name-3
```

#### 3. Create Transformation Script

Write a Python script (or bash script) that makes the changes. Key principles:

**Script Structure:**

```python
#!/usr/bin/env python3
"""
Brief description of what this script does.

Safety checks:
- List any validation performed before making changes
- List any conditions that cause the script to skip/error
"""

import sys
from pathlib import Path

def validate_prerequisites(repo_path: Path) -> bool:
    """Verify repo has necessary files/configs before making changes."""
    # Check that required files exist
    # Verify safety conditions
    return True

def make_changes(repo_path: Path) -> bool:
    """Apply the transformation to the repository."""
    # Implement the actual changes
    # Return True if changes made, False if skipped
    pass

def main():
    repo_path = Path.cwd()

    if not validate_prerequisites(repo_path):
        print(f"ERROR: Prerequisites not met", file=sys.stderr)
        sys.exit(1)

    if make_changes(repo_path):
        print(f"✅ Changes applied")
    else:
        print(f"⏭️  No changes needed")

if __name__ == "__main__":
    main()
```

**Best Practices:**

- **Test-driven**: Write tests for your transformation script first (pytest recommended)
- **Validation**: Always verify prerequisites exist before making changes
- **Idempotent**: Script should be safe to run multiple times
- **Error handling**: Exit with non-zero code on errors
- **Preserve formatting**: Use text-based editing when possible to preserve whitespace/comments
- **Safety first**: When in doubt, skip the repo rather than make incorrect changes

#### 4. Test the Script Locally

Before running turbolift campaign:

```bash
# Clone a test repo manually
git clone git@github.com:org/test-repo.git
cd test-repo

# Run your script
python3 ../transformation-script.py

# Review changes
git diff

# Verify correctness
# Run tests if applicable
```

### Phase 1: Test Campaign (2-5 repos)

Initialize the main turbolift campaign with test repositories:

```bash
cd SRE-XXXX-campaign-name

# Create test repos list (start with 2-5 repos)
head -n 2 repos-all.txt > repos.txt

# Initialize the main campaign (this will be reused for all batches)
turbolift init --name "SRE-XXXX-campaign-name"
cd SRE-XXXX-campaign-name

# Copy transformation script
cp ../transformation-script.py .
```

**Run the test campaign:**

```bash
# 1. Clone repositories
turbolift clone

# 2. Apply transformation
turbolift foreach -- python3 ../transformation-script.py

# 3. Review changes in all repos
turbolift foreach -- git status
turbolift foreach -- git diff

# 4. Manually inspect specific repos
cd work/org/repo-name
git diff
# Review specific files
less .github/workflows/ci.yaml
cd ../../..

# 5. If changes look good, commit
turbolift commit -m "Brief commit title

- Detail about change 1
- Detail about change 2
- Mention safety checks performed

Part of SRE-XXXX"

# 6. Create DRAFT pull requests
turbolift create-prs --draft

# 7. Check PR status
turbolift pr-status
```

#### Manual Validation Required

Before proceeding:

- [ ] Review all draft PRs in GitHub web UI
- [ ] Verify CI passes on all test PRs
- [ ] Check that changes are exactly as intended
- [ ] Validate that no unintended side effects occurred
- [ ] Test in at least one repo manually if applicable

If any issues found:

1. Delete draft PRs
2. Fix the transformation script
3. Reset repos: `turbolift foreach -- git reset --hard HEAD~1`
4. Re-run from step 2

#### Automated CI Monitoring

**Wait for CI to complete** before marking PRs ready:

```bash
# Check CI status for all PRs in campaign
turbolift pr-status

# Use gh to check detailed status for each PR
gh search prs 'org:tatari-tv SRE-XXXX is:draft is:open' \
  --json number,title,repository,statusCheckRollup \
  --jq '.[] | "\(.repository.name): \(.statusCheckRollup[0].state)"'
```

**Monitor CI progress:**

```bash
# Watch a specific PR's CI runs
gh pr checks <PR_NUMBER> --repo org/repo --watch

# Check recent workflow runs across repos
for repo in $(cat repos.txt); do
  echo "=== $repo ==="
  gh run list --repo $repo --limit 1 \
    --json status,conclusion,workflowName,createdAt
done
```

**If CI fails, retrieve logs:**

```bash
# Find the failed run ID
gh run list --repo org/repo --limit 5

# View the logs for failed run
gh run view <RUN_ID> --repo org/repo --log

# Download logs to file for analysis
gh run view <RUN_ID> --repo org/repo --log > ci-failure.log
```

**Fix failures and update PRs:**

```bash
# Navigate to the repo with failures
cd work/org/repo

# Make fixes
# ... edit files ...

# Commit and push updates
git add -A
git commit -m "Fix: address CI failure"
git push

# Verify CI passes
gh pr checks --watch
```

**Only proceed when all CI checks pass** across all draft PRs.

---

**⚠️ STOP: Verify CI Status Before Continuing**

Before proceeding to the next phase:

1. ✅ **Confirm all CI checks have passed** on all draft PRs
2. ✅ **Review any CI failures** and verify fixes are working
3. ✅ **Manually test changes** if applicable
4. ✅ **Review draft PRs** in GitHub UI one final time

**DO NOT proceed to Phase 2 until:**
- All draft PRs show green checkmarks (CI passing)
- You have reviewed and validated the changes
- You are confident the changes are correct

Once ready, you can proceed to Phase 2 to add more repositories to the campaign.

### Phase 2: Small Batch (5-10 repos)

After test campaign succeeds, add more repos to the existing campaign:

```bash
cd ..  # Back to parent directory
cd SRE-XXXX-campaign-name  # Enter the main campaign directory

# Replace repos.txt with the next batch
sed -n '3,10p' ../repos-all.txt > repos.txt

# Clone the newly added repos (turbolift skips already-cloned repos)
turbolift clone

# Run the campaign on the new repos (same steps as Phase 1)
turbolift foreach -- python3 ../transformation-script.py
turbolift foreach -- git diff
turbolift commit -m "Your commit message..."
```

#### Review and Validate

### Phase 3: Batch Processing (groups of 20-30)

Process remaining repos in manageable batches by continuing to append to the existing campaign:

```bash
cd /path/to/SRE-XXXX-campaign-name/SRE-XXXX-campaign-name

# Batch 2 (repos 11-30)
sed -n '11,30p' ../repos-all.txt > repos.txt

turbolift clone
turbolift foreach -- python3 ../transformation-script.py
turbolift foreach -- git diff
turbolift commit -m "..."
turbolift create-prs --draft

# Repeat for subsequent batches by replacing repos.txt:
# sed -n '31,50p' ../repos-all.txt > repos.txt
# turbolift clone
# ... (repeat the same steps)
```

### Phase 4: Batch PR Review & Merge with slam

After creating draft PRs, use `slam` for bulk operations:

#### Step 1: Discover All Draft PRs

```bash
# Find all draft PRs matching your ticket number
gh search prs 'org:tatari-tv SRE-XXXX is:draft is:open' --json number,title,repository
```

---

**⚠️ STOP: Review Draft PRs Before Marking Ready**

Before marking PRs ready for review, complete these validations:

1. ✅ **Review all draft PRs in GitHub UI** - verify changes are correct
2. ✅ **Confirm CI passes on all draft PRs** - no failing checks
3. ✅ **Verify changes match intent** - no unexpected modifications
4. ✅ **Complete manual testing** if applicable to the change type

**DO NOT proceed to Step 2 until:**
- You have opened and reviewed each draft PR in the GitHub web interface
- All CI/CD checks show green (passing)
- You are confident the changes are ready for reviewers to see

This is a manual gate - explicitly confirm you want to proceed before marking PRs ready for review.

---

#### Step 2: Mark PRs Ready for Review

##### For repos in current turbolift campaign

```bash
cd SRE-XXXX-batch-X
turbolift foreach -- gh pr ready
```

##### For repos outside current campaign

```bash
gh pr ready <PR_NUMBER> --repo org/repo-name
```

#### Step 3: Review Changes with slam

```bash
# List all PRs by change ID pattern
slam review ls 'SRE-XXXX'
```

This shows:

- All matching PRs across repos
- Diff of changes for each repo
- Files modified

Verify:

- Changes match intent
- No unexpected modifications
- Formatting preserved

#### Step 4: Batch Approve and Merge

##### Single command to approve and merge all PRs

```bash
# Extract the PR title from the campaign's README.md header
PR_TITLE=$(head -n 1 README.md | sed 's/^# //')
slam review approve "$PR_TITLE"
```

slam automatically:

- Validates each PR (CI passed, not draft, mergeable)
- Approves the PR
- Merges with squash
- Deletes the branch
- Reports success/failure for each

**Monitor the output** - if any PRs fail:

- Review the error message
- Handle failed PRs manually
- Common issues: merge conflicts, CI failures, stale state

#### Step 5: Monitor Main Branch CI After Merge

After slam merges PRs, **actively monitor CI on main branch**:

```bash
# Wait for CI to trigger on main branch (give it a moment)
sleep 10

# Monitor CI status for all merged repos
for repo in $(cat repos.txt); do
  echo "=== $repo ==="

  # Get latest main branch CI run
  gh run list --repo $repo --branch main --limit 1 \
    --json status,conclusion,workflowName,createdAt,databaseId
done
```

**Watch CI runs to completion:**

```bash
# Watch a specific repo's main branch CI
gh run watch --repo org/repo

# Or check all repos periodically
for repo in $(cat repos.txt); do
  echo "=== $repo ==="
  run_id=$(gh run list --repo $repo --branch main --limit 1 --json databaseId --jq '.[0].databaseId')
  gh run view $run_id --repo $repo --json status,conclusion,workflowName \
    --jq '"Status: \(.status) | Conclusion: \(.conclusion) | Workflow: \(.workflowName)"'
done
```

**If CI fails on main branch, retrieve logs:**

```bash
# Find the failed run
gh run list --repo org/repo --branch main --limit 5

# View failure logs
gh run view <RUN_ID> --repo org/repo --log

# Investigate and create hotfix PR if needed
cd work/org/repo
git checkout main
git pull
git checkout -b hotfix-sre-xxxx
# Make fixes
git add -A
git commit -m "Hotfix: resolve main branch CI failure"
git push origin hotfix-sre-xxxx
gh pr create --title "Hotfix: SRE-XXXX CI failure" --body "Fixes CI failure on main"
```

**Verify all repos:**

- ✅ Latest CI run on main branch is complete
- ✅ Conclusion is "success" for all repos
- ✅ No merge-related failures
- ✅ Changes are deployed/published as expected

**DO NOT consider campaign complete until:**
- All main branch CI checks pass
- Any failures have been investigated and resolved
- Production deployments (if applicable) have completed successfully

### Phase 5: Post-Merge Tasks (if applicable)

Some campaigns require follow-up actions after merging:

#### Example: Manual Tagging for Releases

If repos need releases but don't have automated versioning:

```bash
# For each repo requiring a tag
cd /tmp
git clone git@github.com:org/repo.git
cd repo

# Pull latest main with merge
git pull origin main

# Get next version (requires nextver.sh or similar)
version=$(nextver.sh)

# Validate version format
echo "Proposed tag: $version"
# Check against existing releases
gh release list --limit 3

# If correct format, create and push tag
git tag -a -m "${version}" "${version}"
git push origin "refs/tags/${version}"

# Monitor release workflow
gh run watch
```

#### Example: Verification Scripts

Run verification across all modified repos:

```bash
# Script to verify changes are working
for repo in $(cat repos-all.txt); do
  echo "=== $repo ==="
  # Check specific conditions
  # Example: verify file was removed
  if gh api repos/$repo/contents/.github/workflows/old-workflow.yaml 2>&1 | grep -q "Not Found"; then
    echo "✅ File removed"
  else
    echo "❌ File still exists"
  fi
done
```

## Progress Tracking

Create and maintain a `PROGRESS.md` file:

```text
# Campaign Progress

## Status: Phase X - Y/Z repos complete (N%)

**Completed:**
- Phase 1: X repos (merged & validated)
- Phase 2: Y repos (merged)

**Remaining:** Z repos

## Issues Encountered
- Issue 1: Description and resolution
- Issue 2: Description and resolution

## Next Steps
1. Next batch or phase
2. Any follow-up items
```

Update after each phase completion.

## Best Practices & Lessons Learned

### Change Script Development

1. **Write tests first** - Use pytest to test transformation logic

   ```bash
   pytest test_transformation.py -v
   ```

2. **Handle edge cases gracefully**

   - Missing files → skip with message
   - Already transformed → detect and skip
   - Invalid format → error and skip

3. **Preserve formatting**

   - Use text-based replacements when possible
   - Avoid parsing/serializing YAML (loses comments/formatting)
   - Test with `git diff` to verify formatting preserved

4. **Fix cascading dependencies**

   - Example: Removing a job may break `needs:` references in other jobs
   - Script should detect and fix these automatically
   - See SRE-3447 for job dependency fixing example

### Campaign Execution

1. **Always start with test batch** (2-5 repos)

   - Catch script issues early
   - Validate assumptions
   - Refine approach before scaling

2. **Use draft PRs initially**

   - Allows review before making PRs public
   - Easy to delete and recreate if issues found
   - Convert to ready when validated

3. **Process in phases with validation**

   - Test → Small batch → Larger batches
   - Stop and validate after each phase
   - Don't merge everything at once

4. **Track progress meticulously**

   - Maintain PROGRESS.md
   - Document issues and resolutions
   - Record completion percentages

5. **Handle failures gracefully**

   - If script fails on a repo, skip it and continue
   - Track failed repos separately
   - Investigate and handle manually if needed

### Tag and Release Management

When campaigns involve releasing packages:

1. **Always validate tag format before pushing**

   - Run `nextver.sh` for suggestion
   - Check existing releases: `gh release list --limit 3`
   - Verify against tag pattern in publish workflow
   - Don't blindly trust auto-generated versions

2. **Watch for beta/alpha tags confusing version tools**

   - Can produce malformed versions like `vv1.0-beta.v1.0-beta`
   - Manually inspect and override if needed

3. **Verify workflow triggers after tagging**

   ```bash
   gh run list --repo org/repo --workflow publish-release.yaml --limit 1
   ```

### Workflow Validation

1. **Check for dangling job dependencies**

   - After removing jobs, scan for `needs:` references
   - Update or remove broken dependencies
   - Validate workflow syntax: `actionlint`

2. **Verify CI passes before merging**

   - Review CI results in PRs
   - Spot-check a few repos manually
   - Don't merge if CI fails

3. **Preserve existing behavior**

   - Only remove/change what's necessary
   - Keep unrelated configurations intact
   - Test that remaining workflows still function

## Command Reference

Quick reference for common commands. See **REFERENCE.md** for detailed examples and real campaign usage.

### turbolift Commands

```bash
turbolift init --name "campaign-name"           # Initialize campaign
turbolift clone                                  # Clone all repos from repos.txt
turbolift foreach -- <command>                   # Run command in each repo
turbolift commit -m "message"                    # Commit changes across all repos
turbolift create-prs --draft                     # Create draft PRs
turbolift create-prs --draft --sleep 2s          # Create PRs with rate limiting
turbolift pr-status                              # Check PR status
turbolift update-prs                             # Update existing PRs after new commits
```

### slam Commands

```bash
slam review ls 'SRE-XXXX'                        # List PRs by change ID pattern
slam review clone 'SRE-XXXX'                     # Clone all repos with matching PRs
slam review approve "$(head -n 1 README.md | sed 's/^# //')"  # Approve and merge (uses PR title from README.md)
slam review delete "pattern"                     # Close PRs and delete branches
slam review purge                                # Purge all SLAM branches (use with caution)
```

### gh CLI Commands

```bash
gh search prs 'org:name SRE-XXXX is:open'       # Search for PRs across org
gh pr ready                                      # Mark PR ready for review
gh pr list --repo org/repo                       # List PRs in repo
gh pr merge <PR_NUM> --repo org/repo --squash   # Merge PR with squash
gh run list --repo org/repo --branch main        # Check workflow runs
gh run watch --repo org/repo                     # Watch workflow in real-time
gh release list --repo org/repo                  # List releases
```

**For detailed command usage, options, and real examples, see [REFERENCE.md](REFERENCE.md)**

## Troubleshooting

### Script fails on some repos

**Symptoms:** Transformation script exits with error for certain repos

**Solutions:**

- Check error message for specific issue (missing file, wrong format, etc.)
- Add better error handling to script
- Skip problematic repos and handle manually
- Update script to handle edge case and re-run

**Recovery:**

```bash
# Reset a single repo
cd work/org/repo
git reset --hard HEAD~1

# Or reset all repos in campaign
turbolift foreach -- git reset --hard HEAD~1
```

### YAML parsing fails

**Symptoms:** Script using YAML parser fails or produces corrupted output

**Solutions:**

- Switch to text-based editing (regex replacements)
- Preserves comments and formatting
- More robust for varied YAML styles

**Example:**

```python
# Instead of parsing YAML:
content = workflow_file.read_text()
new_content = re.sub(
    r'pattern-to-find',
    r'replacement',
    content
)
workflow_file.write_text(new_content)
```

### PRs fail to create

**Symptoms:** `turbolift create-prs` fails with errors

**Common causes:**

- No commits in some repos (script didn't make changes)
- Rate limiting (too many PRs too fast)
- Authentication issues
- Branch already exists

**Solutions:**

```bash
# Use rate limiting
turbolift create-prs --draft --sleep 2s

# Check which repos have commits
turbolift foreach -- git status

# Re-run for failed repos only
# (create new campaign with just failed repos)
```

### slam merge fails for some PRs

**Symptoms:** `slam review approve` reports failures

**Common causes:**

- CI not passing
- PR is in draft state
- Merge conflicts
- PR already merged
- Stale PR state

**Solutions:**

```bash
# Check PR status
gh pr view <PR_NUMBER> --repo org/repo

# Resolve conflicts manually
cd work/org/repo
git pull origin main
git rebase main
git push --force-with-lease

# Update PR to resolve staleness
turbolift update-prs

# Handle failed PRs manually
gh pr merge <PR_NUMBER> --repo org/repo --squash
```

### CI fails after merge

**Symptoms:** Main branch CI fails after merging campaign PRs

**Common causes:**

- Missed dependencies in workflow files
- Breaking changes not tested properly
- Environment-specific issues

**Solutions:**

```bash
# Check CI failure
gh run view <RUN_ID> --repo org/repo --log

# If workflow issue, create fix PR
# If code issue, revert and reassess

# Revert merge commit
git revert <MERGE_COMMIT_SHA>
git push
```

### Malformed tags or version strings

**Symptoms:** Tag doesn't trigger workflow, or has wrong format

**Example:** `vv1.0-beta.v1.0-beta` instead of `v1.0.5`

**Solution:**

```bash
# Delete malformed tag locally and remotely
git tag -d <malformed-tag>
git push origin :refs/tags/<malformed-tag>

# Determine correct version manually
gh api repos/org/repo/tags --jq '.[0:5] | .[] | .name'
gh release list --repo org/repo --limit 5

# Create correct tag
git tag -a v1.0.5 -m "v1.0.5"
git push origin refs/tags/v1.0.5

# Verify workflow triggered
gh run list --repo org/repo --workflow publish-release.yaml --limit 1
```

**Prevention:** Always validate tag format before pushing (see Phase 5 checklist)

## Example Campaigns

### SRE-3447: Remove PyPICloud Publishing

**Objective:** Remove PyPICloud publishing workflows while preserving CodeArtifact

**Scope:** 63 repositories

**Key Challenges:**

- Two different package managers (Poetry and UV)
- Mixed workflows (some with both PyPI and CodeArtifact)
- Job dependencies that broke when PyPI jobs removed

**Solution:**

- Python script with text-based YAML editing
- Verified CodeArtifact existed before removing PyPI
- Automatically fixed dangling `needs:` references
- Phased rollout: 2 test repos → 5 small batch → batches of 20
- Used slam for batch merge after validation

**Location:** `~/code/work/SRE-3447`

### SRE-3449: Use Read-Only CodeArtifact Role

**Objective:** Update install actions to use read-only role (least privilege)

**Scope:** 124 repositories (64 with changes needed)

**Key Challenges:**

- Distinguish install actions (read-only) from publish actions (write)
- Preserve publish action configurations
- Handle varied YAML formatting
- Regex pattern for `${{ secrets.NAME }}` with flexible spacing

**Solution:**

- Python script with regex-based transformations
- Separate handling for install vs publish actions
- Pattern matching with whitespace flexibility
- Test-driven development with pytest
- Comprehensive verification after merge

**Location:** `~/code/work/SRE-3449`

## Alternative: Without slam

If `slam` is not available in your environment, use this alternative workflow for Phase 4:

### Batch PR Review (gh CLI only)

```bash
# Step 1: List all PRs matching pattern
gh search prs 'org:your-org SRE-XXXX is:open' \
  --json number,title,repository,url \
  --jq '.[] | "\(.repository.name): PR #\(.number) - \(.url)"'

# Step 2: Mark PRs ready (if draft)
for repo in $(cat repos.txt); do
  cd work/$repo
  gh pr ready
  cd ../..
done

# Step 3: Review diffs
for repo in $(cat repos.txt); do
  echo "=== $repo ==="
  gh pr diff --repo $repo
done

# Step 4: Approve and merge (manual loop)
for repo in $(cat repos.txt); do
  echo "=== Processing $repo ==="

  # Get PR number
  pr_number=$(gh pr list --repo $repo --search "SRE-XXXX" --json number --jq '.[0].number')

  if [ -z "$pr_number" ]; then
    echo "⏭️  No PR found, skipping"
    continue
  fi

  # Check CI status
  ci_status=$(gh pr view $pr_number --repo $repo --json statusCheckRollup --jq '.statusCheckRollup[0].conclusion')

  if [ "$ci_status" != "SUCCESS" ]; then
    echo "⚠️  CI not passing ($ci_status), skipping"
    continue
  fi

  # Approve
  gh pr review $pr_number --repo $repo --approve

  # Merge
  gh pr merge $pr_number --repo $repo --squash --delete-branch

  echo "✅ Merged PR #$pr_number"
  sleep 2  # Rate limiting
done
```

### Batch Operations Script

Create a helper script `batch-pr-ops.sh`:

```bash
#!/bin/bash
# Batch PR operations without slam

ACTION=$1  # approve, merge, status
PATTERN=$2 # Search pattern like "SRE-XXXX"

if [ -z "$ACTION" ] || [ -z "$PATTERN" ]; then
  echo "Usage: $0 <approve|merge|status> <pattern>"
  exit 1
fi

# Find all matching PRs
repos=$(gh search prs "org:your-org $PATTERN is:open" --json repository --jq '.[].repository.name' | sort -u)

for repo in $repos; do
  pr_number=$(gh pr list --repo your-org/$repo --search "$PATTERN" --json number --jq '.[0].number')

  if [ -z "$pr_number" ]; then
    continue
  fi

  case $ACTION in
    status)
      gh pr view $pr_number --repo your-org/$repo --json number,title,state,statusCheckRollup \
        --jq '"PR #\(.number): \(.title) - \(.state) - CI: \(.statusCheckRollup[0].conclusion)"'
      ;;
    approve)
      gh pr review $pr_number --repo your-org/$repo --approve
      echo "✅ Approved your-org/$repo PR #$pr_number"
      ;;
    merge)
      gh pr merge $pr_number --repo your-org/$repo --squash --delete-branch
      echo "✅ Merged your-org/$repo PR #$pr_number"
      ;;
  esac

  sleep 1
done
```

## Additional Resources

### Official Documentation

- **turbolift**: <https://github.com/Skyscanner/turbolift>
  - Installation: <https://github.com/Skyscanner/turbolift#installation>
  - Usage guide: <https://github.com/Skyscanner/turbolift#usage>

- **gh CLI**: <https://cli.github.com/>
  - Manual: <https://cli.github.com/manual/>
  - Installation: <https://github.com/cli/cli#installation>

- **slam**: <https://github.com/scottidler/slam>
  - Releases: <https://github.com/scottidler/slam/releases>
  - See "Alternative: Without slam" section above for gh CLI-only workflows

### Related Tools

- **actionlint**: Validate GitHub Actions workflow syntax
  - <https://github.com/rhysd/actionlint>
  - Useful for validating workflow changes

- **yq**: YAML processor for command-line
  - <https://github.com/mikefarah/yq>
  - Alternative to custom YAML parsing

## Notes

- **Tool availability:** Check that `turbolift`, `slam` (or alternatives), and `gh` are installed before starting
- **Authentication:** Ensure GitHub authentication is configured (`gh auth status`)
- **Storage:** Campaigns typically stored in `~/code/work/` or similar directory
- **Safety first:** Use draft PRs initially - easy to review and delete before making public
- **Incremental validation:** Always validate in small batches before scaling to full scope
- **Progress tracking:** Track progress meticulously - campaigns can span days or weeks
- **Manual fallback:** When in doubt, process manually rather than risk incorrect bulk changes
- **Rate limiting:** Be mindful of GitHub API rate limits - use `--sleep` flags when available
