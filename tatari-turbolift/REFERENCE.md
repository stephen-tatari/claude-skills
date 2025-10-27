# Turbolift Campaign Command Reference

Quick reference for actual command usage with real examples from production campaigns.

## Table of Contents

- [turbolift Commands](#turbolift-commands)
- [slam Commands](#slam-commands)
- [gh CLI Commands](#gh-cli-commands)
- [Common Workflows](#common-workflows)
- [Real Campaign Examples](#real-campaign-examples)

---

## turbolift Commands

### Initialize Campaign

```bash
# Basic initialization
turbolift init --name "campaign-name"

# Example: SRE-3447
turbolift init --name "SRE-3447-remove-pypicloud"
cd SRE-3447-remove-pypicloud
```

**Creates:**

- Campaign directory with name
- Empty `repos.txt` file
- `.turbolift` marker file

### Clone Repositories

```bash
# Clone all repos from repos.txt
turbolift clone

# Example output:
# Cloning tatari-tv/repo-1...
# Cloning tatari-tv/repo-2...
# Cloning tatari-tv/repo-3...
```

**Creates:**

- `work/` directory
- Subdirectories: `work/org-name/repo-name/`

### Run Commands Across Repos

```bash
# Basic foreach
turbolift foreach -- <command>

# Single command
turbolift foreach -- git status
turbolift foreach -- ls -la

# Multiple commands (use quotes for shell chains)
turbolift foreach -- 'git add -A && git commit -m "message"'

# Python script
turbolift foreach -- python3 ../transformation-script.py

# With environment variables
turbolift foreach -- 'MYVAR=value python3 ../script.py'
```

**Real examples from SRE-3447:**

```bash
# Apply transformation
turbolift foreach -- python3 ../remove-pypicloud.py

# Review changes
turbolift foreach -- git status
turbolift foreach -- git diff

# Review specific files
turbolift foreach -- git diff pyproject.toml
turbolift foreach -- git diff .github/workflows/

# Commit changes
turbolift commit -m "Remove PyPICloud publishing configuration

- Remove PyPICloud source from pyproject.toml
- Remove pypi-upload/pypi-uv-publish workflow jobs/steps
- Keep CodeArtifact publishing configuration

Part of SRE-3447"
```

### Create Pull Requests

```bash
# Create draft PRs (recommended for initial review)
turbolift create-prs --draft

# Create draft PRs with rate limiting (avoid API throttling)
turbolift create-prs --draft --sleep 2s

# Create ready-for-review PRs
turbolift create-prs

# With custom PR body
turbolift create-prs --draft --pr-body "$(cat ../PR_TEMPLATE.md)"
```

**Real example from SRE-3449:**

```bash
cd SLAM-SRE-3449-use-read-only-codeartifact-role
turbolift create-prs --draft --sleep 2s
```

### Commit Changes

```bash
# Use turbolift commit (applies to all repos with changes)
turbolift commit -m "commit message"

# Or use foreach for more control
turbolift foreach -- git add -A
turbolift foreach -- git commit -m "message"

# Multi-line commit messages (use heredoc)
turbolift foreach -- 'git commit -m "$(cat <<EOF
Title line here

- Bullet point 1
- Bullet point 2

Part of SRE-XXXX
EOF
)"'
```

### Check PR Status

```bash
# Show status of all PRs in campaign
turbolift pr-status

# Example output:
# tatari-tv/repo-1: #123 (open, draft)
# tatari-tv/repo-2: #124 (open, ready)
# tatari-tv/repo-3: #125 (merged)
```

### Update Existing PRs

```bash
# After pushing new commits, update PRs
turbolift update-prs

# Use case: Fixed script, re-ran transformation, need to update PRs
turbolift foreach -- git add -A
turbolift foreach -- git commit -m "Fix: handle edge case"
turbolift foreach -- git push
turbolift update-prs
```

### Verbose Output

```bash
# Add -v flag for detailed output
turbolift -v clone
turbolift -v foreach -- python3 ../script.py
turbolift -v create-prs --draft
```

---

## slam Commands

### Review PRs by Change ID

```bash
# List all PRs matching a pattern
slam review ls 'SRE-XXXX'
slam review ls 'pattern'

# Example: Find all SRE-3447 PRs
slam review ls 'SRE-3447'
```

**Output shows:**

- All matching PRs across repos
- File changes in each repo
- PR status (open, draft, CI status)

### Clone Repos with PRs

```bash
# Clone all repos that have PRs for a change ID
slam review clone 'SRE-XXXX'

# Example:
slam review clone 'SRE-3449'
```

**Creates:**

- Local clones in working directory
- Checks out PR branch in each

### Approve and Merge PRs

```bash
# Single command to approve + merge all matching PRs
# Extract PR title from campaign's README.md header
slam review approve "$(head -n 1 README.md | sed 's/^# //')"
# Real example from SRE-3447:
PR_TITLE=$(head -n 1 README.md | sed 's/^# //')
slam review approve "$PR_TITLE"
```

**What it does:**

1. Finds all PRs matching pattern
2. Validates each PR:
   - CI must be passing
   - Must not be draft
   - Must be mergeable (no conflicts)
3. Approves the PR
4. Merges with squash
5. Deletes branch
6. Reports success/failure per repo

**Example output:**

```text
Processing tatari-tv/repo-1 PR #123
  ✅ CI passed
  ✅ Approved
  ✅ Merged
  ✅ Branch deleted

Processing tatari-tv/repo-2 PR #124
  ❌ CI not passing - skipped

Summary: 1 merged, 1 failed
```

### Delete PRs and Branches

```bash
# Close PRs and delete branches for a change ID
slam review delete "pattern"

# Example: Clean up abandoned PRs
slam review delete "SRE-3447-old"
```

### Purge All SLAM Branches

```bash
# Nuclear option: close ALL PRs and delete ALL SLAM branches
slam review purge

# Use with extreme caution!
```

### Specify Organization

```bash
# Default is tatari-tv, override with --org
slam review ls 'pattern' --org other-org
slam review approve "pattern" --org other-org
```

### Filter by Repository Pattern

```bash
# Only process repos matching pattern
slam review ls 'SRE-XXXX' --repo-ptns 'python-*'
slam review approve "SRE-XXXX" --repo-ptns 'python-tatari-*'
```

---

## gh CLI Commands

### Search for PRs

```bash
# Search PRs across organization
gh search prs 'org:tatari-tv SRE-XXXX'

# With filters
gh search prs 'org:tatari-tv SRE-XXXX is:draft is:open'
gh search prs 'org:tatari-tv SRE-XXXX is:merged'
gh search prs 'org:tatari-tv author:@me is:open'

# With JSON output
gh search prs 'org:tatari-tv SRE-XXXX is:draft is:open' \
  --json number,title,repository,url

# Extract just repo names
gh search prs 'org:tatari-tv SRE-XXXX is:open' \
  --json repository \
  --jq '.[].repository.name' | sort -u
```

**Real example from SRE-3447:**

```bash
# Find all draft PRs for the campaign
gh search prs 'org:tatari-tv SRE-3447 is:draft is:open' \
  --json number,title,repository
```

### List PRs in a Repo

```bash
# List PRs in specific repo
gh pr list --repo org/repo

# With search filter
gh pr list --repo org/repo --search "SRE-XXXX"

# All states
gh pr list --repo org/repo --search "SRE-XXXX" --state all

# With JSON output
gh pr list --repo org/repo --json number,title,state,url
```

### View PR Details

```bash
# View PR in terminal
gh pr view <PR_NUMBER> --repo org/repo

# View in browser
gh pr view <PR_NUMBER> --repo org/repo --web

# JSON output with specific fields
gh pr view <PR_NUMBER> --repo org/repo \
  --json number,title,state,statusCheckRollup,mergeable
```

### Mark PR Ready for Review

```bash
# In repo directory
gh pr ready

# Specify PR and repo
gh pr ready <PR_NUMBER> --repo org/repo

# Real example - mark all PRs in campaign ready:
cd SRE-3447-batch-2
turbolift foreach -- gh pr ready
```

### Review and Approve PR

```bash
# Approve
gh pr review <PR_NUMBER> --repo org/repo --approve

# Request changes
gh pr review <PR_NUMBER> --repo org/repo --request-changes

# Comment
gh pr review <PR_NUMBER> --repo org/repo --comment -b "looks good"
```

### Merge PR

```bash
# Merge with squash (most common)
gh pr merge <PR_NUMBER> --repo org/repo --squash

# With auto-delete branch
gh pr merge <PR_NUMBER> --repo org/repo --squash --delete-branch

# Merge commit
gh pr merge <PR_NUMBER> --repo org/repo --merge

# Rebase
gh pr merge <PR_NUMBER> --repo org/repo --rebase
```

### Check PR Diff

```bash
# View diff in terminal
gh pr diff <PR_NUMBER> --repo org/repo

# Specific file
gh pr diff <PR_NUMBER> --repo org/repo -- path/to/file

# Patch format
gh pr diff <PR_NUMBER> --repo org/repo --patch
```

### Workflow Runs

```bash
# List recent runs
gh run list --repo org/repo

# For specific branch
gh run list --repo org/repo --branch main

# For specific workflow
gh run list --repo org/repo --workflow ci.yaml
gh run list --repo org/repo --workflow publish-release.yaml

# Limit results
gh run list --repo org/repo --limit 5

# JSON output
gh run list --repo org/repo --branch main --limit 1 \
  --json status,conclusion,workflowName,createdAt

# Watch run in real-time
gh run watch --repo org/repo

# View run logs
gh run view <RUN_ID> --repo org/repo --log
```

**Real example from SRE-3447:**

```bash
# Check if publish-release workflow triggered after tag
gh run list --repo tatari-tv/python-tatari-api-client \
  --workflow publish-release.yaml --limit 1
```

### Releases

```bash
# List releases
gh release list --repo org/repo

# Limit output
gh release list --repo org/repo --limit 5

# Create release
gh release create v1.0.0 --repo org/repo --title "v1.0.0"

# With notes
gh release create v1.0.0 --repo org/repo --notes "Release notes here"

# View specific release
gh release view v1.0.0 --repo org/repo
```

### Tags

```bash
# List tags (via API)
gh api repos/org/repo/tags --jq '.[0:5] | .[] | .name'

# Get latest tag
gh api repos/org/repo/tags --jq '.[0].name'

# Create tag locally then push
git tag -a v1.0.0 -m "v1.0.0"
git push origin refs/tags/v1.0.0

# Delete remote tag
git push origin :refs/tags/v1.0.0
```

**Real example from SRE-3447 (fix malformed tag):**

```bash
# Delete malformed tag
git tag -d vv1.0-beta.v1.0-beta.v1.0-beta
git push origin :refs/tags/vv1.0-beta.v1.0-beta.v1.0-beta

# Check existing tags to determine correct format
gh api repos/tatari-tv/python-beeswax-client/tags \
  --jq '.[0:5] | .[] | .name'

# Create correct tag
git tag -a v0.3.65 -m "v0.3.65"
git push origin refs/tags/v0.3.65

# Verify workflow triggered
gh run list --repo tatari-tv/python-beeswax-client \
  --workflow publish-release.yaml --limit 1
```

### Repository Search

```bash
# Search repositories
gh search repos 'org:tatari-tv python'

# With language filter
gh search repos 'org:tatari-tv language:python'

# JSON output
gh search repos 'org:tatari-tv' --json name,owner \
  | jq -r '.[] | "\(.owner.login)/\(.name)"'
```

### Code Search

```bash
# Search for code
gh api search/code -X GET \
  -f q='org:tatari-tv path:.github/workflows filename:ci.yaml'

# Extract repo names
gh api search/code -X GET \
  -f q='org:tatari-tv pypi-upload' \
  --jq '.items[].repository.full_name' | sort -u
```

---

## Common Workflows

### Complete Campaign Workflow

```bash
# 1. Initialize
turbolift init --name "SRE-XXXX-description"
cd SRE-XXXX-description

# 2. Create repos list
cat > repos.txt <<EOF
org/repo-1
org/repo-2
org/repo-3
EOF

# 3. Clone repos
turbolift clone

# 4. Apply transformation
turbolift foreach -- python3 ../transformation-script.py

# 5. Review changes
turbolift foreach -- git diff

# 6. Commit
turbolift commit -m "Description of changes"

# 7. Create draft PRs
turbolift create-prs --draft --sleep 2s

# 8. Check PR status
turbolift pr-status

# 9. Wait for CI to complete on draft PRs
gh search prs 'org:tatari-tv SRE-XXXX is:draft is:open' \
  --json number,repository,statusCheckRollup \
  --jq '.[] | "\(.repository.name): \(.statusCheckRollup[0].state)"'

# 10. If CI fails, retrieve logs and fix
gh run view <RUN_ID> --repo org/repo --log
# Make fixes in work/org/repo, commit, push, verify CI passes

# ⚠️ STOP: Wait for all CI to pass before continuing
# Verify all PRs show green checkmarks before marking ready

# 11. Mark ready (after CI passes and user verification)
turbolift foreach -- gh pr ready

# 12. Batch merge with slam
PR_TITLE=$(head -n 1 README.md | sed 's/^# //')
slam review approve "$PR_TITLE"
```

### Verify Campaign Results

```bash
# 1. List all merged PRs
gh search prs 'org:tatari-tv SRE-XXXX is:merged' \
  --json repository --jq '.[].repository.name' | sort

# 2. Check CI status on main for each repo
for repo in $(cat repos.txt); do
  echo "=== $repo ==="
  gh run list --repo $repo --branch main --limit 1 \
    --json status,conclusion,workflowName
done

# 3. Verify specific files changed
for repo in $(cat repos.txt); do
  echo "=== $repo ==="
  gh api repos/$repo/contents/.github/workflows/old-file.yaml 2>&1 | grep -q "Not Found" \
    && echo "✅ File removed" || echo "❌ File still exists"
done
```

### Handle Failed PRs

```bash
# 1. Find failed PRs
slam review ls 'SRE-XXXX' | grep "CI.*FAILURE"

# 2. Check specific PR
gh pr view <PR_NUMBER> --repo org/repo
gh run view <RUN_ID> --repo org/repo --log

# 3. Fix and update
cd work/org/repo
# Make fixes
git add -A
git commit -m "Fix: description"
git push

# 4. Verify CI passes
gh pr checks <PR_NUMBER> --repo org/repo --watch

# 5. Merge manually if needed
gh pr merge <PR_NUMBER> --repo org/repo --squash --delete-branch
```

### Rollback Changes

```bash
# If PRs are still open, close them
slam review delete "SRE-XXXX"

# If already merged, revert
for repo in $(cat repos.txt); do
  cd work/$repo

  # Find merge commit
  merge_commit=$(git log --grep="SRE-XXXX" --format="%H" -n 1)

  # Create revert PR
  git checkout -b revert-sre-xxxx
  git revert $merge_commit
  git push origin revert-sre-xxxx

  gh pr create --title "Revert SRE-XXXX" --body "Reverting changes from SRE-XXXX"

  cd ../..
done
```

### Tag Multiple Repos for Release

```bash
# Loop through repos needing manual tags
for repo in $(cat repos-needing-tags.txt); do
  echo "=== $repo ==="

  # Clone repo
  cd /tmp
  git clone git@github.com:org/$repo.git
  cd $repo

  # Pull latest
  git pull origin main

  # Get suggested version
  version=$(nextver.sh)
  echo "Suggested version: $version"

  # Validate against existing releases
  echo "Recent releases:"
  gh release list --limit 3

  # If format looks good, create tag
  read -p "Create tag $version? (y/n): " confirm
  if [ "$confirm" = "y" ]; then
    git tag -a $version -m "$version"
    git push origin refs/tags/$version

    # Watch workflow
    gh run watch
  fi

  # Cleanup
  cd /tmp
  rm -rf $repo
done
```

---

## Real Campaign Examples

### SRE-3447: Remove PyPICloud Publishing

**Objective:** Remove PyPICloud publishing workflows, keep CodeArtifact

**Repos:** 63 repositories

**Commands used:**

```bash
# Setup
turbolift init --name "SRE-3447-remove-pypicloud"
cd SRE-3447-remove-pypicloud
cp ../repos-test.txt repos.txt

# Execute
turbolift clone
turbolift foreach -- python3 ../remove-pypicloud.py
turbolift foreach -- git diff
turbolift foreach -- git add -A
turbolift commit -m "Remove PyPICloud publishing configuration

- Remove PyPICloud source from pyproject.toml
- Remove pypi-upload/pypi-uv-publish workflow jobs/steps
- Keep CodeArtifact publishing configuration

Part of SRE-3447"
turbolift create-prs --draft

# Wait for CI to complete
gh search prs 'org:tatari-tv SRE-3447 is:draft' \
  --json repository,statusCheckRollup \
  --jq '.[] | "\(.repository.name): \(.statusCheckRollup[0].state)"'

# ⚠️ Wait for CI to pass before continuing

# After validation
turbolift foreach -- gh pr ready
slam review ls 'SRE-3449'
PR_TITLE=$(head -n 1 README.md | sed 's/^# //')
slam review approve "$PR_TITLE"

# Check merged status
./check-merged-prs.sh
```

### SRE-3449: Use Read-Only CodeArtifact Role

**Objective:** Update install actions to use read-only role (least privilege)

**Repos:** 124 repositories (64 needed changes)

**Commands used:**

```bash
# Setup
turbolift init --name "SLAM-SRE-3449-use-read-only-codeartifact-role"
cd SLAM-SRE-3449-use-read-only-codeartifact-role
cp ../repos-all.txt repos.txt

# Execute
turbolift clone
turbolift foreach -- python3 ../../update_codeartifact_role.py
turbolift commit -m "Use read-only CodeArtifact role for install actions"
turbolift create-prs --draft --sleep 2s

# Status check
turbolift pr-status

# Wait for CI to complete on all PRs
gh search prs 'org:tatari-tv SRE-3449 is:draft' \
  --json repository,statusCheckRollup \
  --jq '.[] | "\(.repository.name): \(.statusCheckRollup[0].state)"'

# ⚠️ Wait for CI to pass before continuing

# After validation
turbolift foreach -- gh pr ready
slam review ls 'SRE-3449'
PR_TITLE=$(head -n 1 README.md | sed 's/^# //')
slam review approve "$PR_TITLE"
# Verify all install actions updated
for repo in $(cat repos.txt); do
  echo "=== $repo ==="
  rg 'PROD_CODEARTIFACT_PUBLISH_ROLE' work/$repo/.github/workflows/ || echo "✅ All updated"
done
```

### Batch Processing Pattern

```bash
# Process in batches of 20
cd /path/to/campaign

# Batch 1
sed -n '1,20p' repos-all.txt > repos-batch-1.txt
turbolift init --name "SRE-XXXX-batch-1"
cd SRE-XXXX-batch-1
cp ../repos-batch-1.txt repos.txt
# ... run campaign

# Batch 2
cd ..
sed -n '21,40p' repos-all.txt > repos-batch-2.txt
turbolift init --name "SRE-XXXX-batch-2"
cd SRE-XXXX-batch-2
cp ../repos-batch-2.txt repos.txt
# ... run campaign

# After all batches, merge with slam
slam review approve "SRE-XXXX"
```

---

## Tips and Tricks

### Rate Limiting

```bash
# Add sleep between PR creations
turbolift create-prs --draft --sleep 2s
turbolift create-prs --draft --sleep 5s

# Add sleep in bash loops
for repo in $(cat repos.txt); do
  gh pr merge $pr_num --repo $repo --squash
  sleep 2
done
```

### Parallel Execution

```bash
# turbolift foreach runs serially by default
# For parallel execution, use xargs:

cat repos.txt | xargs -P 5 -I {} bash -c '
  cd work/{} && python3 ../../../script.py
'
```

### Filtering Repos

```bash
# Only process repos with changes
turbolift foreach -- 'git status --short | grep -q . && echo "Has changes" || echo "No changes"'

# Skip repos with errors
turbolift foreach -- 'python3 ../script.py || echo "FAILED: $(pwd)"'

# Process only Python repos
turbolift foreach -- 'test -f pyproject.toml && python3 ../script.py || echo "Not a Python repo"'
```

### Debugging

```bash
# Verbose mode
turbolift -v foreach -- python3 ../script.py

# Check slam logs
tail -f ~/.local/share/slam/slam.log

# Dry-run for gh commands (check what would happen)
gh pr merge --help  # Check available options first

# Test script on single repo before foreach
cd work/org/test-repo
python3 ../../../script.py
git diff
```

### Working with JSON

```bash
# Pretty print JSON
gh pr list --repo org/repo --json number,title,state | jq '.'

# Extract specific fields
gh pr list --repo org/repo --json number,title,state \
  | jq -r '.[] | "\(.number): \(.title)"'

# Filter by field
gh pr list --repo org/repo --json number,title,state \
  | jq '.[] | select(.state == "OPEN")'

# Count results
gh search prs 'org:tatari-tv SRE-XXXX' --json number | jq 'length'
```
