import asyncio
import json

from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.errors import SessionPasswordNeededError, FloodWaitError

import os
from dotenv import load_dotenv
load_dotenv()


def _has_image(message) -> bool:
    if not message.media:
        return False

    return isinstance(message.media, MessageMediaPhoto)


class APODFetcher:
    def __init__(self, api_id: int, api_hash: str, session_name: str = "session"):
        """
        Initialize the APOD fetcher using Telethon
        
        Args:
            api_id: Telegram API ID from https://my.telegram.org
            api_hash: Telegram API Hash from https://my.telegram.org
            session_name: Name for the session file (persistent authentication)
        """
        self.client = TelegramClient(session_name, api_id, api_hash)

        self.image_path = os.path.join('.', 'image.jpg')


    async def start(self):
        await self.client.start()
        print("✅ Successfully connected to Telegram")


    async def get_channel_messages(self, channel_username: str, limit: int = 10) -> list:
        """
        Fetch messages from a Telegram channel
        
        Args:
            channel_username: Channel username (without @)
            limit: Number of recent messages to fetch
            
        Returns:
            List of messages
        """
        try:
            # Get the channel entity
            channel = await self.client.get_entity(channel_username)
            print(f"📡 Fetching last {limit} messages from @{channel_username}")
            
            # Fetch messages
            messages = []
            async for message in self.client.iter_messages(channel, limit=limit):
                messages.append(message)
            
            print(f"✅ Fetched {len(messages)} messages")
            return messages
            
        except Exception as e:
            print(f"❌ Error fetching messages: {e}")
            return []

    async def fetch(self, channel_username: str, limit: int = 10):
        messages = await self.get_channel_messages(channel_username, limit)

        message = None
        for m in messages:
            if _has_image(m):
                message = m
                break

        if not message:
            print("❌ No messages with images found")
            return
        
        await message.download_media(self.image_path)

        title = message.raw_text.split('\n')[2]
        explanation = message.raw_text.split('\n')[5]

        data = {
            'title': title,
            'explanation': explanation,
        }

        with open('data.json', 'w') as f:
            f.write(json.dumps(data, indent=4))


    async def close(self):
        await self.client.disconnect()
        print("🔌 Disconnected from Telegram")


async def main():
    API_ID = int(os.getenv('API_ID')) # Get from https://my.telegram.org
    API_HASH = os.getenv('API_HASH') # Get from https://my.telegram.org
    CHANNEL_USERNAME = 'apod_telegram' # Channel username without @
    MESSAGE_LIMIT = 5 # Number of recent messages to check
    
    fetcher = APODFetcher(API_ID, API_HASH)
    
    try:
        await fetcher.start()
        await fetcher.fetch(CHANNEL_USERNAME, MESSAGE_LIMIT)
    except SessionPasswordNeededError:
        print("❌ Two-factor authentication is enabled. Please enter your password.")
    except FloodWaitError as e:
        print(f"❌ Rate limited. Please wait {e.seconds} seconds before trying again.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
