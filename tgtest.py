import asyncio
import json
from telethon import TelegramClient
from telethon.tl.types import PeerChannel, PeerColor

# Load the Telegram API credentials
def load_credentials():
    with open('credentials.json') as f:
        return json.load(f)

async def test_peer_color():
    credentials = load_credentials()
    api_id = credentials['api_id']
    api_hash = credentials['api_hash']

    # Create a Telegram client
    client = TelegramClient('test_session', api_id, api_hash)

    async with client:
        channel_usernames = [
            'Team_insane_Pakistan',  # Example channel usernames
            'RCH_NET'
        ]

        for username in channel_usernames:
            try:
                entity = await client.get_entity(username)
                print(f"\n===========================")
                print(f"Chat/Channel/User Name: {entity.title or entity.username}")
                print(f"Entity ID: {entity.id}")
                print(f"Is Channel: {isinstance(entity, PeerChannel)}")

                # Fetch the latest message
                message = await client.get_messages(entity, limit=1)
                message = message[0]

                print(f"\n--- Latest Message Fields ---")
                print(message.to_dict())

                # Checking for PeerColor
                peer = message.peer_id
                if isinstance(peer, PeerChannel):
                    print(f"\n--- Peer Info ---")
                    print(peer)

                    # Attempt to get peer color if available
                    if hasattr(peer, 'color') and isinstance(peer.color, PeerColor):
                        print(f"Peer Color: #{peer.color.color:06x}")
                    else:
                        print("No PeerColor attribute available.")
            except Exception as e:
                print(f"Error for {username}: {e}")

# Run the test script
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_peer_color())
