#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_root="$repo_root/.codex/skills"
target_root="${HOME}/.codex/skills"

mkdir -p "$target_root"

for skill_dir in "$skills_root"/chat-pref-*; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  ln -sfnT "$skill_dir" "$target_root/$skill_name"
  printf 'installed %s -> %s\n' "$target_root/$skill_name" "$skill_dir"
done
