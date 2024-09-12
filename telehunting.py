import asyncio
import re
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import FloodWaitError, ChannelPrivateError
from telethon.tl.types import Channel, User, Channel, Chat
import multiprocessing
from functools import partial
import argparse
import json
import random
import signal
import os
from datetime import datetime
from colorama import init, Fore, Back, Style

init(autoreset=True)

PURPLE_BLUE = '\033[38;2;100;100;255m'
LIGHT_PURPLE = '\033[38;2;200;180;255m'
BOLD_WHITE = '\033[1;37m'

def print_info(message):
    print(f"{PURPLE_BLUE}ℹ {BOLD_WHITE}{message}")

def print_success(message):
    print(f"{LIGHT_PURPLE}✔ {BOLD_WHITE}{message}")

def print_warning(message):
    print(f"{Fore.YELLOW}{Style.BRIGHT}⚠ {BOLD_WHITE}{message}")

def print_error(message):
    print(f"{Fore.RED}✘ {message}")

def print_header(message):
    print(f"\n{PURPLE_BLUE}{Style.BRIGHT}{message}")
    print(f"{PURPLE_BLUE}{'-' * len(message)}{Style.RESET_ALL}")

def print_subheader(message):
    print(f"\n{LIGHT_PURPLE}{Style.BRIGHT}{message}")
    print(f"{LIGHT_PURPLE}{'-' * len(message)}{Style.RESET_ALL}")

def banner():
    print(f"""
          
{Fore.BLUE}{Style.BRIGHT}


                      +++++                      
                    ++{LIGHT_PURPLE}=   +{Style.RESET_ALL}{Fore.BLUE}{Style.BRIGHT}+                     
                    ++{LIGHT_PURPLE}+   ++{Style.RESET_ALL}{Fore.BLUE}{Style.BRIGHT}+                    
                    +++{LIGHT_PURPLE}+++{Style.RESET_ALL}{Fore.BLUE}{Style.BRIGHT}++*                    
                    *+++*+***                    
                     ********                    
                   {LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT}**********                   
                  **{LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT} *********                  
                 ***{LIGHT_PURPLE}##{Fore.BLUE}{Style.BRIGHT}**********                 
               *****{LIGHT_PURPLE}###{Fore.BLUE}{Style.BRIGHT}***********{LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT}              
           *********{LIGHT_PURPLE}####{Fore.BLUE} ******{LIGHT_PURPLE}########{Fore.BLUE}{Style.BRIGHT}          
 ++{LIGHT_PURPLE}+{Fore.BLUE}{Style.BRIGHT}++**************{LIGHT_PURPLE}###   #######{Fore.BLUE}{Style.BRIGHT}  *******++{LIGHT_PURPLE}++{Fore.BLUE}{Style.BRIGHT}++ 
+{LIGHT_PURPLE}++  +{Fore.BLUE}{Style.BRIGHT}**************{LIGHT_PURPLE}#       ##{Fore.BLUE}{Style.BRIGHT} *************  +{LIGHT_PURPLE}{Fore.BLUE}{Style.BRIGHT}++
++{LIGHT_PURPLE}+   +{Fore.BLUE}{Style.BRIGHT}***********  {LIGHT_PURPLE}#       #{Fore.BLUE}{Style.BRIGHT}*************+*  +{LIGHT_PURPLE}{Fore.BLUE}{Style.BRIGHT}++
 +++{LIGHT_PURPLE}++{Fore.BLUE}{Style.BRIGHT}******** {LIGHT_PURPLE}########   ###{Fore.BLUE}{Style.BRIGHT}*************++{LIGHT_PURPLE}++{Fore.BLUE}{Style.BRIGHT}++ 
        {LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT}**{LIGHT_PURPLE}####{Fore.BLUE}{Style.BRIGHT}****** {LIGHT_PURPLE}###{Fore.BLUE}{Style.BRIGHT}***********          
              ************{LIGHT_PURPLE}###{Fore.BLUE}{Style.BRIGHT}*****               
                 **********{LIGHT_PURPLE}##{Fore.BLUE}{Style.BRIGHT}***                 
                  ********* {LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT}**                  
                   ********* *                   
                    ******** {LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT}                   
                    *********                    
                    **+{LIGHT_PURPLE}**{Fore.BLUE}{Style.BRIGHT}+***                    
                    *+{LIGHT_PURPLE}+   +{Fore.BLUE}{Style.BRIGHT}++                    
                     +{LIGHT_PURPLE}+   +{Fore.BLUE}{Style.BRIGHT}++                    
                      ++{LIGHT_PURPLE}+{Fore.BLUE}{Style.BRIGHT}++                      

                    


   
{Style.RESET_ALL}
""")

