#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
DIST = WEB / "dist"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def find_tsc() -> str:
    local = ROOT / "node_modules" / ".bin" / "tsc"
    if local.exists():
        return str(local)
    found = shutil.which("tsc")
    if found:
        return found
    raise SystemExit("TypeScript compiler not found. Run npm install or install TypeScript 5.8.x.")


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    run([find_tsc(), "-p", str(WEB / "tsconfig.json")])

    taxonomy = json.loads((ROOT / "packages" / "taxonomy" / "taxonomy.json").read_text())
    fixture = json.loads((ROOT / "packages" / "fixtures" / "sb802-demo.json").read_text())
    bootstrap = json.dumps({"taxonomy": taxonomy, "fixture": fixture}, separators=(",", ":"), ensure_ascii=False)
    bootstrap = bootstrap.replace("<", "\\u003c")

    template = (WEB / "template.html").read_text()
    styles = (WEB / "src" / "styles.css").read_text()
    app_js = (DIST / "app.js").read_text()
    html = template.replace("__RI_STYLES__", styles).replace("__RI_BOOTSTRAP__", bootstrap).replace("__RI_APP__", app_js)
    output = DIST / "index.html"
    output.write_text(html)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    (DIST / "SHA256.txt").write_text(f"{digest}  index.html\n")
    print(f"Built {output} ({len(html):,} bytes)")
    print(f"SHA-256 {digest}")


if __name__ == "__main__":
    main()
