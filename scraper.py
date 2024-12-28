from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import StaleElementReferenceException
from dotenv import load_dotenv
import os

def send_telegram_message(bot_token, chat_id, profile_name, link,trades, message_id=None, created_trades=None, closed_trades=None):
   
    message = ""
    message += f"*{profile_name}*\n"
    message += f"[Visit Page]({link})\n"
    message += "\n"
    for trade_key, trade in trades.items():

        message += f"Name: *{trade['name']}*\n"
        message += f"Position: *{trade['position']}*\n"
        message += f"Leverage: *{trade['leverage']}*\n"
        message += f"Avg. Entry Price: {trade['avg_entry_price']}\n"
        message += f"Market Price: {trade['market_price']}\n"
        message += f"Order Qty: {trade['order_qty']}\n"
        message += f"*Unrealised P&L: {trade['unrealisedPL']}*\n"
        message += "\n" 
    
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    if message_id is None:
        params = {"chat_id": chat_id, "text": message,             "parse_mode": "Markdown",}
        response = requests.get(telegram_url, params=params)
        if response.status_code == 200:

            print("Message sent successfully!")
        else:
            print(f"Failed to send message: {response.status_code}, {response.text}")
    else:
        # Edit existing message
        edit_url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": message,
            "parse_mode": "Markdown",
        }
        response = requests.get(edit_url, params=params)
        if response.status_code == 200:
            print("Message edited successfully!")
        else:
            print(f"Failed to edit message: {response.status_code}, {response.text}")

    '''
    if created_trades:
        created_message = ""
        for trade in created_trades:
            created_message += "*__TRADE HAS OPENED__*\n"
            created_message += f"Name: *{trade['name']}*\n"
            created_message += f"Position: *{trade['position']}*\n"
            created_message += f"Leverage: *{trade['leverage']}*\n"
            created_message += f"Avg. Entry Price: {trade['avg_entry_price']}\n"

            created_message += f"Order Qty: {trade['order_qty']}\n"


            params = {
                "chat_id": chat_id,
                "text": created_message,
                "parse_mode": "Markdown",
                "reply_to_message_id": message_id,  
            }
            response = requests.get(telegram_url, params=params)
            if response.status_code == 200:
                print("Created trades message sent successfully!")
            else:
                print(f"Failed to send created trades message: {response.status_code}, {response.text}")
    if closed_trades:
        closed_message = ""
        for trade in closed_trades:
            closed_message += "*__TRADE HAS CLOSED__*\n"
            closed_message += f"Name: *{trade['name']}*\n"
            closed_message += f"Position: *{trade['position']}*\n"
            closed_message += f"Leverage: *{trade['leverage']}*\n"
            closed_message += f"Avg. Entry Price: {trade['avg_entry_price']}\n"
            #closed_message += f"Market Price: {trade['market_price']}\n"                     
            closed_message += f"Order Qty: {trade['order_qty']}\n"        
            #closed_message += f"*Unrealised P&L: {trade['unrealisedPL']}*\n\n"

        params = {
            "chat_id": chat_id,
            "text": closed_message,
            "parse_mode": "Markdown",
            "reply_to_message_id": message_id,  
        }
        response = requests.get(telegram_url, params=params)
        if response.status_code == 200:
            print("Closed trades message sent successfully!")
        else:
            print(f"Failed to send closed trades message: {response.status_code}, {response.text}")
    '''
def scrape_trades(driver, url, profile_name):
    driver.get(url)
    trades = {}
    trade_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "radix-:r0:-trigger-orders"))
    )
    trade_button.click()
    try:
        trade_rows = WebDriverWait(driver, 10).until(    
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-table-content .ant-table-tbody .ant-table-row.ant-table-row-level-0"))
        )
        if not trade_rows:
            print(f"No trades found for {profile_name}.")
            return trades
        print(f"Found {len(trade_rows)} trade rows for {profile_name}")
        for row in trade_rows:
            cells = WebDriverWait(row, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-table-cell"))
            )
        
            if not cells:
                continue

            if len(cells) >= 4:
                position_cell = cells[0]
                position_wrap = WebDriverWait(position_cell, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table-position-wrap"))
            )
                
                c = position_wrap.find_element(By.CLASS_NAME, "c").text
                r_sell = position_wrap.find_element(By.CLASS_NAME, "r").text

                if r_sell == "Long":
                    r_sell = "🟢Long"
                elif r_sell == "Short":
                    r_sell = "⛔Short"
                pos_leverage = position_wrap.find_element(By.CLASS_NAME, "pos-leverage").text

                pl_undetermined = cells[4].text
                if pl_undetermined.startswith("-"):
                    pl_undetermined = f"❌ {pl_undetermined}"
                else:
                    pl_undetermined = f"✅ {pl_undetermined}"
                trade = {
                    "name": c,
                    "position": r_sell,
                    "leverage": pos_leverage,
                    "avg_entry_price": cells[1].text,
                    "market_price": cells[2].text,
                    "order_qty": cells[3].text,
                    "unrealisedPL": pl_undetermined,
                }

                trade_key = f"{c}_{cells[1].text}"
                trades[trade_key] = trade



       
    except StaleElementReferenceException:
            print(f"Stale element encountered")
                  
      
    except Exception as e:
            print(f"Error processing row")


    return trades
