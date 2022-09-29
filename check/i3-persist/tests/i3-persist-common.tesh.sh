#!/bin/bash

. src/i3-persist-common.sh

TMP_DIR="tmp"

function i3-msg () {
  cat get_tree.json
}

test_get_focused_container_id_returns_focused_container_id () {
  assertEquals "$(get_focused_container_id)" 94396249129616
}


test_get_all_container_ids_returns_all_container_ids () {
  local ALL_CONTAINERS

  ALL_CONTAINERS="94396248398608
94396248401328
94396248401824
94396248402320
94396248410688
94396248411184
94396248414304
94396248414800
94396249093696
94396248415296
94396249129616
94396248426880
94396249010768"
  assertEquals "$(get_all_container_ids)" "$ALL_CONTAINERS"
}

test_get_parent_and_all_child_container_ids_returns_parent_and_all_child_container_ids () {
  local ALL_CHILD_CONTAINERS

  ALL_CHILD_CONTAINERS="94396249093696
94396248415296
94396249129616"
  assertEquals "$(get_parent_and_all_child_container_ids 94396249093696)" "$ALL_CHILD_CONTAINERS"
}

test_argument_or_focused_container_returns_argument_if_present () {
  assertEquals "$(argument_or_focused_container 123)" 123
}

test_argument_or_focused_container_returns_focus_if_no_argument () {
  assertEquals "$(argument_or_focused_container)" 94396249129616
}

test_is_container_locked_returns_true_if_locked () {
  create_temporary_directory
  lock_container 123
  assertTrue "is_container_locked 123"
  unlock_container 123
}

test_is_container_locked_returns_false_if_unlocked () {
  create_temporary_directory
  unlock_container 123
  assertTrue "! is_container_locked 123"
}

test_has_any_locked_child_containers_returns_true_if_child_locked () {
  create_temporary_directory
  lock_container 94396249093696
  assertTrue "has_any_locked_child_containers 94396249093696"
  unlock_container 94396249093696
}

test_has_any_locked_child_containers_returns_false_if_children_unlocked () {
  create_temporary_directory
  assertTrue "! has_any_locked_child_containers 94396249093696"
}

. shunit2
