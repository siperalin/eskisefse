import discord
from discord.ext import commands
from discord import Intents
import asyncio
import datetime
import random
from datetime import datetime, timezone
import time 
import io
from tkinter import Tk, Label, Frame
from PIL import Image, ImageDraw, ImageFont
import aiohttp
from datetime import datetime, timedelta
from collections import defaultdict
import sqlite3
from discord import AllowedMentions
from datetime import datetime

intents = Intents.default()
intents.message_content = True
intents.members = True


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='-', intents=intents)

conn = sqlite3.connect("voice_activity.db")
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS voice_activity (
    user_id INTEGER,
    join_time TEXT,
    leave_time TEXT,
    duration INTEGER
)
''')
conn.commit()

voice_stats = {}
message_counts = {}

user_voice_sessions = {}
voice_times = defaultdict(dict)  
voice_durations = defaultdict(int)  
afk_users = {}
kesilen_kullanicilar = set()

link_engellenmeyen_role_id = 1360996783399895341  
log_kanal_id = 1358838833000747089
sohbet_kanal_id = 1358841800457978058
hedef_kanal_id = 1358841800457978058
media_log_kanal_id = 1358840805250433084
sil_role_id = 1358493516506075177
kes_role_id = 1358840941997457632
unkes_role_id = 1358840941997457632
nuke_role_id = 1358841063774748943
log_kanal = bot.get_channel(log_kanal_id)


atasozleri = [
    "Azıcık aşım, kaygısız başım.",
    "Ayağını yorganına göre uzat.",
    "Ne ekersen, onu biçersin.",
    "Üzüm üzüme baka baka kararır.",
    "Komşu komşunun külüne muhtaçtır.",
    "Damlaya damlaya göl olur.",
    "Bir elin nesi var, iki elin sesi var.",
    "Sakla samanı, gelir zamanı.",
    "Taş yerinde ağırdır.",
    "İyilik eden iyilik bulur.",
    "Ağaç yaş iken eğilir.",
    "Ak akçe kara gün içindir.",
    "Kervan yolda düzülür.",
    "İyilik eden kötülük bulmaz.",
    "Gülme komşuna, gelir başına.",
    "Sakın ha, denize düşen yılana sarılır.",
    "Gülü seven dikenine katlanır.",
    "Dereyi görmeden paçayı sıvama.",
    "Çay koy geliyorum, demişti… ama gelmedi.",
    "Kahve içmeden karar verme, hata yaparsın.",
    "Sabah 7’de uyanan insan, gönüllü mağdurdur.",
    "Yat kalk şükret, internetin var.",
    "Paran yoksa felsefe yap, bedava kafa açılır.",
    "Sakın deneme, sabah alarmı erteleyerek kazanamazsın.",
    "Dünya yuvarlaktır ama çay bardağı daha önemli.",
    "Evde oturan asla topuklu ayakkabıyla düşmez.",
    "İnsan düşününce yorulur, boşver gitsin.",
    "Kendine gel ama çayını da unutma.",
    "Eğer hâlâ uyanamadıysan... belki de uyumalısın.",
    "İstediğin kadar plan yap, Discord çağırınca gidersin.",
    "Günün sonunda hepimiz yatakta bitiyoruz — düşünme, uyu.",
    "Para mutluluk getirmez ama pizza alır.",
    "Yemek sevmeyenle dost olunmaz.",
    "Yola çıkmadan önce Wi-Fi'ye son bir kez bak."
]


bot_start_time = time.time()

@bot.event
async def on_voice_state_update(member, before, after):
    user_id = member.id
    now = datetime.now(timezone.utc)

    # Kullanıcı kanala girdiğinde
    if before.channel is None and after.channel is not None:
        user_voice_sessions[user_id] = now

    # Kullanıcı kanaldan çıktığında
    elif before.channel is not None and after.channel is None:
        start_time = user_voice_sessions.pop(user_id, None)
        if start_time:
            duration = int((now - start_time).total_seconds())

            if user_id not in voice_activity_db:
                voice_activity_db[user_id] = {"timestamps": []}

            voice_activity_db[user_id]["timestamps"].append((start_time, duration))
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    message_counts[user_id] = message_counts.get(user_id, 0) + 1

    await bot.process_commands(message)


@bot.event
async def on_ready():
    global log_kanal, bot_start_time
    log_kanal = bot.get_channel(log_kanal_id)
    print(f'Bot {bot.user} olarak giriş yaptı!')
    bot_start_time = time.time()  

@bot.command()
async def afk(ctx, *, reason: str = None):
    afk_users[ctx.author.id] = reason or "Sebep belirtilmemiş."
    await ctx.send(f'{ctx.author} artık AFK! Sebep: {reason or "Sebep belirtilmemiş."}')

@bot.command()
async def stat(ctx, member: discord.Member = None):
    member = member or ctx.author

    from datetime import datetime, timedelta, timezone

    embed = discord.Embed(description="📊 İstatistikler yükleniyor...", color=discord.Color.blurple())
    loading_message = await ctx.send(embed=embed)

    now = datetime.now(timezone.utc)

    async def get_message_counts(member, days):
        after = now - timedelta(days=days)
        count = 0
        for channel in ctx.guild.text_channels:
            try:
                async for message in channel.history(after=after, limit=500):
                    if message.author.id == member.id:
                        count += 1
            except (discord.Forbidden, discord.HTTPException):
                continue
        return count

    m1 = await get_message_counts(member, 1)
    m7 = await get_message_counts(member, 7)
    m14 = await get_message_counts(member, 14)

    # Ses süresi verileri (veritabanından çekilir)
    voice_data = await get_voice_data_for_user(member.id)

    def format_duration(seconds):
        if seconds == 0:
            return "Veri yok"
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{int(hours)} saat {int(minutes)} dakika"

    v1 = format_duration(voice_data.get('1d', 0))
    v7 = format_duration(voice_data.get('7d', 0))
    v14 = format_duration(voice_data.get('14d', 0))

    # Embedli istatistik mesajı oluştur
    stat_embed = discord.Embed(
        title=f"{member.display_name} kullanıcısının istatistikleri",
        color=discord.Color.green()
    )
    stat_embed.set_thumbnail(url=member.display_avatar.url)

    stat_embed.add_field(name="📅 Son 1 Gün", value=f"{m1} mesaj", inline=True)
    stat_embed.add_field(name="📆 Son 7 Gün", value=f"{m7} mesaj", inline=True)
    stat_embed.add_field(name="🗓️ Son 14 Gün", value=f"{m14} mesaj", inline=True)

    stat_embed.add_field(name="🔊 Ses (1 Gün)", value=v1, inline=True)
    stat_embed.add_field(name="🔊 Ses (7 Gün)", value=v7, inline=True)
    stat_embed.add_field(name="🔊 Ses (14 Gün)", value=v14, inline=True)

    await loading_message.delete()
    await ctx.send(embed=stat_embed)

import asyncio

voice_activity_db = {
    # user_id: {"timestamps": [(datetime, duration_in_seconds), ...]}
}

async def get_voice_data_for_user(user_id):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    periods = {
        '1d': timedelta(days=1),
        '7d': timedelta(days=7),
        '14d': timedelta(days=14)
    }
    result = {'1d': 0, '7d': 0, '14d': 0}

    entries = voice_activity_db.get(user_id, {}).get("timestamps", [])

    for label, delta in periods.items():
        for ts, duration in entries:
            if ts > now - delta:
                result[label] += duration

    return result

# Veritabanına örnek ses verisi eklemek için (örnek kullanım)
# from datetime import datetime, timezone, timedelta
# voice_activity_db[1234567890] = {
#     "timestamps": [
#         (datetime.now(timezone.utc) - timedelta(days=1), 1800),
#         (datetime.now(timezone.utc) - timedelta(days=3), 7200),
#         (datetime.now(timezone.utc) - timedelta(days=10), 3600),
#     ]
# }

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! Gecikme süresi: {latency}ms')

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)

        embed = discord.Embed(
            title="🔒 Kanal Kilitlendi",
            description=f"{ctx.channel.mention} kanalında artık mesaj gönderilemez.",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Kilitleyen: {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Hata oluştu: {str(e)}")


@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)

        embed = discord.Embed(
            title="🔓 Kanal Açıldı",
            description=f"{ctx.channel.mention} kanalında artık herkes mesaj yazabilir.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Açan: {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Hata oluştu: {str(e)}")


@bot.command()
async def sil(ctx, amount: int):
    if any(role.id == sil_role_id for role in ctx.author.roles):
        await ctx.channel.purge(limit=amount + 1)
    else:
        await ctx.send("Bu komutu kullanmaya yetkiniz yok.")

@bot.command()
async def kes(ctx, user: discord.User):
    if any(role.id == kes_role_id for role in ctx.author.roles):
        kesilen_kullanicilar.add(user.id)
        await ctx.send(f"{user.mention} kullanıcısına kes atıldı!")
    else:
        await ctx.send("Bu komutu kullanmaya yetkiniz yok.")

@bot.command()
async def unkes(ctx, user: discord.User):
    if any(role.id == unkes_role_id for role in ctx.author.roles):
        if user.id in kesilen_kullanicilar:
            kesilen_kullanicilar.remove(user.id)
            await ctx.send(f"{user.mention} kullanıcısının kes durumu kaldırıldı.")
        else:
            await ctx.send(f"{user.mention} kullanıcısına kes atanmış değil.")
    else:
        await ctx.send("Bu komutu kullanmaya yetkiniz yok.")

@bot.command()
async def saril(ctx, user: discord.User):
    embed = discord.Embed(
        title="Sıcacık Sarılma! 🤗",
        description=f"{ctx.author.mention}, {user.mention} kişisine sarildi!",
        color=discord.Color.gold()
    )

    file = discord.File("sarilma.gif", filename="sarilma.gif")
    embed.set_image(url="attachment://sarilma.gif")

    await ctx.send(file=file, embed=embed)



@bot.command()
async def düşman(ctx, member: discord.Member = None):
    author = ctx.author

    if member is None:
        await ctx.send("Lütfen birini etiketle! Örnek: `-düşman @kişi`")
        return

    if member.id == author.id:
        await ctx.send("Kendinle düşman olamazsın... Belki içsel bir savaştasın?")
        return

    düşmanlık_oranı = random.randint(0, 100)
    düşmanlık_seviyesi = ""

    if düşmanlık_oranı >= 90:
        düşmanlık_seviyesi = "👿 Kan davalı gibisiniz lütfen ailenizi öldürmeyin!"
    elif düşmanlık_oranı >= 70:
        düşmanlık_seviyesi = "😠 Bayağı gergin bir ortam var sakınmı olsanız a*."
    elif düşmanlık_oranı >= 40:
        düşmanlık_seviyesi = "😐 Hafif bir gerginlik sezdim sakin olun ."
    elif düşmanlık_oranı >= 10:
        düşmanlık_seviyesi = "🙂 Çok az bir kırgınlık olabilir düzelir ama ."
    else:
        düşmanlık_seviyesi = "🤝 Aranızda düşmanlık yok gibi siz aşıksınız <3 !"

    embed = discord.Embed(
        title="Düşmanlık Ölçer 💢",
        description=f"**{author.display_name}** ile **{member.display_name}** arasındaki düşmanlık oranı:\n\n"
                    f"**%{düşmanlık_oranı}** {düşmanlık_seviyesi}",
        color=discord.Color.red()
    )
    embed.set_thumbnail(url="https://e7.pngegg.com/pngimages/717/227/png-clipart-bing-bong-video-disney-infinity-film-inside-out-anger-pixar-film-thumbnail.png")
    await ctx.send(embed=embed)
@bot.command()
async def ban(ctx, user: discord.User, *, reason: str = None):
    await user.ban(reason=reason)
    await ctx.send(f'{user} banlandı! Sebep: {reason}')

@bot.command()
async def bansay(ctx):
    bans = await ctx.guild.bans()
    await ctx.send(f'Sunucuda {len(bans)} kişi banlanmış.')

@bot.command()
async def kick(ctx, user: discord.User, *, reason: str = None):
    await user.kick(reason=reason)
    await ctx.send(f'{user} sunucudan atıldı! Sebep: {reason}')

@bot.command()
async def nuke(ctx):
    if any(role.id == nuke_role_id for role in ctx.author.roles):
        kanal_adi = ctx.channel.name
        kategori = ctx.channel.category
        await ctx.channel.delete()
        yeni_kanal = await ctx.guild.create_text_channel(kanal_adi, category=kategori)
        await yeni_kanal.send("💣 Kanal yeniden oluşturuldu (nuke edildi)!")
    else:
        await ctx.send("Bu komutu kullanmaya yetkiniz yok.")

@bot.command()
async def otorol(ctx, role: discord.Role):
    await ctx.send(f'{role} rolü ayarlandı.')

class TicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🎫 Ticket Oluştur", style=discord.ButtonStyle.green, custom_id="ticket_button")

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild

        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}")
        if existing_channel:
            await interaction.response.send_message("Zaten açık bir ticket kanalınız var.", ephemeral=True)
            return

        kategori = discord.utils.get(guild.categories, name="Tickets")
        if not kategori:
            kategori = await guild.create_category("Tickets")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        ticket_kanal = await guild.create_text_channel(f"ticket-{user.name}", category=kategori, overwrites=overwrites)
        tarih = datetime.now().strftime("%d %B %Y %H:%M")

        ticket_embed = discord.Embed(
            title="🎫 Destek Talebi",
            description=(f"{user.mention} tarafından **{tarih}** tarihinde oluşturuldu.\n\n"
                         f"Talep üzerinde işlem yapmak için aşağıdaki butonu kullanabilirsiniz."),
            color=discord.Color.blurple()
        )

        view = discord.ui.View(timeout=None)
        view.add_item(CloseButton())

        await ticket_kanal.send(embed=ticket_embed, view=view)
        await interaction.response.send_message(f"{ticket_kanal.mention} kanalında ticket oluşturuldu!", ephemeral=True)

# --- Ticket Kapatma Butonu ---
class CloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="❌ Ticket Kapat", style=discord.ButtonStyle.red, custom_id="close_button")

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("Bu butonu kullanma izniniz yok.", ephemeral=True)
            return
        await interaction.response.send_message("Ticket kapatılsın mı?", view=ConfirmCloseView(), ephemeral=True)

# --- Onaylama View ve Butonları ---
class ConfirmCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ConfirmButton())
        self.add_item(CancelButton())

class ConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="✅ Evet", style=discord.ButtonStyle.green, custom_id="confirm_close")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ticket kapanıyor...", ephemeral=True)
        await interaction.channel.delete()

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="❌ Hayır", style=discord.ButtonStyle.red, custom_id="cancel_close")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ticket kapatma işlemi iptal edildi.", ephemeral=True)

# --- Ticket Komutu ---
@bot.command()
async def ticket(ctx):
    embed = discord.Embed(
        title="🎟️ Destek Sistemi",
        description="Aşağıdaki butona tıklayarak destek talebi oluşturabilirsin.",
        color=discord.Color.green()
    )

    view = discord.ui.View(timeout=None)
    view.add_item(TicketButton())

    await ctx.send(embed=embed, view=view)

# --- Kalıcı View Kayıt ---
@bot.event
async def on_ready():
    bot.add_view(discord.ui.View(timeout=None).add_item(TicketButton()))  
    print(f"{bot.user} olarak giriş yapıldı.")
@bot.command()
async def atasözü(ctx):
    secilen = random.choice(atasozleri)
    embed = discord.Embed(
        title="🧠 Günün (Gerçek ya da Yalancı) Atasözü",
        description=f"> *{secilen}*",
        color=discord.Color.random()
    )
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_channels=True)
async def ticketkapat(ctx):
    if ctx.channel.category and ctx.channel.category.name == "Tickets":
        await ctx.send("Ticket kapatılıyor...")
        await asyncio.sleep(2)
        await ctx.channel.delete()
    else:
        await ctx.send("Bu komut sadece ticket kanallarında kullanılabilir.")

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="genel")  
    if channel:
        embed = discord.Embed(
            title="👋 Hoşgeldin!",
            description=(
                f"Merhaba {member.mention}, sunucumuza hoş geldin!\n"
                "Seninle birlikte daha da güçlüyüz. Kuralları okumayı ve tanıtım kanallarını ziyaret etmeyi unutma!\n\n"
                "🎉 Keyifli vakit geçirmen dileğiyle!"
            ),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text="İsveç Sunucusu | Hoş Geldin Mesajı")
        await channel.send(embed=embed)

@bot.command()
async def botbilgi(ctx):
    # Çalışma süresi hesaplama
    uptime_seconds = time.time() - bot_start_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)

    embed = discord.Embed(
        title="Bot Bilgisi",
        description="Botun istatistikleri ve bilgileri:",
        color=discord.Color.blurple()
    )
    embed.add_field(name="💻 Bot Sahibi", value="Sahip: Asex", inline=True)
    embed.add_field(name="🕒 Çalışma Süresi", value=f"{hours} saat {minutes} dakika {seconds} saniye", inline=True)
    embed.add_field(name="📦 Sunucu Sayısı", value=len(bot.guilds), inline=True)
    embed.add_field(name="📈 Kullanıcı Sayısı", value=len(set(bot.get_all_members())), inline=True)
    embed.set_footer(text="Bot Bilgi Sistemi")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def önerikanalbilgi(ctx):
    oneri_kanal_id = 1360643719287800071  # Buraya öneri kanalının ID'sini yaz
    kanal = bot.get_channel(oneri_kanal_id)

    if kanal is None:
        await ctx.send("❗ Belirttiğin kanal bulunamadı. ID doğru mu?")
        return

    embed = discord.Embed(
        title="📬 Öneri Sistemi",
        description=(
            "Sunucu ile ilgili fikirlerin, geliştirme önerilerin ya da eğlenceli düşüncelerin mi var?\n"
            "Aşağıdaki komutu kullanarak direkt geliştiriciye önerini iletebilirsin!\n\n"
            "🔹 **Komut:** `-öneri <mesaj>`\n"
            "💡 Örnek: `-öneri Eğlence komutlarına tombala eklenebilir.`\n\n"
            "Geri bildirimlerin bizim için çok değerli! ❤️"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="Geliştiriciye özel olarak DM'den iletilir.")
    await kanal.send(embed=embed)
    await ctx.send("✅ Bilgilendirme mesajı başarıyla öneri kanalına gönderildi.")

@bot.command()
@commands.has_permissions(administrator=True)
async def gecmisiac(ctx, rol: discord.Role):
    sayac = 0
    for kanal in ctx.guild.text_channels:
        # YETKİLİ kategorisinde olanları atla
        if kanal.category and kanal.category.name.upper() == "YETKİLİ":
            continue

        # Mevcut izinleri al ve güncelle
        izinler = kanal.overwrites_for(rol)
        if izinler.read_message_history is not True:
            izinler.read_message_history = True
            try:
                await kanal.set_permissions(rol, overwrite=izinler)
                sayac += 1
            except Exception as e:
                await ctx.send(f"⚠️ {kanal.name} kanalında hata: {str(e)}")

    await ctx.send(f"✅ `{rol.name}` rolü için **YETKİLİ kategorisi dışında** `{sayac}` kanalda geçmiş mesaj izni açıldı.")

@bot.command()
@commands.has_permissions(administrator=True)
async def mesajizniaç(ctx, rol: discord.Role):
    sayac = 0
    for kanal in ctx.guild.text_channels:
        if (
            (kanal.category and kanal.category.name.upper() == "KÜTÜPHANE") or
            kanal.name.lower() == "isvec" or
            kanal.name.lower().startswith("ticket")
        ):
            continue

        izinler = kanal.overwrites_for(rol)
        if izinler.send_messages is not True:
            izinler.send_messages = True
            try:
                await kanal.set_permissions(rol, overwrite=izinler)
                sayac += 1
            except Exception as e:
                await ctx.send(f"⚠️ `{kanal.name}` kanalında hata: {str(e)}")

    await ctx.send(f"✅ `{rol.name}` rolü için **{sayac}** kanalda mesaj gönderme izni açıldı (belirtilenler hariç).")


@bot.command()
async def öneri(ctx, *, mesaj: str = None):
    if mesaj is None:
        await ctx.send("❗ Lütfen bir öneri yazın.\nKullanım: `-öneri <mesaj>`")
        return

    bot_owner_id = 1236284001573015673  

    try:
        owner = await bot.fetch_user(bot_owner_id)
        embed = discord.Embed(
            title="📩 Yeni Öneri Geldi!",
            description=f"**Gönderen:** {ctx.author} ({ctx.author.id})\n\n**Öneri:**\n```{mesaj}```",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Sunucu: {ctx.guild.name} | Kanal: #{ctx.channel.name}")
        await owner.send(embed=embed)

        await ctx.send("✅ Öneriniz başarıyla geliştiriciye iletildi. Teşekkürler!")

    except Exception as e:
        await ctx.send("❌ Öneri iletilemedi. Geliştiriciye DM gönderilemiyor olabilir.")

@bot.command()
@commands.has_permissions(administrator=True)
async def durumfix(ctx, user: discord.User):
    await user.send("discord.gg/isvec durumuna alarak yetkili olabilirsin!")
    await ctx.send("✅ Kullanıcıya mesaj gönderildi.")

@durumfix.error
async def durumfix_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komutu yalnızca yöneticiler kullanabilir.")

@bot.command()
async def reklamengel(ctx):
    await ctx.send("Reklamlar engellendi!")
    if log_kanal:
        await log_kanal.send("Reklam engelleme aktif oldu.")

@bot.command()
async def kasaac(ctx):
    import random
    import asyncio

    esyalar = [
        ("🔪 Karambit | Fade", "✨ Efsanevi Bıçak!", discord.Color.red()),
        ("🔫 AK-47 | Fire Serpent", "🔥 Destansı AK-47!", discord.Color.orange()),
        ("🔫 M4A1-S | Hyper Beast", "🎯 Nadir M4A1-S!", discord.Color.blue()),
        ("🔫 AWP | Asiimov", "💥 Harika bir AWP!", discord.Color.purple()),
        ("🔫 Desert Eagle | Blaze", "💨 Efsane Deagle!", discord.Color.gold()),
        ("🔫 USP-S | Kill Confirmed", "🎮 Sakin ama ölümcül.", discord.Color.green()),
        ("🎁 Boş Kasa", "😶 Bu seferlik şanssızsın, devam et!", discord.Color.dark_gray()),
        ("💣 C4 Patlayıcı", "💥 Şaka gibi ama patladı 😆", discord.Color.dark_red()),
        ("📦 Çift Kasa", "📦 İkili ödül! Belki bir tane daha açarsın?", discord.Color.teal()),
        ("🧨 Sahte Skin", "🧃 Hahaha kandırıldın, bu skin sahteydi 😂", discord.Color.light_gray()),
    ]

    secilen = random.choice(esyalar)

    mesaj = await ctx.send("🔓 **Kasa açılıyor...**")
    await asyncio.sleep(2)

    embed = discord.Embed(
        title=f"{secilen[0]}",
        description=secilen[1],
        color=secilen[2]
    )
    embed.set_footer(text="Yeni kasa açmak için: -kasaac 🎲")

    await mesaj.edit(content="", embed=embed)

@bot.command()
async def desteac(ctx):
    import random
    import asyncio
    kartlar = [
        ("🃏 Efsane Kart", discord.Color.gold(), "✨Vay anasını! En nadir kartı çektin oe!"),
        ("🃏 Destansı Kart", discord.Color.purple(), "🔥 Idare eder çakal ! Bu kart oldukça güçlü."),
        ("🃏 Nadir Kart", discord.Color.blue(), "🎯 bokda cıkabılırdı, en azından nadir bir kart yakaladın."),
        ("🎁 Boş", discord.Color.dark_gray(), "😶 Maalesef bu sefer BOK çıktı. Bir dahaki sefere şansın döner (opsiyonel)!")
    ]

    secilen_kart = random.choice(kartlar)

    bekleme = await ctx.send("🎴 **Deste karıştırılıyor...**")
    await asyncio.sleep(2)

    embed = discord.Embed(
        title=f"{secilen_kart[0]} Çıktı!",
        description=secilen_kart[2],
        color=secilen_kart[1]
    )
    embed.set_footer(text="Bir kart açıldı! Şansını tekrar dene 🎲")

    await bekleme.edit(content="", embed=embed)

@bot.command()
async def ship(ctx, member: discord.Member = None):
    if member is None or member == ctx.author:
        return await ctx.send("Lütfen kendinden farklı birini etiketle 😅")

    yuzde = random.randint(0, 100)
    now = datetime.now().strftime("%d.%m.%Y")

    # Yorumlar
    if yuzde <= 20:
        yorum = "💔 Neredeyse imkansız gibi... Belki arkadaş kalabilirsiniz."
    elif yuzde <= 40:
        yorum = "💦 Biraz çaba gerekiyor ama imkansız değil!"
    elif yuzde <= 60:
        yorum = "🙂 Fena değil, tatlı bir uyum olabilir yakın arkadaş olun siz."
    elif yuzde <= 80:
        yorum = "💖 Gayet güzel gidiyor! Arada kıvılcımlar var! sex yaparak alevlendirebilirsiniz!"
    else:
        yorum = "💘 Aşkınız kıskandırır! Gerçek bir uyum var aranızda sikişin ve ikiziniz olsun! 😍"

    embed = discord.Embed(
        title="💞 Ship Ölçer",
        description=f"{ctx.author.mention} ile {member.mention} arasında **{now}** tarihindeki aşk uyumu:\n\n"
                    f"**%{yuzde}** {yorum}",
        color=discord.Color.red()
    )

    file = discord.File("ship.png", filename="ship.png")  
    embed.set_image(url="attachment://ship.png")

    await ctx.send(embed=embed, file=file)

@bot.command()
async def zarat(ctx):
    zar = random.randint(1, 6)
    await ctx.send(f"🎲 Zarın sonucu: **{zar}**")

@bot.command()
async def tkm(ctx, secim: str = None):
    if secim is None:
        await ctx.send(
            "**Hatalı kullanım! 😕**\n"
            "Lütfen bir seçim yap: `taş`, `kağıt`, veya `makas`\n\n"
            "**Doğru kullanım:** `-tkm taş`"
        )
        return

    secim = secim.lower()
    secenekler = ["taş", "kağıt", "makas"]
    if secim not in secenekler:
        await ctx.send(
            f"**taş/kağıt/makas yazıcaksın a* oglu! 🤨** `{secim}` nedir ya?\n"
            "Geçerli seçenekler: `taş`, `kağıt`, `makas`\n"
            "**Doğru kullanım:** `-tkm taş`"
        )
        return

    import random
    bot_secim = random.choice(secenekler)

    if secim == bot_secim:
        sonuc = "🤝 Berabere!"
    elif (secim == "taş" and bot_secim == "makas") or \
         (secim == "kağıt" and bot_secim == "taş") or \
         (secim == "makas" and bot_secim == "kağıt"):
        sonuc = "🎉 Kazandın!"
    else:
        sonuc = "😢 Kaybettin."

    await ctx.send(
        f"Senin seçimin: `{secim}`\n"
        f"Benim seçimin: `{bot_secim}`\n\n"
        f"**{sonuc}**"
    )
@bot.command()
async def reklamlog(ctx):
    await ctx.send("Reklamlar loglandı!")

@bot.command()
async def linkengel(ctx):
    await ctx.send("Linkler engellendi!")
    if log_kanal:
        await log_kanal.send("Link engelleme aktif oldu.")



@bot.command()
async def guard(ctx):
    await ctx.send("""    
    **🚨 Guard Komutları:**

    🔐 **-reklamengel** - Reklamları engeller ve loglar.  
    🔗 **-linkengel** - Link paylaşımını engeller ve loglar.
    """)

@bot.command()
async def yonetim(ctx):
    embed = discord.Embed(
        title="🔧 Yönetim Komutları",
        description="Sunucunuzu kolayca yönetmek için aşağıdaki komutları kullanabilirsiniz.",
        color=discord.Color.dark_blue()
    )

    embed.add_field(
        name="🔐 `-lock`",
        value="Kanalı kilitler (mesaj gönderilemez).",
        inline=False
    )
    embed.add_field(
        name="🔓 `-unlock`",
        value="Kanalın kilidini açar.",
        inline=False
    )
    embed.add_field(
        name="🌟 `-nuke`",
        value="Kanalı temizleyip kopyasını oluşturur (patlatır).",
        inline=False
    )
    embed.add_field(
        name="✨ `-sil <miktar>`",
        value="Belirtilen kadar mesajı siler.",
        inline=False
    )
    embed.add_field(
        name="💬 `-kes @kullanıcı`",
        value="Kullanıcının mesaj yazmasını engeller (timeout).",
        inline=False
    )
    embed.add_field(
        name="🚫 `-unkes @kullanıcı`",
        value="Kullanıcının yazma yasağını kaldırır.",
        inline=False
    )

    embed.set_footer(text="🛠 Komutları kullanırken yetkili olduğunuzdan emin olun.")
    await ctx.send(embed=embed)



@bot.command()
async def eğlence(ctx):
    embed = discord.Embed(
        title="🎉 Eğlence Komutları",
        description="Botla eğlenceli vakit geçirmen için hazırlanmış komutlar:",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="💼 -kasaac",
        value="CS:GO tarzı kasa açarsın. Şansına ne çıkarsa artık!",
        inline=False
    )

    embed.add_field(
        name="🃏 -desteac",
        value="Zula benzeri kart destesi açarsın. Kart koleksiyonunu büyüt!",
        inline=False
    )

    embed.add_field(
        name="🎲 -zarat",
        value="1 ile 5 arasında zar atar. Kumar borcu yok ama heyecan var 😄",
        inline=False
    )

    embed.add_field(
        name="✂️ -tkm [taş|kağıt|makas]",
        value="Botla klasik Taş-Kağıt-Makas oynarsın. Bakalım kazanabilecek misin?",
        inline=False
    )

    embed.add_field(
        name="🧠 -atasözü",
        value=(
            "**Türk kültüründen seçmece atasözleriyle bilgelik kazanın.**\n"
            "Her bir sözü hayatına uygulayacak kadar iddialı mısın? 👀"
        ),
        inline=False
    )

    embed.set_footer(text="Komutlar güncellenmeye devam edecek!")
    await ctx.send(embed=embed)

@bot.command()
async def yardım(ctx):
    embed = discord.Embed(
        title="🇸🇪 **İsveç | Yardım Menüsü**",
        description="**Tüm komut kategorilerini aşağıda büyük başlıklarla bulabilirsiniz.**",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="__💬 GENEL KOMUTLAR__",
        value=(
            "🏓 `-ping` - Botun gecikme süresini gösterir.\n"
            "📊 `-stat` - Kullanıcının mesaj ve ses istatistiklerini gösterir.\n"
            "🛌 `-afk [sebep]` - AFK moduna geçersin."
        ),
        inline=False
    )

    embed.add_field(
        name="__🛠️ AYARLAR KOMUTLARI__",
        value=(
            "🧷 `-otorol [rol]` - Yeni gelenlere otomatik rol atar.\n"
            "🔧 `-durumfix` - Botun durum mesajını düzeltir."
        ),
        inline=False
    )

    embed.add_field(
        name="__📩 ÖNERİ KOMUTLARI__",
        value=(
            "💡 `-öneri [metin]` - Bot geliştiricisine öneride bulunursun.\n"
        ),
        inline=False
    )


    embed.add_field(
        name="__👤 KULLANICI KOMUTLARI__",
        value=(
            "📊 `-stat` - Kullanıcıya ait ses ve mesaj bilgilerini gösterir.\n"
            "🛌 `-afk` - AFK durumuna geçiş yapar."
        ),
        inline=False
    )

    embed.add_field(
        name="__🎯 OTOROL KOMUTU__",
        value=(
            "🧷 `-otorol [rol]` - Yeni üyeler için otomatik rol ayarlar."
        ),
        inline=False
    )

    embed.add_field(
        name="__🎫 TICKET KOMUTLARI__",
        value=(
            "🎟️ `-ticket` - Ticket sistemi hakkında bilgi verir.\n"
            "📨 `Butona basarak` - Yeni bir destek bileti açar.\n"
            "❌ `Buton ile` - Açılmış bileti kapatır (Yetkili).\n"
        ),
        inline=False
    )

    embed.add_field(
        name="__📌 SİSTEMLER__",
        value=(
            "🚫 `-reklamengel` - Reklam engelleme sistemini açar/kapatır.\n"
            "📄 `-reklamlog` - Reklam log kanalını ayarlar.\n"
            "🔗 `-linkengel` - Link engelleme sistemini açar/kapatır."
        ),
        inline=False
    )

    embed.add_field(
        name="__🛡️ YÖNETİM KOMUTLARI__",
        value=(
            "🔒 `-lock` - Kanalı kilitler.\n"
            "🔓 `-unlock` - Kanalın kilidini açar.\n"
            "💣 `-nuke` - Kanalı temizleyip yeniden oluşturur.\n"
            "🧹 `-sil [miktar]` - Belirtilen sayıda mesajı siler.\n"
            "✂️ `-kes @kişi` - Kullanıcının yazmasını engeller.\n"
            "🩹 `-unkes @kişi` - Yazma engelini kaldırır.\n"
            "⛔ `-ban @kişi` - Kullanıcıyı sunucudan yasaklar.\n"
            "👢 `-kick @kişi` - Kullanıcıyı sunucudan atar."
        ),
        inline=False
    )

    embed.add_field(
        name="__🎉 EĞLENCE KOMUTLARI__",
        value=(
            "🎯 `-kasaac` - CS:GO tarzı rastgele bir **kasa açarsın**, sürpriz ödüller içerir.\n"
            "📦 `-desteac` - Zula benzeri **deste açarsın**, kartlar gelir.\n"
            "🎲 `-zarat` - 1 ile 5 arasında **rastgele bir zar atar**.\n"
            "✂️ `-tkm [taş|kağıt|makas]` - Botla **Taş, Kağıt, Makas** oynarsın.\n"
            "📜 `-atasözü` - Türk kültüründen **kapsamlı ve anlamlı atasözleri** getirir.\n"
            "😈 `-düşman @kişi` - Arandaki **düşmanlık oranını** hesaplar.\n"
            "🤗 `-saril @kişi` - Kullanıcıyı **sanal olarak sarilirsin**.\n"
            ":heart: `-ship @kişi` - Kullanıcıyla aranda olan ** aşkı derecesini ölcer**.\n"
            "🏓 `-ping` - Botun **gecikme süresini** gösterir."
        ),
        inline=False
    )


    embed.add_field(
        name="__📢 BİLGİLENDİRME__",
        value=(
            "🤖 `-botbilgi` - Bot hakkında genel istatistikleri gösterir."
        ),
        inline=False
    )



    embed.set_footer(text="İsveç Bot Yardım Menüsü")
    embed.set_thumbnail(url="https://tenor.com/view/the-simpsons-sweden-olympics-sweden-flag-swedish-gif-25732619")
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        del afk_users[message.author.id]
        await message.channel.send(f'{message.author} artık AFK değil!')

    if message.mentions:
        for user in message.mentions:
            if user.id in afk_users:
                await message.channel.send(f'{user} şu anda AFK! Sebep: {afk_users[user.id]}')

    if message.channel.id == sohbet_kanal_id and message.attachments:
        hedef_kanal = bot.get_channel(hedef_kanal_id)
        for attachment in message.attachments:
            await hedef_kanal.send(f"{message.author.mention} bir dosya gönderdi:", file=await attachment.to_file())
        await asyncio.sleep(60)
        try:
            await message.delete()
        except:
            pass

    # --- Medya log ---
    if message.attachments:
        media_log_channel = bot.get_channel(media_log_kanal_id)

        if media_log_channel is None:
            print("❌ media_log_channel bulunamadı! Kanal ID doğru mu?")
        else:
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov', '.webm', '.webp', '.avi']):
                    try:
                        await media_log_channel.send(
                            f"{message.author.mention} bir medya gönderdi:",
                            file=await attachment.to_file()
                        )
                    except Exception as e:
                        print(f"⚠️ Medya log gönderim hatası: {e}")
            await asyncio.sleep(60)
            try:
                await message.delete()
            except:
                pass



    if message.author.id in kesilen_kullanicilar:
        try:
            await message.delete()
        except:
            pass

    izinli_rol = message.guild.get_role(link_engellenmeyen_role_id)
    if 'http' in message.content or 'www' in message.content or "discord.gg/" in message.content or ".gg/" in message.content or "/" in message.content:
        if not izinli_rol or izinli_rol not in message.author.roles:
            try:
                await message.delete()
            except:
                pass

        if log_kanal:
            await log_kanal.send(
                f"Link tespit edildi: {message.content}\n"
                f"Gönderen: {message.author} ({message.author.id})\n"
                f"Kanal: {message.channel.mention}"
            )

    reklam_kelimesi = ['win', 'free', 'prize', 'bitcoin']
    if any(reklam in message.content.lower() for reklam in reklam_kelimesi):
        try:
            await message.delete()
        except:
            pass
        if log_kanal:
            await log_kanal.send(
                f"Reklam engellendi: {message.content} | Gönderen: {message.author} | Kanal: {message.channel}"
            )

    await bot.process_commands(message)

@bot.event
async def on_ready():
    global log_kanal
    log_kanal = bot.get_channel(log_kanal_id)
    print(f'{bot.user} olarak giriş yapıldı!')

@bot.event
async def on_ready():
    global log_kanal
    log_kanal = bot.get_channel(log_kanal_id)

    print(f"{bot.user} olarak giriş yapıldı.")
    if log_kanal is None:
        print("❌ log_kanal alınamadı! ID yanlış olabilir.")
    else:
        print(f"✅ log_kanal başarıyla alındı: #{log_kanal.name}")


@bot.event
async def on_member_join(member):
    hesap_yasi = (datetime.now(timezone.utc) - member.created_at).days
    if hesap_yasi < 7:
        try:
            dm = await member.create_dm()
            await dm.send("Şüpheli bir giriş tespit edildi.")
        except:
            pass
        if log_kanal:
            bilgi = (
                f"⚠️ Şüpheli Giriş Tespit Edildi\n"
                f"👤 Kullanıcı: {member.mention}\n"
                f"🆔 ID: {member.id}\n"
                f"📅 Hesap Oluşturulma: {member.created_at.strftime('%d.%m.%Y %H:%M:%S')}\n"
                f"📥 Sunucuya Katılma: {member.joined_at.strftime('%d.%m.%Y %H:%M:%S') if member.joined_at else 'Bilinmiyor'}"
            )
            await log_kanal.send(bilgi)




bot.run("MTM1ODUwNjY2NjE0Nzk3NTM4MA.GznjFU.QmjBvRq35iObTxBxq5TvFSqJY-JDHohwKLdjvQ")
