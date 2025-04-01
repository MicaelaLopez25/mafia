import asyncio
import discord
import random
elecciones_mafiosos = {}


async def fase_noche(partida, bot):
    """Gestiona la fase de Noche en la partida de Mafia."""


##Verificamos los mafiosos en la partida
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


##Esperar las elecciones de los mafiosos
    await asyncio.sleep(30)  # Aquí puedes ajustar el tiempo de espera


    # Anunciar la eliminación
    if elecciones_mafiosos:
        jugador_eliminado = elecciones_mafiosos.get(mafiosos[0])  # Suponiendo que solo haya 1 elección final
        if jugador_eliminado:
            jugador = await bot.fetch_user(jugador_eliminado)
            await partida["canal"].send(f"🌅 ¡Amaneció! {jugador.mention} ha sido eliminado por los mafiosos.")
            # Aquí agregaríamos lógica para eliminar al jugador de la partida y cambiar la fase


    # Limpiar la elección de los mafiosos
    elecciones_mafiosos.clear()


    return "✅ La fase de Noche ha terminado."


