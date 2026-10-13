#!/usr/bin/env python3
"""Five Production Studios brand source upgrade.
All logo shapes taken from named studio's original media kit or current wordmark.
Posters + hovers are Nuvio editorial derivatives, NOT original issued posters.
"""
from pathlib import Path
import io, re, json, hashlib, urllib.parse, zipfile
import requests, cairosvg
from PIL import Image,ImageOps,ImageDraw,ImageFilter

OUT=Path("production-studios")
S=requests.Session()
S.headers.update({"User-Agent":"Nuvio-Artwork-QC/2.0 (https://github.com/spawn53/nuvio-assets)","Accept":"*/*"})
COLORS={"pathe":"#FDC400","sky-studios":"#6AC8FF","itv-studios":"#65A5E9","tims-and-b":"#D7AF6B","bkm-film":"#EE418E"}
def commons(name):
    n=name.replace(" ","_")
    d=hashlib.md5(n.encode("utf-8")).hexdigest()
    return "https://upload.wikimedia.org/wikipedia/commons/"+d[0]+"/"+d[:2]+"/"+urllib.parse.quote(n)
def get(url,timeout=40):
    r=S.get(url,timeout=timeout);r.raise_for_status()
    if not 100<len(r.content)<15_000_000: raise ValueError("source length suspicious")
    return r.content,r.url
def from_bytes(b,url):
    if b"<svg" in b[:5000] or url.split("?")[0].endswith(".svg"):
        b=cairosvg.svg2png(bytestring=b,output_width=1700)
    i=Image.open(io.BytesIO(b)).convert("RGBA")
    if min(i.size)<30:raise ValueError("source too small")
    return i
def remove_flat(i):
    i=i.copy().convert("RGBA")
    w,h=i.size;corners=[i.getpixel((x,y)) for x,y in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]]
    samples=[px for px in corners if px[3]>200]
    if len(samples)<4 or max(max(abs(c[j]-samples[0][j]) for j in range(3)) for c in samples)>35:
        return crop(i)
    bg=samples[0][:3]
    import numpy as np
    a=np.array(i)
    diff=np.abs(a[:,:,:3].astype("int16")-np.array(bg)).max(axis=2)
    opacity=np.minimum(255,np.maximum(0,(diff-20)*255/37)).astype("uint8")
    a[:,:,3]=(a[:,:,3].astype("float32")*opacity.astype("float32")/255).astype("uint8")
    return crop(Image.fromarray(a,"RGBA"))
def crop(i):
    bb=i.getchannel("A").getbbox()
    return i.crop(bb) if bb else i
def darkfix(i):
    import numpy as np
    a=np.array(i)
    vis=a[:,:,3]>100
    if not vis.any():raise ValueError("empty logo")
    dark=(a[:,:,:3].max(axis=2)<100) & vis
    if dark.sum()/vis.sum()>0.32:
        # Brighten ONLY dark lettering on dark UI, keeping other colors.
        a[dark,0:3]=248
        return crop(Image.fromarray(a,"RGBA")),True
    return i,False
def source_pathé():
    attempts=["Pathé Logo.svg","Pathe logo.svg","Path%C3%A9_Logo.svg"]
    errs=[]
    for nm in attempts:
        try:
            url=commons(nm) if "%" not in nm else "https://commons.wikimedia.org/wiki/Special:Redirect/file/"+nm
            b,final=get(url)
            return from_bytes(b,final),url,"brand-original-mirror",{"reference":"https://fr.wikipedia.org/wiki/Path%C3%A9_Films"}
        except Exception as e:errs.append(str(e)[:90])
    raise RuntimeError("Pathé official-shaped logo not retrievable: "+"; ".join(errs))
def source_sky():
    # Authentic Sky Studios mark, third-party mirror; not Sky Group tagline and not Sky Studios Elstree.
    url="https://images.seeklogo.com/logo-png/43/1/sky-studios-logo-png_seeklogo-437793.png"
    b,final=get(url)
    return from_bytes(b,final),url,"brand-original-thirdparty-mirror",{"brand_ref":"https://skygroup.sky/en-gb/about/work-with-us/production","mirror_page":"https://seeklogo.com/vector-logo/437793/sky-studios"}
def source_itv():
    urls=[
      "https://www.itv.com/presscentre/presscentre/presscentre/presscentre/system/files/styles/social/private/2025-02/itv_studios_1.jpg?itok=QRnN3bvG",
      "https://www.itv.com/presscentre/system/files/styles/social/private/2025-02/itv_studios_1.jpg?itok=QRnN3bvG",
    ]
    errs=[]
    for u in urls:
        try:
            b,final=get(u)
            return from_bytes(b,final),u,"first-party-itv-press",{"press_page":"https://www.itv.com/presscentre/media-releases/itv-studios-announces-expanded-roles-its-senior-global-partnerships-team"}
        except Exception as e:errs.append(str(e)[:110])
    raise RuntimeError("ITV press image not retrievable "+" | ".join(errs))
