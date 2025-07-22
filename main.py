import os
import discord
from discord.ext import commands
import pandas as pd
import aiohttp
from datetime import datetime

from dotenv import load_dotenv
import os

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

@bot.event
async def on_ready():
    print(f"Bot {bot.user} is now online!")

@bot.command()
async def cek(ctx, *, kode):
    await ctx.send(f"Mencari data untuk kode: `{kode}` ...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open("data.xlsx", "wb") as f:
                    f.write(await resp.read())

        df = pd.read_excel("data.xlsx", sheet_name="Data", header=None)

        kode = kode.lower().strip()
        indeks_awal = None

        for i in range(0, len(df), 27):
            kode_cell = str(df.iloc[i, 1]).lower().strip()
            if "/" in kode_cell:
                kode_cell = kode_cell.split("/")[-1]
            if kode_cell == kode:
                indeks_awal = i
                break

        if indeks_awal is None:
            await ctx.send("❌ Data tidak ditemukan.")
            return

        jenis = "Classic" if kode.startswith("cl") else "Core"

        tanggal_cell = df.iloc[indeks_awal + 1, 1]
        try:
            tanggal_obj = pd.to_datetime(str(tanggal_cell))
            hari = hari_dict[tanggal_obj.strftime("%A")]
            tanggal = f"{hari}, {tanggal_obj.strftime('%d %B %Y')}"
        except:
            tanggal = str(tanggal_cell)

        status_cell = str(df.iloc[indeks_awal + 1, 10]).strip().lower()
        if status_cell == "beres":
            hasil = "✅ BERES"
        elif status_cell == "belum beres":
            hasil = "❌ BELUM BERES"
        else:
            hasil = "❓ STATUS TIDAK DIKENALI"

        peserta_terakhir = str(df.iloc[indeks_awal + 17, 1]).strip()
        jumlah_run = "1x Run" if jenis == "Classic" or peserta_terakhir.lower() in ["", "nan"] else "2x Run"

        drop_items = []
        if jenis == "Classic":
            item_harga_map = [
                (indeks_awal + 9, indeks_awal + 12),
                (indeks_awal + 13, indeks_awal + 14),
                (indeks_awal + 16, indeks_awal + 17)
            ]
        else:
            item_harga_map = [
                (indeks_awal + 9, indeks_awal + 10),
                (indeks_awal + 12, indeks_awal + 13),
                (indeks_awal + 15, indeks_awal + 16)
            ]

        for item_row, harga_row in item_harga_map:
            for col in range(3, 8):
                if item_row >= len(df) or harga_row >= len(df):
                    continue
                item = str(df.iloc[item_row, col]).strip()
                if item.lower() not in ["", "nan", "none"]:
                    harga = str(df.iloc[harga_row, col]).strip()
                    if harga.lower() not in ["", "nan", "none"]:
                        drop_items.append(f"✅ {item} — 💰 {harga}")
                    else:
                        drop_items.append(f"❌ {item}")

        peserta = []
        for j in range(8):
            row = indeks_awal + 10 + j
            ign = str(df.iloc[row, 0]).strip()
            pilot = str(df.iloc[row, 1]).strip()
            status_index = 13 if jenis.lower() == "core" else 14
            status_n = str(df.iloc[row, status_index]).strip().lower()
            if ign.lower() not in ["", "nan"]:
                tanda = "✅" if status_n == "sudah lunas" else ("❌" if status_n == "belum lunas" else "❓")
                peserta.append(f"{tanda} {ign} ({pilot})")

        run2_info = ""
        if jenis.lower() == "core" and jumlah_run == "2x Run":
            run2_replacements = []
            for j in range(8):
                row_offset = 10 + j
                ign1 = str(df.iloc[indeks_awal + row_offset, 0]).strip()
                pilot1 = str(df.iloc[indeks_awal + row_offset, 1]).strip()
                ign2 = str(df.iloc[indeks_awal + row_offset, 15]).strip()
                pilot2 = str(df.iloc[indeks_awal + row_offset, 16]).strip()
                status2 = str(df.iloc[indeks_awal + row_offset, 18]).strip().lower()

                ign1_clean = ign1.lower()
                ign2_clean = ign2.lower()
                pilot1_clean = pilot1.lower()
                pilot2_clean = pilot2.lower()

                if ign2_clean in ["", "nan"] and pilot2_clean in ["", "nan"]:
                    continue
                if ign1_clean == ign2_clean and pilot1_clean == pilot2_clean:
                    continue

                status_emoji = "✅" if status2 == "lunas" else ("❌" if status2 == "belum lunas" else "❓")

                if ign1_clean != ign2_clean and pilot1_clean == pilot2_clean:
                    run2_replacements.append(f"~~{ign1}~~ → {ign2}")
                elif ign1_clean == ign2_clean and pilot1_clean != pilot2_clean:
                    run2_replacements.append(f"~~{ign1}~~ → {ign2} ({pilot2}) {status_emoji}")
                elif ign1_clean != ign2_clean and pilot1_clean != pilot2_clean:
                    run2_replacements.append(f"~~{ign1} ({pilot1})~~ → {ign2} ({pilot2}) {status_emoji}")

            if run2_replacements:
                run2_info = "\n**Catatan pergantian run 2:**\n" + "\n".join(run2_replacements)

pesan = f"""
📌 Code   : `{kode.upper()}`
📦 Type   : {jenis}
📅 Date   : {tanggal}
💸 Status Gajian : {hasil}
🔁 Run    : {jumlah_run}

🎁 **Drop Item:**
{chr(10).join(drop_items)}

👥 **Peserta:**
{chr(10).join(peserta)}
{run2_info}
"""

        await ctx.send(pesan)

    except Exception as e:
        await ctx.send("⚠️ Terjadi kesalahan saat memproses data.")
        print(f"Error: {e}")

bot.run(TOKEN)
