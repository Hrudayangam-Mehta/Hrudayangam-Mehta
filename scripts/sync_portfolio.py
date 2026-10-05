"""Copy generated public website files into a local checkout of the user's Portfolio."""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    destination = args.destination.resolve()
    if not (destination / ".git").exists():
        raise SystemExit("Destination must be an existing Git checkout.")
    origin = subprocess.check_output(
        ["git", "-C", str(destination), "remote", "get-url", "origin"], text=True
    ).strip()
    normalized = origin.lower().removesuffix(".git").rstrip("/")
    if not normalized.endswith("hrudayangam-mehta/portfolio"):
        raise SystemExit("Destination is not the Hrudayangam-Mehta/Portfolio repository.")
    source = ROOT / "website"
    copied = []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        # Application-specific CVs are private handoff files, not public site downloads.
        if "anthology" in path.name.lower():
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(str(relative))
    (destination / "MAINTENANCE.txt").write_text(
        "This site is generated from the shared profile source in\n"
        "https://github.com/Hrudayangam-Mehta/Hrudayangam-Mehta\n\n"
        "Edit content/profile.json and content/research-evidence.json there, then run:\n"
        "  python scripts/build_documents.py\n"
        "  python scripts/build_profile.py\n"
        "  python scripts/sync_portfolio.py PATH_TO_THIS_CHECKOUT\n\n"
        "Commit the generated changes here and review the Vercel preview.\n"
        "Production is the main branch of Hrudayangam-Mehta/Portfolio.\n"
        "Do not promote the unrelated chess preview branch.\n",
        encoding="utf-8",
    )
    print("Copied public site files to", destination)
    for path in copied:
        print(" ", path)


if __name__ == "__main__":
    main()
