#!/bin/bash
MAIN="bin/i3-persist.sh"

test_invalid_operand_returns_invalid_operand_message () {
  assertTrue "Expected an invalid operand message." "grep -i invalid <($MAIN xyzzy)"
  assertFalse "Expected a non-0 status code" "$MAIN xyzzy"
}

test_no_operand_returns_syntax_message () {
  assertTrue "Expected a syntax message" "grep -i syntax <($MAIN)"
}

. shunit2
