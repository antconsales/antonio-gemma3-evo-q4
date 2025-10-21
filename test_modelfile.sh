#!/bin/bash
##
# Antonio Gemma3 Evo Q4 - Modelfile Quality Test
# Tests: Math reasoning, bilingual, code generation, logic
##

MODEL_NAME="${1:-antconsales/antonio-gemma3-evo-q4}"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║      🧠 Antonio Modelfile Quality Test v0.5.0                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Testing model: $MODEL_NAME"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASSED=0
FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        echo "   Expected: $2"
        echo "   Got: $3"
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 TEST 1: Simple Greeting (Italian)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(ollama run $MODEL_NAME "Ciao!" 2>/dev/null)
echo "Response: $RESPONSE"
echo -n "Check: Contains 'Antonio'... "

if echo "$RESPONSE" | grep -qi "antonio"; then
    test_result 0
else
    test_result 1 "Contains 'Antonio'" "$RESPONSE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧮 TEST 2: Math Reasoning - Written Numbers (Italian)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(ollama run $MODEL_NAME "Se un cane ha quattro zampe e ne perde una, quante ne ha?" 2>/dev/null)
echo "Full Response:"
echo "┌────────────────────────────────────────────────────────────┐"
echo "$RESPONSE" | sed 's/^/│ /'
echo "└────────────────────────────────────────────────────────────┘"

echo -n "Check 1: Contains 'Ragioniamo'... "
if echo "$RESPONSE" | grep -qi "ragioniamo"; then
    test_result 0
else
    test_result 1 "Step-by-step format" "$RESPONSE"
fi

echo -n "Check 2: Correct answer (3)... "
if echo "$RESPONSE" | grep -q "3"; then
    test_result 0
else
    test_result 1 "Answer = 3" "$RESPONSE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 TEST 3: Bilingual Support (English)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(ollama run $MODEL_NAME "What's your name?" 2>/dev/null)
echo "Response: $RESPONSE"
echo -n "Check: Responds in English... "

if echo "$RESPONSE" | grep -qi "antonio\|my name"; then
    test_result 0
else
    test_result 1 "English response with 'Antonio'" "$RESPONSE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💻 TEST 4: Code Generation (Python)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(ollama run $MODEL_NAME "Scrivi una funzione Python che somma due numeri" 2>/dev/null)
echo "Response preview:"
echo "$RESPONSE" | head -15

echo -n "Check: Contains 'def' or 'python'... "
if echo "$RESPONSE" | grep -qi "def\|python"; then
    test_result 0
else
    test_result 1 "Python code with 'def'" "$RESPONSE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧠 TEST 5: Logic Problem (Trains)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(ollama run $MODEL_NAME "Un treno parte da Milano alle 9:00 e uno da Roma alle 9:30. Vanno alla stessa velocità. Chi arriva prima?" 2>/dev/null)
echo "Response preview:"
echo "$RESPONSE" | head -10

echo -n "Check: Mentions 'Milano' or '9:00'... "
if echo "$RESPONSE" | grep -qi "milano\|9:00"; then
    test_result 0
else
    test_result 1 "Logic reasoning about trains" "$RESPONSE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔢 TEST 6: Advanced Math (Rate Problem)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(ollama run $MODEL_NAME "Se 5 macchine fanno 5 ruote in 5 minuti, quante ruote fanno 100 macchine in 100 minuti?" 2>/dev/null)
echo "Response preview:"
echo "$RESPONSE" | head -15

echo -n "Check: Contains reasoning structure... "
if echo "$RESPONSE" | grep -qi "ragioniamo\|rate\|calcolo"; then
    test_result 0
else
    test_result 1 "Step-by-step rate calculation" "$RESPONSE"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                       📊 TEST SUMMARY                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "   ${GREEN}✓ PASSED: $PASSED${NC}"
echo -e "   ${RED}✗ FAILED: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 ALL TESTS PASSED - Modelfile is production ready!         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠️  Some tests failed - Review Modelfile configuration       ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
