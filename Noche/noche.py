import asyncio
import discord
import random

elecciones_mafiosos = {}
partidas = {}

async def matar(message, partida_id: int, jugador_a_matar: str):
    """Permite a los mafiosos elegir a un jugador para matar durante la Noche."""
    partida = partidas.get(partida_id)
    
    if not partida:
        await message.channel.send("❌ La partida no existe.")
        return
    
    # Verificamos si el usuario es un mafioso
    if message.author.id not in [jugador_id for jugador_id, rol in partida['roles_asignados'].items() if rol == "Mafioso"]:
        await message.channel.send("❌ No eres un mafioso. Solo los mafiosos pueden hacer esta acción.")
        return

    # Guardamos la elección del mafioso
    elecciones_mafiosos[message.author.id] = jugador_a_matar

    await message.channel.send(f"✅ Has elegido matar a {jugador_a_matar}.")

async def fase_noche(partida_id: int, bot: discord.Client):
    """Gestiona la fase de Noche en la partida de Mafia."""
    partida = partidas.get(partida_id)
    if not partida:
        return "❌ La partida no existe."

    # Verificamos los mafiosos en la partida
    mafiosos = [jugador_id for jugador_id, rol in partida['roles_asignados'].items() if rol == "Mafioso"]

    if not mafiosos:
        return "❌ No hay mafiosos en esta partida."

    # Enviar mensaje a los mafiosos en canales privados
    for mafioso_id in mafiosos:
        jugador = await bot.fetch_user(mafioso_id)
        try:
            await jugador.send("🌙 ¡Es la fase de Noche! Elige a un jugador para eliminar. Usa !matar [jugador].")
        except discord.Forbidden:
            await jugador.send(f"⚠️ No pude enviarte un mensaje privado, asegúrate de tenerlos habilitados.")

    # Esperar las elecciones de los mafiosos
    await asyncio.sleep(30)  # Ajusta el tiempo de espera según lo necesites

    # Anunciar la eliminación
    if elecciones_mafiosos:
        # Contamos las elecciones para determinar quién fue elegido
        votos = {}
        for jugador_id in elecciones_mafiosos.values():
            votos[jugador_id] = votos.get(jugador_id, 0) + 1

        # Determinamos al jugador con más votos
        jugador_eliminado_id = max(votos, key=votos.get)

        jugador_eliminado = await bot.fetch_user(jugador_eliminado_id)
        await partida["canal"].send(f"🌅 ¡Amaneció! {jugador_eliminado.mention} ha sido eliminado por los mafiosos.")
        
        # Aquí eliminaríamos al jugador de la partida y actualizamos el estado
        partida['jugadores'] = [jugador_id for jugador_id in partida['jugadores'] if jugador_id != jugador_eliminado_id]
        
        # Si ya no quedan jugadores, finalizar la partida
        if len(partida['jugadores']) == 0:
            await partida["canal"].send("❌ Todos los jugadores han sido eliminados. La partida ha terminado.")

    # Limpiar la elección de los mafiosos
    elecciones_mafiosos.clear()

    return "✅ La fase de Noche ha terminado."
