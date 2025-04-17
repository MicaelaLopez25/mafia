import discord
from discord.ext import commands
import random
import asyncio
import json
import os

archivo_puntos = 'puntos.json'
puntos = {}

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!mafia ", intents=intents)


jugadores = []
partidas = {}
puntos = {}
roles = {}
fase = "día"
mafioso = None
doctor = None
detective = None
jugador_muerto = None
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


modo_rapido = False
tiempo_votacion = 30  # segundos por defecto para votar en modo rápido


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Evita que el bot se responda a sí mismo

    if message.content.lower() == "hola":
        await message.channel.send("¡Hola! 👋 Soy un bot hecho con Python.")

    # Muy importante: asegura que los comandos también se sigan procesando
    await bot.process_commands(message)

def esta_vivo(jugador):
    """Verifica si el jugador sigue en la partida."""
    return jugador in jugadores

async def eliminar_permisos(jugador):
    """Remueve los permisos del jugador en los canales privados al morir."""
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

    await asyncio.sleep(30)  # La noche dura 30s 

    await amanecer(ctx)

async def amanecer(ctx):
    global fase, jugador_muerto, jugador_salvado

    fase = "día"

    if jugador_muerto is not None and jugador_muerto == jugador_salvado:
        await ctx.send(f"☀️ Amanece y **{jugador_salvado.name}** fue atacado, ¡pero el doctor lo salvó! 🩺")
        jugador_muerto = None  # Nadie muere
    elif jugador_muerto is not None:
        await ctx.send(f"☀️ Amanece y encontramos el cuerpo de **{jugador_muerto.name}**. Era **{roles.get(jugador_muerto, 'Desconocido')}**.")
        jugadores.remove(jugador_muerto)
        del roles[jugador_muerto]

    jugador_salvado = None  # Reiniciar la salvación para la siguiente noche
    
    await iniciar_votacion(ctx)


async def iniciar_votacion(ctx):
    print(f"Fase actual: {fase}")  # Esto te ayudará a verificar si la fase está correcta.

    # Verifica si la fase es "día"
    if fase != "día":
        await ctx.send("⚠️ ¡La fase no está en día! No se puede iniciar la votación.")
        return

    await ctx.send("🌞 Comienza la fase de día. ¡A debatir y votar!")

    # Verifica si hay más de un jugador vivo antes de procesar el ganador
    if len(jugadores) > 1:
        await verificar_ganador(ctx)
    else:
        await ctx.send("🏁 La partida ha terminado. Usa `!mafia crear X` para empezar otra.")
 
    await ctx.send("🗳️ Tienen 60 segundos para votar usando `!mafia votar @jugador`.")

    # Iniciar temporizador
    asyncio.create_task(temporizador_votacion_dia(ctx))

    await verificar_ganador(ctx)
 # Solo enviar el mensaje de votación si la fase es de "día" y si hay jugadores vivos
    if fase == "día" and len(jugadores) > 1:  # Asegúrate de que haya más de un jugador vivo
        await ctx.send("Es el momento de votar. Usen `!mafia votar @jugador` para elegir a alguien.")
    elif len(jugadores) <= 1:
        # Si solo queda 1 jugador, el juego ha terminado, no mostrar la votación.
        await ctx.send("🏁 La partida ha terminado. Usa `!mafia crear X` para empezar otra.")
    

async def temporizador_votacion_dia(ctx):
    await asyncio.sleep(60)

    if fase == "día":
        if votos:
            await contar_votos(ctx)
        else:
            await ctx.send("⏱ Se acabó el tiempo y nadie votó. Pasamos a la noche.")
            await noche(ctx)


