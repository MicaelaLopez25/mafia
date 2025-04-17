import discord
from discord.ext import commands
import random, asyncio, json

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Lista de roles disponibles
ROLES = ["Mafia", "Ciudadano", "Doctor", "Juez", "Espía"]

# Archivo de puntos
archivo_puntos = "mafia_ranking.json"
TIEMPO_RONDA = 30  # segundos por ronda

# Funciones de persistencia de ranking
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

# Comando principal !mafia
@bot.command()
async def mafia(ctx, modo=None):
    if modo == "ranking":
        if not ranking:
            await ctx.send("Todavía no hay ranking.")
        else:
            top = sorted(ranking.items(), key=lambda x: x[1], reverse=True)[:5]
            msg = "\n".join([f"#{i+1} {u}: {p} pts" for i, (u, p) in enumerate(top)])
            await ctx.send(f"🏆 Ranking Mafia:\n{msg}")
    else:
        await ctx.send("Usá `!start @jugador1 @jugador2 ...` para comenzar.")

# Comando para iniciar la partida
@bot.command()
async def start(ctx, *players: discord.Member):
    if len(players) < 3:
        return await ctx.send("Se necesitan al menos 3 jugadores.")

    # Asignar roles aleatorios
    roles_disponibles = ROLES * ((len(players) // len(ROLES)) + 1)
    roles_asignados = random.sample(roles_disponibles, len(players))
    asignados = dict(zip(players, roles_asignados))

    await ctx.send(f"🎮 Juego iniciado con {len(players)} jugadores. ¡Modo rápido activado! 🕒")

    # Informar rol a cada jugador por privado
    for jugador, rol in asignados.items():
        habilidad = ""
        if rol == "Mafia":
            habilidad = "Podés elegir a quién eliminar."
        elif rol == "Doctor":
            habilidad = "Podés elegir a quién curar."
        elif rol == "Juez":
            habilidad = "Tu voto cuenta doble durante el juicio."
        elif rol == "Espía":
            habilidad = "Podés investigar a un jugador."
        elif rol == "Ciudadano":
            habilidad = "Intentá sobrevivir y votar bien."

        try:
            await jugador.send(f"🎭 Tu rol es **{rol}**.\n🛠 Habilidad: {habilidad}")
        except:
            await ctx.send(f"No pude enviarle DM a {jugador.name}. Asegurate de tener los mensajes privados habilitados.")

    # Simulación de rondas con tiempo límite
    for ronda in range(1, 4):
        await ctx.send(f"🌀 **Ronda {ronda}** - Tienen {TIEMPO_RONDA} segundos para discutir y actuar.")
        await asyncio.sleep(TIEMPO_RONDA)
        await ctx.send(f"⏰ Ronda {ronda} finalizada.")

    # Fin de juego - asignar puntos básicos
    for jugador in players:
        nombre = str(jugador)
        ranking[nombre] = ranking.get(nombre, 0) + 10  # puntos por participación

    guardar_ranking(ranking)
    await ctx.send("🎉 ¡Fin del juego! Puntos actualizados en el ranking.")

