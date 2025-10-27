---
name: tatari-turbolift
description: Automate bulk code changes across multiple GitHub repositories using turbolift for campaign management, slam for batch PR review/merge, and gh CLI. Use when making identical or similar changes to many repositories, running bulk refactoring campaigns, or automating mass updates. (project, gitignored)
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
Campaign management tool for bulk repository operations:
- Clones multiple repos in a workspace
- Applies changes uniformly
- Creates PRs across all repos
- Tracks campaign progress

**Installation:** Already installed at `~/bin/turbolift`

### slam
Batch PR review and merge tool:
- Reviews PRs across multiple repos by change ID
- Approves and merges PRs in bulk
- Validates CI status before merging
- Cleans up branches automatically

**Installation:** Already installed at `~/bin/slam`

### gh
GitHub CLI for individual repository operations:
- Searches for PRs across organization
- Manages PR states (draft → ready)
- Checks workflow runs and releases
- Validates tags and deployments

**Installation:** Standard system installation

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
```
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

Initialize a turbolift campaign with test repositories:

```bash
cd SRE-XXXX-campaign-name

# Create test repos list
head -n 2 repos-all.txt > repos-test.txt

# Initialize campaign
turbolift init --name "SRE-XXXX-test"
cd SRE-XXXX-test

# Copy files
cp ../repos-test.txt repos.txt
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
turbolift foreach -- git add -A
turbolift foreach -- git commit -m "Brief commit title

- Detail about change 1
- Detail about change 2
- Mention safety checks performed

Part of SRE-XXXX"

# 6. Create DRAFT pull requests
turbolift create-prs --draft

# 7. Check PR status
turbolift pr-status
```

**STOP: Manual Validation Required**

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

### Phase 2: Small Batch (5-10 repos)

After test campaign succeeds:

```bash
cd ..  # Back to SRE-XXXX-campaign-name

# Create small batch list
sed -n '3,10p' repos-all.txt > repos-batch-1.txt

# New campaign for small batch
turbolift init --name "SRE-XXXX-batch-1"
cd SRE-XXXX-batch-1

cp ../repos-batch-1.txt repos.txt
cp ../transformation-script.py .

# Run the campaign (same steps as Phase 1)
turbolift clone
turbolift foreach -- python3 ../transformation-script.py
turbolift foreach -- git diff
turbolift foreach -- git add -A
turbolift foreach -- 'git commit -m "Your commit message..."'
turbolift create-prs --draft
```

**STOP: Review and Validate**

### Phase 3: Batch Processing (groups of 20-30)

Process remaining repos in manageable batches:

```bash
cd /path/to/SRE-XXXX-campaign-name

# Batch 2 (repos 11-30)
sed -n '11,30p' repos-all.txt > repos-batch-2.txt

turbolift init --name "SRE-XXXX-batch-2"
cd SRE-XXXX-batch-2
cp ../repos-batch-2.txt repos.txt
cp ../transformation-script.py .

turbolift clone
turbolift foreach -- python3 ../transformation-script.py
turbolift foreach -- git diff
turbolift foreach -- git add -A
turbolift foreach -- 'git commit -m "..."'
turbolift create-prs --draft

# Repeat for subsequent batches...
```

### Phase 4: Batch PR Review & Merge with slam

After creating draft PRs, use `slam` for bulk operations:

#### Step 1: Discover All Draft PRs

```bash
# Find all draft PRs matching your ticket number
gh search prs 'org:tatari-tv SRE-XXXX is:draft is:open' --json number,title,repository
```

#### Step 2: Mark PRs Ready for Review

**For repos in current turbolift campaign:**
```bash
cd SRE-XXXX-batch-X
turbolift foreach -- gh pr ready
```

**For repos outside current campaign:**
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

**Single command to approve and merge all PRs:**
```bash
slam review approve "SRE-XXXX: Brief description"
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

#### Step 5: Verify Merged Changes

```bash
# Check CI status for merged repos
for repo in <list-of-repos>; do
  echo "=== $repo ==="
  gh run list --repo org/$repo --branch main --limit 1 \
    --json status,conclusion,workflowName,createdAt
done
```

Verify:
- Latest CI run from merge is complete
- Conclusion is "success"
- Changes are in main branch

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

```markdown
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

### turbolift Commands

```bash
# Initialize campaign
turbolift init --name "campaign-name"

# Clone all repos from repos.txt
turbolift clone

# Run command in each repo
turbolift foreach -- <command>
turbolift foreach -- 'multi && command && chain'

# Commit changes across all repos
turbolift commit -m "commit message"
# Or manual commit:
turbolift foreach -- git add -A
turbolift foreach -- 'git commit -m "message"'

# Create PRs
turbolift create-prs --draft                    # Create draft PRs
turbolift create-prs --draft --sleep 2s         # With rate limiting
turbolift create-prs                            # Create ready PRs

# Check PR status
turbolift pr-status

# Update existing PRs (after pushing new commits)
turbolift update-prs
```

### slam Commands

```bash
# List PRs by change ID pattern
slam review ls 'SRE-XXXX'
slam review ls 'pattern'

# Clone all repos with PRs for a change ID
slam review clone 'SRE-XXXX'

# Approve and merge all PRs matching pattern
slam review approve "SRE-XXXX: Description"

# Delete all PRs matching pattern (close and delete branches)
slam review delete "pattern"

# Purge all SLAM branches (nuclear option)
slam review purge

# Specify different org
slam review ls 'pattern' --org other-org

# Filter by repo patterns
slam review ls 'pattern' --repo-ptns 'repo-pattern'
```

### gh CLI Commands

```bash
# Search for PRs across org
gh search prs 'org:tatari-tv SRE-XXXX is:draft is:open' --json number,title,repository

# Mark PR ready for review
gh pr ready                                      # In repo directory
gh pr ready <PR_NUMBER> --repo org/repo         # Specify repo

# List PRs in repo
gh pr list --repo org/repo --search "SRE-XXXX" --state all

# Check workflow runs
gh run list --repo org/repo --branch main --limit 5
gh run list --repo org/repo --workflow publish-release.yaml

# Watch workflow in real-time
gh run watch --repo org/repo

# Manage releases
gh release list --repo org/repo --limit 5
gh release create v1.0.0 --repo org/repo

# Check tags
gh api repos/org/repo/tags --jq '.[0:5] | .[] | .name'
```

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

## Additional Resources

- turbolift GitHub: https://github.com/Skyscanner/turbolift
- slam is an internal Tatari tool
- gh CLI docs: https://cli.github.com/manual/

## Notes

- Both `turbolift` and `slam` are already installed at `~/bin/`
- Campaigns typically stored in `~/code/work/`
- Use draft PRs for safety - easy to review and delete before making public
- Always validate in small batches before scaling to full scope
- Track progress meticulously - campaigns can span days or weeks
- When in doubt, process manually rather than risk incorrect bulk changes
