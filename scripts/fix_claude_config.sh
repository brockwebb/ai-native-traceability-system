#!/bin/bash
# Fix Claude Desktop config to use explicit Python path for trace-mcp

set -e

CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
BACKUP_FILE="$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"

echo "=== Fix Claude Desktop Config for trace-mcp ==="
echo

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Config file not found at $CONFIG_FILE"
    exit 1
fi

# Backup config
echo "1. Creating backup..."
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "   ✓ Backup saved to: $BACKUP_FILE"
echo

# Update config using Python
echo "2. Updating config..."
python3 - <<'PYTHON_SCRIPT'
import json
import sys

config_file = sys.argv[1]

# Read current config
with open(config_file, 'r') as f:
    config = json.load(f)

# Update trace server config
if 'mcpServers' in config and 'trace' in config['mcpServers']:
    config['mcpServers']['trace'] = {
        "command": "/opt/anaconda3/bin/python",
        "args": ["-m", "mcp_server.server"],
        "cwd": "/Users/brock/Documents/GitHub/ai-native-traceability-system",
        "env": {
            "TRACE_DIR": "/Users/brock/Documents/GitHub/ai-native-traceability-system/.trace"
        }
    }
    print("   ✓ Updated trace server config")
else:
    print("   ⚠ Warning: trace server not found in config, adding it")
    if 'mcpServers' not in config:
        config['mcpServers'] = {}
    config['mcpServers']['trace'] = {
        "command": "/opt/anaconda3/bin/python",
        "args": ["-m", "mcp_server.server"],
        "cwd": "/Users/brock/Documents/GitHub/ai-native-traceability-system",
        "env": {
            "TRACE_DIR": "/Users/brock/Documents/GitHub/ai-native-traceability-system/.trace"
        }
    }

# Write updated config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("   ✓ Config file updated")
PYTHON_SCRIPT
echo

# Validate JSON
echo "3. Validating JSON..."
if python3 -c "import json; json.load(open('$CONFIG_FILE'))" 2>/dev/null; then
    echo "   ✓ Config is valid JSON"
else
    echo "   ❌ Error: Config is invalid JSON, restoring backup"
    cp "$BACKUP_FILE" "$CONFIG_FILE"
    exit 1
fi
echo

# Show the trace config
echo "4. New trace config:"
echo "---"
python3 -c "import json; config = json.load(open('$CONFIG_FILE')); print(json.dumps(config['mcpServers']['trace'], indent=2))"
echo "---"
echo

echo "✅ Config updated successfully!"
echo
echo "Next steps:"
echo "1. Restart Claude Desktop"
echo "2. Check logs: tail -f ~/Library/Logs/Claude/mcp-server-trace.log"
echo "3. Look for: 'Server started and connected successfully' (without errors)"
echo
echo "If something goes wrong, restore from backup:"
echo "cp \"$BACKUP_FILE\" \"$CONFIG_FILE\""
