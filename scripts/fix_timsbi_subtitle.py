from pathlib import Path
import json
from PIL import Image
source=Path("scripts/upgrade_production_studios_five.py").read_text()
scope={}
exec(source.split("\nsources={",1)[0],scope)
base=Path("production-studios")
slug="tims-and-b"
path=base/slug/"logo-v2.png"
im=Image.open(path).convert("RGBA")
pixels=[]
n=0
for r,g,b,a in im.getdata():
    if a>0 and max(r,g,b)<105:
        pixels.append((246,246,246,a))
        n+=1
    else:pixels.append((r,g,b,a))
assert n>250,"Expected dark subtitling absent; stop"
im.putdata(pixels)
bb=im.getchannel("A").getbbox()
assert bb
scope["save_assets"](slug,im.crop(bb))
manifest_path=base/"SOURCE-UPGRADE-v2.json"
manifest=json.loads(manifest_path.read_text())
ent=next(x for x in manifest if x["slug"]==slug)
ent["black_to_white_dark_ui_adaptation"]=True
ent["contrast_qc"]="PRODUCTIONS subtitle changed from near black to near white; original TIMSBI letterform and gold color preserved"
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
sheet=Image.new("RGB",(1000,350),(16,17,20))
for k,row in enumerate(manifest):
    p=Image.open(base/row["slug"]/"poster-v2.webp")
    sheet.paste(p.resize((200,300)),(k*200,0))
sheet.save(base/"QC-five-studios-v2.webp",quality=90)
print("TIMSBI_SUBTITLE_CONTRAST_PASS",n)
