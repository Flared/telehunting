import asyncio
import argparse
from config import load_config, create_default_config
from telegram_client import create_client, TelegramClientWrapper
from channel_manager import ChannelManager
from message_processor import CybersecuritySentimentAnalyzer
from batch_processor import BatchProcessor
from utils import print_header, print_info, print_error, banner, ensure_nltk_data
from datetime import datetime
from telethon.errors import FloodWaitError

async def run_scraper(client_wrapper, config, message_depth, channel_depth, rate_limit):
    channel_manager = ChannelManager()
    cybersecurity_sia = CybersecuritySentimentAnalyzer()
    batch_processor = BatchProcessor(cybersecurity_sia=cybersecurity_sia)
    
    for link in config['initial_channel_links']:
        channel_manager.add_channel(link)
    
    start_time = datetime.now()
    print_header(f"Scraping started at {start_time}")

    depth = 0
    while channel_manager.has_unprocessed_channels() and depth < channel_depth:
        print_header(f"Crawling at depth {depth + 1}/{channel_depth}")
        channel_manager.display_status()
        
        await process_channels(client_wrapper, channel_manager, message_depth, config['message_keywords'], batch_processor, rate_limit)
        
        depth += 1
        await asyncio.sleep(5)
    
    end_time = datetime.now()
    duration = end_time - start_time
    print_header(f"Scraping completed at {end_time}")
    print_info(f"Total duration: {duration}")
    print_info(f"Total messages scraped: {batch_processor.total_messages}")
    print_info(f"Total channels processed: {len(channel_manager.processed_channels)}")

    batch_processor.finalize()

async def process_channels(client_wrapper, channel_manager, message_depth, keywords, batch_processor, rate_limit):
    while channel_manager.has_unprocessed_channels():
        link = channel_manager.get_next_channel()
        affiliated_channel = channel_manager.get_affiliation(link)
        try:
            join_success = await client_wrapper.join_channel(channel_manager, link)
            if join_success:
                entity = await client_wrapper.get_entity(link)
                entity_messages, channel_name = await client_wrapper.scrape_messages(entity, message_depth, keywords, channel_manager, affiliated_channel)
                batch_processor.add_messages(entity_messages, channel_name, affiliated_channel)
            else:
                print_error(f"Skipping entity {link} due to joining failure")
        except Exception as e:
            print_error(f"Failed to process entity {link}: {e}")
        finally:
            channel_manager.mark_as_processed(link)
        
        await asyncio.sleep(rate_limit)

if __name__ == "__main__":
    banner()
    ensure_nltk_data()

    parser = argparse.ArgumentParser(description='Telegram Content Crawler')
    parser.add_argument('--config', type=str, default='config.json', help='Path to the configuration file')
    parser.add_argument('--message-depth', type=int, default=1000, help='Number of messages to crawl per channel')
    parser.add_argument('--channel-depth', type=int, default=2, help='Depth of channel crawling')
    parser.add_argument('--api-id', type=str, help='API ID for Telegram client')
    parser.add_argument('--api-hash', type=str, help='API hash for Telegram client')
    parser.add_argument('--phone-number', type=str, help='Phone number for Telegram client')
    parser.add_argument('--rate-limit', type=float, default=1.0, help='Rate limit in seconds between channel processing')
    args = parser.parse_args()

    config = load_config(args.config)
    if config is None:
        user_input = input(f"Config file '{args.config}' not found. Create a default config? (y/n): ")
        if user_input.lower() == 'y':
            config = create_default_config(args.config)
        else:
            print_error("Please provide a valid config file. Exiting.")
            exit(1)

    client = create_client(args.api_id, args.api_hash, args.phone_number)
    client_wrapper = TelegramClientWrapper(client)

    with client:
        client.loop.run_until_complete(run_scraper(client_wrapper, config, args.message_depth, args.channel_depth, args.rate_limit))
