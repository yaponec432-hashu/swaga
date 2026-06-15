#!/usr/bin/env bash
# SPDX-License-Identifier: 0BSD
# Run the bots
set -e

get_master_id() {
    for i in {0..60}; do
        [[ -s "${master_id_file}" ]] && break
        sleep 1
    done
    cat ./master_id
}

main() {
    uv run ./master.py &
    local MASTER_ID
    MASTER_ID="$(get_master_id)"
    MASTER_ID="${MASTER_ID}" uv run ./slave.py
    # TODO: More workers, export
}

main
