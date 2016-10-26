#!/bin/bash
#
# Continuously upload a LOCAL_PATH to a REMOTE_PATH using rsync via ssh.
#
# NOTE: SSH connection will be kept alive while only as long as the computer
#       remain connected to the network.

function print_usage() {
  echo "usage: $0 [LOCAL_PATH] [REMOTE_HOST] [REMOTE_PATH]"
}

function die() {
  echo "Life's tough... and the script didn't work..."
  exit 42
}

function get_date() {
  date '+%Y-%m-%d %H:%M:%S'
}

function run_rsync_in_loop() {
  local LOCAL_PATH=$1; shift
  local REMOTE_HOST=$1; shift
  local REMOTE_PATH=$1; shift

  local SSH_KEEP_ALIVE_SECS=3600
  local SSH_CMD="ssh \
      -6 \
      -o ControlMaster=auto \
      -o ControlPersist=${SSH_KEEP_ALIVE_SECS} \
      -o ControlPath=${HOME}/.ssh/buck-sync-ctl/%r@%h:%p"

  local RSYNC_CMD="rsync \
      --archive \
      --human-readable \
      --compress \
      --verbose \
      -e \"${SSH_CMD}\" \
      ${LOCAL_PATH} \
      ${USER}@${REMOTE_HOST}:${REMOTE_PATH}"

# For pretty printing.
RSYNC_CMD=`echo ${RSYNC_CMD} | sed -e's/  */ /g'`

  while true; do
    echo -e "[$(get_date)] Running command: [${RSYNC_CMD}]..."

    time eval ${RSYNC_CMD} || die

    local SLEEP_SECS=5
    echo -e "[$(get_date)] Sleeping ${SLEEP_SECS} seconds..."
    sleep ${SLEEP_SECS}
  done
}

if [[ $# -eq 3 ]]; then
  # Run with bash arguments.
  run_rsync_in_loop $1 $2 $3
else
  print_usage
  exit 21
fi