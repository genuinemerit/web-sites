"""Check every site's JavaScript (sites/*/static/js/*.js).

This project deliberately has no Node toolchain, so this stands in for a
linter, using a pure-Python parser (esprima, a dev dependency):

  1. Syntax: each file must parse as an ES2017 script. Keeping to ES2017
     also keeps browser support wide.
  2. Policy (design/music.md): no HTML built from strings and no code
     from strings - the tokens innerHTML, outerHTML, insertAdjacentHTML,
     document.write/writeln, eval, `new Function`, and string arguments
     to setTimeout/setInterval are rejected. Checked on the parser's
     tokens, so comments and string contents don't trigger it.

Run via `poetry run` (needs esprima). Exit 0 when clean, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

import esprima

REPO_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = {"innerHTML", "outerHTML", "insertAdjacentHTML", "eval", "writeln"}


def check(path: Path) -> list[str]:
    rel = path.relative_to(REPO_ROOT)
    source = path.read_text(encoding="utf-8")
    try:
        esprima.parseScript(source)
        tokens = esprima.tokenize(source, {"loc": True})
    except esprima.Error as exc:
        return [f"{rel}: not valid ES2017 - {exc}"]
    problems = []
    for i, tok in enumerate(tokens):
        line = tok.loc.start.line
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        after = tokens[i + 2] if i + 2 < len(tokens) else None
        if tok.type == "Identifier" and tok.value in FORBIDDEN:
            problems.append(f"{rel}:{line}: '{tok.value}' is not allowed")
        elif tok.type == "Identifier" and tok.value == "write":
            prev = tokens[i - 2] if i >= 2 else None
            if prev is not None and prev.value == "document":
                problems.append(f"{rel}:{line}: 'document.write' is not allowed")
        elif (
            tok.type == "Keyword"
            and tok.value == "new"
            and nxt is not None
            and nxt.value == "Function"
        ):
            problems.append(f"{rel}:{line}: 'new Function' is not allowed")
        elif (
            tok.type == "Identifier"
            and tok.value in ("setTimeout", "setInterval")
            and nxt is not None
            and nxt.value == "("
            and after is not None
            and after.type in ("String", "Template")
        ):
            problems.append(
                f"{rel}:{line}: {tok.value} with a string argument is not allowed"
            )
    return problems


def main() -> int:
    files = sorted(REPO_ROOT.glob("sites/*/static/js/*.js"))
    problems = [p for f in files for p in check(f)]
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(
        f"JavaScript OK ({len(files)} file(s): ES2017 syntax, no HTML/code from strings)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
