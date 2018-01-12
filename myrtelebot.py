import json
import requests
import time
import six.moves.urllib as urllib
from urllib.request import urlopen, Request
import pandas as pd
from datetime import datetime, timedelta
from coinmarketcap import Market
import subprocess
import pytz

TOKEN = ""
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

def getcurdiff():
    command = '/home/cannings/storage/myriadcoin/src/myriadcoin-cli getmininginfo'
    data = subprocess.check_output(command, shell=True)
    d = json.loads(data)
    return d

def getcurblock():
    command = '/home/cannings/storage/myriadcoin/src/myriadcoin-cli getblockcount'
    data = subprocess.check_output(command, shell=True)
    d = json.loads(data)
    return d

def getblockhash(block):
    command = '/home/cannings/storage/myriadcoin/src/myriadcoin-cli getblockhash {}'.format(block)
    data = subprocess.check_output(command, shell=True)
    return str(data).replace('\\n', '')

def getblock(hash):
    command = '/home/cannings/storage/myriadcoin/src/myriadcoin-cli getblock {}'.format(hash)
    data = subprocess.check_output(command, shell=True)
    d = json.loads(data)
    return d

def gethashrate():
    content = urlopen('https://cryptap.us/myr/insight/api/blocks?blockDate={}'.format(datetime.now().strftime('%Y-%m-%d'))).read()
    js = json.loads(content)
    hashdict = {}
    for x in js['blocks']:
        hashdict[x['height']] = x['pow_algo']
    diff = getcurdiff()
    df = pd.Series(hashdict).to_frame()
    df.columns = {'pow'}
    daycomp = (datetime.now().hour / 24) * 144
    shacount = len(df[(df['pow'] == 'sha256d')])
    scryptcount = len(df[(df['pow'] == 'scrypt')])
    groestlcount = len(df[(df['pow'] == 'groestl')])
    skeincount = len(df[(df['pow'] == 'skein')])
    yescount = len(df[(df['pow'] == 'yescrypt')])
    shahash = (shacount / daycomp * diff['difficulty_sha256d'] * 2 ** 32 / 300)
    scrypthash = (scryptcount / daycomp * diff['difficulty_scrypt'] * 2 ** 32 / 300)
    groestlhash = (shacount / daycomp * diff['difficulty_groestl'] * 2 ** 32 / 300)
    skeinhash = (shacount / daycomp * diff['difficulty_skein'] * 2 ** 32 / 300)
    yeshash = (shacount / daycomp * diff['difficulty_yescrypt'] * 2 ** 32 / 300)
    return "SHA256d: {:.2f} TH/s\r\nScrypt: {:.2f} MH/s\r\nGroestl: {:.2f}  MH/s\r\nSkein: {:.2f}  MH/s\r\nYescrypt: {:.2f}  MH/s".format(shahash/1000000000000, scrypthash/1000000, groestlhash/1000000, skeinhash/1000000, yeshash/1000000)

def getcrypto(coin):
    try:
        mk = Market().ticker(coin.lower())
        return "{} is #{} \r\nLast Price: ${:.2f}/{} BTC \r\n24h Volume: {:,.0f} \r\n24h Change: {:.2f}%\r\nAvailable Coins: {:,.0f}/{:,.0f}".format(mk[0]['symbol'], mk[0]['rank'], float(mk[0]['price_usd']), mk[0]['price_btc'], float(mk[0]['24h_volume_usd']), float(mk[0]['percent_change_24h']), float(mk[0]['available_supply']), float(mk[0]['total_supply']))
    except:
        content = urlopen('https://min-api.cryptocompare.com/data/all/coinlist').read()
        js = json.loads(content)
        for x in js['Data']:
            if js['Data'][x]['Symbol'].lower() == coin.lower():
                try:
                    mk = Market().ticker(js['Data'][x]['CoinName'].lower())
                    return "{} is #{} \r\nLast Price: ${:.2f}/{} BTC \r\n24h Volume: {:,.0f} \r\n24h Change: {:.2f}%\r\nAvailable Coins: {:,.0f}/{:,.0f}".format(mk[0]['symbol'], mk[0]['rank'], float(mk[0]['price_usd']), mk[0]['price_btc'], float(mk[0]['24h_volume_usd']), float(mk[0]['percent_change_24h']), float(mk[0]['available_supply']), float(mk[0]['total_supply']))
                except:
                    return "Could not find {}".format(coin)
        return "Could not find {}".format(coin)

