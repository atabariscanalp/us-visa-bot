import os
import requests
from dotenv import load_dotenv

# .env dosyasını yükleyin
load_dotenv()
# TOKEN = os.getenv('TOKEN')
TOKEN = "7495129379:AAHMwBN64yZP45hN9NsUoJHv49YTJFbelEQ"

def get_updates():
    url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
    response = requests.get(url)
    return response.json()

if __name__ == "__main__":
    print(TOKEN)
    updates = get_updates()
    print(updates)  # Gelen güncellemeleri yazdır

    # Güncellemelerdeki chat ID'leri bulma
    if 'result' in updates:
        for update in updates['result']:
            chat_id = update['message']['chat']['id']
            print(f"Chat ID: {chat_id}")