async def contar_votos(ctx):

    """Cuenta los votos y elimina al jugador más votado."""
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
    candidatos = [jugador for jugador, votos in conteo.items() if votos == max_votos]

    if len(candidatos) > 1:
        await ctx.send("⚠️ Hubo un empate en la votación. Nadie es eliminado esta ronda.")
        votos.clear()
        await noche(ctx)
        return


    # El jugador más votado es eliminado
    jugador_eliminado = candidatos[0]
    await ctx.send(f"🔪 **{jugador_eliminado.name}** ha sido eliminado. Era **{roles[jugador_eliminado]}**.")
    
    jugadores.remove(jugador_eliminado)
    del roles[jugador_eliminado]

    votos.clear()

    # Verificar si el mafioso murió
    if jugador_eliminado == mafioso:
        await ctx.send("🎉 ¡El mafioso ha sido eliminado! **Los ciudadanos ganan.**")
        await terminar_partida(ctx)
        return

    await noche(ctx)

async def verificar_ganador(ctx):
    global jugadores, mafioso, fase

    if mafioso not in jugadores:
        await ctx.send("🎉 ¡El mafioso ha sido eliminado! **Los ciudadanos ganan.**")
        await terminar_partida(ctx)
        return

    if len(jugadores) == 1 and mafioso in jugadores:
        await ctx.send("🔪 El mafioso ha eliminado a todos. **Gana el mafioso.** 😈")
        await terminar_partida(ctx)
        return

    fase = "día"

@bot.command()
async def crear(ctx, cantidad: int):
    global jugadores, roles, votos, mafioso_channel, doctor_channel, detective_channel

    if cantidad < 4:
        await ctx.send("⚠️ Se necesitan al menos 4 jugadores para empezar la partida.")
        return

    jugadores = []
    roles = {}
    votos = {}

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
    global jugadores, mafioso, doctor, detective, juez, espia, roles

    if len(jugadores) < 6:
        await ctx.send("⚠️ Se necesitan al menos 6 jugadores para empezar la partida.")
        return

    random.shuffle(jugadores)

    mafioso = jugadores[0]
    doctor = jugadores[1]
    detective = jugadores[2]
    juez = jugadores[3]  # Asignamos el rol de juez
    espia = jugadores[4]  # Asignamos el rol de espía
    ciudadanos = jugadores[5:]

    roles[mafioso] = "Mafioso"
    roles[doctor] = "Doctor"
    roles[detective] = "Detective"
    roles[juez] = "Juez"  # Rol de juez asignado
    roles[espia] = "Espía"  # Rol de espía asignado
    for ciudadano in ciudadanos:
        roles[ciudadano] = "Ciudadano"

    await mafioso_channel.set_permissions(mafioso, read_messages=True, send_messages=True)
    await doctor_channel.set_permissions(doctor, read_messages=True, send_messages=True)
    await detective_channel.set_permissions(detective, read_messages=True, send_messages=True)
    await mafioso_channel.set_permissions(juez, read_messages=True, send_messages=True)  # Permisos para el juez
    await mafioso_channel.set_permissions(espia, read_messages=True, send_messages=True)  # Permisos para el espía

    for jugador, rol in roles.items():
        try:
            mensaje = f"🎭 Tu rol en la partida es: **{rol}**.\n"
            if rol == "Mafioso":
                mensaje += f"😈 Puedes matar a alguien cada noche en: {mafioso_channel.jump_url}"
            elif rol == "Doctor":
                mensaje += f"🩺 Puedes salvar a un jugador cada noche en: {doctor_channel.jump_url}"
            elif rol == "Detective":
                mensaje += f"🔍 Puedes investigar a un jugador en: {detective_channel.jump_url}"
            elif rol == "Juez":
                mensaje += f"⚖️ Eres el Juez. Puedes eliminar a un jugador en cualquier momento."
            elif rol == "Espía":
                mensaje += f"👁️ Eres el Espía. Puedes investigar la identidad de un jugador durante la noche."
            await jugador.send(mensaje)
        except:
            await ctx.send(f"⚠️ No pude enviar un mensaje privado a {jugador.mention}. Activa tus DMs.")

    await ctx.send("🏁 ¡La partida ha comenzado! La primera noche inicia ahora.")
    await noche(ctx)


