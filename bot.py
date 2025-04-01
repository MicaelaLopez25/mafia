import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from CreacionDePartida.eventos import crear_partida, unirse_partida, iniciar_partida

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Crear el bot con los permisos adecuados
intents = discord.Intents.default()
intents.message_content = True  # Asegúrate de tener los permisos correctos
bot = commands.Bot(command_prefix='!mafia ', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:  # Ignorar los mensajes enviados por el bot
        return

    # Aquí procesamos el mensaje manualmente
    if message.content.startswith('!mafia'):
        command = message.content.split()[1]  # El comando será la segunda palabra

        # Comando crear
        if command == 'crear' and len(message.content.split()) == 3:
            num_jugadores = int(message.content.split()[2])
            await crear_partida(message, num_jugadores)

        # Comando unirse
        elif command == 'unirse' and len(message.content.split()) == 3:
            partida_id = int(message.content.split()[2])
            await unirse_partida(message, partida_id)

        # Comando iniciar
        elif command == 'iniciar' and len(message.content.split()) == 3:
            partida_id = int(message.content.split()[2])
            await iniciar_partida(message, partida_id, bot)  # Pasamos 'bot' a la función iniciar_partida

        # Comando desconocido
        else:
            await message.channel.send("❌ Comando no reconocido o parámetros incorrectos.")
    
    # Responder al mensaje 'hola'
    if message.content.lower() == 'hola':
        await message.channel.send('¡Hola! Soy un bot hecho en Python. 🤖')

bot.run(TOKEN)
