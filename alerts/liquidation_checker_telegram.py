import os
import asyncio
import logging
import requests
from telegram import Bot

# Telegram bot token and channel ID
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Logging configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def fetch_and_filter_data(url, url_label, min_health_factor, max_health_factor, min_total_debt):
    try:
        # Send a GET request to the endpoint
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()['data']
        
        # Filter items based on health_factor and total_debt
        filtered_data = [
            item for item in data 
            if min_health_factor < float(item['health_factor']) <= max_health_factor and float(item['total_debt']) > min_total_debt
        ]
        
        # Format the message to be sent to Telegram
        message = f"\n### {url_label} ###\n\n"
        message += f"| {'acc_id':<10} | {'acc_kind':<10} | {'hf':<10} | {'debt':<10} |\n"
        message += f"| {'-'*10} | {'-'*10} | {'-'*10} | {'-'*10} |\n"
        
        for item in filtered_data:
            acc_id = item['account_id']
            acc_kind = item['account_kind']
            hf = float(item['health_factor'])
            debt = float(item['total_debt']) / 1000000
            message += f"| {acc_id:<10} | {acc_kind:<10} | {hf:<10.4f} | {debt:<10.4f} |\n"
        
        return message
    except requests.RequestException as e:
        return f"Failed to retrieve data from {url_label}: {e}"
    except ValueError as e:
        return f"Error processing data from {url_label}: {e}"

async def send_alert():
    bot = Bot(token=BOT_TOKEN)
    urls = {
        'OSMO CM': 'https://api.marsprotocol.io/v1/unhealthy_positions/osmosis/creditmanager',
        'OSMO RB': 'https://api.marsprotocol.io/v1/unhealthy_positions/osmosis/redbank',
        'NTRN RB': 'https://api.marsprotocol.io/v1/unhealthy_positions/neutron/redbank'
    }
    
    # Predefined thresholds
    min_health_factor = 0.2
    max_health_factor = 1.0
    min_total_debt = 1000000
    
    # Aggregate messages
    full_message = ""
    for label, url in urls.items():
        full_message += fetch_and_filter_data(url, label, min_health_factor, max_health_factor, min_total_debt) + "\n"
    
    await bot.send_message(chat_id=CHANNEL_ID, text=f"```\n{full_message}\n```", parse_mode='Markdown')

asyncio.run(send_alert())