'''
def compare_trades(old_trades, new_trades):
    def simplify_trade(trade):
        return {
            "name": trade["name"],
            "position": trade["position"],
            "leverage": trade["leverage"],
            "avg_entry_price": trade["avg_entry_price"],
            "order_qty": trade["order_qty"],
        }

    simplified_old_trades = {key: simplify_trade(trade) for key, trade in old_trades.items()}
    simplified_new_trades = {key: simplify_trade(trade) for key, trade in new_trades.items()}

    created_trades = []
    closed_trades = []

    for trade_key, new_trade in simplified_new_trades.items():
            if trade_key not in simplified_old_trades:
                created_trades.append(new_trades[trade_key])  # Use original trade for output

        # Find closed trades
    for trade_key, old_trade in simplified_old_trades.items():
            if trade_key not in simplified_new_trades:
                closed_trades.append(old_trades[trade_key])  # Use original trade for output

    return created_trades, closed_trades


def process_profile(profile_name, url, message_id, driver, previous_trades):
    trades, created_trades, closed_trades = scrape_trades(driver, url, profile_name, previous_trades)
    send_telegram_message(
        BOT_TOKEN,
        CHAT_ID,
        profile_name,
        url,
        trades,
        message_id,
        created_trades,
        closed_trades,
    )
    return trades
'''
def process_profile(profile_name, url, message_id, driver):
    trades = scrape_trades(driver, url, profile_name)
    
 
    if not trades:
       
        send_telegram_message(
            BOT_TOKEN,
            CHAT_ID,
            f"No trades found for {profile_name}.",
            url,
            {},
            message_id,
        )
    else:
        send_telegram_message(
            BOT_TOKEN,
            CHAT_ID,
            profile_name,
            url,
            trades,
            message_id,
        )
    
    return trades

if __name__ == "__main__":

    load_dotenv()
    profiles = {
        "HFT. Sort of": "https://www.bybit.com/copyTrade/trade-center/detail?leaderMark=1nj7BISHIY5aXxhWQWAnEQ%3D%3D&profileDay=30&copyFrom=CTIndex",
        "digital trading systems ISA": "https://www.bybit.com/copyTrade/trade-center/detail?leaderMark=q5wPVsX46k3wTEnSO1pq4A%3D%3D&copyFrom=CTList",
        "INVESTCOIN AI": "https://www.bybit.com/copyTrade/trade-center/detail?leaderMark=M770G43ebV7YOITZRdMPjA%3D%3D&copyFrom=CTList",
        "Pepe coin": "https://www.bybit.com/copyTrade/trade-center/detail?leaderMark=VokGVdDwyelsLAb5UHJ8rA%3D%3D&profileDay=30&copyFrom=CTIndex",
    }
    message_ids = {
        "HFT. Sort of": 133,
        "digital trading systems ISA": 132,
        "INVESTCOIN AI": 131,
        "Pepe coin": 130,
    }
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
  
    drivers = {name: webdriver.Chrome() for name in profiles}

    #previous_trades = {name: {} for name in profiles}

    try:
        with ThreadPoolExecutor(max_workers=len(profiles)) as executor:
            while True:
                futures = []
                for profile_name, url in profiles.items():
                    futures.append(
                        executor.submit(
                            process_profile,
                            profile_name,
                            url,
                            message_ids[profile_name],
                            drivers[profile_name],
                           # previous_trades[profile_name],
                        )
                    )

                for future, profile_name in zip(futures, profiles.keys()):
                   future.result()
                time.sleep(15)
    finally:
        for driver in drivers.values():
            driver.quit()
