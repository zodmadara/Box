import random
import time
import requests
import telebot
from datetime import datetime, timedelta
import os

# Initialize bot with token
token = input('Enter your bot token: ')
bot = telebot.TeleBot(token)

# Dictionary to track last request time for each user
user_last_request = {}
request_limit_time = 5  # time limit in seconds for requests

# Helper function to safely make a request
def safe_request(url):
    try:
        return requests.get(url, timeout=10)
    except requests.exceptions.RequestException:
        return None

# Rate limiting check
def is_request_allowed(user_id):
    now = datetime.now()
    last_request_time = user_last_request.get(user_id)

    if last_request_time is None or (now - last_request_time) > timedelta(seconds=request_limit_time):
        user_last_request[user_id] = now
        return True
    return False

# Check if website has captcha
def check_captcha(url):
    response = safe_request(url)
    if response is None:
        return False
    return ('https://www.google.com/recaptcha/api' in response.text or
            'captcha' in response.text or
            'verifyRecaptchaToken' in response.text or
            'grecaptcha' in response.text or
            'www.google.com/recaptcha' in response.text)

# Check for multiple payment systems in the website
def check_credit_card_payment(url):
    response = safe_request(url)
    if response is None:
        return 'Error accessing the website'
    
    gateways = []
    if 'stripe' in response.text:
        gateways.append('Stripe')
    if 'Cybersource' in response.text:
        gateways.append('Cybersource')
    if 'paypal' in response.text:
        gateways.append('Paypal')
    if 'authorize.net' in response.text:
        gateways.append('Authorize.net')
    if 'Bluepay' in response.text:
        gateways.append('Bluepay')
    if 'Magento' in response.text:
        gateways.append('Magento')
    if 'woo' in response.text:
        gateways.append('WooCommerce')
    if 'Shopify' in response.text:
        gateways.append('Shopify')
    if 'adyen' in response.text or 'Adyen' in response.text:
        gateways.append('Adyen')
    if 'braintree' in response.text:
        gateways.append('Braintree')
    if 'square' in response.text:
        gateways.append('Square')
    if 'payflow' in response.text:
        gateways.append('Payflow')
    
    return ', '.join(gateways) if gateways else 'No recognized payment gateway found'

# Check for cloud services in the website
def check_cloud_in_website(url):
    response = safe_request(url)
    if response is None:
        return False
    return 'cloudflare' in response.text.lower()

# Check for GraphQL
def check_graphql(url):
    response = safe_request(url)
    if response is None:
        return False
    if 'graphql' in response.text.lower() or 'query {' in response.text or 'mutation {' in response.text:
        return True
    
    # Optionally, try querying the /graphql endpoint directly
    graphql_url = url.rstrip('/') + '/graphql'
    graphql_response = safe_request(graphql_url)
    if graphql_response and graphql_response.status_code == 200:
        return True
    
    return False

# Check if the path /my-account/add-payment-method/ exists
def check_auth_path(url):
    auth_path = url.rstrip('/') + '/my-account/add-payment-method/'
    response = safe_request(auth_path)
    if response is not None and response.status_code == 200:
        return 'Auth ✔️'
    return 'None ❌'

# Get the status code
def get_status_code(url):
    response = safe_request(url)
    if response is not None:
        return response.status_code
    return 'Error'

# Check for platform (simplified)
def check_platform(url):
    response = safe_request(url)
    if response is None:
        return 'None'
    if 'wordpress' in response.text.lower():
        return 'WordPress'
    if 'shopify' in response.text.lower():
        return 'Shopify'
    return 'None'

# Check for error logs (simplified)
def check_error_logs(url):
    response = safe_request(url)
    if response is None:
        return 'None'
    if 'error' in response.text.lower() or 'exception' in response.text.lower():
        return 'Error logs found'
    return 'None'

# Command to check URLs from a file
@bot.message_handler(content_types=['document'])
def handle_document(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = f'temp_{message.document.file_name}'
    
    # Save the document temporarily
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    # Read URLs from the file
    with open(file_path, 'r') as file:
        urls = file.readlines()
    
    # Process each URL
    for url in urls:
        url = url.strip()
        if url:  # Only process non-empty lines
            if is_request_allowed(message.from_user.id):
                loading_message = bot.reply_to(message, f'Checking URL: <code>{url}</code>', parse_mode='HTML')
                time.sleep(1)  # Simulate processing time

                captcha = check_captcha(url)
                cloud = check_cloud_in_website(url)
                payment = check_credit_card_payment(url)
                graphql = check_graphql(url)
                auth_path = check_auth_path(url)
                platform = check_platform(url)
                error_logs = check_error_logs(url)
                status_code = get_status_code(url)

                captcha_emoji = "😞" if captcha else "🔥"
                cloud_emoji = "😞" if cloud else "🔥"

                # Create formatted message with <code> tag for the URL
                response_message = (
                    "🔍 Gateways fetched successfully \n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔗 URL: <code>{url}</code>\n"
                    f"💳 Payment Gateways: <code>{payment}</code>\n"
                    f"👾 Captcha: <code>{captcha} {captcha_emoji}</code>\n"
                    f"☁️ Cloudflare: <code>{cloud} {cloud_emoji}</code>\n"
                    f"📊 GraphQL: <code>{graphql}</code>\n"
                    f"🛤️ Auth Path: <code>{auth_path}</code>\n"
                    f"⭐ Platform: <code>{platform}</code>\n"
                    f"🤖 Error Logs: <code>{error_logs}</code>\n"
                    f"🌡️ Status: <code>{status_code}</code>\n"
                    "\nBot By: @YourBot"
                )

                bot.edit_message_text(response_message, message.chat.id, loading_message.message_id, parse_mode='HTML')

    # Clean up the temporary file
    os.remove(file_path)

# Command to check single URL with /url
@bot.message_handler(commands=['url'])
def check_url(message):
    if len(message.text.split()) < 2:
        bot.reply_to(message, 'Please provide a valid URL after the /url command')
        return

    user_id = message.from_user.id
    if not is_request_allowed(user_id):
        bot.reply_to(message, 'Please wait a few seconds before making another request')
        return

    url = message.text.split()[1]

    captcha = check_captcha(url)
    cloud = check_cloud_in_website(url)
    payment = check_credit_card_payment(url)
    graphql = check_graphql(url)
    auth_path = check_auth_path(url)
    platform = check_platform(url)
    error_logs = check_error_logs(url)
    status_code = get_status_code(url)

    loading_message = bot.reply_to(message, '<strong>[~]-Loading... 🥸</strong>', parse_mode="HTML")
    time.sleep(1)

    captcha_emoji = "😞" if captcha else "🔥"
    cloud_emoji = "😞" if cloud else "🔥"

    # Create formatted message with <code> tag for the URL
    response_message = (
        "🔍 Gateways fetched successfully \n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 URL: <code>{url}</code>\n"
        f"💳 Payment Gateways: <code>{payment}</code>\n"
        f"👾 Captcha: <code>{captcha} {captcha_emoji}</code>\n"
        f"☁️ Cloudflare: <code>{cloud} {cloud_emoji}</code>\n"
        f"📊 GraphQL: <code>{graphql}</code>\n"
        f"🛤️ Auth Path: <code>{auth_path}</code>\n"
        f"⭐ Platform: <code>{platform}</code>\n"
        f"🤖 Error Logs: <code>{error_logs}</code>\n"
        f"🌡️ Status: <code>{status_code}</code>\n"
        "\nBot By: @ZodMadara"
    )

    bot.edit_message_text(response_message, message.chat.id, loading_message.message_id, parse_mode='HTML')

# Start the bot
bot.polling()