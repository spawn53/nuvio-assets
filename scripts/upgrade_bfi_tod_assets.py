#!/usr/bin/env python3
"""Upgrade two streaming logos using first-party and commissioned-designer sources."""
from pathlib import Path
import io, re, json, html
from PIL import Image
import requests
src=Path("scripts/build_streaming_services_artwork.py").read_text()
ns={}
exec(src.split("\nresult=[]\n",1)[0],ns)
OUT=ns["OUT"]; export=ns["export"]; tight=ns["tight"]; SOURCE=OUT/"SOURCE-MANIFEST.json"
manifest=json.loads(SOURCE.read_text())
by={x["slug"]:x for x in manifest}
s=requests.Session();s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; Nuvio artwork source QC/1.0)"})

def fetch_image(url):
    r=s.get(url,timeout=30);r.raise_for_status()
    assert 1500<len(r.content)<12000000, "invalid image payload"
    return Image.open(io.BytesIO(r.content)).convert("RGBA")

# The designer who was commissioned to create BFI Player's identity.
bfi_source="https://d33wubrfki0l68.cloudfront.net/2387c9352d1b9e3dad252ddc90a9e6ff92e72c7d/f4adf/img/projects/bfiplayer/bfi_player_design_logo1.jpg"
try:
    im=fetch_image(bfi_source)
    pix=im.load(); count=0
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=pix[x,y]
            # Designer's stark white logotype isolated from charcoal background.
            bright=min(r,g,b)
            alpha=max(0,min(255,int((bright-93)*255/130)))
            if alpha:count+=1
            pix[x,y]=(255,255,255,alpha)
    if count<im.width*im.height*.01: raise RuntimeError("no logotype detected")
    export(OUT/"bfi-player",tight(im),"BFI Player","#FF4D51")
    by["bfi-player"].update({
        "asset_classification":"designer-source-derived",
        "source_file":"bfi_player_design_logo1.jpg","source_url":bfi_source,
        "source_detail":"Official BFI Player wordmark by British Film Institute-commissioned UFO Studio; charcoal background digitally removed",
        "logo_is_official_unmodified":False,"dark_ui_contrast_derivative":True
    })
    print("BFI_PLAYER_DESIGNER_SOURCE_PASS",flush=True)
except Exception as e:
    print("BFI source upgrade skipped, prior derivative retained:",str(e)[:200],flush=True)

# Digiturk's own Android application, NOT TOD by beIN in the MENA region.
play="https://play.google.com/store/apps/details?id=com.digiturk.tod.mobil&hl=tr"
try:
    page=s.get(play,timeout=30);page.raise_for_status()
    # Google Play lists the application's official icon in open-graph metadata.
    img_url=None
    for tag in re.findall(r'<meta\b[^>]*>',page.text,re.I):
        if re.search(r'property=["\']og:image["\']',tag,re.I):
            mt=re.search(r'content=["\']([^"\']+)',tag)
            if mt:img_url=html.unescape(mt.group(1));break
    if not img_url or not img_url.startswith("https://play-lh.googleusercontent.com/"):
        raise RuntimeError("verified Play Store icon URL not present")
    im=fetch_image(img_url)
    if min(im.size)<200: raise RuntimeError("icon too small")
    pixels=im.load();count=0
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=pixels[x,y]
            # The contemporary Türkiye TOD symbol is golden yellow on near-black.
            yellow=(r>125 and g>85 and r>g*.90 and b<min(175, g*.82))
            if yellow: count+=1
            pixels[x,y]=(r,g,b,a if yellow else 0)
    if count<im.width*im.height*.03:raise RuntimeError("app icon did not contain enough yellow official TOD mark")
    export(OUT/"tod",tight(im),"TOD","#FFC124")
    by["tod"].update({
        "asset_classification":"first-party-app-icon-derived",
        "source_file":"Google Play official Digiturk TOD application icon","source_url":img_url,
        "source_detail":"Official September 2026 Digiturk Türkiye app icon. Yellow logotype digitally isolated; not the TOD MENA identity.",
        "logo_is_official_unmodified":False,"dark_ui_contrast_derivative":True
    })
    print("TOD_TR_OFFICIAL_ICON_PASS",flush=True)
except Exception as e:
    print("TOD source upgrade skipped, prior clearly-labelled alternative retained:",str(e)[:250],flush=True)
SOURCE.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
