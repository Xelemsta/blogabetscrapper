# -*- coding: utf-8 -*-
import os

import telebot
from flask import Flask, request
import psycopg2

import time
import atexit
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from lxml import html
import requests
from requests import Session
import logging

TOKEN = 'XXXXXXXXXX'
bot = telebot.TeleBot(TOKEN)
tipsters = [
    'gdtrpicks',
    'pawelpl', 
    'valuepiks', 
    'sr4private', 
    'pandatrader', 
    'ferrarif430', 
    'annobonno1', 
    'vladdow', 
    'ayoubjounaid', 
    'tipsfromslovakia', 
    'radobet', 
    'sololapaz23', 
    'poloss', 
    'basketcase', 
    'rugbys', 
    'ufcprofit',
    'rostov-on-don',
    'cheser',
    'marocco',
    'haloo',
    'ferrari458italia',
    'overtwogoals',
    'jackpot1x2',
    'thaipicks'
]
server = Flask(__name__)
scheduler = BackgroundScheduler()
logging.basicConfig(level=logging.DEBUG)
atexit.register(lambda: scheduler.shutdown())

def fix_date(date):
    splitted = date.split(',')
    str1 = splitted[1].replace('th', '')
    str2 = str1.replace('rd', '')
    str3 = str2.replace('st', '')
    str4 = str3.replace('nd', '')
    splitted[1] = str4
    return ','.join(splitted)

def get_tips_from_tipster(tipster):
    session = Session()
    SOURCE_SITE_URL = 'https://' + tipster + '.blogabet.com/blog/dashboard'
    session.head(SOURCE_SITE_URL)
    response = session.get(
        SOURCE_SITE_URL,
        headers={'Referer': 'https://' + tipster + '.blogabet.com/',
                 'Accept-Encoding': 'gzip, deflate, br',
                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
                 'Cookie': 'login_string=XXXXXXXXXXXXX; remember_me=1',
                 'X-Compress': 'null',
                 'X-Requested-With': 'XMLHttpRequest',
                 'Connection': 'keep-alive'
                 })
    tree = html.fromstring(response.content)
    return tree.xpath(".//div[@id='_blogPostsContent']/ul/ul/li")

def check_new_tips():
    for tipster in tipsters:
        logging.debug('Checking tips from tipster ' + tipster)
        try:
            lst = get_tips_from_tipster(tipster)
            logging.debug("Found " + str(len(lst)) + " tips from tipster " + tipster)
            for li in lst:
                tip = li.xpath("div/div[@class='feed-pick-title']/div[1]")[0]
                published_date = (li.xpath("div/div[@class='title-name']/div[@class='col-sm-5 col-lg-6 title-age']/small")[0].text)
                published_date = fix_date(published_date)
                logging.debug(tip.xpath("h3/a")[0].text)

                date_object = datetime.strptime(published_date, "%a, %b %d, %Y, %H:%M")  + timedelta(hours=2)
                delta = datetime.now() - date_object
                if delta.total_seconds() / 60 > 3:
                    logging.debug("Bet is too old")
                    logging.debug(datetime.now())
                    logging.debug(date_object)
                    continue
                logging.debug("Found fresh new tips for tipster " + tipster)
                msg='New tip from '+tipster+' published at '+ published_date +'\n'
                msg+= tip.xpath("h3/a")[0].text+'\n'
                labels = tip.xpath("div[@class='labels']")[0]
                msg+=labels.xpath("span")[0].text+' '+labels.xpath("a")[0].text+'\n'
                pick_line = tip.xpath("div[@class='pick-line']")[0]
                msg+=' '.join(pick_line.text.split())+' '+pick_line.xpath("span")[0].text+'\n'
                sport_line = tip.xpath("div[@class='sport-line']/small/span")
                for b in sport_line:
                    msg+=b.text+b.tail.replace('\n','').rstrip(' ')+'\n'
                bot.send_message(1525920757, msg)
        except Exception as err:
            logging.critical('Error on ' + tipster + ' pick: '+ repr(err))
            continue
if __name__ == "__main__":
    scheduler.start()
    scheduler.add_job(func=check_new_tips,trigger=IntervalTrigger(seconds=60),id='check_new_tips',name='Checking for new tips',replace_existing=True)
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
