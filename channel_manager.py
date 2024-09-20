from utils import print_subheader

class ChannelManager:
    def __init__(self):
        self.discovered_channels = set()
        self.joined_channels = set()
        self.processed_channels = set()
        self.channel_affiliations = {}
        self.initial_channels = set()

    def add_channel(self, link, source_channel=None):
        if link and link not in self.joined_channels and link not in self.processed_channels:
            self.discovered_channels.add(link)
            if source_channel:
                self.channel_affiliations[link] = source_channel
            else:
                self.initial_channels.add(link)

    def mark_as_joined(self, link):
        if link:
            self.joined_channels.add(link)
            self.discovered_channels.discard(link)

    def mark_as_processed(self, link):
        if link:
            self.processed_channels.add(link)
            self.discovered_channels.discard(link)

    def has_unprocessed_channels(self):
        return len(self.discovered_channels) > 0

    def get_next_channel(self):
        if self.discovered_channels:
            return self.discovered_channels.pop()
        return None

    def get_affiliation(self, link):
        return self.channel_affiliations.get(link, None)

    def display_status(self):
        print_subheader("Channel Status")
        print(f"  Channels waiting to be processed: {len(self.discovered_channels)}")
        print(f"  Channels joined: {len(self.joined_channels)}")
        print(f"  Channels processed: {len(self.processed_channels)}")
