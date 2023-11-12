# Brought to you by Nexus
from scratchcloud import CloudClient, CloudChange
import threading
import discord
import asyncio

# Constants
LETTERS_FILE = r'Scratchcord\Letters\all_letters.txt'

# Change these for your actual secrets
TOKEN = 'Y0UR-T0K3N-H3R3'
SCRATCH_USERNAME = 'Username here'
SCRATCH_PASSWORD = 'SuperSecretPassword!'
CHANNEL_ID = 12345678901234567890  # Channel id
HANDSHAKE_ID = 1234567890987654321234567890  # Customize handshake ID and validator
HANDSHAKE_VALIDATOR = '290318123123414812'

handshake = ''
status = 0
sender = ''
history = []

# Scratch init
client = CloudClient('CastyEZ', '897885598')
letters = []


def decrypt(numbers: int):
    global letters
    result = ''
    if len(letters) == 0:
        with open(LETTERS_FILE, 'r') as file:
            letters = [i[:-1] for i in file.readlines()]
    return ''.join([result + letters[int(str(numbers)[i:i + 2]) - 1] for i in range(0, len(str(numbers)), 2)] if len(str(numbers)) % 2 == 0 else 'Error')


def encrypt(words: str):
    global letters
    if len(letters) == 0:
        with open(LETTERS_FILE, 'r') as file:
            letters = [i[:-1] for i in file.readlines()]
    return ''.join([str(letters.index(words[i]) + 1).rjust(2, '0') for i in range(len(words))])


# Scratch hooks
@client.event
async def on_connect():
    print('Scratch hook connected')


@client.event
async def on_disconnect():
    print('Scratch hook disconnected')


@client.event
async def on_message(cloud: CloudChange):
    global status, sender
    if cloud.name == 'Status':
        status = int(cloud.value)

    if cloud.name == '__key':
        if cloud.value == HANDSHAKE_ID:
            await client.set_cloud('__key', HANDSHAKE_VALIDATOR)

    elif cloud.name == 'Sender':
        sender = decrypt(cloud.value)

    elif cloud.name == 'Value' and handshake == HANDSHAKE_VALIDATOR:
        if status == 1:  # Post message
            value = decrypt(cloud.value)
            print(f'Request by {sender} to post a message')
            print(f'Decrypted value \'{value}\'')

            bot.loop.create_task(send_message_to_channel(': '.join([sender, value])))

            await client.set_cloud('Status', '0')

        elif status == 2:  # Read message
            value = int(cloud.value)

            print(f'Request by {sender} to read {value} messages')

            max_pack = 3

            await client.set_cloud('Index', '0')
            for i, v in enumerate([encrypt('&'.join(history[:int(value)][i:i + max_pack])) for i in range(0, value, max_pack)]):
                await client.set_cloud('Value', v)
                await client.set_cloud('Status', '9') if i == 0 else None
                await client.set_cloud('Index', str(i + 1))
                await asyncio.sleep(0.7)
            await client.set_cloud('Value', '')
            await client.set_cloud('Status', '0')

# Discord hooks
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
bot = discord.Client(intents=intents)


async def send_message_to_channel(message):
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(message)


@bot.event
async def on_message(message):
    global history
    channel = bot.get_channel(CHANNEL_ID)
    print('Message!')

    if message.author != bot.user:
        content = [message.content async for message in channel.history(limit=1)][0]
        formatted_message = f'{str(message.author)[:-2]}: {content}'
        print(formatted_message)
        await message.delete()
        await channel.send(formatted_message)

    history.clear()
    async for msg in channel.history(limit=30):
        history.append(msg.content)


@bot.event
async def on_ready():
    global history
    channel = bot.get_channel(CHANNEL_ID)
    history = [message.content async for message in channel.history(limit=30)]
    print('Discord bot ready')

# Main loop
scratchthread = threading.Thread(target=client.run, args=('CastyLoz17#HateU',))
scratchthread.start()
bot.run(TOKEN)
