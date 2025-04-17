import discord
from discord.ext import commands
import random
import asyncio
import os
import json
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!mafia ", intents=intents)

jugadores = []
roles = {}
fase = "día"
mafioso = None
doctor = None
detective = None
jugador_muerto = None
jugador_salvado = None
votos = {}
mafioso_channel = None
doctor_channel = None
detective_channel = None
jugador_salvado = None

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Evita que el bot se responda a sí mismo

    if message.content.lower() == "hola":
        await message.channel.send("¡Hola! 👋 Soy un bot hecho con Python.")

    # Muy importante: asegura que los comandos también se sigan procesando
    await bot.process_commands(message)



# --------- RANKING ---------
ARCHIVO_RANKING = "ranking.json"

def cargar_ranking():
    try:
        with open(ARCHIVO_RANKING, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def guardar_ranking(ranking):
    with open(ARCHIVO_RANKING, "w") as f:
        json.dump(ranking, f, indent=4)

def actualizar_puntaje(nombre, puntos):
    ranking = cargar_ranking()
    ranking[nombre] = ranking.get(nombre, 0) + puntos
    guardar_ranking(ranking)

def obtener_ranking_ordenado():
    ranking = cargar_ranking()
    return sorted(ranking.items(), key=lambda x: x[1], reverse=True)
# ----------------------------

def esta_vivo(jugador):
    return jugador in jugadores

async def eliminar_permisos(jugador):
    if mafioso_channel:
        await mafioso_channel.set_permissions(jugador, read_messages=False, send_messages=False)
    if doctor_channel:
        await doctor_channel.set_permissions(jugador, read_messages=False, send_messages=False)
    if detective_channel:
        await detective_channel.set_permissions(jugador, read_messages=False, send_messages=False)

async def noche(ctx):
    global fase, jugador_muerto
    fase = "noche"
    jugador_muerto = None
    await ctx.send("🌙 Es de noche. Todos los jugadores duermen...")
    await asyncio.sleep(60)
    await amanecer(ctx)

async def amanecer(ctx):
    global fase, jugador_muerto, jugador_salvado
    fase = "día"

    if jugador_muerto is not None and jugador_muerto == jugador_salvado:
        await ctx.send(f"☀️ Amanece y **{jugador_salvado.name}** fue atacado, ¡pero el doctor lo salvó! 🩺")
        jugador_muerto = None
    elif jugador_muerto is not None:
        await ctx.send(f"☀️ Amanece y encontramos el cuerpo de **{jugador_muerto.name}**. Era **{roles.get(jugador_muerto, 'Desconocido')}**.")
        jugadores.remove(jugador_muerto)
        del roles[jugador_muerto]

    jugador_salvado = None
    await verificar_ganador(ctx)
 # Solo enviar el mensaje de votación si la fase es de "día" y si hay jugadores vivos
    if fase == "día" and len(jugadores) > 1:  # Asegúrate de que haya más de un jugador vivo
        await ctx.send("Es el momento de votar. Usen `!mafia votar @jugador` para elegir a alguien.")
    elif len(jugadores) <= 1:
        # Si solo queda 1 jugador, el juego ha terminado, no mostrar la votación.
        await ctx.send("🏁 La partida ha terminado. Usa `!mafia crear X` para empezar otra.")
    
@bot.command()
async def crear(ctx, cantidad: int):
    global jugadores, roles, votos, mafioso_channel, doctor_channel, detective_channel

    if cantidad < 4:
        await ctx.send("⚠️ Se necesitan al menos 4 jugadores para empezar la partida.")
        return

    jugadores.clear()
    roles.clear()
    votos.clear()

    guild = ctx.guild
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False)}

    mafioso_channel = await guild.create_text_channel("mafioso-secreto", overwrites=overwrites)
    doctor_channel = await guild.create_text_channel("doctor-secreto", overwrites=overwrites)
    detective_channel = await guild.create_text_channel("detective-secreto", overwrites=overwrites)

    await ctx.send(f"¡La partida ha sido creada con {cantidad} jugadores! Usa `!mafia unirme` para entrar.")