# Ensure NLTK data is downloaded
def ensure_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        print_info("Downloading NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('vader_lexicon', quiet=True)

# Extract Telegram channel links from messages
def extract_channel_links(text):
    if not text or not isinstance(text, str):
        return []
    pattern = r't\.me/(?:joinchat/)?[a-zA-Z0-9_-]+'
    return re.findall(pattern, text)

# Clean and format channel links
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

# Manage discovered channels
class ChannelManager:
    def __init__(self):
        self.discovered_channels = set()
        self.joined_channels = set()
        self.processed_channels = set()
        self.channel_affiliations = {}
        self.initial_channels = set()

    def add_channel(self, link, source_channel=None):
        cleaned_link = clean_link(link)
        if cleaned_link and cleaned_link not in self.joined_channels and cleaned_link not in self.processed_channels:
            self.discovered_channels.add(cleaned_link)
            if source_channel:
                self.channel_affiliations[cleaned_link] = source_channel
            else:
                self.initial_channels.add(cleaned_link)  # Mark as initial channel if no source

    def mark_as_joined(self, link):
        cleaned_link = clean_link(link)
        if cleaned_link:
            self.joined_channels.add(cleaned_link)
            self.discovered_channels.discard(cleaned_link)

    def mark_as_processed(self, link):
        cleaned_link = clean_link(link)
        if cleaned_link:
            self.processed_channels.add(cleaned_link)
            self.discovered_channels.discard(cleaned_link)

    def has_unprocessed_channels(self):
        return len(self.discovered_channels) > 0

    def get_next_channel(self):
        if self.discovered_channels:
            return self.discovered_channels.pop()
        return None

    def get_affiliation(self, link):
        cleaned_link = clean_link(link)
        return self.channel_affiliations.get(cleaned_link, None)

    def display_status(self):
        print_subheader("Channel Status")
        print(f"  Channels waiting to be processed: {len(self.discovered_channels)}")
        print(f"  Channels joined: {len(self.joined_channels)}")
        print(f"  Channels processed: {len(self.processed_channels)}")

# Join channel by url
async def join_channel(client, channel_manager, link, max_retries=3):
    cleaned_link = clean_link(link)
    if not cleaned_link:
        print_warning(f"Invalid link format: {link}")
        return False

    retries = 0
    while retries < max_retries:
        try:
            entity = await client.get_entity(cleaned_link)
            entity_name = await get_entity_name(entity)
            
            if isinstance(entity, (Channel, Chat)):
                if entity.username:
                    await client(JoinChannelRequest(entity))
                else:
                    print_warning(f"Cannot join private channel {entity_name} without an invite link")
                    return False
            elif isinstance(entity, User):
                print_info(f"Entity {entity_name} is a user, no need to join")
            else:
                print_warning(f"Unknown entity type for {entity_name}")
                return False
            
            print_success(f"Successfully processed entity: {entity_name}")
            channel_manager.mark_as_joined(cleaned_link)
            return True

        except FloodWaitError as e:
            wait_time = min(e.seconds, 30)
            print_warning(f"FloodWaitError encountered. Waiting for {wait_time} seconds. (Attempt {retries + 1}/{max_retries})")
            await asyncio.sleep(wait_time)
        except Exception as e:
            print_error(f"Failed to process entity {cleaned_link}: {e}")
        
        retries += 1
        await asyncio.sleep(1)

    print_warning(f"Max retries exceeded. Failed to process entity: {cleaned_link}")
    return False

# Load configuration
def load_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return None

# Create a default config file, if no config present (providing one anyways for clarity sake)
def create_default_config(config_path):
    default_config = {
        "initial_channel_links": [],
        "message_keywords": [],
        "batch_size": 100
    }
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=4)
    print_success(f"Default config file created at {config_path}")
    print_info("Please edit this file with your channel links and keywords.")
    return default_config

