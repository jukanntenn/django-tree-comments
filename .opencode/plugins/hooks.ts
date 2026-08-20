import { extname, resolve } from "node:path"
import type { Plugin } from "@opencode-ai/plugin"

/**
 * OpenCode plugin: PostToolUse formatter.
 *
 * Delegates to prek (the format group, single source of truth) — no formatter
 * logic lives here, so it can never drift from prek/CI. prek discovers the
 * workspace root from cwd and routes the file to the right project formatter.
 *
 * Plugin SDK: packages/plugin/src/index.ts (tool.execute.after)
 * Write/edit tool args: { filePath: string }; apply_patch: { patchText }
 *
 * The Stop-hook lint gate cannot be replicated: OpenCode event hooks are
 * fire-and-forget with no channel to feed a block decision back into the
 * session. Lint enforcement therefore falls back to prek's pre-commit gate
 * and CI.
 */

const PATCH_FILE_RE = /^\*\*\* (?:Update|Add) File: (.+)$/
const PATCH_MOVE_RE = / -> \*\*\* Move to: (.+)$/

// The desktop app launches the sidecar with cwd=$HOME, so anchor on the
// plugin file location (always inside the project) instead of the process cwd.
const PROJECT_ROOT = resolve(import.meta.dir, "../..")

function extractPaths(filePath: string | undefined, patchText: string | undefined): string[] {
  if (filePath) return [filePath]
  if (!patchText) return []
  const paths: string[] = []
  for (const line of patchText.split("\n")) {
    const m = line.match(PATCH_FILE_RE)
    if (!m) continue
    const move = m[1].match(PATCH_MOVE_RE)
    const p = (move ? move[1] : m[1]).trim()
    if (p) paths.push(p)
  }
  return paths
}

export const HooksPlugin: Plugin = async ({ $ }) => {
  return {
    "tool.execute.after": async (input) => {
      if (input.tool !== "write" && input.tool !== "edit" && input.tool !== "apply_patch") return
      const args = (input.args ?? {}) as { filePath?: string; patchText?: string }
      const paths = extractPaths(args.filePath, args.patchText).filter((p) => extname(p))
      if (paths.length === 0) return

      // Best-effort: format via prek, never block the session.
      await $`uv run prek run --group format --files ${paths}`
        .cwd(PROJECT_ROOT)
        .quiet()
        .nothrow()
    },
  }
}
