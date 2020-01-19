import csv
import os
import smtplib
from configparser import ConfigParser
from email.message import EmailMessage
from time import strftime

import requests
from bs4 import BeautifulSoup


config = ConfigParser()

if os.path.isfile('config.mine.ini'):
    config.read('config.mine.ini')
else:
    config.read('config.ini')

URL = config.get('URLS', 'Url')
PRICELOGS = config.get('PRICELOGS', 'Location')
HOST = config.get('EMAILSERVER', 'Host')
PORT = config.get('EMAILSERVER', 'Port')
USER = config.get('EMAILSERVER', 'User')
PASSWORD = config.get('EMAILSERVER', 'Password')
RECIPIENT = config.get('RECIPIENT', 'Recipient')


def scrape_webpage(scrape_url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 '
                             'Safari/537.36'}
    page = requests.get(scrape_url, headers=headers).text
    soup = BeautifulSoup(page, 'html.parser')
    return soup


def get_product_name(page):
    product = page.find(id='productTitle').text.strip()
    return product


def get_price(page):
    price = page.find(id='priceblock_saleprice').text.strip()[1:]
    return price


def create_list_of_price_logs():
    with open(PRICELOGS, "r") as log_file:
        logs = csv.reader(log_file, delimiter=',')
        data = [log for log in logs if log]
    return data


def get_last_product_price(price_logs):
    return float(price_logs[-1][2])


def get_price_reduction_percentage(price, last_price_log):
    price = float(price)
    if price < last_price_log:
        percentage_reduction = round(((last_price_log - price) / last_price_log) * 100)
        return percentage_reduction


def log_product_price(product, price):
    with open(PRICELOGS, "a") as log:
        log.write("{0},{1},{2}\n".format(strftime("%Y-%m-%d %H:%M:%S"), str(product), str(price)))


def set_up_email_server():
    try:
        server = smtplib.SMTP(HOST, PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(USER, PASSWORD)
        return server
    except Exception as e:
        print(e)


def create_email_message(name, reduce_percentage, price, last_price):
    msg = EmailMessage()
    msg['Subject'] = 'PRICE REDUCED ' + str(reduce_percentage) + '% - ' + name
    msg['From'] = USER
    msg['To'] = RECIPIENT
    email_body = name + ' is reduced by ' + str(reduce_percentage) + '%, was £' + str(last_price) + ' now £' + str(price)
    msg.set_content(f'<a href={URL}>{email_body}</a>','html')
    return msg


if __name__ == "__main__":
    price_reduced_percentage = None
    web_page = scrape_webpage(URL)
    product_name = get_product_name(web_page)
    product_price = get_price(web_page)

    if os.path.isfile(PRICELOGS):
        product_price_logs = create_list_of_price_logs()
        last_product_price = get_last_product_price(product_price_logs)
        price_reduced_percentage = get_price_reduction_percentage(product_price, last_product_price)

    if price_reduced_percentage:
        email_server = set_up_email_server()
        message = create_email_message(product_name, price_reduced_percentage, product_price, last_product_price)
        print(product_name + ' is reduced by ' + str(price_reduced_percentage) + '%, was £' + str(last_product_price) + ' now £' + str(product_price))
        email_server.send_message(message)
        print('Notification sent to ' + RECIPIENT)
        email_server.quit()

    log_product_price(product_name, product_price)




