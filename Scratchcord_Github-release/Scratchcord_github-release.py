# Brought to you by Nexus
from scratchcloud import CloudClient, CloudChange
import threading
import discord
import asyncio
import uuid
import random

# Constants
LETTERS_FILE = r'Scratchcord\Letters\all_letters.txt'
HANDSHAKE_ID = str(random.randrange(1000000000000000,10000000000000000))
HANDSHAKE_VALIDATOR = str(uuid.uuid4())[:-3].upper()

TOKEN = 'Bot token here'
SCRATCH_USERNAME = 'Username here'
SCRATCH_PASSWORD = 'Password here'
SCRATCH_PROJECT_ID = 'Project ID here'
CHANNEL_ID = 1020304050607080900  # Replace with actual chnnel

handshake = ''
status = 0
sender = ''
history = []

# Scratch init
client = CloudClient(SCRATCH_USERNAME, SCRATCH_PROJECT_ID)
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
    print(f'Random UUID: {HANDSHAKE_VALIDATOR}XXX')
    print(f'Key: {HANDSHAKE_ID}')


@client.event
async def on_disconnect():
    print('Scratch hook disconnected')


@client.event
async def on_message(cloud: CloudChange):
    global status, sender, handshake
    if cloud.name == 'Status':
        status = int(cloud.value)

    if cloud.name == '__key':
        print('Incoming validation')
        if cloud.value == HANDSHAKE_ID:
            await client.set_cloud('__key', '1')
            handshake = HANDSHAKE_VALIDATOR + sender[:3].upper()
            print('Validation success')
            print(f'Handshake validator: {handshake}')


    elif cloud.name == 'Sender':
        sender = decrypt(cloud.value)

    elif cloud.name == 'Value' and handshake == HANDSHAKE_VALIDATOR + sender[:3].upper():
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
    await channel.send(f'(Scratch) {message}')


@bot.event
async def on_message(message):
    global history
    channel = bot.get_channel(CHANNEL_ID)
    print('Message!')

    if message.author != bot.user:
        content = [message.content async for message in channel.history(limit=1)][0]
        formatted_message = f'(Discord) {str(message.author)[:-2]}: {content}'
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
scratchthread = threading.Thread(target=client.run, args=(SCRATCH_PASSWORD, ))
scratchthread.start()
bot.run(TOKEN)