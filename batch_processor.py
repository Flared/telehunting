import pandas as pd
from utils import print_success, print_info, print_warning
from report_generator import generate_sentiment_report

class BatchProcessor:
    def __init__(self, batch_size=1000, cybersecurity_sia=None):
        self.batch = []
        self.batch_size = batch_size
        self.batch_counter = 1
        self.total_messages = 0
        self.cybersecurity_sia = cybersecurity_sia
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
