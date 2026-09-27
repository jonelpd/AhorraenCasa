#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
errors=[]

html_files=sorted(ROOT.rglob("*.html"))
all_paths={p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}

def resolve_path(page, href):
    if href.startswith("/"):
        return None
    base=page.parent
    target=(base / href.split("#",1)[0].split("?",1)[0]).resolve()
    try:
        rel=target.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None
    if target.is_dir():
        rel=(Path(rel)/"index.html").as_posix()
    return rel

for page in html_files:
    text=page.read_text(encoding="utf-8", errors="replace")
    rel=page.relative_to(ROOT).as_posix()

    if text.lower().count("<!doctype html>") != 1:
        errors.append(f"{rel}: expected exactly one DOCTYPE")
    if text.lower().count("</html>") != 1:
        errors.append(f"{rel}: expected exactly one </html>")
    tail=text.lower().split("</html>",1)[-1].strip()
    if tail:
        errors.append(f"{rel}: content exists after </html>")
    if re.search(r"https?://(?:www\.)?leroymerlin\.es", text, re.I):
        errors.append(f"{rel}: Leroy Merlin link remains")
    if re.search(r"""(?:href|src)\s*=\s*["']/[^/][^"']*""", text, re.I):
    if re.search(r'href=["\']#["\']', text, re.I):
        errors.append(f"{rel}: empty # link remains")
    if len(re.findall(r"<title>", text, re.I)) != 1:
        errors.append(f"{rel}: expected exactly one <title>")
    if len(re.findall(r"<h1\b", text, re.I)) != 1:
        errors.append(f"{rel}: expected exactly one <h1>")
    if not re.search(r'<meta[^>]+name=["\']description["\']', text, re.I):
        errors.append(f"{rel}: missing meta description")
    for am in re.findall(r'(?:href|src)=["\']([^"\']*amazon\.es[^"\']*)["\']', text, re.I):
        if not re.search(r'[?&]tag=jonelpd-21(?:&|$)', am, re.I):
            errors.append(f"{rel}: Amazon link without tag=jonelpd-21 -> {am}")

        errors.append(f"{rel}: root-absolute internal URL may break on GitHub Pages")
    for m in re.finditer(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", text, re.I):
        href=m.group(1).strip()
        if not href or href.startswith(("#","mailto:","tel:","javascript:","data:")):
            continue
        parsed=urlparse(href)
        if parsed.scheme or parsed.netloc:
            continue
        target=resolve_path(page, href)
        if target and target not in all_paths:
            errors.append(f"{rel}: broken internal link -> {href} (expected {target})")

    scripts=re.findall(r'<script(?![^>]*type=["\']application/ld\+json["\'])(?:\s[^>]*)?>([\s\S]*?)</script>', text, re.I)
    for i,script in enumerate(scripts,1):
        if not script.strip():
            continue
        tmp=ROOT/".audit-inline.js"
        tmp.write_text(script,encoding="utf-8")
        proc=subprocess.run(["node","--check",str(tmp)],capture_output=True,text=True)
        tmp.unlink(missing_ok=True)
        if proc.returncode:
            errors.append(f"{rel}: inline JavaScript #{i} syntax error: {proc.stderr.strip()}")


# Validate sitemap coverage and canonical/hreflang targets.
sitemap_path=ROOT/"sitemap.xml"
if sitemap_path.exists():
    sitemap=sitemap_path.read_text(encoding="utf-8", errors="replace")
    locs=re.findall(r"<loc>([^<]+)</loc>", sitemap)
    base="https://jonelpd.github.io/AhorraenCasa/"
    sitemap_paths=set()
    for loc in locs:
        if loc.startswith(base):
            rel=loc[len(base):]
            sitemap_paths.add((rel+"index.html") if rel.endswith("/") else rel)
    expected={p.as_posix() for p in html_files}
    for missing in sorted(expected-sitemap_paths):
        errors.append(f"sitemap.xml: HTML page missing from sitemap -> {missing}")
    for stale in sorted(sitemap_paths-expected):
        errors.append(f"sitemap.xml: URL does not map to an HTML file -> {stale}")
else:
    errors.append("sitemap.xml: missing")

for page in html_files:
    text=page.read_text(encoding="utf-8", errors="replace")
    rel=page.relative_to(ROOT).as_posix()
    for url in re.findall(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', text, re.I):
        if url.startswith("https://jonelpd.github.io/AhorraenCasa/"):
            target=url.split("https://jonelpd.github.io/AhorraenCasa/",1)[1]
            target=(target+"index.html") if target.endswith("/") else target
            if target not in all_paths:
                errors.append(f"{rel}: canonical target missing -> {url}")
    for url in re.findall(r'<link[^>]+hreflang=["\'][^"\']+["\'][^>]+href=["\']([^"\']+)', text, re.I):
        if url.startswith("https://jonelpd.github.io/AhorraenCasa/"):
            target=url.split("https://jonelpd.github.io/AhorraenCasa/",1)[1]
            target=(target+"index.html") if target.endswith("/") else target
            if target not in all_paths:
                errors.append(f"{rel}: hreflang target missing -> {url}")

if errors:
    print("\n".join(errors))
    print(f"\nAUDIT FAILED: {len(errors)} issue(s)")
    sys.exit(1)

print(f"AUDIT PASSED: {len(html_files)} HTML files checked; internal links, basic HTML structure, Leroy Merlin removal and inline JavaScript syntax are clean.")