# Cuando un jugador es eliminado (por votación o por el mafioso) (Nuevo codigo VALEN)
async def eliminar_jugador(ctx, jugador_eliminado, jugador_que_elimina):
    """Elimina a un jugador y otorga puntos a quien lo eliminó."""
    if jugador_eliminado != jugador_que_elimina:
        # Asignamos puntos al jugador que elimina
        puntos[jugador_que_elimina] = puntos.get(jugador_que_elimina, 0) + 10
        await ctx.send(f"🎯 **{jugador_que_elimina.mention}** ha ganado 10 puntos por eliminar a **{jugador_eliminado.mention}**.")
    else:
        await ctx.send(f"⚠️ **{jugador_que_elimina.mention}** no puede eliminarse a sí mismo.")
    
    # Eliminar al jugador eliminado
    jugadores.remove(jugador_eliminado)
    del roles[jugador_eliminado]

    await ctx.send(f"🔪 **{jugador_eliminado.mention}** ha sido eliminado. Era **{roles[jugador_eliminado]}**.")

# Comando para asignar el rol de Juez y Espía
@bot.command()
async def asignar_roles(ctx):
    """Asigna roles adicionales como Juez y Espía."""
    if len(jugadores) < 6:
        await ctx.send("⚠️ Se necesitan al menos 6 jugadores para asignar los roles de Juez y Espía.")
        return

    random.shuffle(jugadores)

    # Asignación de roles
    global juez, espia
    juez = jugadores[4]  # El quinto jugador es el Juez
    espia = jugadores[5]  # El sexto jugador es el Espía

    roles[juez] = "Juez"
    roles[espia] = "Espía"

    await ctx.send(f"⚖️ **{juez.mention}** es el Juez y 👁️ **{espia.mention}** es el Espía.")
    await ctx.send("Los jugadores restantes son ciudadanos.")

# Comando para eliminar a un jugador (solo lo puede usar el Juez)
@bot.command()
async def eliminar_juez(ctx, miembro: discord.Member):
    """Permite al juez eliminar a un jugador."""
    if ctx.author != juez:
        await ctx.send("⚠️ Solo el Juez puede usar este comando.")
        return

    if not esta_vivo(miembro):
        await ctx.send(f"⚠️ {miembro.mention} ya está muerto.")
        return

    jugadores.remove(miembro)
    del roles[miembro]
    await ctx.send(f"⚖️ **{miembro.mention}** ha sido eliminado por el Juez. Era **{roles.get(miembro)}**.")
    await noche(ctx)

# Comando para investigar a un jugador (solo lo puede usar el Espía durante la noche)
@bot.command()
async def investigar(ctx, miembro: discord.Member):
    """Permite al espía investigar a un jugador durante la noche."""
    if ctx.author != espia or fase != "noche":  # Asegúrate de que la fase sea "noche"
        await ctx.send("⚠️ Solo el Espía puede usar este comando durante la noche.")
        return

    if not esta_vivo(miembro):
        await ctx.send(f"⚠️ {miembro.mention} ya está muerto.")
        return

    rol_investigado = roles.get(miembro)
    await ctx.send(f"👁️ El Espía ha investigado a {miembro.mention} y ha descubierto que su rol es: **{rol_investigado}**.")

@bot.command()
async def matar(ctx, miembro: discord.Member):
    """Permite al mafioso matar a un jugador durante la noche."""
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

    if jugador_muerto is not None:
        await ctx.send(f"⚠️ Ya has elegido a {jugador_muerto.mention}. Espera al amanecer.")
        return

    if miembro == ctx.author:
        await ctx.send("⚠️ No puedes matarte a ti mismo.")
        return

    if not esta_vivo(miembro):
        await ctx.send(f"⚠️ {miembro.mention} ya está muerto. Elige a alguien vivo.")
        return

    jugador_muerto = miembro

    await ctx.send(f"🕵️‍♂️ El mafioso ha elegido a {miembro.mention}. Se procesará al amanecer.")

    await ctx.send(f"🕵️‍♂️ Has elegido a {miembro.mention}. El asesinato se procesará al amanecer.")


