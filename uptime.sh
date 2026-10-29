#!/usr/bin/env bash
# SPDX-License-Identifier: 0BSD
# Store uptime
set -e -o pipefail

download() {
    local file="${1}"

    local link
    link='https://raw.githubusercontent.com/Sekai-World/uptime-monitor/master'
    link+='/history/summary.json'

    echo '###### sekai.best\n' > "${file}"
    echo '```' > "${file}"
    curl -f "${link}" | grep -m1 '"uptime"' >> "${file}"
    echo '```' > "${file}"
}

commit() {
    local file="${1}"

    git config user.name github-actions
    git config user.email github-actions@github.com
    git add "${file}"
    git commit -m "$(date -I)"
    git push
}

main() {
    local file='./README.md'
    download "${file}"
    commit "${file}"
}

main
