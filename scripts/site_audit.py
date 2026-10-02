#!/usr/bin/env python3
import re, subprocess, sys, json
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]; errors=[]
html_files=sorted(p for p in ROOT.rglob("*.html") if "admin" not in p.relative_to(ROOT).parts)
all_files={p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
def rel_of(p): return p.relative_to(ROOT).as_posix()
def resolve_path(page,href):
    if href.startswith("/"): return None
    target=(page.parent/href.split("#",1)[0].split("?",1)[0]).resolve()
    try: rel=target.relative_to(ROOT.resolve()).as_posix()
    except ValueError: return None
    return (Path(rel)/"index.html").as_posix() if target.is_dir() else rel
def expected_lang(rel):
    if rel.startswith("en/"): return ("en",)
    if rel.startswith("hi/"): return ("hi","hi-IN")
    if rel.startswith("zh/"): return ("zh","zh-CN","zh-Hans")
    return ("es",)
def logical(rel):
    rel=re.sub(r"^(en|hi|zh)/","",rel)
    return re.sub(r"^guides/","guias/",rel)

for page in html_files:
    text=page.read_text(encoding="utf-8",errors="replace"); rel=rel_of(page)
    if text.lower().count("<!doctype html>")!=1: errors.append(f"{rel}: DOCTYPE")
    if text.lower().count("</html>")!=1: errors.append(f"{rel}: </html>")
    if not re.search(r"<meta[^>]+name=[\"']viewport[\"']",text,re.I): errors.append(f"{rel}: viewport")
    canon_links=re.findall(r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']+)[\"']",text,re.I)
    if len(canon_links)!=1: errors.append(f"{rel}: canonical count")
    elif not canon_links[0].startswith("https://ahorraencasaya.es/"): errors.append(f"{rel}: canonical not on custom domain -> {canon_links[0]}")
    og_url=re.findall(r"<meta[^>]+property=[\"']og:url[\"'][^>]+content=[\"']([^\"']+)[\"']",text,re.I)
    if og_url and canon_links and og_url[0]!=canon_links[0]: errors.append(f"{rel}: og:url differs from canonical")
    if "AhorraEnCasa" in re.sub(r"AhorraEnCasaYa","",text): errors.append(f"{rel}: stale brand AhorraEnCasa")
    if text.lower().split("</html>",1)[-1].strip(): errors.append(f"{rel}: content after </html>")
    if len(re.findall(r"<title>",text,re.I))!=1: errors.append(f"{rel}: title count")
    if len(re.findall(r"<h1\b",text,re.I))!=1: errors.append(f"{rel}: h1 count")
    if not re.search(r'<meta[^>]+name=["\']description["\']',text,re.I): errors.append(f"{rel}: meta description")
    if re.search(r"https?://(?:www\.)?leroymerlin\.es",text,re.I): errors.append(f"{rel}: Leroy Merlin link")
    if re.search(r'''(?:href|src)\s*=\s*["']/[^/][^"']*''',text,re.I): errors.append(f"{rel}: root-absolute internal URL")
    markup=re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>","",text,flags=re.I)
    if re.search(r'href=["\']#["\']',markup,re.I): errors.append(f"{rel}: empty # link")
    m=re.search(r'<html[^>]+lang=["\']([^"\']+)',text,re.I)
    if not m or m.group(1).lower() not in {x.lower() for x in expected_lang(rel)}: errors.append(f"{rel}: wrong lang")
    for j in re.findall(r"<script[^>]+type=[\"']application/ld\\+json[\"'][^>]*>([\\s\\S]*?)</script>",text,re.I):
        try:
            jd=json.loads(j)
            if isinstance(jd,dict) and "inLanguage" in jd and str(jd["inLanguage"]).lower() not in {x.lower() for x in expected_lang(rel)}:
                errors.append(f"{rel}: JSON-LD wrong inLanguage -> {jd['inLanguage']}")
        except Exception:
            pass
    for m in re.finditer(r'''<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>''',text,re.I):
        href=m.group(1).strip(); tag=m.group(0)
        if re.search(r'target=["\']_blank["\']',tag,re.I) and not re.search(r'rel=["\'][^"\']*(?:noopener|noreferrer)',tag,re.I):
            errors.append(f"{rel}: target blank without noopener -> {href}")
        if "amazon.es" in href.lower() and not re.search(r'[?&](?:amp;)?tag=jonelpd-21(?:&|$)',href,re.I):
            errors.append(f"{rel}: Amazon link missing tag -> {href}")
        if href and not href.startswith(("#","mailto:","tel:","javascript:","data:")):
            u=urlparse(href)
            if not u.scheme and not u.netloc:
                target=resolve_path(page,href)
                if target and target not in all_files: errors.append(f"{rel}: broken internal -> {href}")
    for m in re.finditer(r'''<img\b([^>]*)>''',text,re.I):
        attrs=m.group(1); sm=re.search(r'src=["\']([^"\']+)["\']',attrs,re.I)
        if not sm: errors.append(f"{rel}: img without src"); continue
        src=sm.group(1).strip(); am=re.search(r'alt=["\']([^"\']*)["\']',attrs,re.I); hidden=re.search(r'aria-hidden=["\']true["\']',attrs,re.I)
        if not am and not hidden: errors.append(f"{rel}: image missing alt -> {src}")
        if am and not am.group(1).strip() and not hidden: errors.append(f"{rel}: empty alt -> {src}")
        if src.startswith("http://"): errors.append(f"{rel}: insecure image -> {src}")
        if not urlparse(src).scheme and not src.startswith("data:"):
            target=resolve_path(page,src)
            if target and target not in all_files: errors.append(f"{rel}: missing image asset -> {src}")
    for i,script in enumerate(re.findall(r'<script(?![^>]*type=["\']application/ld\+json["\'])(?:\s[^>]*)?>([\s\S]*?)</script>',text,re.I),1):
        if not script.strip(): continue
        tmp=ROOT/".audit-inline.js"; tmp.write_text(script,encoding="utf-8")
        p=subprocess.run(["node","--check",str(tmp)],capture_output=True,text=True); tmp.unlink(missing_ok=True)
        if p.returncode: errors.append(f"{rel}: JS syntax #{i}")
    for j in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',text,re.I):
        try: json.loads(j)
        except Exception as e: errors.append(f"{rel}: invalid JSON-LD {e}")
    if rel.startswith(("en/","hi/","zh/")):
        visible=re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>"," ",text,flags=re.I)
        visible=re.sub(r'''https?://[^\\s\"\'<>]+''', ' ', visible); visible=re.sub(r'\\s+', ' ', visible)
        residue=[r"\bpara empezar\b",r"\bpara resolver\b",r"\bpara comprar\b",r"\bCómo\b",r"\bCalcula(?:r)?\b",r"\bconsumo eléctrico\b",r"\bproductos? para\b",r"\bguías? para\b",r"\bVer guía\b",r"\bLeer guía\b",r"\bVer comparativa\b",r"\bAviso legal\b",r"\bPrivacidad\b",r"\bCookies\b",r"\bInformación reciente\b",r"\bAntes de comprar\b",r"\bAhorra electricidad\b"]
        for pat in residue:
            if re.search(pat,visible,re.I): errors.append(f"{rel}: Spanish residue -> {pat}")

for path in ["data/amazon-products-live.json","data/amazon-products.json","data/news.json"]:
    p=ROOT/path
    if not p.exists(): errors.append(f"{path}: missing")
    else:
        try: json.loads(p.read_text(encoding="utf-8"))
        except Exception as e: errors.append(f"{path}: invalid JSON {e}")

sitemap=ROOT/"sitemap.xml"
if not sitemap.exists(): errors.append("sitemap.xml: missing")
else:
    base="https://ahorraencasaya.es/"; locs=re.findall(r"<loc>([^<]+)</loc>",sitemap.read_text(encoding="utf-8",errors="replace")); got=set()
    for loc in locs:
        if loc.startswith(base):
            r=loc[len(base):]; got.add("index.html" if not r else (r+"index.html" if r.endswith("/") else r))
    if len(locs)!=len(set(locs)): errors.append("sitemap: duplicate loc")
    expected={rel_of(p) for p in html_files if rel_of(p) not in {"404.html", "admin/estadisticas.html"}}
    for x in sorted(expected-got): errors.append(f"sitemap missing -> {x}")
    for x in sorted(got-expected): errors.append(f"sitemap stale -> {x}")

pages={rel_of(p):p for p in html_files}
for rel,page in pages.items():
    text=page.read_text(encoding="utf-8",errors="replace")
    links=re.findall(r"<link[^>]+hreflang=['\"]([^'\"]+)['\"][^>]+href=['\"]([^'\"]+)",text,re.I)
    if rel.startswith(("en/","hi/","zh/")) and "es" not in {x[0].lower() for x in links}:
        errors.append(f"{rel}: missing hreflang es")
    for lang,u in links:
        if u.startswith("https://ahorraencasaya.es/"):
            r=u.split("https://ahorraencasaya.es/",1)[1]
            r="index.html" if not r else (r+"index.html" if r.endswith("/") else r)
            if r not in pages: errors.append(f"{rel}: hreflang target missing -> {u}")

es_paths={logical(r) for r in pages if not r.startswith(("en/","hi/","zh/")) and r != "404.html"}
for lang in ("en","hi","zh"):
    paths={logical(r) for r in pages if r.startswith(lang+"/")}
    for x in sorted(es_paths-paths): errors.append(f"parity {lang} missing -> {x}")
    for x in sorted(paths-es_paths): errors.append(f"parity {lang} extra -> {x}")

if errors:
    print("\n".join(errors)); print(f"\nAUDIT FAILED: {len(errors)} issue(s)"); sys.exit(1)
print(f"AUDIT PASSED: {len(html_files)} HTML files; structure, links, visuals/assets, affiliate markup, JSON, sitemap, language parity and hreflang are clean.")
