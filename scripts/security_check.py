"""Fail if desktop-only business code gains prohibited game-integration APIs."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANNED = (
    "Read" + "ProcessMemory",
    "Write" + "ProcessMemory",
    "Open" + "Process",
    "Create" + "RemoteThread",
    "Virtual" + "QueryEx",
    "packet " + "sniffing",
    "input " + "automation",
)


def main() -> int:
    hits = []
    for path in (ROOT / "app").rglob("*.py"):
        if path == ROOT / "app" / "__init__.py":  # Required boundary comment.
            continue
        text = path.read_text(encoding="utf-8").casefold()
        hits.extend(
            f"{path.relative_to(ROOT)}: {term}"
            for term in BANNED
            if term.casefold() in text
        )
    if hits:
        print("Security boundary violation:\n" + "\n".join(hits))
        return 1
    print("Security boundary check passed: screen pixels and desktop window APIs only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

