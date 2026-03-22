#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
state_file="${script_dir}/state.json"
if [[ ! -f "${state_file}" ]]; then
  printf 'mcp-zen-of-docs init (bash) failed: missing state file at %s\n' "${state_file}" >&2
  exit 1
fi
printf 'mcp-zen-of-docs init (bash) completed: %s\n' "${state_file}"