# Home made sentiment lexicon (this is my first time doing this, it may suck)
class CybersecuritySentimentAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.cybersecurity_lexicon = {
            'vulnerability': 2.0,
            'exploit': -3.0,
            'patch': 2.0,
            'hack': -2.0,
            'secure': 3.0,
            'breach': -4.0,
            'protect': 3.0,
            'malware': -3.0,
            'ransomware': -4.0,
            'encryption': 2.0,
            'backdoor': -3.0,
            'firewall': 2.0,
            'phishing': -3.0,
            'authentication': 2.0,
            'threat': -2.0,
            'zero-day': -4.0,
            'security': 1.0,
            'attack': -2.0,
            'defense': 2.0,
            'compromise': -3.0
        }
        self.sia.lexicon.update(self.cybersecurity_lexicon)

    def polarity_scores(self, text):
        return self.sia.polarity_scores(text)

# Global variables
current_batch = []
batch_counter = 1

# keyboard interrupt (Ctrl+C)
def signal_handler(sig, frame):
    global current_batch, batch_counter
    print_warning(f"\nKeyboard interrupt received. Saving current batch and exiting...")
    save_current_batch(current_batch, batch_counter)
    exit(0)

# Save current batch to CSV
def save_current_batch(batch, batch_counter):
    if batch:
        df = pd.DataFrame(batch, columns=['Sender ID', 'Date', 'Message', 'Sentiment', 'Compound_Sentiment'])
        
        # If sentiment analysis hasn't been done, do it now
        if df['Sentiment'].isnull().all():
            cybersecurity_sia = CybersecuritySentimentAnalyzer()
            df['Sentiment'] = df['Message'].apply(cybersecurity_sia.polarity_scores)
            df['Compound_Sentiment'] = df['Sentiment'].apply(lambda x: x['compound'] if isinstance(x, dict) else None)
        
        batch_filename = f"telegram_scraped_messages_batch_{batch_counter}.csv"
        df.to_csv(batch_filename, index=False)
        print_success(f"Saved batch {batch_counter} with {len(batch)} messages to {batch_filename}")
    else:
        print_info(f"No messages in the current batch.")

