#!/usr/bin/env python3
"""Production Studios first-pass audit corrections: Sky Studios is not Sky's slogan."""
from pathlib import Path
import json
from PIL import Image
src=Path("scripts/build_production_studios_artwork.py").read_text()
scope={}
exec(src.split("\nentries=[]\n",1)[0],scope)
root=scope["ROOT"]
manifest=json.loads((root/"SOURCE-MANIFEST.json").read_text())
by={x["slug"]:x for x in manifest}
def update(slug,kind,logo,url,notes,adapted):
    x=by[slug]
    scope["compose"](root/slug,logo,next(z[4] for z in scope["SOURCES"] if z[0]==slug))
    x["classification"]=kind
    x["original_source"]=url
    x["notes"]=notes
    x["contrast_modified"]=adapted
    x["download_errors"]=[]
# The first pass fetched a generic Sky Group slogan "Believe in Better", not Sky Studios.
slug="sky-studios"
update(slug,"alternative",scope["fallback"]("Sky Studios","#82C3F5"),None,
       "Official Sky Studios-specific standalone logo not reliably retrieved; neutral letterform, NOT a Sky Group official logo.",False)
for slug,url,notes in [
    ("itv-studios","https://www.itv.com/presscentre/presscentre/presscentre/media-releases/itv-studios-confirms-new-home-its-award-winning-daytime-shows","First-party ITV Studios press release: ITV Studios logo image"),
    ("pathe","https://www.pathe.com/","First-party Pathé corporate logo, selected from official website")]:
    try:
        logo,origin=scope["official_logo"](url,slug)
        logo,adapted=scope["legible"](logo)
        update(slug,"official-web",logo,origin,notes,adapted)
        print("UPGRADED",slug,origin)
    except Exception as e:
        by[slug]["download_errors"].append("official site retry: "+str(e)[:140])
        print("KEPT_ALTERNATIVE",slug,str(e)[:160])
scope["contact"](manifest)
(root/"SOURCE-MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("STUDIOS_SECOND_PASS_PASS")
