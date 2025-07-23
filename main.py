# main.py

import os
import threading
import io
import time
from flask import Flask
import discord
from discord.ext import commands
import pandas as pd
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
EXCEL_URL = os.getenv("EXCEL_URL")

# ——— HEALTH‐CHECK SERVER UNTUK RENDER.COM ————————————————————
app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

def run_health():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

threading.Thread(target=run_health, daemon=True).start()
# ———————————————————————————————————————————————————————

# ——— EXCEL CACHE (5 MENIT) —————————————————————————————
_excel_cache = None
_excel_timestamp = 0
_CACHE_TTL = 300  # detik

async def fetch_excel():
    global _excel_cache, _excel_timestamp
    now = time.time()
    if _excel_cache is None or now - _excel_timestamp > _CACHE_TTL:
        async with aiohttp.ClientSession() as session:
            async with session.get(EXCEL_URL) as resp:
                resp.raise_for_status()
                data = await resp.read()
        _excel_cache = pd.read_excel(io.BytesIO(data), sheet_name="Data", header=None)
        _excel_timestamp = now
    return _excel_cache
# ———————————————————————————————————————————————————————

# ——— DISCORD BOT SETUP ———————————————————————————————————
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

hari_dict = {
    'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
    'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu',
}

pilot_ids = {
    'abuan':'1298923893121351694','acenk':'1064220685611827200','boken':'884138267031781436',
    'chan':'410375555708616706','dansu':'549091908815945764','darrel':'915194622047838229',
    'dendi':'782554583468867584','kyu':'1253017447162712125','naellza':'283210722740011008',
    'rendi':'935586563004456991','robet':'465717181733142529','rotimitsu':'462286148014833684',
    'san':'295531896119492610','adhe':'1357972698948440065','aingwae':'1046077925776171028',
    'alvian':'961456254486741003','amancha':'1119789372661841940','aquaa':'780089709346684968',
    'ari':'605402286931574784','ariefeko':'923233290008268800','asep':'308080448913932298',
    'ayam':'1099044843235328073','bayu':'1175027369464049675','binoy':'568088651666423818',
    'bryn':'1052498777044418600','budi':'906508313452232714','cado':'565319883760336896',
    'dedy':'1354668608508137553','demise':'1375812022645821532','dienzer':'434668876702416896',
    'dylance':'235412551922483200','erickoston':'959679338607964171','faizar':'380772532883685376',
    'finm':'1185550143211192330','fiqry':'450614677911633934','imari':'1031842209152106526',
    'genz':'1096058282570948709','haniel':'322014651040661514','hanif':'573999520598458368',
    'iky':'630381424700030996','jay':'1003647336741883904','irvanh':'1367807282859085824',
    'maron':'734727203203579936','nan':'418014287987212288','nnuday':'353344061471719425',
    'pachul':'1074953978267324466','raply':'401276901328551936','rey':'1371991852290543778',
    'roxy':'934116775946240060','rudy':'1100287172994674749','songel':'442311898357301258',
    'tini':'266527276051595274','orbi':'455407919702212619','vezot':'1344928060159561801',
    'xenk':'355887335440777220','yan':'558301901909786635','yunus':'1344336844032053379',
    'zen':'346173796241244160','zetan':'430677429023932426',
}

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} is now online!")