# generate sentiment report
def generate_sentiment_report(df):
    try:
        # Ensure Compound_Sentiment is float
        df['Compound_Sentiment'] = pd.to_numeric(df['Compound_Sentiment'], errors='coerce')
        
        # Calculate average sentiment scores
        avg_sentiment = pd.DataFrame(df['Sentiment'].dropna().tolist()).mean()
        
        # Categorise messages based on compound sentiment
        df['Sentiment_Category'] = df['Compound_Sentiment'].apply(lambda x: 
            'High Alert' if x <= -0.5 else
            'Potential Threat' if -0.5 < x <= -0.1 else
            'Neutral' if -0.1 < x < 0.1 else
            'Potentially Positive' if 0.1 <= x < 0.5 else
            'Very Positive'
        )
        sentiment_counts = df['Sentiment_Category'].value_counts()
        total_messages = len(df)

        # Calculate overall sentiment score
        overall_score = avg_sentiment.get('compound', 0) * 100

        report = f"""
Sentiment Analysis Report
{'-' * 50}
Total messages analyzed: {total_messages}

Overall Sentiment Score: {overall_score:.1f}/100
Interpretation: 
{interpret_overall_score(overall_score)}

Message Sentiment Breakdown:
"""

        categories = [
            ('High Alert', "Severe Threats"),
            ('Potential Threat', "Potential Threats"),
            ('Neutral', "Neutral Messages"),
            ('Potentially Positive', "Potentially Positive"),
            ('Very Positive', "Strong Security Indicators")
        ]

        for category, description in categories:
            count = sentiment_counts.get(category, 0)
            percentage = (count / total_messages) * 100
            report += f"{category} ({description}): {count} messages ({percentage:.1f}%)\n"

        report += f"\nTop 5 Most Concerning Messages (Potential Threats):\n"

        for _, row in df.nsmallest(5, 'Compound_Sentiment').iterrows():
            threat_level = abs(row['Compound_Sentiment']) * 100
            report += f"- {row['Message'][:100]}... (Threat Level: {threat_level:.1f}/100)\n"

        report += f"\nTop 5 Most Positive Messages (Potential Security Improvements):\n"

        for _, row in df.nlargest(5, 'Compound_Sentiment').iterrows():
            positivity_level = row['Compound_Sentiment'] * 100
            report += f"- {row['Message'][:100]}... (Positivity Level: {positivity_level:.1f}/100)\n"

        with open('sentiment_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)

        print_success("Sentiment analysis report generated and saved to 'sentiment_report.txt'")
        
        # Print the sentiment category counts to the console with colors
        print_info("Sentiment Category Counts:")
        for category, description in categories:
            count = sentiment_counts.get(category, 0)
            percentage = (count / total_messages) * 100
            color = get_category_color(category)
            print(f"{color}{category}: {count} ({percentage:.1f}%){Style.RESET_ALL}")

    except Exception as e:
        print_error(f"Error generating sentiment report: {e}")
        print_error(f"DataFrame info:\n{df.info()}")

def get_category_color(category):
    color_map = {
        'High Alert': Fore.RED,
        'Potential Threat': Fore.YELLOW,
        'Neutral': Fore.WHITE,
        'Potentially Positive': Fore.LIGHTGREEN_EX,
        'Very Positive': Fore.GREEN
    }
    return color_map.get(category, '')

def interpret_overall_score(score):
    if score <= -50:
        return "Critical situation. Numerous severe threats detected. Immediate action required."
    elif -50 < score <= -10:
        return "Concerning situation. Multiple potential threats identified. Heightened vigilance needed."
    elif -10 < score < 10:
        return "Neutral situation. No significant threats or improvements detected. Maintain standard security measures."
    elif 10 <= score < 50:
        return "Positive situation. Some potential security improvements identified. Consider implementing suggested measures."
    else:
        return "Very positive situation. Strong security indicators present. Continue current security practices and look for areas of improvement."

def analyze_sentiment(cybersecurity_sia, message):
    return cybersecurity_sia.polarity_scores(message)

def process_messages(messages, num_processes=multiprocessing.cpu_count()):
    df = pd.DataFrame(messages, columns=['Sender ID', 'Date', 'Message', 'Sentiment', 'Compound_Sentiment'])
    
    cybersecurity_sia = CybersecuritySentimentAnalyzer()
    
    # Parallelize sentiment analysis
    with multiprocessing.Pool(processes=num_processes) as pool:
        partial_analyze = partial(analyze_sentiment, cybersecurity_sia)
        df['Sentiment'] = pool.map(partial_analyze, df['Message'])
    
    df['Compound_Sentiment'] = df['Sentiment'].apply(lambda x: x['compound'])
    
    generate_sentiment_report(df)
    return df

async def get_entity_name(entity):
    if isinstance(entity, User):
        return f"@{entity.username}" if entity.username else f"User({entity.id})"
    elif isinstance(entity, (Channel, Chat)):
        return entity.title or f"Channel({entity.id})"
    else:
        return f"Unknown({type(entity).__name__})"

async def scrape_messages(client, entity, message_limit, keywords, channel_manager, affiliated_channel=None):
    messages = []
    try:
        entity_name = await get_entity_name(entity)
        async for message in client.iter_messages(entity, limit=message_limit):
            if message.text:
                if affiliated_channel:
                    print_info(f"Message from {Fore.CYAN}{Style.BRIGHT}{entity_name}{Style.RESET_ALL}.{Fore.YELLOW}{Style.BRIGHT} <-- {affiliated_channel}{Style.RESET_ALL}: {message.text}")
                else:
                    print_info(f"Message from {Fore.CYAN}{Style.BRIGHT}{entity_name}{Style.RESET_ALL}: {message.text}")
                messages.append([message.sender_id, message.date, message.text, None, None])
                
                # Process t.me links in the message
                links = extract_channel_links(message.text)
                for link in links:
                    channel_manager.add_channel(link, source_channel=entity_name)
            
            await asyncio.sleep(0.1)
    except FloodWaitError as e:
        print_warning(f"FloodWaitError in scrape_messages: {e}")
        await asyncio.sleep(min(e.seconds, 30))
    except Exception as e:
        print_error(f"Error scraping entity {entity_name}: {e}")
    
    return messages, entity_name

async def process_channels(client, channel_manager, message_depth, keywords, batch_processor):
    while channel_manager.has_unprocessed_channels():
        link = channel_manager.get_next_channel()
        affiliated_channel = channel_manager.get_affiliation(link)
        try:
            join_success = await retry_with_backoff(join_channel(client, channel_manager, link))
            if join_success:
                entity = await client.get_entity(link)
                entity_messages, channel_name = await scrape_messages(client, entity, message_depth, keywords, channel_manager, affiliated_channel)
                
                # Add messages to batch processor with channel name and affiliation
                batch_processor.add_messages(entity_messages, channel_name, affiliated_channel)
            else:
                print_warning(f"Skipping entity {link} due to joining failure")
        except Exception as e:
            print_error(f"Failed to process entity {link}: {e}")
        finally:
            channel_manager.mark_as_processed(link)
        
        await asyncio.sleep(1)  # Small delay between processing channels

async def process_single_channel(client, channel_manager, link, message_depth, keywords):
    try:
        join_success = await retry_with_backoff(join_channel(client, channel_manager, link))
        if join_success:
            entity = await client.get_entity(link)
            entity_name = await get_entity_name(entity)
            print_info(f"Scraping messages from: {entity_name}")
            entity_messages = await scrape_messages(client, entity, message_depth, keywords, channel_manager)
            return entity_messages
        else:
            print_warning(f"Skipping entity {link} due to joining failure")
    except Exception as e:
        print_error(f"Failed to process entity {link}: {e}")
    return []

async def retry_with_backoff(coroutine, max_retries=5, base_delay=1, max_delay=60):
    retries = 0
    while True:
        try:
            return await coroutine
        except FloodWaitError as e:
            if retries >= max_retries:
                raise
            delay = min(base_delay * (2 ** retries) + random.uniform(0, 1), max_delay)
            print_warning(f"FloodWaitError encountered. Retrying in {delay:.2f} seconds. (Attempt {retries + 1}/{max_retries})")
            await asyncio.sleep(delay)
            retries += 1
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            raise



class BatchProcessor:
    def __init__(self, batch_size=1000, cybersecurity_sia=None):
        self.batch = []
        self.batch_size = batch_size
        self.batch_counter = 1
        self.total_messages = 0
        self.cybersecurity_sia = cybersecurity_sia or CybersecuritySentimentAnalyzer()
        self.all_messages_df = pd.DataFrame(columns=['Sender ID', 'Date', 'Message', 'Sentiment', 'Compound_Sentiment', 'Channel Name', 'Affiliated Channel'])

    def add_messages(self, messages, channel_name, affiliated_channel):
        messages_with_info = [
            message + [channel_name, affiliated_channel if affiliated_channel else "Initial Config"]
            for message in messages
        ]
        self.batch.extend(messages_with_info)
        self.total_messages += len(messages)
        if len(self.batch) >= self.batch_size:
            self.save_batch()

    def save_batch(self):
        if self.batch:
            df = pd.DataFrame(self.batch, columns=['Sender ID', 'Date', 'Message', 'Sentiment', 'Compound_Sentiment', 'Channel Name', 'Affiliated Channel'])
            df['Sentiment'] = df['Message'].apply(self.cybersecurity_sia.polarity_scores)
            df['Compound_Sentiment'] = df['Sentiment'].apply(lambda x: x['compound']).astype(float)
            
            batch_filename = f"telegram_scraped_messages_batch_{self.batch_counter}.csv"
            df.to_csv(batch_filename, index=False)
            print_success(f"Saved batch {self.batch_counter} with {len(self.batch)} messages to {batch_filename}")
            
            # Ensure consistent dtypes
            for col in df.columns:
                if col in self.all_messages_df.columns:
                    df[col] = df[col].astype(self.all_messages_df[col].dtype)
            
            self.all_messages_df = pd.concat([self.all_messages_df, df], ignore_index=True)
            
            self.batch = []
            self.batch_counter += 1

    def generate_final_report(self):
        print_info(f"Generating final report. Total messages: {len(self.all_messages_df)}")
        
        if self.all_messages_df.empty:
            print_warning("No messages to generate report from.")
            return
        
        generate_sentiment_report(self.all_messages_df)

    def finalize(self):
        self.save_batch()  # Save any remaining messages
        self.generate_final_report()

    def __del__(self):
        self.save_batch()  # Save any remaining messages when the object is destroyed

# pretty much our main func at this point
async def run_scraper(config, message_depth, channel_depth):
    await client.start()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        channel_manager = ChannelManager()
        cybersecurity_sia = CybersecuritySentimentAnalyzer()
        batch_processor = BatchProcessor(cybersecurity_sia=cybersecurity_sia)
        
        # Add initial channels from config
        for link in config['initial_channel_links']:
            channel_manager.add_channel(link)
        
        start_time = datetime.now()
        print_header(f"Scraping started at {start_time}")

        depth = 0
        while channel_manager.has_unprocessed_channels() and depth < channel_depth:
            print_subheader(f"Crawling at depth {depth + 1}/{channel_depth}")
            channel_manager.display_status()
            
            await process_channels(client, channel_manager, message_depth, config['message_keywords'], batch_processor)
            
            depth += 1
            
            # Allow time for rate limiting
            await asyncio.sleep(5)
        
        end_time = datetime.now()
        duration = end_time - start_time
        print_header(f"Scraping completed at {end_time}")
        print_info(f"Total duration: {duration}")
        print_info(f"Total messages scraped: {batch_processor.total_messages}")
        print_info(f"Total channels processed: {len(channel_manager.processed_channels)}")

        # Finalize batch processing and generate report
        batch_processor.finalize()

    except Exception as e:
        print_error(f"An error occurred during scraping: {e}")
    finally:
        await client.disconnect()

async def process_all_channels(client, channel_manager, message_depth, keywords):
    all_messages = []
    channels_to_process = list(channel_manager.discovered_channels)
    
    for link in channels_to_process:
        try:
            join_success = await retry_with_backoff(join_channel(client, channel_manager, link))
            if join_success:
                entity = await client.get_entity(link)
                entity_name = await get_entity_name(entity)
                print_info(f"Scraping messages from: {entity_name}")
                entity_messages = await scrape_messages(client, entity, message_depth, keywords, channel_manager)
                all_messages.extend(entity_messages)
                
                # Process newly discovered channels
                new_channels = channel_manager.get_new_channels()
                for new_link in new_channels:
                    channel_manager.add_channel(new_link)
            else:
                print_warning(f"Skipping entity {link} due to joining failure")
        except Exception as e:
            print_error(f"Failed to process entity {link}: {e}")
        
        await asyncio.sleep(1)  # Small delay between processing channels
    
    return all_messages

async def process_discovered_channels(client, channel_manager, message_depth, keywords, max_channels_per_depth):
    channels_processed = 0
    while channel_manager.discovered_channels and channels_processed < max_channels_per_depth:
        link = channel_manager.get_next_channel()
        if await join_channel(client, channel_manager, link):
            try:
                channel = await client.get_entity(link)
                print_info(f"Scraping messages from newly discovered channel: {channel.title}")
                await scrape_messages(client, channel, message_depth, keywords, channel_manager)
                channels_processed += 1
            except Exception as e:
                print_error(f"Failed to scrape newly discovered channel {link}: {e}")
        
        await asyncio.sleep(2)

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
    args = parser.parse_args()

    config = load_config(args.config)
    if config is None:
        user_input = input(f"Config file '{args.config}' not found. Create a default config? (y/n): ")
        if user_input.lower() == 'y':
            config = create_default_config(args.config)
        else:
            print_error("Please provide a valid config file. Exiting.")
            exit(1)

    API_ID = ""
    API_HASH = ""
    PHONE_NUMBER = ""

    api_id = args.api_id or API_ID
    api_hash = args.api_hash or API_HASH
    phone_number = args.phone_number or PHONE_NUMBER

    if not api_id or not api_hash or not phone_number:
        print_error("API credentials are missing. Please provide them either as command-line arguments or in the script. (Line 664-666)")
        exit(1)

    client = TelegramClient('session_name', api_id, api_hash)

    with client:
        client.loop.run_until_complete(run_scraper(config, args.message_depth, args.channel_depth))
