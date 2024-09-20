from nltk.sentiment import SentimentIntensityAnalyzer

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

def analyze_sentiment(cybersecurity_sia, message):
    return cybersecurity_sia.polarity_scores(message)
