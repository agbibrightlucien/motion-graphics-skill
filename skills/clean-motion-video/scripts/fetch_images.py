"""Find and download real, free-to-use images for a video (history, places, people, events, objects).

    python -I fetch_images.py <project_dir> "<search>" [--n 6] [--source both|commons|openverse] [--min-width 1200] [--tag beat-id]

- Sources: Wikimedia Commons (best for history: archive photos, paintings, maps, documents) and Openverse
  (indexes Commons, Flickr, museums, NASA, rawpixel public-domain sets...).
- Licences kept: public domain / PDM / CC0 / CC BY (any version). Rejected: NonCommercial, NoDerivatives,
  ShareAlike, "fair use", unknown. CC BY needs a credit: CREDITS.md is written for you.
- Files land in <project>/assets/images/<tag>-<n>.jpg (max 2400 px, JPEG q90), indexed in
  <project>/assets/images/images.json with title, author, licence, source page, size.
- Contact sheet: <project>/assets/images/_sheet-<tag>.jpg, so you can LOOK at what you got before using it.
Downloads are untrusted data: they are only re-encoded with ffmpeg, never opened or executed otherwise.
"""
import json, os, re, subprocess, sys, urllib.parse, urllib.request, html

UA = "clean-motion-video/1.0 (local video tool)"
OK_LIC = re.compile(r"^(public domain|pd|pdm|cc0|cc[- ]?zero|cc[- ]?by(?![- ]?(sa|nc|nd))[- ]?[\d.]*)$", re.I)


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def lic_ok(name):
    n = (name or "").strip().lower().replace("_", " ")
    if any(b in n for b in ("nc", "nd", "sa", "fair use", "non-commercial", "noncommercial")) and not n.startswith("public domain"):
        if re.search(r"\b(nc|nd|sa)\b|fair use|non-?commercial", n):
            return False
    return bool(OK_LIC.match(n)) or n.startswith("public domain") or n in ("cc by", "attribution")


def commons(q, n, minw):
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrsearch": q, "gsrnamespace": 6,
        "gsrlimit": 40, "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 2400})
    pages = json.loads(get(api)).get("query", {}).get("pages", {})
    out = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = html.unescape(re.sub("<[^>]+>", "", md.get("LicenseShortName", {}).get("value", "")))
        if not lic_ok(lic) or ii.get("width", 0) < minw or ii.get("mime") not in ("image/jpeg", "image/png", "image/tiff"):
            continue
        author = html.unescape(re.sub("<[^>]+>", "", md.get("Artist", {}).get("value", "unknown")))[:120].strip()
        out.append({"title": p["title"].replace("File:", ""), "url": ii.get("thumburl") or ii["url"], "page": ii.get("descriptionurl", ""),
                    "author": author, "license": lic, "width": ii["width"], "height": ii["height"], "source": "Wikimedia Commons"})
        if len(out) >= n:
            break
    return out


def openverse(q, n, minw):
    url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q": q, "license": "cc0,pdm,by", "page_size": 20})   # anonymous max is 20 (more -> 401)
    res = json.loads(get(url)).get("results", [])
    out = []
    for r in res:
        if (r.get("width") and r["width"] < minw) or r.get("license") not in ("cc0", "pdm", "by"):
            continue
        lic = {"cc0": "CC0", "pdm": "Public domain", "by": f"CC BY {r.get('license_version', '')}".strip()}[r["license"]]
        out.append({"title": r["title"], "url": r["url"], "page": r.get("foreign_landing_url", ""), "author": r.get("creator") or "unknown",
                    "license": lic, "width": r.get("width") or 0, "height": r.get("height") or 0, "source": f"Openverse/{r.get('source')}"})
        if len(out) >= n:
            break
    return out


def main():
    proj, q = os.path.abspath(sys.argv[1]), sys.argv[2]
    a = sys.argv[3:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    n, src, minw = int(opt("--n", "6")), opt("--source", "both"), int(opt("--min-width", "1200"))
    tag = re.sub(r"[^a-z0-9]+", "-", opt("--tag", q).lower()).strip("-")[:30]
    out = os.path.join(proj, "assets", "images")
    os.makedirs(out, exist_ok=True)
    found = []
    if src in ("both", "commons"):
        try: found += commons(q, n, minw)
        except Exception as e: print("commons search failed:", e)
    if src in ("both", "openverse") and len(found) < n:
        try: found += openverse(q, n - len(found), minw)
        except Exception as e: print("openverse search failed:", e)
    idx_p = os.path.join(out, "images.json")
    idx = json.load(open(idx_p, encoding="utf-8")) if os.path.exists(idx_p) else []
    got = []
    for i, f in enumerate(found, 1):
        name = f"{tag}-{i}.jpg"
        raw = os.path.join(out, "_dl.bin")
        try:
            open(raw, "wb").write(get(f["url"], 60))
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", raw, "-vf",
                            "scale='min(2400,iw)':-2", "-frames:v", "1", "-update", "1", "-q:v", "3", os.path.join(out, name)], check=True)
        except Exception as e:
            print(f"  skip {f['title'][:50]}: {e}"); continue
        finally:
            if os.path.exists(raw): os.remove(raw)
        f.update({"file": f"assets/images/{name}", "query": q, "tag": tag})
        idx = [x for x in idx if x.get("file") != f["file"]] + [f]
        got.append(f)
        print(f"  {name:22s} {f['license']:14s} {f['width']}x{f['height']}  {f['title'][:60]}")
    json.dump(idx, open(idx_p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    lines = ["# Image credits", "", "Use these credits in the video description (CC BY requires it; public domain/CC0 are listed as courtesy).", ""]
    lines += [f"- {x['title']} by {x['author']}, {x['license']}, via {x['source']}: {x['page']}" for x in idx]
    open(os.path.join(out, "CREDITS.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    if got:
        ins = sum((["-i", os.path.join(out, os.path.basename(g["file"]))] for g in got), [])
        k = len(got)
        fc = "".join(f"[{i}:v]scale=480:320:force_original_aspect_ratio=decrease,pad=480:320:(ow-iw)/2:(oh-ih)/2:color=0x222222[v{i}];" for i in range(k))
        fc += "".join(f"[v{i}]" for i in range(k)) + f"hstack=inputs={k}" if k > 1 else fc.rstrip(";").replace("[v0]", "")
        sheet = os.path.join(out, f"_sheet-{tag}.jpg")
        if k > 1:
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ins, "-filter_complex", fc, "-frames:v", "1", sheet])
        print(f"{len(got)} images -> {out}  (look at {os.path.basename(sheet) if k > 1 else got[0]['file']} before using)")
    else:
        print("nothing usable found; try a more concrete search (people, place, year, object)")


if __name__ == "__main__":
    main()
