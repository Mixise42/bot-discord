import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI
import random
import json
import yt_dlp

music_queue = []

def load_xp():
    try:
        with open("xp.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_xp(data):
    with open("xp.json", "w") as f:
        json.dump(data, f, indent=4)

xp_data = load_xp()

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

client_ai = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    user_id = str(message.author.id)

    if user_id not in xp_data:
        xp_data[user_id] = {
            "xp": 0,
            "level": 1
        }

    xp_data[user_id]["xp"] += 5

    xp = xp_data[user_id]["xp"]
    level = xp_data[user_id]["level"]

    if xp >= level * 100:
        xp_data[user_id]["level"] += 1

        await message.channel.send(
            f"🎉 {message.author.mention} passe niveau {level + 1} !"
        )

    save_xp(xp_data)

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté !")
    print("Je suis fonctionnel")

    print("Commandes chargées :")
    for command in bot.commands:
        print("-", command.name)

@bot.event
async def on_disconnect():
    print("Je ne suis plus fonctionnel")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1516500081933553845)

    if channel:
        await channel.send(
            f"Bienvenue {member.mention} sur le serveur ! 🎉"
        )

# ===== COMMANDES =====
@bot.command()
async def queue(ctx):

    if not music_queue:
        await ctx.send("📭 La file d'attente est vide.")
        return

    texte = ""

    for i, musique in enumerate(music_queue, start=1):
        texte += f"{i}. {musique}\n"

    await ctx.send(
        f"📜 File d'attente :\n```{texte}```"
    )

async def play_next(ctx):

    if len(music_queue) > 0:

        url = music_queue.pop(0)

        voice = ctx.voice_client

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]

        source = discord.FFmpegPCMAudio(
            audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )

        voice.play(
            source,
            after=lambda e: bot.loop.create_task(
                play_next(ctx)
            )
        )

@bot.command()
async def join(ctx):

    if ctx.author.voice is None:
        await ctx.send("❌ Tu dois être dans un salon vocal.")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.send("✅ Je suis déjà connecté.")
        return

    await channel.connect()
    await ctx.send("🎵 Connecté au salon vocal.")

@bot.command()
async def leave(ctx):

    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Déconnecté du salon vocal.")
    else:
        await ctx.send("❌ Je ne suis dans aucun salon vocal.")

@bot.command()
async def play(ctx, *, url):

    if ctx.author.voice is None:
        await ctx.send("❌ Rejoins un salon vocal.")
        return

    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()

    voice = ctx.voice_client

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        audio_url = info["url"]

        source = discord.FFmpegPCMAudio(
            audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )

        voice.play(source)

        await ctx.send(
            f"🎶 Lecture : {info['title']}"
        )

    except Exception as e:
        await ctx.send(f"❌ Erreur : {e}")

@bot.command()
async def leaderboard(ctx):

    classement = sorted(
        xp_data.items(),
        key=lambda x: x[1]["xp"],
        reverse=True
    )

    texte = ""

    for i, (user_id, data) in enumerate(classement[:10], start=1):

        membre = bot.get_user(int(user_id))

        nom = membre.name if membre else "Inconnu"

        texte += (
            f"{i}. {nom} - "
            f"Niveau {data['level']} "
            f"({data['xp']} XP)\n"
        )

    embed = discord.Embed(
        title="🏆 Classement XP",
        description=texte,
        color=discord.Color.gold()
    )

    await ctx.send(embed=embed)

@bot.command()
async def rank(ctx):

    user_id = str(ctx.author.id)

    if user_id not in xp_data:
        await ctx.send(
            "Tu n'as pas encore d'XP."
        )
        return

    xp = xp_data[user_id]["xp"]
    level = xp_data[user_id]["level"]

    embed = discord.Embed(
        title=f"Profil de {ctx.author.name}",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="⭐ Niveau",
        value=level
    )

    embed.add_field(
        name="📈 XP",
        value=xp
    )

    await ctx.send(embed=embed)

@bot.command()
async def bonjour(ctx):
    await ctx.send(f"Bonjour {ctx.author.mention} !")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

@bot.command()
async def say(ctx, *, texte):
    await ctx.send(texte)

@bot.command()
async def coin(ctx):
    resultat = random.choice(["Pile", "Face"])
    await ctx.send(f"🪙 {resultat}")

@bot.command()
async def dice(ctx):
    resultat = random.randint(1, 6)
    await ctx.send(f"🎲 Tu as obtenu : {resultat}")

@bot.command()
async def userinfo(ctx, membre: discord.Member = None):
    membre = membre or ctx.author

    embed = discord.Embed(
        title=f"Informations sur {membre}",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Nom",
        value=membre.name,
        inline=False
    )

    embed.add_field(
        name="ID",
        value=membre.id,
        inline=False
    )

    embed.add_field(
        name="A rejoint le serveur",
        value=membre.joined_at.strftime("%d/%m/%Y"),
        inline=False
    )

    await ctx.send(embed=embed)

# ===== MODERATION =====

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, nombre: int):
    await ctx.channel.purge(limit=nombre + 1)

    message = await ctx.send(
        f"🧹 {nombre} messages supprimés."
    )

    await message.delete(delay=3)

# ===== ARRET DU BOT =====
OWNER_ID = 1457787561576759306

@bot.command()
async def stop(ctx):
    if ctx.author.id == OWNER_ID:
        await ctx.send("Je ne suis plus fonctionnel")
        await bot.close()
    else:
        await ctx.send(
            "Vous n'avez pas la permission."
        )

# ===== HELP PERSONNALISE =====

@bot.command()
async def aide(ctx):
    embed = discord.Embed(
        title="Liste des commandes",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Fun",
        value="""
!bonjour
!ping
!say
!coin
!dice
!userinfo
!join
!skip
!play
!resume
!leave
!pause
""",
        inline=False
    )

    embed.add_field(
        name="Administration",
        value="""
!clear
!stop
""",
        inline=False
    )

    await ctx.send(embed=embed)

@bot.command()
async def ask(ctx, *, question):
    await ctx.send("🤔 Je réfléchis...")

    try:
        response = client_ai.responses.create(
            model="gpt-5",
            input=question
        )

        await ctx.send(
            f"{ctx.author.mention}\n\n{response.output_text}"
        )

    except Exception as e:

        if "insufficient_quota" in str(e):
            await ctx.send(
                "❌ Le quota de l'IA est épuisé. Vérifie les crédits API OpenAI."
            )

        else:
            await ctx.send(
                f"Erreur : {e}"
            )
@bot.command()
async def pause(ctx):

    if ctx.voice_client and ctx.voice_client.is_playing():

        ctx.voice_client.pause()

        await ctx.send("⏸️ Musique mise en pause.")

    else:
        await ctx.send("❌ Aucune musique en cours.")
@bot.command()
async def resume(ctx):

    if ctx.voice_client and ctx.voice_client.is_paused():

        ctx.voice_client.resume()

        await ctx.send("▶️ Lecture reprise.")

    else:
        await ctx.send("❌ Aucune musique en pause.")
@bot.command()
async def skip(ctx):

    if ctx.voice_client and ctx.voice_client.is_playing():

        ctx.voice_client.stop()

        await ctx.send("⏭️ Musique passée.")

    else:
        await ctx.send("❌ Aucune musique à passer.")

bot.run(TOKEN)