#!/usr/bin/env python3
"""Build 23 Production Studios Nuvio artwork sets.
Source files are original studio-origin marks when confirmed, not official collection posters.
All poster & hover layouts are original compositions. Never label a fallback as official.
"""
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse
from hashlib import md5
from io import BytesIO
import json, re, time
import requests, cairosvg
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops, ImageFilter

ROOT=Path("production-studios")
ROOT.mkdir(exist_ok=True)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SOURCES=[
# slug, title, origin_kind, filename or official URL, color, backup/notes
("studio-charts","Studio Charts","editorial",None,"#7FADEB","Neutral editorial studio-ranking artwork"),
("amblin-entertainment","Amblin Entertainment","official-web","https://amblin.com/","#80B6DD","Official Amblin site, ET moon silhouette; no Amblin Partners logo substitution"),
("bad-robot","Bad Robot","commons","Bad Robot Productions.svg","#DA3B40","Bad Robot Productions original wordmark"),
("legendary-entertainment","Legendary Entertainment","commons","Legendary Entertainment logo variant.svg","#D2BE91","Legendary Entertainment source attribution www.legendary.com"),
("cbs-studios","CBS Studios","commons","CBS Studios.svg","#72A3EA","CBS Studios logo, not CBS network"),
("skydance","Skydance","commons","Skydance Corporation Dark Logo 2026.svg","#A2CEEE","2026 Skydance corporation brand, not Paramount logo"),
("film4-productions","Film4 Productions","commons","Film4 logo 2018.svg","#FC4C65","Film4 UK/Channel 4 production identity; do not use Hungary Film4"),
("gaumont","Gaumont","commons","Gaumont 2026 (wordmark).svg","#B9D8CF","May 2026 new identity"),
("pathe","Pathé","commons","Pathe logo.svg","#E7B647","Pathé film studio emblem"),
("working-title-films","Working Title Films","official-web","https://www.workingtitlefilms.com/","#82C9CD","Official site says Working Title Logo"),
("toho","Toho","commons","Toho logo.svg","#DFDDD9","Original Toho kanji emblem"),
("cj-enm","CJ ENM / CJ Entertainment","commons","CJ ENM Logo.svg","#CF9ADD","CJ ENM current corporate mark; folder includes CJ Entertainment"),
("sky-studios","Sky Studios","official-web","https://www.skygroup.sky/","#82C3F5","Distinct Sky Studios brand, NOT Sky television network logo"),
("itv-studios","ITV Studios","commons","ITV Studios.svg","#E8AF55","ITV Studios studio identity, not ITV network"),
("fremantle","Fremantle","commons","Fremantle 2018 logo.svg","#E4E4E4","Entertainment production company, not Australian publisher/sports club"),
("banijay","Banijay","commons","Banijay 2020 logo.svg","#E4D7F7","Banijay 2020 brand as described on official site"),
("studio-dragon","Studio Dragon","commons","Studio Dragon LOGO (2022).png","#ED8695","Original Studio Dragon South Korean producer mark"),
("fifth-season","Fifth Season","commons","Fifth Season logo.svg","#DDF2F6","Fifth Season original wordmark"),
("ay-yapim","Ay Yapım","commons","Ay Yapım (2014).png","#DAC8B0","Original mark sourced to ayyapim.com, year 2014"),
("ogm-pictures","OGM Pictures","commons","1599490879 OGM Pictures Logo.jpg","#C8A8E4","Logo source references ogmpictures.com"),
("medyapim","Medyapım","official-web","https://medyapim.com/","#DFDFEA","Official Turkish production company site"),
("tims-and-b","TIMS&B","official-web","https://timsbi.com/","#E4BC72","Company rebranded to TİMSBİ in 2026; folder name retained"),
("bkm-film","BKM Film","official-web","https://www.bkm.com.tr/","#FC9D6F","BKM official corporate studio mark"),
]
S=requests.Session()
S.headers.update({"User-Agent":"NuvioArtworkResearch/1.0 (noncommercial; https://github.com/spawn53/nuvio-assets)","Accept":"image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"})
def commons_url(name):
    name=name.replace(" ","_")
    h=md5(name.encode()).hexdigest()
    return "https://upload.wikimedia.org/wikipedia/commons/"+h[0]+"/"+h[:2]+"/"+quote(name)
