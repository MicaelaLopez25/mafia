import discord
from discord.ext import commands
import random, asyncio, json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

ROLES = ["Mafia", "Ciudadano", "Doctor", "Juez", "Espía"]
archivo_puntos = "ranking.json"
TIEMPO_RONDA = 30

asignados = {}
vivos = set()
fase = None
jugadores = []
ranking = {}

# ------------------ RANKING ------------------

def cargar_ranking():
    if not os.path.exists(archivo_puntos):
        return {}
    with open(archivo_puntos, "r") as f:
        return json.load(f)

def guardar_ranking(data):
    with open(archivo_puntos, "w") as f:
        json.dump(data, f, indent=4)

ranking = cargar_ranking()

# ------------------ EVENTOS ------------------

@bot.event
async def on_ready():
    print(f"🟢 {bot.user} conectado.")

# ------------------ COMANDOS ------------------

@bot.command()
async def mafia(ctx, modo=None):
    if modo == "ranking":
        if not ranking:
            await ctx.send("📉 Todavía no hay ranking.")
        else:
            top = sorted(ranking.items(), key=lambda x: x[1], reverse=True)[:5]
            msg = "\n".join([f"#{i+1} {u}: {p} pts" for i, (u, p) in enumerate(top)])
            await ctx.send(f"🏆 **Ranking Mafia:**\n{msg}")
    else:
        await ctx.send("Usá `!mafia start @jugador1 @jugador2 ...` para comenzar.")

@bot.command()
async def start(ctx, *players: discord.Member):
    global asignados, vivos, fase, jugadores

    if len(players) < 3:
        return await ctx.send("⚠️ Se necesitan al menos 3 jugadores.")

    jugadores = list(players)
    roles = random.sample(ROLES * ((len(jugadores) // len(ROLES)) + 1), len(jugadores))
    asignados = dict(zip(jugadores, roles))
    vivos = set(jugadores)

    for p, r in asignados.items():
        await p.send(f"🎭 Tu rol: **{r}**")

    await ctx.send(f"🎮 Juego iniciado con {len(jugadores)} jugadores. ¡Buena suerte!")

    await avanzar_rondas(ctx)

@bot.command()
async def matar(ctx, victima: discord.Member):
    global vivos

    if fase != "noche":
        return await ctx.send("⚠️ Solo se puede matar durante la fase de noche.")

    if ctx.author not in vivos or asignados.get(ctx.author) != "Mafia":
        return await ctx.send("❌ Solo un jugador Mafia vivo puede usar este comando.")

    if victima not in vivos:
        return await ctx.send("⚠
