import discord
from roles import asignar_roles

partidas = {}

async def crear_partida(message, num_jugadores: int):
    """Crea una partida de Mafia"""
    if num_jugadores < 4:
        await message.channel.send("⚠️ El número mínimo de jugadores es 4.")
        return None  # En caso de error, retorna None

    # Crear la partida
    partida_id = len(partidas) + 1
    partidas[partida_id] = {
        'jugadores': [],
        'num_jugadores': num_jugadores,
        'estado': 'creada'
    }

    # Verificar y mostrar el diccionario de partidas
    print(f"[DEBUG] Partidas actuales: {partidas}")  # Agrega este print para verificar las partidas
    await message.channel.send(f"🎉 ¡Partida {partida_id} creada con {num_jugadores} jugadores! Usa `!mafia unirse {partida_id}` para unirte.")
    
    # Devuelve el ID de la partida creada para usarlo más tarde
    return partida_id

async def unirse_partida(message, partida_id: int):
    """Permite a un jugador unirse a una partida existente"""
    print(f"[DEBUG] Comando 'unirse' recibido con partida ID {partida_id}")  # Depuración
    if partida_id not in partidas:
        await message.channel.send("❌ La partida no existe. Asegúrate de usar un ID válido.")
        return

    partida = partidas[partida_id]

    if len(partida['jugadores']) >= partida['num_jugadores']:
        await message.channel.send("⚠️ La partida ya está llena. No puedes unirte.")
        return

    if message.author.id in partida['jugadores']:
        await message.channel.send("🔹 Ya estás en esta partida.")
        return
    
    partida['jugadores'].append(message.author.id)
    await message.channel.send(f"✅ {message.author.mention} se ha unido a la partida {partida_id}. ({len(partida['jugadores'])}/{partida['num_jugadores']}) jugadores.")

async def iniciar_partida(message, partida_id: int, bot: discord.Client):
    """Inicia la partida y envía los roles a los jugadores"""
    print(f"[DEBUG] Comando 'iniciar' recibido con partida ID {partida_id}")  # Depuración

    if partida_id not in partidas:
        await message.channel.send("❌ La partida no existe.")
        print(f"[DEBUG] No existe partida con ID {partida_id}")
        return

    partida = partidas[partida_id]

    print(f"[DEBUG] Jugadores en la partida: {partida['jugadores']}")  # Verificación de jugadores
    if len(partida['jugadores']) < partida['num_jugadores']:
        await message.channel.send(f"⚠️ Aún no se han unido todos los jugadores. Necesitas {partida['num_jugadores']} jugadores.")
        print(f"[DEBUG] Número de jugadores en la partida: {len(partida['jugadores'])} / {partida['num_jugadores']}")
        return

    # Asignamos los roles a los jugadores
    try:
        roles_asignados = asignar_roles(partida['jugadores'])
        print(f"[DEBUG] Roles asignados: {roles_asignados}")  # Depuración
    except ValueError as e:
        await message.channel.send(str(e))  # Enviar mensaje si hay menos de 4 jugadores
        print(f"[DEBUG] Error al asignar roles: {str(e)}")
        return
    except Exception as e:
        await message.channel.send(f"❌ Ocurrió un error al asignar roles: {str(e)}")
        print(f"[ERROR] Error al asignar roles: {str(e)}")
        return

    # Enviar mensajes privados con el rol asignado
    for jugador_id, rol in roles_asignados.items():
        try:
            # Usamos el bot directamente, no 'message.client'
            jugador = await bot.fetch_user(jugador_id)  # Obtener el jugador por su ID
            await jugador.send(f"🔹 Tu rol en la partida {partida_id} es: **{rol}**")
        except discord.Forbidden:
            await message.channel.send(f"⚠️ No pude enviar un mensaje privado a <@{jugador_id}>. Activa los mensajes privados.")
            print(f"[DEBUG] No pude enviar mensaje a <@{jugador_id}> - Puede que tenga los DM desactivados.")
        except Exception as e:
            await message.channel.send(f"❌ Ocurrió un error al enviar el mensaje privado a <@{jugador_id}>.")
            print(f"[ERROR] Error al enviar mensaje privado a <@{jugador_id}>: {e}")

    await message.channel.send(f"✅ ¡La partida {partida_id} ha comenzado! Revisa tu mensaje privado para conocer tu rol.")