def handle_updates(updates):
    for update in updates["result"]:
        if 'new_chat_participant' in update['message']:
            try:
                chat = update["message"]["chat"]["id"]
                doclink = 'https://docs.google.com/document/d/1Q_bPIvlr8dmD4GO2KrGk1MJjir7vTPkj5Bt6XEy1d3c/edit'
                
                username = 'new member'
                try:
                    username = str(update["message"]["new_chat_participant"]["username"])
                except:
                    pass
                if username == 'new member':
                    try:
                        username = str(update["message"]["new_chat_participant"]["first_name"])
                    except:
                        pass
                print(username)
                send_message('`Welcome to Myriadcoin Chat` @{} `you can find our FAQ here:` [Myriad FAQ]({})'.format(username, str(doclink)), chat)
            except Exception as e:
                print("error", e)
                print(update)
                pass
        else:
            try:
                text = update["message"]["text"]
                chat = update["message"]["chat"]["id"]
                print(text)
                if 'roadmap' in text.lower() and 'where' in text.lower():
                    send_message('The roadmap for myriadcoin in on the [Trello Board](https://trello.com/b/BCamm97g/myriad-roadmap)', chat)
                elif 'where' in text.lower() and 'whitepaper' in text.lower():
                    send_message('The whitepaper is currently being finalised however please check out our trello board for what is being worked on: [Trello Board](https://trello.com/b/BCamm97g/myriad-roadmap)', chat)
                elif '!teldiff' in text.lower():
                    diff = getcurdiff()
                    send_message('SHA256 Difficulty: {:.2f} \r\nScrypt Difficulty: {:.2f} \r\nGroestly Difficulty: {:.2f} \r\nSkein Difficulty: {:.2f} \r\nYescrypt Difficulty: {:.2f}'.format(diff['difficulty_sha256d'], diff['difficulty_scrypt'], diff['difficulty_groestl'], diff['difficulty_skein'], diff['difficulty_yescrypt']), chat)
                elif '!telhash' in text.lower():
                    send_message(gethashrate(), chat)
                elif '!cmc' in text.lower():
                    currency = text.replace('!cmc ', '')
                    send_message(getcrypto(currency), chat)
                elif '/teldiff' in text.lower():
                    diff = getcurdiff()
                    send_message('SHA256 Difficulty: {:.2f} \r\nScrypt Difficulty: {:.2f} \r\nGroestly Difficulty: {:.2f} \r\nSkein Difficulty: {:.2f} \r\nYescrypt Difficulty: {:.2f}'.format(diff['difficulty_sha256d'], diff['difficulty_scrypt'], diff['difficulty_groestl'], diff['difficulty_skein'], diff['difficulty_yescrypt']), chat)
                elif '/telhash' in text.lower():
                    send_message(gethashrate(), chat)
                elif '/cmc' in text.lower():
                    currency = text.replace('/cmc ', '').replace('@myriadinfobot', '')
                    send_message(getcrypto(currency), chat)
                elif '/faq' in text.lower():
                    send_message('FAQ here: [Myriad FAQ](https://docs.google.com/document/d/1Q_bPIvlr8dmD4GO2KrGk1MJjir7vTPkj5Bt6XEy1d3c/edit)', chat)   
                elif 'i' in text.lower() and 'love' in text.lower() and 'bot' in text.lower():
                    try:
                        sender = update["message"]["from"]["username"]
                    except:
                        sender = update["message"]["from"]["first_name"]
                    send_message("I Love you too @{}".format(sender), chat)
                elif '/traderchat' in text.lower():
                    send_message('For speculation chat, please go to [Myriad Trader Chat](http://t.me/myriadtrader)', chat)
                elif '/roadmap' in text.lower():
                    send_message('The roadmap for myriadcoin in on the [Trello Board](https://trello.com/b/BCamm97g/myriad-roadmap)', chat)
                elif '/myriadstats' in text.lower():
                    send_message('Please find the simple myriadcoin stats here [Simple Myriadcoin Stats](https://cryptap.us/myr/myrstat/)', chat)
                elif '/getblock' in text.lower():
                    send_message(str(getcurblock()), chat)
                elif '/segwitcountdown' in text.lower():
                    currentblock = getcurblock()
                    segwit = 2306305
                    firstblock = getblock(getblockhash(2302273))
                    curblock = getblock(getblockhash(currentblock))
                    totaltime = (datetime.fromtimestamp(curblock['time'], tz=pytz.UTC) - datetime.fromtimestamp(firstblock['time'], tz=pytz.UTC)) / float(currentblock - 2302273)
                    secs = totaltime.seconds * (segwit - currentblock) 
                    h, remainder = divmod(secs, 3600)
                    m, s = divmod(remainder, 60)
                    send_message('We are on {}/{} with {} blocks left to go which based on average of {} seconds per block is {} hours {} minutes {} seconds away at {:%d/%m/%Y %H:%M:%S} UTC'.format(currentblock, segwit, segwit-int(currentblock), totaltime.seconds, h, m, s, datetime.utcnow() + (totaltime * (segwit - currentblock))), chat)
            except Exception as e:
                print("error", e)
                print(update)
                pass

def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["results"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown&disable_web_page_preview=1".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    urlopen(url).read()

def get_json_from_url(url):
    content = urlopen(url).read()
    js = json.loads(content)
    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=10"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    #print(js)
    return js

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(float(update["update_id"]))
    return max(update_ids)

def main():
    try:
        last_update_id = None
        while True:
            try:
                updates = get_updates(last_update_id)
                if len(updates["result"]) > 0:
                    last_update_id = get_last_update_id(updates) + 1
                    handle_updates(updates)
                time.sleep(0.5)
            except:
                pass
    except KeyboardInterrupt:
        print('Interrupted!')

if __name__ == '__main__':
    main()

# Botfather command list:
# cmc - <currency> to get the coinmarketcap stats for that currency
# faq - for a link to the frequently asked questions
# telhash - for a rubbish set of numbers that mean nothing
# telldiff - for network difficulty
# roadmap - for the trello board / roadmap
# myriadstats - link to the simple myriad stats by cryptapus
# getblock - gets latest block number
# segwitcountdown - countdown to segwit activation!