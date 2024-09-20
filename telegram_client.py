from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import FloodWaitError, ChannelPrivateError
from telethon.tl.types import Channel, User, Chat
import asyncio
import re
from utils import print_warning, print_success, print_info, print_error
from tqdm import tqdm

def create_client(api_id, api_hash, phone_number):
    return TelegramClient('session_name', api_id, api_hash)

class TelegramClientWrapper:
    def __init__(self, client):
        self.client = client

    async def retry_with_flood_control(self, coroutine, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                return await coroutine
            except FloodWaitError as e:
                wait_time = max(e.seconds, 30)
                print_warning(f"FloodWaitError encountered. Waiting for {wait_time} seconds. (Attempt {retries + 1}/{max_retries})")
                
                # Create and update progress bar
                with tqdm(total=wait_time, unit="s", desc="Waiting", ncols=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
                    for _ in range(wait_time):
                        await asyncio.sleep(1)
                        pbar.update(1)
                
                retries += 1
        raise Exception(f"Max retries ({max_retries}) exceeded due to FloodWaitError")

    async def join_channel(self, channel_manager, link):
        cleaned_link = self.clean_link(link)
        if not cleaned_link:
            print_warning(f"Invalid link format: {link}")
            return False

        async def join_attempt():
            entity = await self.client.get_entity(cleaned_link)
            entity_name = await self.get_entity_name(entity)
            
            if isinstance(entity, (Channel, Chat)):
                await self.client(JoinChannelRequest(entity))
                print_success(f"Successfully joined channel: {entity_name}")
                channel_manager.mark_as_joined(cleaned_link)
                return True
            elif isinstance(entity, User):
                print_info(f"Entity {entity_name} is a user, no need to join")
                return True
            else:
                print_warning(f"Unknown entity type for {entity_name}")
                return False

        try:
            return await self.retry_with_flood_control(join_attempt())
        except ChannelPrivateError:
            print_warning(f"Cannot join private channel {cleaned_link} without an invite link")
            return False
        except Exception as e:
            print_error(f"Failed to process entity {cleaned_link}: {e}")
            return False

    async def get_entity_name(self, entity):
        if isinstance(entity, User):
            return f"@{entity.username}" if entity.username else f"User({entity.id})"
        elif isinstance(entity, (Channel, Chat)):
            return entity.title or f"Channel({entity.id})"
        else:
            return f"Unknown({type(entity).__name__})"

    async def scrape_messages(self, entity, message_limit, keywords, channel_manager, affiliated_channel=None):
        messages = []
        entity_name = await self.get_entity_name(entity)

        async def scrape_attempt():
            nonlocal messages
            async for message in self.client.iter_messages(entity, limit=message_limit):
                if message.text:
                    if affiliated_channel:
                        print_info(f"Message from {entity_name} <-- {affiliated_channel}: {message.text}")
                    else:
                        print_info(f"Message from {entity_name}: {message.text}")
                    messages.append([message.sender_id, message.date, message.text, None, None])
                    
                    links = self.extract_channel_links(message.text)
                    for link in links:
                        channel_manager.add_channel(link, source_channel=entity_name)
                
                await asyncio.sleep(0.1)
            return messages, entity_name

        try:
            return await self.retry_with_flood_control(scrape_attempt())
        except Exception as e:
            print_error(f"Error scraping entity {entity_name}: {e}")
            return messages, entity_name

    @staticmethod
    def clean_link(link):
        if not link or not isinstance(link, str):
            return None
        
        link = link.split(')')[0].strip()
        
        if re.match(r'^[a-zA-Z0-9_]{5,}$', link):
            return link
        
        match = re.search(r't\.me/(?:joinchat/)?([a-zA-Z0-9_-]+)', link)
        if match:
            username_or_hash = match.group(1)
            
            if 'joinchat' in link:
                return f'https://t.me/joinchat/{username_or_hash}'
            
            return username_or_hash
        
        return None

    @staticmethod
    def extract_channel_links(text):
        if not text or not isinstance(text, str):
            return []
        pattern = r't\.me/(?:joinchat/)?[a-zA-Z0-9_-]+'
        return re.findall(pattern, text)

    async def get_entity(self, link):
        async def get_entity_attempt():
            return await self.client.get_entity(link)

        return await self.retry_with_flood_control(get_entity_attempt())