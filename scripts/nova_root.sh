# Resolve the plugin root, wherever nova is installed from.
# Source this, then use "$NOVA_ROOT/scripts/...". Claude Code sets CLAUDE_PLUGIN_ROOT for installed
# plugins; the fallbacks cover a cloned repo, a manual ~/.claude/skills install, and running in-tree.
nova_root() {
  if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/cv_score.py" ]; then
    echo "$CLAUDE_PLUGIN_ROOT"; return 0
  fi
  for c in "${BASH_SOURCE[0]%/*}/.." "$PWD" "$PWD/nova" \
           "$HOME/.claude/plugins/nova" "$HOME/.claude/plugins/marketplaces/nova-cv/nova" \
           "$HOME/.claude/plugins/marketplaces/nova-cv"; do
    [ -f "$c/scripts/cv_score.py" ] && { (cd "$c" && pwd); return 0; }
  done
  c=$(find "$HOME/.claude" -maxdepth 6 -name cv_score.py -path '*/scripts/*' 2>/dev/null | head -1)
  [ -n "$c" ] && { echo "${c%/scripts/cv_score.py}"; return 0; }
  echo "nova: cannot locate plugin root — set CLAUDE_PLUGIN_ROOT" >&2; return 1
}
NOVA_ROOT="$(nova_root)"; export NOVA_ROOT
