import os
import threading
import io
import time
import asyncio
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
    # (data pilot_id tetap sama seperti punya kamu)
}

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} is now online!")

@bot.command()
@commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
async def cek(ctx, *, kode):
    """Cari data kode dan tampilkan informasi gajian."""
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
            return await ctx.send(f"Mencari data untuk kode: `{kode}` …\n\n❌ Data tidak ditemukan.")

        # ———————————————————————————————————————————————————————
# ——— helper ambil nilai beruntun per +26 baris —————————
def _get_chained_value(df, base_idx, col_idx, start_offset_0_based, step=26):
    """
    Ambil nilai dari (base_idx + start_offset) pada kolom col_idx,
    lalu lanjut +step (default 26 baris) selama masih ada nilai non-kosong.
    Kembalikan nilai terakhir yang non-kosong (stripped).
    """
    r = start_offset_0_based
    last_val = None
    n = len(df)
    while True:
        row = base_idx + r
        if row >= n:
            break
        val = df.iloc[row, col_idx]
        if pd.notna(val) and str(val).strip():
            last_val = str(val).strip()
            r += step
        else:
            break
    return last_val
# ———————————————————————————————————————————————————————

run = "1x Run" if jenis=="Classic" or lastp.lower() in ["","nan"] else "2x Run"

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

        msg = f"Mencari data untuk kode: `{kode}` …\n\n" + f"""
📌 Code   : `{ki.upper()}`
📦 Type   : {jenis}
📅 Date   : {tanggal}
💸 Status : {hasil}
🔁 Run    : {run}
{gaji_block}

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
@commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
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

        batch_size = 5
        for i in range(0, len(tags), batch_size):
            await ctx.send(" ".join(tags[i:i+batch_size]))
            await asyncio.sleep(1)

    except Exception as e:
        await ctx.send("⚠️ Terjadi kesalahan saat memproses ping.")
        print(f"❌ Error ping: {e}")

bot.run(TOKEN)
