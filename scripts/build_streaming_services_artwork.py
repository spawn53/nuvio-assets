#!/usr/bin/env python3
"""Streaming Services (14 folders) artwork builder. All layouts are derivatives.
Do not confuse official source brand logos with platform-issued collection posters.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, io, json, math, re, urllib.parse
import requests
import cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

OUT=Path("streaming-services")
OUT.mkdir(exist_ok=True)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BASE=[
 ("streaming-charts","Streaming Charts",None,"#3CA6FF","editorial", "Independent collection title; no corporate logo"),
 ("new-upcoming-turkiye","New & Upcoming — Türkiye",None,"#ED4361","editorial", "Independent Türkiye discovery collection"),
 ("sundance-now","Sundance Now",None,"#E6DAD0","alternative", "Official 2026 relaunch confirmed; exact reusable 2026 logo file not verified"),
 ("tabii","tabii","Tabii logo.svg","#F1AC36","official-source", "TRT tabii logo; Wikimedia cites TRT"),
 ("gain","GAİN","GAİN LOGO.jpg","#E6DDED","official-source", "GAİN Medya-supplied logo; background removed; check current brand"),
 ("exxen","Exxen","Exxen.png","#F6D624","official-source", "Exxen logo sourced from exxen.com; black background removed"),
 ("puhutv","puhutv","Puhutv logo.svg","#FAA221","official-source", "Wordmark attributed to Puhutv by Wikimedia; secondary fallback available"),
 ("tod","TOD",None,"#A0C8EE","alternative", "Türkiye Digiturk TOD typography, NOT an official sourced logo"),
 ("canal-plus","CANAL+","CanalPlus.svg","#EEEEEE","official-source", "Canal+ logo from Canal+ Group"),
 ("skyshowtime","SkyShowtime","SkyShowtime Logo.svg","#77B4FF","official-source", "SkyShowtime official 2022 vector supplied by Comcast and Paramount"),
 ("britbox","BritBox","BritBox 2026.svg","#94DAF4","official-source", "New 22 January 2026 wordmark; BritBox / Sibling Rivalry"),
 ("bfi-player","BFI Player","BFI Logo.svg","#FF4D51","derived-brand", "Authentic British Film Institute symbol + generated PLAYER text; not official BFI Player logo"),
 ("stan","Stan","Stan logo.svg","#429DFF","official-source", "Official Stan Entertainment vector"),
 ("roku-channel","The Roku Channel","The Roku Channel Logo.svg","#B69AF4","official-source", "Roku, Inc. wordmark"),
]
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"NuvioArtworkResearch/1.0 (noncommercial original-source design; contact https://github.com/spawn53/nuvio-assets)","Accept":"image/svg+xml,image/png,image/jpeg,image/webp,*/*"})

def commons_url(fname):
    fname=fname.replace(" ","_")
    h=hashlib.md5(fname.encode("utf-8")).hexdigest()
    return "https://upload.wikimedia.org/wikipedia/commons/"+h[0]+"/"+h[:2]+"/"+urllib.parse.quote(fname)

def fetch_logo(fname):
    urls=[commons_url(fname)]
    if fname=="Puhutv logo.svg":
        urls += [commons_url("Puhutv.png")]
    errors=[]
    for url in urls:
        try:
            response=SESSION.get(url, timeout=30)
            response.raise_for_status()
            raw=response.content
            if not 100 < len(raw) < 10000000:
                raise ValueError("suspicious file length")
            if b"<svg" in raw[:700]:
                png=cairosvg.svg2png(bytestring=raw,output_width=1500)
                img=Image.open(io.BytesIO(png)).convert("RGBA")
            else:
                img=Image.open(io.BytesIO(raw)).convert("RGBA")
            if min(img.size)<40:
                raise ValueError("source dimensions too small")
            return img,url,errors
        except Exception as exc:
            errors.append(type(exc).__name__+": "+str(exc)[:180])
    raise RuntimeError("; ".join(errors))

def font(size): return ImageFont.truetype(FONT,size)
def hexrgb(s): return tuple(int(s[i:i+2],16) for i in (1,3,5))
def tight(img):
    if img.mode!="RGBA": img=img.convert("RGBA")
    bb=img.getchannel("A").getbbox()
    return img.crop(bb) if bb else img

def strip_flat_background(img):
    # Only process raster logos from media files, not arbitrary SVG vector artwork.
    w,h=img.size
    samples=[img.getpixel((x,y)) for x,y in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]]
    if max(sum(abs(samples[i][j]-samples[0][j]) for j in range(3)) for i in range(4))>65:
        return tight(img)
    bg=samples[0]
    p=img.load()
    for y in range(h):
        for x in range(w):
            rgba=p[x,y]
            dist=max(abs(rgba[i]-bg[i]) for i in range(3))
            if dist<=22:
                p[x,y]=(rgba[0],rgba[1],rgba[2],0)
            elif dist<60:
                p[x,y]=(rgba[0],rgba[1],rgba[2],int(rgba[3]*(dist-22)/38))
    return tight(img)

def wordmark(title,accent,large=False):
    size=104 if large else (99 if len(title)<18 else 64)
    if len(title)>25:size=58
    line=title
    if title=="New & Upcoming — Türkiye":line="NEW & UPCOMING\nTÜRKİYE"
    if title=="Streaming Charts":line="STREAMING\nCHARTS"
    if title=="The Roku Channel":line="THE ROKU CHANNEL"
    lines=line.split("\n")
    f=font(size)
    widths=[int(ImageDraw.Draw(Image.new("RGBA",(1,1))).textbbox((0,0),t,font=f)[2]) for t in lines]
    w=min(1450,max(widths)+110)
    h=round(len(lines)*size*1.22)+60
    out=Image.new("RGBA",(w,h))
    d=ImageDraw.Draw(out)
    for i,t in enumerate(lines):
        bb=d.textbbox((0,0),t,font=f)
        d.text(((w-(bb[2]-bb[0]))/2,20+i*size*1.23),t,font=f,fill=(*hexrgb(accent),255),stroke_width=0)
    return tight(out)

def make_bfi(img):
    # Official BFI mark preserved, PLAYER is derivative typography.
    base=Image.new("RGBA",(1200,500))
    symbol=ImageOps.contain(img,(320,320),Image.Resampling.LANCZOS)
    base.alpha_composite(symbol,(60,90))
    d=ImageDraw.Draw(base)
    d.text((425,170),"PLAYER",fill="white",font=font(142))
    return tight(base)

def protect_dark_wordmark(img):
    img=tight(img.convert("RGBA"))
    thumb=img.resize((max(1,int(img.width/7)),max(1,int(img.height/7))))
    pix=list(thumb.getdata())
    vis=[v for v in pix if v[3]>120]
    if not vis: raise RuntimeError("logo is blank")
    lum=sum(.2126*v[0]+.7152*v[1]+.0722*v[2] for v in vis)/len(vis)
    if lum<67:
        # White outline, marked as visibility adaptation; original color remains inside
        a=img.getchannel("A").filter(ImageFilter.MaxFilter(9))
        outline=Image.new("RGBA",img.size,(255,255,255,0))
        outline.putalpha(a.point(lambda p:int(p*.8)))
        outline.alpha_composite(img)
        return outline,True
    return img,False

def background(w,h,accent):
    c=hexrgb(accent)
    im=Image.new("RGB",(w,h))
    p=im.load()
    for y in range(h):
        for x in range(w):
            u=x/w;v=y/h
            glow=max(0,1-math.sqrt(((u-.51)/.78)**2+((v-.51)/.58)**2))
            strength=(glow**2.5)*.28
            grain=0
            p[x,y]=tuple(int(min(255,10+8*v + c[i]*strength+grain)) for i in range(3))
    return im

def paste_center(bg,mark,wmax,hmax,yfraction=.45):
    mark=ImageOps.contain(mark,(wmax,hmax),Image.Resampling.LANCZOS)
    x=(bg.width-mark.width)//2
    y=int(bg.height*yfraction-mark.height/2)
    bg.paste(mark,(x,y),mark)

def export(asset,logo,title,accent):
    # PNG logo, fully transparent background
    l=Image.new("RGBA",(960,360))
    scale=ImageOps.contain(logo,(840,268),Image.Resampling.LANCZOS)
    l.alpha_composite(scale,((960-scale.width)//2,(360-scale.height)//2))
    l.save(asset/"logo-v1.png",optimize=True)
    p=background(720,1080,accent)
    paste_center(p,logo,650,330,.43)
    p.save(asset/"poster-v1.webp",quality=90,method=6)
    hover=background(1280,720,accent)
    paste_center(hover,logo,1040,340,.52)
    hover.save(asset/"hover-v1.webp",quality=90,method=6)
    for filename,size in [("logo-v1.png",(960,360)),("poster-v1.webp",(720,1080)),("hover-v1.webp",(1280,720))]:
        path=asset/filename
        assert Image.open(path).size==size and path.stat().st_size>1200, str(path)

result=[]
for slug,title,filename,accent,kind,description in BASE:
    asset=OUT/slug
    asset.mkdir(parents=True,exist_ok=True)
    actual_kind=kind
    errors=[]
    origin=None
    if filename:
        try:
            source,origin,errors=fetch_logo(filename)
            if filename.lower().endswith((".jpg",".jpeg",".png")):
                source=strip_flat_background(source)
            logo=source
            if slug=="bfi-player":logo=make_bfi(source)
        except Exception as exc:
            errors.append(str(exc)[:250])
            actual_kind="alternative"
            logo=wordmark(title,accent)
    else:
        logo=wordmark(title,accent)
    logo,adapted=protect_dark_wordmark(logo)
    export(asset,logo,title,accent)
    result.append({
      "slug":slug,"title":title,"asset_classification":actual_kind,
      "source_file":filename,"source_url":origin,"source_detail":description,
      "legibility_outline_added":adapted,"fetch_errors":errors,
      "files":["logo-v1.png","poster-v1.webp","hover-v1.webp"],
      "poster_and_hover_are_original_nuvio_compositions":True,
      "logo_is_official_unmodified":actual_kind=="official-source" and not adapted,
    })
    print(slug,actual_kind,"from",origin or "Nuvio-built alternative",flush=True)
(OUT/"SOURCE-MANIFEST.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert len(result)==14
print("ARTWORK_QC_PASS: 14 sets, 42 files")