@bot.command()
async def salvar(ctx, miembro: discord.Member):
    global jugador_muerto, jugador_salvado

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
    """Comando para votar por un jugador durante el día."""
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

    if modo_rapido and len(votos) == len(jugadores):
        await contar_votos(ctx)

    
    # Si todos los jugadores vivos han votado, contar los votos
    #if len(votos) == len(jugadores):
    #   await contar_votos(ctx)

async def temporizador_votacion(ctx):
    await asyncio.sleep(tiempo_votacion)
    if fase == "día" and votos:
        await ctx.send("⏱ Se acabó el tiempo de votación.")
        await contar_votos(ctx)
    elif fase == "día" and not votos:
        await ctx.send("⏱ Se acabó el tiempo. Nadie votó. Pasamos a la noche.")
        await noche(ctx)

def asignar_puntos_ganadores(jugadores, ganadores_ids):
    print(f"Asignando puntos. Jugadores: {[j.name for j in jugadores]}, Ganadores IDs: {ganadores_ids}")
    for jugador in jugadores:
        puntos = 10 if jugador.id in ganadores_ids else 2
        print(f"Dando {puntos} puntos a {jugador.name}")
        agregar_puntos(jugador, puntos)

def agregar_puntos(jugador, puntos_nuevos):
    print(f"Agregando {puntos_nuevos} puntos a {jugador.name} (ID: {jugador.id})")
    try:
        with open("ranking.json", "r") as f:
            puntos_actuales = json.load(f)
            print(f"Puntos actuales antes de agregar: {puntos_actuales}")
    except FileNotFoundError:
        puntos_actuales = {}
        print("Archivo ranking.json no encontrado, creando uno nuevo.")

    id_str = str(jugador.id)
    puntos_actuales[id_str] = puntos_actuales.get(id_str, 0) + puntos_nuevos

    with open("ranking.json", "w") as f:
        json.dump(puntos_actuales, f)
        print(f"Puntos guardados: {puntos_actuales}")

@bot.command()
async def mafia(ctx, subcomando: str, *args):
    print(f"**[DEBUG MAFIA COMANDO]** Subcomando recibido: {subcomando}, Args: {args}")
    if subcomando == "ranking":
        try:
            with open("ranking.json", "r") as f:
                puntos = json.load(f)
                print(f"**[DEBUG RANKING]** Contenido de ranking.json al leer: {puntos}")  # Log detallado
        except FileNotFoundError:
            puntos = {}
            print("**[DEBUG RANKING]** Archivo ranking.json no encontrado al leer.")

        if not puntos:
            await ctx.send("⚠️ No hay puntuaciones registradas.")
            return

        print("**[DEBUG RANKING]** Puntos leídos correctamente. Tipo: {type(puntos)}, Contenido: {puntos}") # Verificar el diccionario

        ranking_ordenado = sorted(puntos.items(), key=lambda x: x[1], reverse=True)
        print(f"**[DEBUG RANKING]** Ranking ordenado: {ranking_ordenado}") # Ver la lista ordenada

        mensaje = "🏆 **Ranking de jugadores:**\n"
        for i, (jugador_id, puntos_jugador) in enumerate(ranking_ordenado[:10], start=1):
            print(f"**[DEBUG RANKING]** Procesando jugador ID: {jugador_id}, Puntos: {puntos_jugador}, Tipo ID: {type(jugador_id)}, Tipo Puntos: {type(puntos_jugador)}") # Detalles del jugador
            try:
                miembro = await ctx.guild.fetch_member(int(jugador_id))
                if miembro:
                    mensaje += f"{i}. {miembro.display_name} - {puntos_jugador} puntos\n"
                else:
                    mensaje += f"{i}. Jugador Desconocido (ID: {jugador_id}) - {puntos_jugador} puntos\n"
            except Exception as e:
                print(f"**[DEBUG RANKING]** Error al obtener miembro para ID {jugador_id}: {e}") # Capturar errores al buscar miembro

        await ctx.send(mensaje)

