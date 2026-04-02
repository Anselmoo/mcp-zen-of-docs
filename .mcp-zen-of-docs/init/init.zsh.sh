#!/usr/bin/env zsh
emulate -L zsh
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "$0")" && pwd -P)"
state_file="${script_dir}/state.json"
if [[ ! -f "${state_file}" ]]; then
  printf 'mcp-zen-of-docs init (zsh) failed: missing state file at %s\n' "${state_file}" >&2
  exit 1
fi
printf 'mcp-zen-of-docs init (zsh) completed: %s\n' "${state_file}"
