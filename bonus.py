import discord
from discord.ext import commands
import random, asyncio, json

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ROLES = ["Mafia", "Ciudadano", "Doctor", "Juez", "Espía"]
archivo_puntos = "mafia_ranking.json"
tiempo_ronda = 30 

def cargar_ranking():
    try:
        with open(archivo_puntos, "r") as f:
            return json.load(f)
    except: 
        return {}

def guardar_ranking(data):
    with open(archivo_puntos, "w") as f:
        json.dump(data, f)

ranking = cargar_ranking()

@bot.event
async def on_ready():
    print(f"🟢 {bot.user} conectado.")

@bot.command()
async def mafia(ctx, modo=None):
    if modo == "ranking":
        if not ranking:
            await ctx.send("Todavía no hay ranking..")
        else:
            top = sorted(ranking.items(), key=lambda x: x[1], reverse=True)[:5]
            msg = "\n".join([f"#{i+1} {u}: {p} pts" for i, (u, p) in enumerate(top)])
            await ctx.send(f"🏆 Ranking Mafia:\n{msg}")
    else:
        await ctx.send("Usá `!mafia start @jugador1 @jugador2 ...` para comenzar.")

@bot.command()
async def start(ctx, *players: discord.Member):
    if len(players) < 3:
        return await ctx.send("Se necesitan 3 jugadores.")

    roles = random.sample(ROLES * ((len(players) // len(ROLES)) + 1), len(players))
    asignados = dict(zip(players, roles))

    for p, r in asignados.items():
        await p.send(f"🎭 Tu rol: **{r}**")

    await ctx.send(f"Juego iniciado con {len(players)} jugadores. Modo rápido activado! 🕒")

    for ronda in range(1, 4):
        await ctx.send(f"🌀 Ronda {ronda} (tienen {TIEMPO_RONDA}s)")
        await asyncio.sleep(TIEMPO_RONDA)
        await ctx.send(f"⏰ Ronda {ronda} finalizada.")

    for p in players:
        nombre = str(p)
        ranking[nombre] = ranking.get(nombre, 0) + 10  

    guardar_ranking(ranking)
    await ctx.send("¡Fin del juego!. Los puntajes están actualizados.")

