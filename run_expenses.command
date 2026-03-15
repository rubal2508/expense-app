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

# ── Check required files ──────────────────────────────────────────────────────
MISSING=0

if [ ! -f "resources/main_chat.txt" ]; then
    echo -e "${RED}✗ resources/main_chat.txt not found${NC}"
    MISSING=1
fi

if [ ! -f "scripts/parse_expenses.py" ]; then
    echo -e "${RED}✗ scripts/parse_expenses.py not found${NC}"
    MISSING=1
fi

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo "  Make sure these files are in the same folder as this script:"
    echo "    • resources/main_chat.txt   (exported from WhatsApp)"
    echo "    • scripts/parse_expenses.py"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

# ── Month selection ───────────────────────────────────────────────────────────
DEFAULT_DISPLAY=$(date -v-1m '+%b %y' | tr '[:upper:]' '[:lower:]')   # e.g. "feb 26"
DEFAULT_LABEL=$(date -v-1m '+%b_%Y'   | tr '[:upper:]' '[:lower:]')   # e.g. "feb_2026"

echo -e "  Enter month-year ${YELLOW}(e.g. feb 26)${NC} [default: ${BOLD}${DEFAULT_DISPLAY}${NC}]:"
read -r MONTH_INPUT
MONTH_INPUT="${MONTH_INPUT:-$DEFAULT_DISPLAY}"

# Parse "feb 26" or "feb 2026" → label "feb_2026"
MONTH_PART=$(echo "$MONTH_INPUT" | awk '{print tolower($1)}')
YEAR_PART=$(echo  "$MONTH_INPUT" | awk '{print $2}')
if [ ${#YEAR_PART} -eq 2 ]; then
    YEAR_PART="20${YEAR_PART}"
fi
MONTH_LABEL="${MONTH_PART}_${YEAR_PART}"

# Validate by letting Python parse it
if ! "$PYTHON" -c "from datetime import datetime; datetime.strptime('01_${MONTH_LABEL}', '%d_%b_%Y')" 2>/dev/null; then
    echo -e "${RED}✗ Could not parse '${MONTH_INPUT}' — use a format like 'feb 26' or 'jan 2026'.${NC}"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

EXP_CSV="expenses_${MONTH_LABEL}.csv"
REV_CSV="needs_review_${MONTH_LABEL}.csv"

# ── Run parser ────────────────────────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}Chat file :${NC} resources/main_chat.txt"
echo -e "  ${BOLD}Month     :${NC} ${MONTH_LABEL}"
echo -e "  ${BOLD}Output    :${NC} ${EXP_CSV}  |  ${REV_CSV}"
echo ""

PYTHONPATH="scripts" "$PYTHON" scripts/parse_expenses.py main_chat.txt "$MONTH_LABEL"
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}${BOLD}  Done! ${EXP_CSV} updated.${NC}"
else
    echo -e "${RED}✗ Script exited with error code $EXIT_CODE${NC}"
    echo "  Check the output above for details."
fi

echo ""
read -p "Press Enter to close..."
osascript -e 'tell application "Terminal" to close front window' &
