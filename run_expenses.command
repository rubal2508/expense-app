#!/bin/bash
# ── Change to the folder this script lives in ─────────────────────────────────
cd "$(dirname "$0")"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

echo ""
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo -e "${BOLD}   💰 WhatsApp Expense Parser             ${NC}"
echo -e "${BOLD}══════════════════════════════════════════${NC}"
echo ""

# ── Check Python 3 ────────────────────────────────────────────────────────────
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null && "$candidate" -c "import sys; sys.exit(0 if sys.version_info.major==3 else 1)" 2>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}✗ Python 3 not found.${NC}"
    echo "  Install it from https://www.python.org/downloads/ or via Homebrew:"
    echo "    brew install python"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

# ── Check openpyxl ────────────────────────────────────────────────────────────
if ! "$PYTHON" -c "import openpyxl" &>/dev/null; then
    echo -e "${YELLOW}⚙ openpyxl not found — installing...${NC}"
    "$PYTHON" -m pip install openpyxl --quiet
    if ! "$PYTHON" -c "import openpyxl" &>/dev/null; then
        echo -e "${RED}✗ Failed to install openpyxl. Try running manually:${NC}"
        echo "    pip3 install openpyxl"
        echo ""
        read -p "Press Enter to close..."
        exit 1
    fi
    echo -e "${GREEN}✓ openpyxl installed${NC}"
fi

# ── Check required files ──────────────────────────────────────────────────────
MISSING=0

if [ ! -f "_chat.txt" ]; then
    echo -e "${RED}✗ _chat.txt not found in this folder${NC}"
    MISSING=1
fi

if [ ! -f "parse_expenses.py" ]; then
    echo -e "${RED}✗ parse_expenses.py not found in this folder${NC}"
    MISSING=1
fi

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo "  Make sure these files are in the same folder as this script:"
    echo "    • _chat.txt       (exported from WhatsApp)"
    echo "    • parse_expenses.py"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

# ── Run parser ────────────────────────────────────────────────────────────────
echo -e "  ${BOLD}Chat file :${NC} _chat.txt"
echo -e "  ${BOLD}Output    :${NC} expenses.xlsx"
echo ""

"$PYTHON" parse_expenses.py _chat.txt expenses.xlsx
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}${BOLD}  Done! expenses.xlsx updated.${NC}"
else
    echo -e "${RED}✗ Script exited with error code $EXIT_CODE${NC}"
    echo "  Check the output above for details."
fi

echo ""
read -p "Press Enter to close..."
osascript -e 'tell application "Terminal" to close front window' &
