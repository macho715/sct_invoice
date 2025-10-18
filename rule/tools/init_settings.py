#!/usr/bin/env python3
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

def main():
    ws = ROOT / ".cursor" / "config" / "workspace.json"
    ws.parent.mkdir(parents=True, exist_ok=True)
    if not ws.exists():
        ws.write_text(json.dumps({
            "active_tabs": ["Docs","Rules","Code","Git","Terminals"],
            "docs_default": ["docs/HVDC_INVOICE_README.md","README.md"],
            "rules_path": ".cursor/rules/",
            "git_auto_init": True,
            "terminal_commands": [
                "pytest --maxfail=1 -q",
                "ruff check .",
                "ruff format --check",
                "black --check .",
                "isort --check-only .",
                "bandit -q -r src",
                "pip-audit --strict"
            ]
        }, indent=2))
    if not (ROOT / ".git").exists():
        subprocess.run(["git","init","-b","main"], check=False)
    try:
        subprocess.run([sys.executable,"-m","pip","install","-U","pip","pre-commit","ruff","black","isort","pytest"], check=True)
        subprocess.run(["pre-commit","install"], check=True)
        subprocess.run(["pre-commit","install","--hook-type","commit-msg"], check=True)
    except Exception as e:
        print("[warn] pre-commit setup skipped:", e)
    print("Workspace initialized.")

if __name__ == "__main__":
    main()
