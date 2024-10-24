#!/usr/bin/env bash

# Enable monitor mode on the network interface which name is saved to the `INTERFACE` environment variable

# Dependencies:
# - Bash;
# - `net-tools` (for `ifconfig`);
# - `wireless-tools` (for `iwconfig`).

# Exit codes:
# 0 - Success
# 1 - Unknown error
# 2 - `INTERFACE` environment variable is not defined
# 3 - Failed to bring the interface down
# 4 - Failed to change the interface mode to monitor
# 5 - Failed to change the interface channel

script_name="$(basename "$0")"

## Log a message to console, optionally exit with a specified exit code
##
## $1 - Optional exit code (can be omitted)
## $* - Log message
log() {
	local exit_code

	if [[ "$1" =~ /[0-9]+/ ]]; then
		exit_code="$1"
		shift
	else
		exit_code='false'
	fi

	local msg="$*"

	if [ -n "$INTERFACE" ]; then
		echo "[$script_name] [$INTERFACE] $msg"
	else
		echo "[$script_name] $msg"
	fi

	if [ "$exit_code" != 'false' ]; then
		exit "$exit_code"
	fi
}

if [ -z "$INTERFACE" ]; then
	# shellcheck disable=SC2016  # Expressions don't expand in single quotes, use double quotes for that.
	log 2 'The `INTERFACE` environment variable is not defined'
fi

ifconfig "$INTERFACE" down || log 3 'Failed to bring the interface down'
iwconfig "$INTERFACE" mode monitor || log 4 'Failed to change the interface mode to monitor'
ifconfig "$INTERFACE" up || log 4 'Failed to bring the interface up'
iwconfig "$INTERFACE" channel 8 || log 5 'Failed to change the interface channel'

log 'Monitor mode enabled'