def guardar_puntos():
    with open(archivo_puntos, 'w') as f:
        json.dump(puntos, f)

def cargar_puntos():
    global puntos
    if os.path.exists(archivo_puntos):
        with open(archivo_puntos, 'r') as f:
            puntos = json.load(f)

def agregar_puntos(jugador, puntos_nuevos):
    jugador_id = str(jugador.id)
    if jugador_id in puntos:
        puntos[jugador_id]["puntos"] += puntos_nuevos
    else:
        puntos[jugador_id] = {"nombre": jugador.name, "puntos": puntos_nuevos}
    guardar_puntos()


@bot.command()
async def terminar_partida(ctx):
    global jugadores, roles, votos, mafioso_channel, doctor_channel, detective_channel

    ganadores_ids = []
    if mafioso not in jugadores:
        ganadores_ids = [jugador.id for jugador in jugadores if roles.get(jugador) != "Mafioso"]
        await ctx.send("🎉 ¡El mafioso ha sido eliminado! **Los ciudadanos ganan.**")
    elif len(jugadores) == 1 and mafioso in jugadores:
        ganadores_ids = [mafioso.id]
        await ctx.send("🔪 El mafioso ha eliminado a todos. **Gana el mafioso.** 😈")

    asignar_puntos_ganadores(jugadores, ganadores_ids)

    await ctx.send("🏁 La partida ha terminado. Usa `!mafia crear X` para empezar otra.")

    for channel in [mafioso_channel, doctor_channel, detective_channel]:
        if channel:
            await channel.delete()

    jugadores = []
    roles = {}
    votos = {}

@bot.command()
async def mafia_ranking(ctx):
    cargar_puntos()
    if not puntos:
        await ctx.send("📊 No hay puntos registrados todavía.")
        return

    ranking_ordenado = sorted(puntos.items(), key=lambda x: x[1]["puntos"], reverse=True)
    
    mensaje = "**🏆 Ranking de Mafia 🏆**\n\n"
    for i, (user_id, data) in enumerate(ranking_ordenado[:10], 1):
        mensaje += f"{i}. **{data['nombre']}** - {data['puntos']} puntos\n"
    
    await ctx.send(mensaje)

@bot.command(name='ranking')
async def mostrar_ranking(ctx):
    cargar_puntos()
    if not puntos:
        await ctx.send("📊 No hay puntos registrados todavía.")
        return

    ranking_ordenado = sorted(puntos.items(), key=lambda x: x[1]["puntos"], reverse=True)

    mensaje = "**🏆 Ranking de Mafia 🏆**\n\n"
    for i, (user_id, data) in enumerate(ranking_ordenado[:10], 1):
        mensaje += f"{i}. **{data['nombre']}** - {data['puntos']} puntos\n"

    await ctx.send(mensaje)

@bot.command()
async def modo_rapido_on(ctx):
    global modo_rapido
    modo_rapido = True
    await ctx.send("⚡ Modo rápido activado. Las votaciones tendrán un tiempo límite.")

@bot.command()
async def modo_rapido_off(ctx):
    global modo_rapido
    modo_rapido = False
    await ctx.send("🐢 Modo rápido desactivado. Las votaciones no tendrán límite de tiempo.")


bot.run("MTM1NDkxOTM1MjI1OTg0MjA3Ng.GVqEnI.wnakazEyFJsZOblj5OANNaXexpmJ0WhZRmPqR4")