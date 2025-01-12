"""
ПУБЛИКА ГОЛЬТЬЕ ЭТО ИРОНИЯ НА РЕАЛИИ РУССКОЙ КУЛЬТУРЫ.
-----------------------------------------------------
Парсер для мониторинга сайта https://publikagaultier.com/
"""

import requests
import time
from bs4 import BeautifulSoup
import json
from datetime import datetime
import random
import telebot
import logging
from fake_useragent import UserAgent

# Logging
logging.basicConfig(
    filename='website_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Telegram
TELEGRAM_BOT_TOKEN = 'Сюда токен для бота'
TELEGRAM_CHAT_ID = 'Сюда свой чат id'
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

URL = 'https://publikagaultier.com/collection/all'
PRODUCTS_FILE = 'previous_products.json'


class WebsiteMonitor:
    def __init__(self):
        self.user_agent = UserAgent()
        self.session = requests.Session()
        self.previous_products = self.load_previous_products()

    def load_previous_products(self):
        try:
            with open(PRODUCTS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_products(self, products):
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump(products, f)

    def get_random_headers(self):
        return {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def send_telegram_message(self, message):
        try:
            bot.send_message(TELEGRAM_CHAT_ID, message, parse_mode='HTML')
            logging.info(f"Telegram message sent: {message}")
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {str(e)}")

    def fetch_website(self):
        try:
            time.sleep(random.uniform(1, 3))

            response = self.session.get(
                URL,
                headers=self.get_random_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            error_message = f"Error fetching website: {str(e)}"
            logging.error(error_message)
            self.send_telegram_message(f"⚠️ {error_message}")
            return None

    def parse_products(self, html):
        products = {}
        try:
            soup = BeautifulSoup(html, 'html.parser')
            catalog_items = soup.find_all('a', class_='catalog__item')

            for item in catalog_items:
                name = item.find('div', class_='catalog__name').text.strip()
                price = item.find('span', class_='catalog__price').text.strip()
                link = f"https://publikagaultier.com{item.get('href')}"

                products[name] = {
                    'price': price,
                    'link': link
                }

            return products
        except Exception as e:
            error_message = f"Error parsing products: {str(e)}"
            logging.error(error_message)
            self.send_telegram_message(f"⚠️ {error_message}")
            return None

    def check_for_changes(self, current_products):
        if not current_products:
            return

        new_products = {
            name: data for name, data in current_products.items()
            if name not in self.previous_products
        }

        removed_products = {
            name: data for name, data in self.previous_products.items()
            if name not in current_products
        }

        price_changes = {
            name: (self.previous_products[name]['price'], data['price'])
            for name, data in current_products.items()
            if name in self.previous_products and
               self.previous_products[name]['price'] != data['price']
        }

        if new_products:
            message = "🆕 New products found:\n\n"
            for name, data in new_products.items():
                message += f"<b>{name}</b>\n"
                message += f"Price: {data['price']}\n"
                message += f"Link: {data['link']}\n\n"
            self.send_telegram_message(message)

        if removed_products:
            message = "❌ Products removed:\n\n"
            for name in removed_products:
                message += f"<b>{name}</b>\n"
            self.send_telegram_message(message)

        if price_changes:
            message = "💰 Price changes detected:\n\n"
            for name, (old_price, new_price) in price_changes.items():
                message += f"<b>{name}</b>\n"
                message += f"Old price: {old_price}\n"
                message += f"New price: {new_price}\n"
                message += f"Link: {current_products[name]['link']}\n\n"
            self.send_telegram_message(message)

        self.previous_products = current_products
        self.save_products(current_products)

    def monitor(self):
        while True:
            try:
                html = self.fetch_website()
                if html:
                    current_products = self.parse_products(html)
                    if current_products:
                        self.check_for_changes(current_products)

                # Wait 10 minutes before next check
                time.sleep(600)

            except Exception as e:
                error_message = f"Monitoring error: {str(e)}"
                logging.error(error_message)
                self.send_telegram_message(f"⚠️ {error_message}")
                time.sleep(60)


if __name__ == "__main__":
    monitor = WebsiteMonitor()
    print("🚀 Website monitoring started")
    monitor.send_telegram_message("🚀 Website monitoring started")

    monitor.monitor()