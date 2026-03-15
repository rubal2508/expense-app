#!/bin/bash
cd "$(dirname "$0")"

RED='\033[0;31m'; GREEN='\033[0;32m'; BOLD='\033[1m'; NC='\033[0m'

echo ""
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo -e "${BOLD}   📊 Expense Analyser                    ${NC}"
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo ""

PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null && "$candidate" -c "import sys; sys.exit(0 if sys.version_info.major==3 else 1)" 2>/dev/null; then
        PYTHON="$candidate"; break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}✗ Python 3 not found.${NC}"
    read -p "Press Enter to close..."; exit 1
fi

PYTHONPATH="scripts" "$PYTHON" scripts/analyse_expenses.py "$@"
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}✗ Script exited with error code $EXIT_CODE${NC}"
fi

echo ""
read -p "Press Enter to close..."
osascript -e 'tell application "Terminal" to close front window' &