def try_image(url):
    r=S.get(url,timeout=22)
    r.raise_for_status()
    if not 90<len(r.content)<12_000_000:raise ValueError("bad length")
    raw=r.content
    if b'<svg' in raw[:5000] or r.headers.get("content-type","").startswith("image/svg"):
        img=Image.open(BytesIO(cairosvg.svg2png(bytestring=raw,output_width=1400))).convert("RGBA")
    else:
        img=Image.open(BytesIO(raw)).convert("RGBA")
    if min(img.size)<35:raise ValueError("source too small")
    return img
def official_logo(origin,slug):
    html=S.get(origin,timeout=23)
    html.raise_for_status()
    soup=BeautifulSoup(html.text,"html.parser")
    scored=[]
    for el in soup.find_all(["img","source","link","meta"]):
        src=el.get("src") or el.get("data-src") or el.get("href") or el.get("content") or ""
        if not src: continue
        txt=" ".join([str(el.get(k,"")) for k in ["alt","title","id","class"]])+" "+src
        full=urljoin(html.url,src)
        host=urlparse(full).netloc.lower()
        if not full.startswith("https://") or not any(t in full.lower() for t in (".svg",".png",".webp",".jpg",".jpeg")):continue
        if any(x in txt.lower() for x in ("movie","post","feature","poster","backdrop","trailer","banner","header-img","photo","social-share")):continue
        score=(6 if "logo" in txt.lower() else 0)+(2 if slug.split("-")[0] in txt.lower() else 0)+(1 if host==urlparse(html.url).netloc.lower() else 0)
        if score>=6:scored.append((score,full))
    for _,src in sorted(set(scored),reverse=True)[:12]:
        try:return try_image(src),src
        except Exception:pass
    raise RuntimeError("No first-party logo asset confidently located on official landing page")
def stripped(img):
    img=img.convert("RGBA")
    bg=img.getpixel((0,0));corners=[img.getpixel((img.width-1,0)),img.getpixel((0,img.height-1)),img.getpixel((img.width-1,img.height-1))]
    if bg[3]>245 and all(max(abs(c[i]-bg[i]) for i in range(3))<25 for c in corners):
        px=img.load()
        for y in range(img.height):
            for x in range(img.width):
                v=px[x,y];diff=max(abs(v[i]-bg[i]) for i in range(3))
                if diff<=20:px[x,y]=(v[0],v[1],v[2],0)
                elif diff<50:px[x,y]=(v[0],v[1],v[2],int(v[3]*(diff-20)/30))
    b=img.getchannel("A").getbbox()
    return img.crop(b) if b else img
