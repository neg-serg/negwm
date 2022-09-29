#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

if ! command -v shunit2
then
  echo -e "${RED}Please install shunit2 first.$NC"
  exit 1
fi

echo > tests.log

for FILE in tests/*
do
  [ -e $FILE ] || continue
  [ -x $FILE ] && ./"$FILE" | tee -a tests.log
done

if ! grep -q "ASSERT:" tests.log
then
  echo -e "${GREEN}All tests passed!$NC"
  exit 0
fi

echo "--------------------------------------------\n"
echo -e "$RED$(grep -c "ASSERT:" tests.log) tests failed!$NC"
echo "Failed tests:"
grep -B1 "ASSERT:" tests.log | grep -v "ASSERT:" | sed 's/^/- /'

exit 1
