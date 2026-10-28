#!/usr/bin/env bash
# SPDX-License-Identifier: 0BSD
# Store uptime
set -e -o pipefail

download() {
    local link
    link='https://raw.githubusercontent.com/Sekai-World/uptime-monitor/master'
    link+='/history/summary.json'
    local file='./README.md'

    echo '###### sekai.best' > "${file}"
    curl -f "${link}" | grep -m1 '"uptime"' >> "${file}"
}

commit() {
    git config user.name github-actions
    git config user.email github-actions@github.com
    git add "${file}"
    git commit -m "$(date -I)"
    git push
}

main() {
    download
    commit
}

main
