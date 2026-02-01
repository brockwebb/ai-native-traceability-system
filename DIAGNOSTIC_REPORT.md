# MCP Server Debug Report - trace-mcp

**Date:** 2025-02-01
**Status:** 🔴 Issue Identified - PATH Problem

## Issue Summary

The `trace-mcp` command is not in Claude Desktop's PATH, causing connection failures.

## Diagnostic Findings

### 1. Log Analysis ✅

**Location:** `~/Library/Logs/Claude/mcp-server-trace.log`

**Key Error:**
```
Failed to spawn process: No such file or directory
```

**Claude Desktop PATH:**
```
/usr/local/bin
/opt/homebrew/bin
/usr/bin
/bin
/usr/sbin
/sbin
```

**Issue:** `/opt/anaconda3/bin` is NOT in this PATH!

### 2. Server Installation ✅

- **trace-mcp location:** `/opt/anaconda3/bin/trace-mcp`
- **Python location:** `/opt/anaconda3/bin/python`
- **Shebang:** `#!/opt/anaconda3/bin/python`
- **MCP version:** 1.9.4
- **MCP imports:** ✅ Working

### 3. Current Config ❌

```json
"trace": {
    "command": "trace-mcp",
    "env": {
        "TRACE_DIR": "/Users/brock/Documents/GitHub/ai-native-traceability-system/.trace"
    }
}
```

**Problem:** Uses bare command name `trace-mcp` which Claude Desktop can't find.

### 4. Working Configs (for comparison) ✅

All other MCP servers use explicit Python paths:

```json
"census-mcp": {
    "command": "/opt/anaconda3/envs/census-mcp/bin/python",
    "args": ["/Users/brock/Documents/GitHub/census-mcp-server/src/census_mcp_server.py"],
    ...
}

"arnold-profile": {
    "command": "/opt/anaconda3/envs/arnold/bin/python",
    "args": ["/Users/brock/Documents/GitHub/arnold/src/arnold-profile-mcp/arnold_profile_mcp/server.py"],
    ...
}
```

## Root Cause

Claude Desktop has a limited PATH and doesn't include conda/anaconda bin directories. Using bare command names like `trace-mcp` fails because it's not in the search path.

## Solution

Update config to use explicit Python path with `-m` module flag:

```json
"trace": {
    "command": "/opt/anaconda3/bin/python",
    "args": ["-m", "mcp_server.server"],
    "cwd": "/Users/brock/Documents/GitHub/ai-native-traceability-system",
    "env": {
        "TRACE_DIR": "/Users/brock/Documents/GitHub/ai-native-traceability-system/.trace"
    }
}
```

**Why this works:**
- Uses absolute Python path (Claude Desktop can find it)
- Uses `-m mcp_server.server` to run the module
- Sets `cwd` so Python can import the module
- Keeps TRACE_DIR env variable

## Alternative Solution

Create symlink in a directory that's in Claude Desktop's PATH:

```bash
sudo ln -s /opt/anaconda3/bin/trace-mcp /usr/local/bin/trace-mcp
```

But the explicit Python path is more reliable and matches the pattern of all other working servers.

## Tests Performed

- ✅ trace-mcp exists and is executable
- ✅ Python and MCP imports work
- ✅ Server code is valid (12/12 tests pass)
- ✅ Entry point is sync wrapper (fixed in commit 8b4ed38)
- ✅ Config JSON is valid
- ❌ trace-mcp not in Claude Desktop's PATH

## Recommended Action

Update `~/Library/Application Support/Claude/claude_desktop_config.json`:

**Replace:**
```json
"trace": {
    "command": "trace-mcp",
    "env": {
        "TRACE_DIR": "/Users/brock/Documents/GitHub/ai-native-traceability-system/.trace"
    }
}
```

**With:**
```json
"trace": {
    "command": "/opt/anaconda3/bin/python",
    "args": ["-m", "mcp_server.server"],
    "cwd": "/Users/brock/Documents/GitHub/ai-native-traceability-system",
    "env": {
        "TRACE_DIR": "/Users/brock/Documents/GitHub/ai-native-traceability-system/.trace"
    }
}
```

Then restart Claude Desktop.

## Verification Steps (after fix)

1. Restart Claude Desktop
2. Check logs: `tail -f ~/Library/Logs/Claude/mcp-server-trace.log`
3. Should see: "Server started and connected successfully" WITHOUT "Failed to spawn"
4. In Claude Desktop chat, tools should appear

---

**Status:** Ready to fix - config update needed
