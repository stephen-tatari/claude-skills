# LogQL Reference

Quick reference for Loki's query language.

## Label Selectors

```logql
{label="value"}           # Exact match
{label=~"regex.*"}        # Regex match
{label!="value"}          # Not equal
{label!~"regex.*"}        # Regex not match
```

Multiple labels (AND):

```logql
{namespace="prod", app="api", container="main"}
```

## Line Filters

```logql
|= "text"     # Contains (case-sensitive)
!= "text"     # Does not contain
|~ "regex"    # Regex match
!~ "regex"    # Regex not match
```

Chain filters:

```logql
{app="api"} |= "error" != "healthcheck" |~ "user_id=[0-9]+"
```

## Common Regex Patterns

```logql
# Case-insensitive
|~ "(?i)error"

# Multiple terms (OR)
|~ "error|exception|failed|panic"

# Word boundary
|~ "\\berror\\b"

# Capture groups not supported in filters, only in parsers
```

## JSON Parsing

```logql
{app="api"} | json

# Access nested fields
{app="api"} | json | level="error"

# Rename fields
{app="api"} | json msg="message"
```

## Time Formatting

Loki uses Unix nanoseconds for timestamps.

### Portable (recommended)

Use arithmetic for cross-platform compatibility (works in bash, zsh, nix shells):

```bash
# Current time
END_SECS=$(date +%s)
echo "${END_SECS}000000000"

# 1 hour ago
START_SECS=$(($(date +%s) - 3600))
echo "${START_SECS}000000000"

# 30 minutes ago
START_SECS=$(($(date +%s) - 1800))
echo "${START_SECS}000000000"

# 2 hours ago
START_SECS=$(($(date +%s) - 7200))
echo "${START_SECS}000000000"
```

### macOS-specific

```bash
# 1 hour ago (may not work in all shells)
date -v-1H +%s000000000

# 30 minutes ago
date -v-30M +%s000000000
```

### Linux-specific

```bash
# 1 hour ago
date -d '1 hour ago' +%s000000000

# 30 minutes ago
date -d '30 minutes ago' +%s000000000
```

## API Endpoints

### Query Range (time-series)

```text
GET /loki/api/v1/query_range
```

Parameters:

- `query` - LogQL query
- `start` - Start time (Unix nanoseconds)
- `end` - End time (Unix nanoseconds)
- `limit` - Max entries (default 100)
- `direction` - `forward` or `backward` (default)

### Instant Query

```text
GET /loki/api/v1/query
```

Parameters:

- `query` - LogQL query
- `time` - Evaluation time (Unix nanoseconds)
- `limit` - Max entries

### Labels

```text
GET /loki/api/v1/labels          # List all labels
GET /loki/api/v1/label/<name>/values  # Values for label
```

## Response Parsing with jq

```bash
# Extract just log lines
jq -r '.data.result[].values[][1]'

# With timestamps (human readable)
jq -r '.data.result[].values[] | "\(.[0] | tonumber / 1000000000 | strftime("%Y-%m-%d %H:%M:%S")) \(.[1])"'

# Count results
jq '.data.result | map(.values | length) | add'

# Get stream labels
jq '.data.result[].stream'
```

## Error Patterns to Search

```logql
# General errors
|~ "(?i)(error|exception|failed|failure|panic|fatal)"

# HTTP errors
|~ "status[=: ]+[45][0-9]{2}"

# Timeouts
|~ "(?i)(timeout|timed out|deadline exceeded)"

# Connection issues
|~ "(?i)(connection refused|connection reset|no route to host)"

# Memory issues
|~ "(?i)(out of memory|oom|memory limit)"

# Kubernetes events
|~ "(?i)(crashloopbackoff|imagepullbackoff|evicted)"
```

## Performance Tips

1. **Always use label selectors** - Avoid `{job=~".+"}`, be specific
2. **Limit time range** - Smaller ranges = faster queries
3. **Use line filters before parsers** - Filter early to reduce processing
4. **Set reasonable limits** - Start with `limit=500`, increase if needed
5. **Avoid regex when possible** - `|= "text"` is faster than `|~ "text"`
