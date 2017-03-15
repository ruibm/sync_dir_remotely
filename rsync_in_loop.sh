#!/bin/bash
#
# Continuously upload a LOCAL_PATH to a REMOTE_PATH using rsync via ssh.
#
# NOTE: SSH connection will be kept alive while only as long as the computer
#       remain connected to the network.

function print_usage() {
  echo "usage: $0 [LOCAL_PATH] [REMOTE_HOST] [REMOTE_PATH] [EXCLUDE_PATHS]*"
}

function die() {
  local MSG=$1
  echo "Life's tough... and the script didn't work with msg=[${MSG}]..."
  exit 42
}

function get_date() {
  date '+%Y-%m-%d %H:%M:%S'
}

function run_rsync_in_loop() {
  local LOCAL_PATH=$1; shift
  local REMOTE_HOST=$1; shift
  local REMOTE_PATH=$1; shift

  if [ ! -d ${LOCAL_PATH} ]; then
    print_usage
    echo "ERROR: Local directory [${LOCAL_PATH}] does not exist."
    exit 84
  fi

  host "$REMOTE_HOST" &> /dev/null
  ERROR_RESOLVING_HOST=$?
  if [ $ERROR_RESOLVING_HOST != 0 ]; then
    print_usage
    echo "ERROR: Cannot resolved hostname [$REMOTE_HOST]."
    exit 63
  fi

  local EXCLUDE_LIST=""
  local EXCLUDE_CMD=""
  while [ $# -gt 0 ]; do
    local NEXT_EXCLUDE="$1"; shift
    EXCLUDE_LIST="${EXCLUDE_LIST} \"${NEXT_EXCLUDE}\""
    EXCLUDE_CMD="${EXCLUDE_CMD} --exclude \"${NEXT_EXCLUDE}\""

    # NOTE(ruibm): Uncomment below for debug.
    # echo $EXCLUDE_CMD
  done

  echo "Will now continously rsync:"
  echo "     FROM: ${HOSTNAME}@${LOCAL_PATH}"
  echo "       TO: ${REMOTE_HOST}@${REMOTE_PATH}"
  if [ ! -z "${EXCLUDE_LIST}" ]; then
    echo "  EXCLUDE:${EXCLUDE_LIST}"
  fi
  echo ""
  read -p "Press enter to continue..."

  local SSH_CONTROL_PATH="${HOME}/.ssh/rsync_in_loop"
  mkdir -p ${SSH_CONTROL_PATH} || die 'Failed to create control path.'
  local SSH_KEEP_ALIVE_SECS=3600
  local SSH_CMD="ssh \
      -6 \
      -o ControlMaster=auto \
      -o ControlPersist=${SSH_KEEP_ALIVE_SECS} \
      -o ControlPath=${SSH_CONTROL_PATH}/%r@%h:%p}"

  local RSYNC_CMD="rsync \
      --archive \
      --human-readable \
      --compress \
      --verbose \
      --delete \
      ${EXCLUDE_CMD} \
      -e \"${SSH_CMD}\" \
      ${LOCAL_PATH} \
      ${USER}@${REMOTE_HOST}:${REMOTE_PATH}"

  # For pretty printing.
  RSYNC_CMD=`echo ${RSYNC_CMD} | sed -e's/  */ /g'`

  while true; do
    echo -e "[$(get_date)] Running command: [${RSYNC_CMD}]..."

    time eval ${RSYNC_CMD} || die 'Failed to run rsync.'

    local SLEEP_SECS=5
    echo -e "[$(get_date)] Sleeping ${SLEEP_SECS} seconds..."
    sleep ${SLEEP_SECS}
  done
}


if [[ $# -ge 3 ]]; then
  # Run with bash arguments.
  run_rsync_in_loop "$@"
else
  print_usage
  exit 21
fi