def source_timsbi():
    url=commons("TIMSBI Productions (2026).png")
    b,final=get(url)
    return from_bytes(b,final),url,"first-party-mark-mirror",{"first_party":"https://timsbi.tv/","file_info":"https://commons.wikimedia.org/wiki/File:TIMSBI_Productions_(2026).png","rebrand":"2026 TIMS&B -> TİMSBİ, folder name preserved"}
def source_bkm():
    u="https://bkmonline.net/uploads/2025102715542082282.zip"
    b,final=get(u)
    z=zipfile.ZipFile(io.BytesIO(b))
    names=z.namelist()
    print("BKM OFFICIAL MEDIA KIT:",names,flush=True)
    choices=sorted([n for n in names if n.lower().endswith((".jpg",".jpeg",".png",".webp"))],key=lambda n: (0 if "logo" in n.lower() else 1,0 if n.lower().endswith(".png") else 1,len(n)))
    if not choices:raise RuntimeError("BKM ZIP has no raster image")
    for n in choices:
        try:
            image=from_bytes(z.read(n),n)
            return image,u,"first-party-official-brand-kit",{"media_kit":"https://bkmonline.net/tr/basin-odasi/kurumsal-dokumanlar","member":n,"all_files":names}
        except Exception as e:print("BKM ZIP MEMBER ERROR",n,str(e)[:90])
    raise RuntimeError("No usable BKM logo from ZIP")
def background(w,h,color):
    # Quiet cinematic glow in same family as prior 23 studio posters.
    bg=Image.new("RGB",(w,h),(8,10,15))
    layer=Image.new("RGBA",(w,h))
    d=ImageDraw.Draw(layer)
    rgb=tuple(int(color[i:i+2],16) for i in (1,3,5))
    cx,cy=w//2,int(h*.49)
    for radius in range(int(min(w,h)*.73),60,-40):
        alpha=int(8+14*(1-radius/(min(w,h)*.73)))
        d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=rgb+(alpha,))
    layer=layer.filter(ImageFilter.GaussianBlur(42))
    bg.paste(layer,(0,0),layer)
    return bg
def save_assets(slug,logo):
    folder=OUT/slug;folder.mkdir(exist_ok=True)
    l=Image.new("RGBA",(960,360))
    mark=ImageOps.contain(logo,(860,285),Image.Resampling.LANCZOS)
    l.alpha_composite(mark,((960-mark.width)//2,(360-mark.height)//2))
    l.save(folder/"logo-v2.png",optimize=True)
    for name,w,h,box in [("poster-v2.webp",720,1080,(650,310)),("hover-v2.webp",1280,720,(1130,320))]:
        bg=background(w,h,COLORS[slug])
        logo_fit=ImageOps.contain(logo,box,Image.Resampling.LANCZOS)
        bg.paste(logo_fit,((w-logo_fit.width)//2,(h-logo_fit.height)//2),logo_fit)
        bg.save(folder/name,quality=91,method=6)
    assert all((folder/f).stat().st_size>1700 for f in ("logo-v2.png","poster-v2.webp","hover-v2.webp"))
sources={
 "pathe":source_pathé,
 "sky-studios":source_sky,
 "itv-studios":source_itv,
 "tims-and-b":source_timsbi,
 "bkm-film":source_bkm,
}
res=[]
for slug,fn in sources.items():
    img,url,cls,metadata=fn()
    rawsize=img.size
    cleaned=remove_flat(img)
    adapted,brightened=darkfix(cleaned)
    save_assets(slug,adapted)
    res.append({"slug":slug,"source_classification":cls,"source_url":url,"source_details":metadata,
                "source_resolution":rawsize,"background_removed":True,
                "black_to_white_dark_ui_adaptation":brightened,
                "rendered_files":["poster-v2.webp","logo-v2.png","hover-v2.webp"],
                "studio_logo_based":True,"studio_issued_poster":False})
    print("SOURCE_UPGRADE_PASS",slug,cls,url,rawsize,"adapted",brightened,flush=True)
(OUT/"SOURCE-UPGRADE-v2.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n")
# 5 editorial poster previews
sheet=Image.new("RGB",(1000,350),(16,17,20))
for k,row in enumerate(res):
    p=Image.open(OUT/row["slug"]/"poster-v2.webp")
    thumb=p.resize((200,300))
    sheet.paste(thumb,(k*200,0))
sheet.save(OUT/"QC-five-studios-v2.webp",quality=90)
print("UPGRADE_QC_PASS 5 sets 15 files",flush=True)
