---
name: loki-debug
description: Debug Kubernetes pod failures by querying logs from Loki. Use when investigating errors, crashes, or unexpected behavior in pods. Provide a cluster, namespace, and service name to start.
---

# Loki Log Debugging Skill

Query Kubernetes pod logs stored in Loki to debug failures, errors, and unexpected behavior.

## When to Use

Use this skill when:

- Investigating pod failures or crashes
- Debugging application errors in Kubernetes
- Searching for specific log patterns across pods
- Troubleshooting service issues in a cluster

## Prerequisites

Ensure these tools are available:

- `kubectl` - configured with cluster contexts
- `curl` - for HTTP requests
- `jq` - for JSON parsing

## Workflow

### Step 1: Gather Information

Ask the user for:

1. **Cluster** - Which cluster to search (test, staging, prod, apps, ops)
2. **Namespace** - Kubernetes namespace (e.g., `default`, `payments`)
3. **Service/App** - Deployment or service name to filter
4. **Time range** - How far back to search (e.g., "last 1 hour", "last 30 minutes")

### Step 2: Connect to Loki

Switch kubectl context and set up port-forward:

```bash
# Switch to the target cluster
kubectl config use-context <cluster>

# Start port-forward to Loki gateway (run in background)
kubectl port-forward -n loki-system svc/loki-gateway 3100:80 &
LOKI_PF_PID=$!

# Wait for port-forward to establish
sleep 2
```

**If port-forward fails or is blocked:** Ask the user to run the port-forward
command manually in a separate terminal:

```bash
kubectl port-forward -n loki-system svc/loki-gateway 3100:80
```

Then continue with the log queries once they confirm it's running.

### Step 3: Discover Available Labels

Query Loki for available log labels:

```bash
curl -s http://localhost:3100/loki/api/v1/labels | jq '.data[]'
```

Common labels include: `namespace`, `pod`, `container`, `app`, `stream`

To see values for a specific label:

```bash
curl -s "http://localhost:3100/loki/api/v1/label/<label_name>/values" | jq '.data[]'
```

### Step 4: Query Logs

Construct and execute the LogQL query:

```bash
# Calculate time range (example: last 1 hour)
# Use arithmetic for shell compatibility (works in bash, zsh, nix shells)
END_SECS=$(date +%s)
START_SECS=$((END_SECS - 3600))

# Query logs and save to temp file (avoids zsh brace parsing issues)
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={namespace="<namespace>", app="<app>"}' \
  --data-urlencode "start=${START_SECS}000000000" \
  --data-urlencode "end=${END_SECS}000000000" \
  --data-urlencode "limit=500" > /tmp/loki_logs.json

# Parse the results
jq -r '.data.result[].values[][1]' /tmp/loki_logs.json
```

**Important:** Use single quotes around the query parameter to avoid shell escaping
issues with curly braces. Write output to a temp file before piping to jq to avoid
zsh parsing errors.

### Step 5: Analyze Results

When reviewing logs:

1. **Look for error patterns** - Search for "error", "exception", "failed", "panic"
2. **Check timestamps** - Identify when issues started
3. **Trace request flows** - Follow request IDs or trace IDs
4. **Compare pods** - Check if issue affects all pods or specific ones

To filter for errors only:

```bash
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={namespace="<namespace>", app="<app>"} |~ "(?i)error|exception|failed"' \
  --data-urlencode "start=${START_SECS}000000000" \
  --data-urlencode "end=${END_SECS}000000000" \
  --data-urlencode "limit=500" > /tmp/loki_logs.json

jq -r '.data.result[].values[][1]' /tmp/loki_logs.json
```

### Step 6: Iterate and Refine

Based on initial results:

- Narrow time range around the incident
- Add more specific pattern filters
- Query different labels (e.g., specific pod instead of app)
- Check related services or upstream dependencies

### Step 7: Cleanup

Kill the port-forward when done:

```bash
kill $LOKI_PF_PID 2>/dev/null
```

## Common LogQL Patterns

```logql
# All logs from a namespace
{namespace="payments"}

# Logs from specific app
{namespace="payments", app="checkout-service"}

# Filter by log level
{namespace="payments"} |= "ERROR"

# Case-insensitive error search
{namespace="payments"} |~ "(?i)error"

# Exclude health checks
{namespace="payments"} != "healthcheck" != "/health"

# JSON log parsing
{namespace="payments"} | json | level="error"

# Multiple conditions
{namespace="payments", app="checkout"} |~ "error|exception" != "expected"
```

## Troubleshooting

### Port-forward fails

```bash
# Check if Loki service exists
kubectl get svc -n loki-system

# Check if you can reach the cluster
kubectl cluster-info
```

### No logs returned

- Verify label names with `/loki/api/v1/labels`
- Expand time range
- Check if the namespace/app labels match exactly

### Connection refused

- Ensure port-forward is running: `ps aux | grep port-forward`
- Try restarting the port-forward
- Check if port 3100 is already in use

### Query timeout

- Reduce time range
- Add more specific filters
- Reduce limit parameter

### Shell parsing errors

If you see `parse error near '('` or similar zsh errors:

- Use single quotes around the LogQL query: `'query={...}'`
- Write curl output to a temp file before parsing with jq
- Use arithmetic for time calculations: `$(($(date +%s) - 3600))`
- Avoid the `-v` flag with `date` (use arithmetic instead)