@bot.command()
async def unirme(ctx):
    if ctx.author in jugadores:
        await ctx.send("⚠️ Ya estás en la partida.")
        return

    jugadores.append(ctx.author)
    jugadores_lista = "\n".join([f"- {jugador.mention}" for jugador in jugadores])
    await ctx.send(f"✅ {ctx.author.mention} se ha unido a la partida.\n\n📜 **Lista de jugadores:**\n{jugadores_lista}")

    if len(jugadores) >= 4:
        await iniciar_partida(ctx)

async def iniciar_partida(ctx):
    global jugadores, mafioso, doctor, detective, roles

    if len(jugadores) < 4:
        await ctx.send("⚠️ Se necesitan al menos 4 jugadores para empezar la partida.")
        return

    random.shuffle(jugadores)

    mafioso, doctor, detective = jugadores[:3]
    for i, rol in zip([mafioso, doctor, detective], ["Mafioso", "Doctor", "Detective"]):
        roles[i] = rol
    for ciudadano in jugadores[3:]:
        roles[ciudadano] = "Ciudadano"

    await mafioso_channel.set_permissions(mafioso, read_messages=True, send_messages=True)
    await doctor_channel.set_permissions(doctor, read_messages=True, send_messages=True)
    await detective_channel.set_permissions(detective, read_messages=True, send_messages=True)

    for jugador, rol in roles.items():
        try:
            mensaje = f"🎭 Tu rol en la partida es: **{rol}**.\n"
            if rol == "Mafioso":
                mensaje += f"😈 Puedes matar a alguien cada noche en: {mafioso_channel.jump_url}"
            elif rol == "Doctor":
                mensaje += f"🩺 Puedes salvar a un jugador cada noche en: {doctor_channel.jump_url}"
            elif rol == "Detective":
                mensaje += f"🔍 Puedes investigar a un jugador en: {detective_channel.jump_url}"
            await jugador.send(mensaje)
        except:
            await ctx.send(f"⚠️ No pude enviar un mensaje privado a {jugador.mention}. Activa tus DMs.")

    await ctx.send("🏁 ¡La partida ha comenzado! La primera noche inicia ahora.")
    await noche(ctx)

@bot.command()
async def matar(ctx, miembro: discord.Member):
    global jugador_muerto

    if ctx.channel != mafioso_channel:
        await ctx.send("⚠️ Este comando solo puede usarse en el canal privado del mafioso.")
        return

    if ctx.author != mafioso or fase != "noche":
        await ctx.send("⚠️ No puedes usar este comando ahora.")
        return

    if not esta_vivo(ctx.author):
        await ctx.send("⚠️ No puedes matar porque estás muerto.")
        return

    if not esta_vivo(miembro):
        await ctx.send(f"⚠️ {miembro.mention} ya está muerto. Elige a alguien vivo.")
        return

    jugador_muerto = miembro
    await ctx.send(f"🕵️‍♂️ El mafioso ha elegido a {miembro.mention}. Se procesará al amanecer.")

@bot.command()
async def salvar(ctx, miembro: discord.Member):
    global jugador_salvado

    if ctx.author != doctor or fase != "noche":
        await ctx.send("⚠️ Solo el doctor puede usar este comando durante la noche.")
        return

    if not esta_vivo(miembro):
        await ctx.send(f"⚠️ {miembro.mention} ya está muerto.")
        return

    jugador_salvado = miembro
    await ctx.send(f"🩺 Has elegido salvar a **{miembro.mention}** esta noche.")

