from deep_translator import GoogleTranslator

def translate_to_german(text):
    translator = GoogleTranslator(source='en', target='de')
    return translator.translate(text)

if __name__ == "__main__":
    print("English to German Translator. Press Ctrl-C to stop.")
    
    try:
        while True:
            text = input("Enter text to translate: ")
            translated_text = translate_to_german(text)
            print(f"German Translation: {translated_text}\n")
    
    except KeyboardInterrupt:
        print("\nTranslation app stopped.")
