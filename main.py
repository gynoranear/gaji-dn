import os
import discord
from discord.ext import commands
import pandas as pd
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
EXCEL_URL = os.getenv("EXCEL_URL")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

hari_dict = {
    'Monday': 'Senin',
    'Tuesday': 'Selasa',
    'Wednesday': 'Rabu',
    'Thursday': 'Kamis',
    'Friday': 'Jumat',
    'Saturday': 'Sabtu',
    'Sunday': 'Minggu',
}

# Mapping pilot → Discord user ID
pilot_ids = {
    'abuan':      '1298923893121351694',
    'acenk':      '1064220685611827200',
    'boken':      '884138267031781436',
    'chan':       '410375555708616706',
    'dansu':      '549091908815945764',
    'darrel':     '915194622047838229',
    'dendi':      '782554583468867584',
    'kyu':        '1253017447162712125',
    'naellza':    '283210722740011008',
    'rendi':      '935586563004456991',
    'robet':      '465717181733142529',
    'rotimitsu':  '462286148014833684',
    'san':        '295531896119492610',
    'adhe':       '1357972698948440065',
    'aingwae':    '1046077925776171028',
    'alvian':     '961456254486741003',
    'amancha':    '1119789372661841940',
    'aquaa':      '780089709346684968',
    'ari':        '605402286931574784',
    'ariefeko':   '923233290008268800',
    'asep':       '308080448913932298',
    'ayam':       '1099044843235328073',
    'bayu':       '1175027369464049675',
    'binoy':      '568088651666423818',
    'bryn':       '1052498777044418600',
    'budi':       '906508313452232714',
    'cado':       '565319883760336896',
    'dedy':       '1354668608508137553',
    'demise':     '1375812022645821532',
    'dienzer':    '434668876702416896',
    'dylance':    '235412551922483200',
    'erickoston': '959679338607964171',
    'faizar':     '380772532883685376',
    'finm':       '1185550143211192330',
    'fiqry':      '450614677911633934',
    'imari':      '1031842209152106526',
    'genz':       '1096058282570948709',
    'haniel':     '322014651040661514',
    'hanif':      '573999520598458368',
    'iky':        '630381424700030996',
    'jay':        '1003647336741883904',
    'irvanh':     '1367807282859085824',
    'maron':      '734727203203579936',
    'nan':        '418014287987212288',
    'nnuday':     '353344061471719425',
    'pachul':     '1074953978267324466',
    'raply':      '401276901328551936',
    'rey':        '1371991852290543778',
    'roxy':       '934116775946240060',
    'rudy':       '1100287172994674749',
    'songel':     '442311898357301258',
    'tini':       '266527276051595274',
    'orbi':       '455407919702212619',
    'vezot':      '1344928060159561801',
    'xenk':       '355887335440777220',
    'yan':        '558301901909786635',
    'yunus':      '1344336844032053379',
    'zen':        '346173796241244160',
    'zetan':      '430677429023932426',
}

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} is now online!")

