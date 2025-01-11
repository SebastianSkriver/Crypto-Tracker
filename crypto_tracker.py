import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import pandas as pd
from datetime import datetime
import os
import logging

# Set up logging for troubleshooting
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the working directory to where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_dir)

logging.debug("Current working directory: %s", os.getcwd())  # To verify if it's correct

# Define your portfolio
portfolio = {
    "axelar": 14000,  # Replace with your holdings
    "any-inu": 1200000000,
}

# Define your target portfolio value
TARGET_PORTFOLIO_VALUE = 50000  # Replace with your target value in USD

# Email credentials
EMAIL_FROM = "Stock.tracker.python@gmail.com"
EMAIL_PASSWORD = "bdib awge zrjw dhnn"
EMAIL_TO = "skriver.sebastian@gmail.com"


# Fetch prices from CoinGecko
def fetch_prices(coins):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(coins),
        "vs_currencies": "usd"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching data from CoinGecko: %s", e)
        return {}


# Calculate portfolio value
def calculate_portfolio_value(prices, portfolio):
    total_value = 0
    data = []
    for coin, quantity in portfolio.items():
        if coin in prices:
            price = prices[coin]["usd"]
            value = price * quantity
            total_value += value
            data.append({"Coin": coin, "Quantity": quantity, "Price (USD)": price, "Value (USD)": value})
        else:
            logging.warning("No price data for coin: %s", coin)
    return total_value, data


# Log data to CSV
def log_to_csv(data, total_value):
    df = pd.DataFrame(data)
    df["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
    df["Total Portfolio Value (USD)"] = total_value  # Add total portfolio value for the day
    file_name = os.path.join(script_dir, "crypto_portfolio.csv")  # Save as CSV in the same directory

    # Check if the file exists
    if os.path.exists(file_name):
        logging.debug("File exists, attempting to append data.")
        try:
            # Read the existing CSV file
            existing_data = pd.read_csv(file_name)
            # Concatenate the new data with the existing data
            df = pd.concat([existing_data, df], ignore_index=True)
        except Exception as e:
            logging.error("Error reading existing file: %s", e)
            return
    else:
        logging.debug("File does not exist, creating a new one.")

    # Save the DataFrame to the CSV file
    try:
        df.to_csv(file_name, index=False)
        logging.info("Portfolio logged to %s", file_name)
    except Exception as e:
        logging.error("Error saving file: %s", e)


# Send email notification
def send_email(subject, body):
    try:
        # Set up the email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg["Subject"] = subject

        # Add the email body
        msg.attach(MIMEText(body, "plain"))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)

        logging.info("Email sent successfully to %s", EMAIL_TO)
    except Exception as e:
        logging.error("Error sending email: %s", e)

# Main program
def main():
    coins = list(portfolio.keys())
    prices = fetch_prices(coins)
    if prices:
        total_value, data = calculate_portfolio_value(prices, portfolio)
        logging.debug("Portfolio Value (USD): %s", total_value)
        for item in data:
            logging.debug(item)
        log_to_csv(data, total_value)  # Pass total value to the log function

        # Check if the portfolio value exceeds the target
        if total_value >= TARGET_PORTFOLIO_VALUE:
            subject = "Crypto Portfolio Alert: Target Reached!"
            body = f"Your portfolio value has reached ${total_value:.2f}, which is above your target of ${TARGET_PORTFOLIO_VALUE:.2f}. Consider selling your holdings."
            send_email(subject, body)
    else:
        logging.error("Failed to fetch prices.")

if __name__ == "__main__":
    main()
