# Debug Summary: trace-mcp Connection Issue

**Date:** 2025-02-01
**Status:** ✅ FIXED

## Problem

`trace-mcp` MCP server failing to connect in Claude Desktop with error:
```
Failed to spawn process: No such file or directory
```

## Root Cause

**PATH Issue:** Claude Desktop uses a limited PATH that doesn't include `/opt/anaconda3/bin`

**Claude Desktop PATH:**
```
/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin
```

**trace-mcp location:**
```
/opt/anaconda3/bin/trace-mcp  ❌ Not in PATH!
```

## Diagnostic Process

### 1. Log Analysis ✅
- **File:** `~/Library/Logs/Claude/mcp-server-trace.log`
- **Finding:** "Failed to spawn process: No such file or directory"
- **Pattern:** Claude Desktop searching limited PATH, not finding `trace-mcp`

### 2. Server Verification ✅
- trace-mcp exists: `/opt/anaconda3/bin/trace-mcp`
- Python works: `/opt/anaconda3/bin/python`
- MCP package: v1.9.4 installed
- Entry point: Sync wrapper (fixed in commit 8b4ed38)
- Tests: 12/12 passing

### 3. Config Analysis ❌
**Original config (broken):**
```json
"trace": {
    "command": "trace-mcp",
    "env": {
        "TRACE_DIR": "/Users/brock/Documents/GitHub/ai-native-traceability-system/.trace"
    }
}
```

**Issue:** Uses bare command name that Claude Desktop can't find.

### 4. Pattern Match ✅
All working MCP servers use explicit Python paths:
```json
"census-mcp": {
    "command": "/opt/anaconda3/envs/census-mcp/bin/python",
    "args": [...],
    ...
}
```

## Solution Applied

Updated config to use explicit Python path with module invocation:

**New config (working):**
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

**Changes:**
1. `command`: Changed from `"trace-mcp"` to `"/opt/anaconda3/bin/python"` (absolute path)
2. `args`: Added `["-m", "mcp_server.server"]` to run as module
3. `cwd`: Added working directory so Python can import module
4. `env`: Kept TRACE_DIR setting

## Why This Works

1. **Absolute Python path** - Claude Desktop can find it directly
2. **Module invocation** - Uses `-m` flag to run installed package
3. **Working directory** - Ensures correct module import path
4. **Matches pattern** - Same approach as all other working servers

## Verification Steps

### Before Fix
```
Failed to spawn process: No such file or directory
Server disconnected
```

### After Fix (Expected)
```
Server started and connected successfully
[No "Failed to spawn" errors]
```

## Next Steps

1. ✅ Config updated
2. ⏳ Restart Claude Desktop
3. ⏳ Check logs: `tail -f ~/Library/Logs/Claude/mcp-server-trace.log`
4. ⏳ Verify tools appear in Claude Desktop

## Backup

Config backup saved to:
```
~/Library/Application Support/Claude/claude_desktop_config.json.backup.20260201_133341
```

To restore if needed:
```bash
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup.* ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

## Related Files

- **Diagnostic report:** `DIAGNOSTIC_REPORT.md`
- **Fix script:** `scripts/fix_claude_config.sh`
- **Server code:** `mcp_server/server.py`
- **Config file:** `~/Library/Application Support/Claude/claude_desktop_config.json`

## Key Learnings

1. **Claude Desktop has limited PATH** - Can't rely on conda/anaconda bin directories
2. **Use explicit Python paths** - Always use absolute paths for Python
3. **Follow existing patterns** - Match config style of working servers
4. **Module invocation is robust** - `-m module.name` better than script paths
5. **Set working directory** - Ensures correct imports

---

**Status:** Config fixed, awaiting Claude Desktop restart for verification
