import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables del archivo .env
TOKEN = os.getenv('DISCORD_TOKEN')

# Asegúrate de que el token no sea None antes de ejecutar el bot
if TOKEN is None:
    raise ValueError("❌ No se encontró el token. Verifica el archivo .env")

# Aquí inicia el bot
import discord

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Bot conectado como {client.user}')

client.run(TOKEN)
