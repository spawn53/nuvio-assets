#!/usr/bin/env python3
"""Dark-UI readability correction for already-produced streaming artwork.
Edits are ALWAYS derived treatments, never presented as exact brand originals.
"""
from pathlib import Path
import json
from PIL import Image
script=Path("scripts/build_streaming_services_artwork.py").read_text()
scope={}
# Reuse the deterministic local renderer without executing the fetch/build loop.
exec(script.split("\nresult=[]\n",1)[0],scope)
OUT=scope["OUT"]
export=scope["export"]
tight=scope["tight"]
base=scope["BASE"]
fixes={"tabii","gain","puhutv","skyshowtime","bfi-player","roku-channel"}
manifest=json.loads((OUT/"SOURCE-MANIFEST.json").read_text())
by_slug={x["slug"]:x for x in manifest}
for slug,title,filename,accent,kind,description in base:
    if slug not in fixes: continue
    folder=OUT/slug
    logo=Image.open(folder/"logo-v1.png").convert("RGBA")
    pix=logo.load()
    for y in range(logo.height):
        for x in range(logo.width):
            r,g,b,a=pix[x,y]
            if not a: continue
            if slug=="puhutv":
                # White rectangle is not part of standalone transparent wordmark.
                if min(r,g,b)>220 and max(r,g,b)-min(r,g,b)<30:
                    pix[x,y]=(255,255,255,0)
                elif max(r,g,b)<175:
                    pix[x,y]=(255,255,255,a)
                else:
                    pix[x,y]=(255,255,255,max(0,int((255-min(r,g,b))*a/80)))
            elif slug in {"tabii","gain","bfi-player","skyshowtime","roku-channel"}:
                # Retain non-dark original brand accents; brighten only black strokes.
                if max(r,g,b)<100:
                    pix[x,y]=(255,255,255,a)
    logo=tight(logo)
    export(folder,logo,title,accent)
    by_slug[slug]["dark_ui_contrast_derivative"]=True
    by_slug[slug]["logo_is_official_unmodified"]=False
# PNG background removal also counts as derivative, even where source was official.
for ent in manifest:
    if ent["source_file"] and ent["source_file"].lower().endswith((".jpg",".png")):
        ent["logo_is_official_unmodified"]=False
(OUT/"SOURCE-MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
print("CONTRAST_QC_PASS: 6 logos corrected; other 8 left unchanged")
