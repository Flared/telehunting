from colorama import init, Fore, Back, Style
import nltk

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

def ensure_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        print_info("Downloading NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('vader_lexicon', quiet=True)

def get_category_color(category):
    color_map = {
        'High Alert': Fore.RED,
        'Potential Threat': Fore.YELLOW,
        'Neutral': Fore.WHITE,
        'Potentially Positive': Fore.LIGHTGREEN_EX,
        'Very Positive': Fore.GREEN
    }
    return color_map.get(category, '')