@bot.command()
async def votar(ctx, miembro: discord.Member):
    global votos

    if fase != "día":
        await ctx.send("⚠️ Solo puedes votar durante el día.")
        return

    if not esta_vivo(ctx.author):
        await ctx.send("⚠️ No puedes votar porque estás muerto.")
        return

    if ctx.author in votos:
        await ctx.send("⚠️ Ya has votado.")
        return

    if not esta_vivo(miembro):
        await ctx.send(f"⚠️ {miembro.mention} ya está muerto y no puede ser votado.")
        return

    votos[ctx.author] = miembro
    await ctx.send(f"🗳️ {ctx.author.mention} ha votado por {miembro.mention}.")

    if len(votos) == len(jugadores):
        await contar_votos(ctx)

async def contar_votos(ctx):
    global votos, jugador_muerto

    if not votos:
        await ctx.send("⚠️ Nadie votó. La ronda continúa sin eliminaciones.")
        votos.clear()
        await noche(ctx)
        return

    conteo = {}
    for voto in votos.values():
        conteo[voto] = conteo.get(voto, 0) + 1

    max_votos = max(conteo.values(), default=0)
    candidatos = [jugador for jugador, cantidad in conteo.items() if cantidad == max_votos]

    if len(candidatos) > 1:
        await ctx.send("⚠️ Hubo un empate en la votación. Nadie es eliminado esta ronda.")
        votos.clear()
        await noche(ctx)
        return

    jugador_eliminado = candidatos[0]
    await ctx.send(f"🔪 **{jugador_eliminado.name}** ha sido eliminado. Era **{roles[jugador_eliminado]}**.")

    jugadores.remove(jugador_eliminado)
    del roles[jugador_eliminado]
    votos.clear()

    if jugador_eliminado == mafioso:
        await ctx.send("🎉 ¡El mafioso ha sido eliminado! **Los ciudadanos ganan.**")
        for jugador in roles:
            if roles[jugador] != "Mafioso":
                actualizar_puntaje(jugador.name, 10)
        actualizar_puntaje(jugador_eliminado.name, -5)
        await terminar_partida(ctx)
    else:
        await noche(ctx)

async def verificar_ganador(ctx):
    global jugadores, mafioso, fase

    if mafioso not in jugadores:
        await ctx.send("🎉 ¡El mafioso ha sido eliminado! **Los ciudadanos ganan.**")
        for jugador in roles:
            if roles[jugador] != "Mafioso":
                actualizar_puntaje(jugador.name, 10)
        actualizar_puntaje(mafioso.name, -5)
        await terminar_partida(ctx)
    elif len(jugadores) == 1 and mafioso in jugadores:
        await ctx.send("🔪 El mafioso ha eliminado a todos. **Gana el mafioso.** 😈")
        actualizar_puntaje(mafioso.name, 15)
        await terminar_partida(ctx)
    else:
        fase = "día"

@bot.command()
async def terminar_partida(ctx):
    global jugadores, roles, votos, mafioso_channel, doctor_channel, detective_channel

    await ctx.send("🏁 La partida ha terminado. Usa `!mafia crear X` para empezar otra.")

    for channel in [mafioso_channel, doctor_channel, detective_channel]:
        if channel:
            await channel.delete()

    jugadores.clear()
    roles.clear()
    votos.clear()

    # MOSTRAR RANKING AUTOMÁTICAMENTE
    ranking = obtener_ranking_ordenado()
    if ranking:
        mensaje = "📊 **Ranking de jugadores:**\n"
        for i, (nombre, puntos) in enumerate(ranking, 1):
            mensaje += f"{i}. {nombre}: {puntos} puntos\n"
        await ctx.send(mensaje)
    else:
        await ctx.send("🏆 No hay puntajes aún.")


@bot.command()
async def ranking(ctx):
    ranking = obtener_ranking_ordenado()
    if not ranking:
        await ctx.send("🏆 No hay puntajes aún.")
        return

    mensaje = "📊 **Ranking de jugadores:**\n"
    for i, (nombre, puntos) in enumerate(ranking, 1):
        mensaje += f"{i}. {nombre}: {puntos} puntos\n"
    await ctx.send(mensaje)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() == "hola":
        await message.channel.send(f"¡Hola {message.author.mention}! 👋")

    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