@bot.command()
async def cek(ctx, *, kode):
    """Cari data kode dan tampilkan informasi gajian."""
    await ctx.send(f"Mencari data untuk kode: `{kode}` …")
    try:
        df = await fetch_excel()
        ki = kode.lower().strip()
        idx = None
        for i in range(0, len(df), 27):
            c = str(df.iloc[i,1]).lower().strip()
            if "/" in c: c = c.split("/")[-1]
            if c == ki:
                idx = i; break
        if idx is None:
            return await ctx.send("❌ Data tidak ditemukan.")

        jenis = "Classic" if ki.startswith("cl") else "Core"
        tc = df.iloc[idx+1,1]
        try:
            to = pd.to_datetime(tc)
            hari = hari_dict[to.strftime("%A")]
            tanggal = f"{hari}, {to.day:02d} {to.strftime('%B')} {to.year}"
        except:
            tanggal = str(tc)

        sc = str(df.iloc[idx+1,10]).strip().lower()
        if sc == "beres": hasil = "✅ BERES"
        elif sc == "belum beres": hasil = "❌ BELUM BERES"
        else: hasil = "❓ STATUS TIDAK DIKENALI"

        lastp = str(df.iloc[idx+17,1]).strip()
        run = "1x Run" if jenis=="Classic" or lastp.lower() in ["","nan"] else "2x Run"

        drops = []
        map_rows = (
            [(idx+9,idx+12),(idx+13,idx+14),(idx+16,idx+17)]
            if jenis=="Classic"
            else [(idx+9,idx+10),(idx+12,idx+13),(idx+15,idx+16)]
        )
        for ir, hr in map_rows:
            for c in range(3,8):
                if ir>=len(df) or hr>=len(df): continue
                itm, hrg = df.iat[ir,c], df.iat[hr,c]
                if pd.notna(itm) and str(itm).strip():
                    s = str(itm).strip()
                    if pd.notna(hrg) and str(hrg).strip():
                        drops.append(f"✅ {s} — 💰 {hrg}")
                    else:
                        drops.append(f"❌ {s}")

        pes = []
        for j in range(8):
            r = idx+10+j
            ign = str(df.iloc[r,0]).strip()
            pil = str(df.iloc[r,1]).strip()
            st_i = 13 if jenis=="Core" else 14
            stn = str(df.iloc[r,st_i]).strip().lower()
            if pd.notna(ign) and ign:
                t = "✅" if stn in ["sudah lunas","lunas"] else ("❌" if stn in ["belum lunas"] else "❓")
                pes.append(f"{t} {ign} ({pil})")

        # Run 2 info (Core) – hanya perbedaan, lewati jika sama
        run2 = ""
        if jenis.lower()=="core" and run=="2x Run":
            rr = []
            for j in range(8):
                b = idx+10+j
                i1 = str(df.iloc[b,0]).strip()
                p1 = str(df.iloc[b,1]).strip()
                i2 = str(df.iloc[b,15]).strip()
                p2 = str(df.iloc[b,16]).strip()
                s2 = str(df.iloc[b,18]).strip().lower()
                if not i2 and not p2: continue
                if i1.lower()==i2.lower() and p1.lower()==p2.lower(): continue
                em = "✅" if s2=="lunas" else ("❌" if s2=="belum lunas" else "❓")
                if i1.lower()!=i2.lower() and p1.lower()==p2.lower():
                    rr.append(f"~~{i1}~~ → {i2}")
                elif i1.lower()==i2.lower() and p1.lower()!=p2.lower():
                    rr.append(f"~~{i1}~~ → {i2} ({p2}) {em}")
                else:
                    rr.append(f"~~{i1} ({p1})~~ → {i2} ({p2}) {em}")
            if rr:
                run2 = "\n**Catatan pergantian run 2:**\n" + "\n".join(rr)

        msg = f"""
📌 Code   : `{ki.upper()}`
📦 Type   : {jenis}
📅 Date   : {tanggal}
💸 Status : {hasil}
🔁 Run    : {run}

🎁 Drop Item:
{chr(10).join(drops)}

👥 Peserta:
{chr(10).join(pes)}{run2}
"""
        await ctx.send(msg)

    except Exception as e:
        await ctx.send("⚠️ Terjadi kesalahan saat memproses data.")
        print(f"❌ Error cek: {e}")

@bot.command()
async def tag(ctx, *, pilot_name):
    key = pilot_name.lower().strip()
    uid = pilot_ids.get(key)
    if uid:
        await ctx.send(f"<@{uid}>")
    else:
        await ctx.send("❌ Pilot tidak ditemukan.")

@bot.command()
async def ping(ctx, *, kode):
    await ctx.send(f"Mengirim ping untuk kode `{kode}`…")
    try:
        df = await fetch_excel()
        ki = kode.lower().strip()
        idx = None
        for i in range(0, len(df), 27):
            c = str(df.iloc[i,1]).lower().strip()
            if "/" in c: c = c.split("/")[-1]
            if c == ki:
                idx = i; break
        if idx is None:
            return await ctx.send("❌ Data tidak ditemukan.")
        tags = []
        for j in range(8):
            p = str(df.iloc[idx+10+j,1]).lower().strip()
            if p in pilot_ids:
                tags.append(f"<@{pilot_ids[p]}>")
        if not tags:
            return await ctx.send("❌ Tidak ada pilot valid.")
        await ctx.send(" ".join(tags))
    except Exception as e:
        await ctx.send("⚠️ Terjadi kesalahan saat memproses ping.")
        print(f"❌ Error ping: {e}")

bot.run(TOKEN)