@bot.command()
async def cek(ctx, *, kode):
    """Cari data kode dan tampilkan informasi gajian."""
    await ctx.send(f"Mencari data untuk kode: `{kode}` ...")

    try:
        # Ambil data Excel
        async with aiohttp.ClientSession() as session:
            async with session.get(EXCEL_URL) as resp:
                if resp.status != 200:
                    await ctx.send(f"Gagal mengambil data (status {resp.status})")
                    return
                with open("data.xlsx", "wb") as f:
                    f.write(await resp.read())

        df = pd.read_excel("data.xlsx", sheet_name="Data", header=None)
        kode_input = kode.lower().strip()
        indeks_awal = None

        # Cari blok berdasarkan 27 baris
        for i in range(0, len(df), 27):
            cell = str(df.iloc[i,1]).lower().strip()
            if "/" in cell:
                cell = cell.split("/")[-1]
            if cell == kode_input:
                indeks_awal = i
                break

        if indeks_awal is None:
            return await ctx.send("❌ Data tidak ditemukan.")

        jenis = "Classic" if kode_input.startswith("cl") else "Core"

        # Tanggal
        tanggal_cell = df.iloc[indeks_awal + 1, 1]
        try:
            tanggal_obj = pd.to_datetime(tanggal_cell)
            hari = hari_dict[tanggal_obj.strftime("%A")]
            tanggal = f"{hari}, {tanggal_obj.day:02d} {tanggal_obj.strftime('%B')} {tanggal_obj.year}"
        except:
            tanggal = str(tanggal_cell)

        # Status gajian
        status_cell = str(df.iloc[indeks_awal + 1, 10]).strip().lower()
        if status_cell == "beres": hasil = "✅ BERES"
        elif status_cell == "belum beres": hasil = "❌ BELUM BERES"
        else: hasil = "❓ STATUS TIDAK DIKENALI"

        # Peserta dan drop items
        # ... (kode peserta dan drop items tetap sama seperti sebelumnya) ...
        peserta_terakhir = str(df.iloc[indeks_awal + 17, 1]).strip()
        jumlah_run = "1x Run" if jenis == "Classic" or peserta_terakhir.lower() in ["","nan"] else "2x Run"

        # Drop items
        drop_items = []
        if jenis == "Classic":
            item_harga_map = [
                (indeks_awal+9, indeks_awal+12),
                (indeks_awal+13, indeks_awal+14),
                (indeks_awal+16, indeks_awal+17),
            ]
        else:
            item_harga_map = [
                (indeks_awal+9, indeks_awal+10),
                (indeks_awal+12, indeks_awal+13),
                (indeks_awal+15, indeks_awal+16),
            ]
        for item_row, harga_row in item_harga_map:
            for col in range(3,8):
                if item_row>=len(df) or harga_row>=len(df): continue
                item = df.iat[item_row, col]
                harga = df.iat[harga_row, col]
                if pd.notna(item) and str(item).strip():
                    item_str = str(item).strip()
                    if pd.notna(harga) and str(harga).strip():
                        drop_items.append(f"✅ {item_str} — 💰 {harga}")
                    else:
                        drop_items.append(f"❌ {item_str}")

        # Peserta
        peserta = []
        for j in range(8):
            row = indeks_awal + 10 + j
            ign = str(df.iloc[row, 0]).strip()
            pilot = str(df.iloc[row, 1]).strip()
            status_idx = 13 if jenis.lower() == "core" else 14
            status_n = str(df.iloc[row, status_idx]).strip().lower()
            if pd.notna(ign) and ign:
                tanda = "✅" if status_n in ["sudah lunas","lunas"] else ("❌" if status_n in ["belum lunas"] else "❓")
                peserta.append(f"{tanda} {ign} ({pilot})")

        # Run 2 info (Core)
        run2_info = ""
        if jenis.lower() == "core" and jumlah_run == "2x Run":
            run2_repls = []
            for j in range(8):
                base = indeks_awal + 10 + j
                ign1 = str(df.iloc[base,0]).strip()
                pilot1 = str(df.iloc[base,1]).strip()
                ign2 = str(df.iloc[base,15]).strip()
                pilot2 = str(df.iloc[base,16]).strip()
                status2 = str(df.iloc[base,18]).strip().lower()
                if not ign2 and not pilot2: continue
                st = "✅" if status2=="lunas" else ("❌" if status2=="belum lunas" else "❓")
                if ign1.lower()==ign2.lower() and pilot1.lower()!=pilot2.lower():
                    run2_repls.append(f"~~{ign1}~~ → {ign2} ({pilot2}) {st}")
                elif ign1.lower()!=ign2.lower() and pilot1.lower()==pilot2.lower():
                    run2_repls.append(f"~~{ign1}~~ → {ign2}")
                elif ign1.lower()!=ign2.lower() and pilot1.lower()!=pilot2.lower():
                    run2_repls.append(f"~~{ign1} ({pilot1})~~ → {ign2} ({pilot2}) {st}")
            if run2_repls:
                run2_info = "\n**Catatan pergantian run 2:**\n" + "\n".join(run2_repls)

        pesan = f"""
📌 Code   : `{kode_input.upper()}`
📦 Type   : {jenis}
📅 Date   : {tanggal}
💸 Status Gajian : {hasil}
🔁 Run    : {jumlah_run}

🎁 **Drop Item:**
{chr(10).join(drop_items)}

👥 **Peserta:**
{chr(10).join(peserta)}{run2_info}
"""
        await ctx.send(pesan)

    except Exception as e:
        await ctx.send("⚠️ Terjadi kesalahan saat memproses data.")
        print(f"❌ Error: {e}")

@bot.command()
async def tag(ctx, *, pilot_name):
    """Tag Discord user berdasarkan nama pilot."""
    key = pilot_name.lower().strip()
    user_id = pilot_ids.get(key)
    if user_id:
        await ctx.send(f"<@{user_id}>")
    else:
        await ctx.send("❌ Pilot tidak ditemukan. Pastikan penulisan nama benar.")

@bot.command()
async def ping(ctx, *, kode):
    """Tag semua pilot peserta untuk kode tertentu."""
    kode_input = kode.lower().strip()
    await ctx.send(f"Mengirim ping untuk kode `{kode_input}`…")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(EXCEL_URL) as resp:
                if resp.status != 200:
                    await ctx.send(f"Gagal mengambil data (status {resp.status})")
                    return
                with open("data.xlsx", "wb") as f:
                    f.write(await resp.read())
        df = pd.read_excel("data.xlsx", sheet_name="Data", header=None)
        indeks_awal = None
        for i in range(0, len(df), 27):
            cell = str(df.iloc[i,1]).lower().strip()
            if "/" in cell: cell = cell.split("/")[-1]
            if cell == kode_input:
                indeks_awal = i
                break
        if indeks_awal is None:
            return await ctx.send("❌ Data tidak ditemukan.")
        tags = []
        for j in range(8):
            pilot = str(df.iloc[indeks_awal + 10 + j, 1]).lower().strip()
            if pilot and pilot in pilot_ids:
                tags.append(f"<@{pilot_ids[pilot]}>")
        if not tags:
            return await ctx.send("❌ Tidak ada pilot valid untuk di-ping.")
        await ctx.send(" ".join(tags))
    except Exception as e:
        print(f"❌ Error !ping: {e}")
        await ctx.send("⚠️ Terjadi kesalahan saat memproses ping.")

bot.run(TOKEN)
