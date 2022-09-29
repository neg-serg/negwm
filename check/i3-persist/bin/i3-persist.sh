#!/bin/sh
# i3-persist 0 extends i3 window management with persistent containers
VERSION=1.0.3
FILE="`readlink -f "$0"`"

print_version () {
  echo "i3-persist version $VERSION"
}

print_help () {
  echo "Syntax: i3-persist [lock|unlock|toggle|kill] [id]"
}

print_invalid () {
  printf "i3-persist: invalid operand\nTry 'i3-persist --help' for more information.\n"
}

# import library
. "`dirname $FILE`/../src/i3-persist-common.sh"

# Main
create_temporary_directory
remove_expired_container_locks

if [ -z "$1" -o "$1" = "--help" ]
then
  print_help
  exit 0
fi

if [ -z "$1" -o "$1" = "--version" ]
then
  print_version
  exit 0
fi

while getopts "vh" opt
do
  case "$opt" in
    v)  print_version
        exit 0
        ;;
    h)  print_help
        exit 0
        ;;
    *)  print_invalid
        exit 1
        ;;
  esac
done


CONTAINER=`argument_or_focused_container "$2"`

if [ "$1" = "lock" ]
then
  lock_container "$CONTAINER"
  exit 0
fi

if [ "$1" = "unlock" ]
then
  unlock_container "$CONTAINER"
  exit 0
fi

if [ "$1" = "toggle" ]
then
  if ! is_container_locked "$CONTAINER"
  then
    lock_container "$CONTAINER"
  else
    unlock_container "$CONTAINER"
  fi
  exit 0
fi

if [ "$1" = "kill" ]
then
  ! is_container_locked "$CONTAINER" && ! has_any_locked_child_containers "$CONTAINER" && i3-msg "[con_id=\"$CONTAINER\"]" kill
  exit 0
fi

print_invalid
exit 1