def legible(img):
    img=stripped(img)
    a=img.getchannel("A")
    # Preserve real brand mark silhouette. Any brightening is a derivative for dark Nuvio.
    pix=img.load()
    dark=0;nonzero=0
    for y in range(0,img.height,max(1,img.height//130)):
        for x in range(0,img.width,max(1,img.width//130)):
            r,g,b,v=pix[x,y]
            if v>125:
                nonzero+=1
                if max(r,g,b)<105:dark+=1
    if not nonzero:raise RuntimeError("transparent source has no logo")
    if dark/nonzero>.25:
        for y in range(img.height):
            for x in range(img.width):
                r,g,b,v=pix[x,y]
                if v and max(r,g,b)<110:pix[x,y]=(241,244,249,v)
        return img,True
    return img,False
def fallback(title,accent):
    text=title
    if title=="Studio Charts":text="STUDIO\nCHARTS"
    if title=="CJ ENM / CJ Entertainment":text="CJ ENM"
    if title=="Working Title Films":text="WORKING TITLE"
    if title=="Amblin Entertainment":text="AMBLIN\nENTERTAINMENT"
    if title=="TIMS&B":text="TIMS&B"
    if title=="BKM Film":text="BKM FILM"
    if title=="Medyapım":text="MEDYAPIM"
    if title=="Sky Studios":text="SKY STUDIOS"
    size=125 if len(text)<18 else 76
    if len(text)>26:size=61
    f=ImageFont.truetype(FONT,size)
    rows=text.split("\n")
    dummy=ImageDraw.Draw(Image.new("RGBA",(4,4)))
    widths=[dummy.textbbox((0,0),s,font=f)[2] for s in rows]
    w=max(widths)+70;h=int(len(rows)*size*1.35)+50
    img=Image.new("RGBA",(w,h));d=ImageDraw.Draw(img)
    rgb=tuple(int(accent[i:i+2],16) for i in (1,3,5))
    for j,t in enumerate(rows):
        d.text(((w-widths[j])/2,18+j*size*1.26),t,font=f,fill=rgb+(255,))
    return stripped(img)
def create_canvas(w,h,accent):
    bg=Image.new("RGB",(w,h),(8,10,15))
    overlay=Image.new("RGBA",(w,h),(0,0,0,0));d=ImageDraw.Draw(overlay)
    rgb=tuple(int(accent[i:i+2],16) for i in (1,3,5))
    cx=w*.52;cy=h*.48
    for k in range(15,0,-1):
        rr=int(min(w,h)*.82*k/15)
        opacity=int(15*(1-k/15)**1.3)
        d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr), fill=(*rgb,opacity))
    overlay=overlay.filter(ImageFilter.GaussianBlur(max(30,int(w*.08))))
    bg.paste(overlay,(0,0),overlay)
    return bg
def compose(out,logo,accent):
    out.mkdir(parents=True,exist_ok=True)
    logopng=Image.new("RGBA",(960,360))
    thumb=ImageOps.contain(logo,(830,285),Image.Resampling.LANCZOS)
    logopng.alpha_composite(thumb,((960-thumb.width)//2,(360-thumb.height)//2))
    logopng.save(out/"logo-v1.png",optimize=True)
    for name,w,h,maxw,maxh in [("poster-v1.webp",720,1080,666,346),("hover-v1.webp",1280,720,1100,360)]:
        bg=create_canvas(w,h,accent)
        thumb=ImageOps.contain(logo,(maxw,maxh),Image.Resampling.LANCZOS)
        bg.paste(thumb,((w-thumb.width)//2,(h-thumb.height)//2),thumb)
        bg.save(out/name,format="WEBP",quality=89,method=6)
        assert Image.open(out/name).size==(w,h)
def contact(entries):
    cols=6;sw=180;sh=290
    board=Image.new("RGB",(cols*sw,4*sh),(18,18,22))
    d=ImageDraw.Draw(board);f=ImageFont.truetype(FONT,16)
    for i,e in enumerate(entries):
        im=Image.open(ROOT/e["slug"]/"poster-v1.webp").convert("RGB")
        im=ImageOps.contain(im,(172,258))
        x=(i%cols)*sw+(sw-im.width)//2;y=(i//cols)*sh+2
        board.paste(im,(x,y))
        d.text(((i%cols)*sw+4,(i//cols)*sh+262),e["title"][:22],font=f,fill=(245,245,245))
    board.save(ROOT/"QC-contact-sheet.webp",quality=90,method=6)
entries=[]
for slug,title,kind,source,accent,notes in SOURCES:
    origin=None;errors=[];classification=kind
    if kind=="commons":
        try: logo=try_image(commons_url(source));origin=commons_url(source)
        except Exception as exc:
            errors.append(repr(exc)[:220]);classification="alternative";logo=fallback(title,accent)
    elif kind=="official-web":
        try:logo,origin=official_logo(source,slug)
        except Exception as exc:
            errors.append(repr(exc)[:220]);classification="alternative";logo=fallback(title,accent)
    else:logo=fallback(title,accent)
    logo,adapted=legible(logo)
    compose(ROOT/slug,logo,accent)
    entries.append({"slug":slug,"title":title,"classification":classification,
                    "original_source":origin,"intended_source":source,
                    "notes":notes,"contrast_modified":adapted,"download_errors":errors,
                    "poster_and_hover_are_derived_nuvio_compositions":True,
                    "files":["poster-v1.webp","logo-v1.png","hover-v1.webp"]})
    print(f"{slug}: {classification} ({origin or 'Nuvio alternative'})",flush=True)
assert len(entries)==23
contact(entries)
(ROOT/"SOURCE-MANIFEST.json").write_text(json.dumps(entries,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert all((ROOT/e['slug']/f).stat().st_size>1400 for e in entries for f in e["files"])
print("PRODUCTION_STUDIOS_ASSETS_PASS 23 sets / 69 files",flush=True)
