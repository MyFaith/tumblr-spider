# coding: utf-8

import requests
import threading
import queue
import time
import argparse
from bs4 import BeautifulSoup
from pymongo import MongoClient
from colorama import init, Fore

db = MongoClient(host='127.0.0.1').tumblr
init(autoreset=True)

mutex = threading.Lock()

class Tumblr(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.user_queue = queue
        self.total_user = []
        self.total_url = []

    def download(self, url):
        tmp_user = []
        tmp_source = []

        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            source = iframe.get('src','').strip()
            if source and source.find('https://www.tumblr.com/video') != -1 and source not in self.total_url:
                self.total_url.append(source)
                tmp_source.append(source)
                print(Fore.GREEN + '新链接: %s' %source)

        new_user = soup.find_all(class_='reblog-link')
        for user in new_user:
            username = user.text.strip()
            if username and username not in self.total_user:
                self.user_queue.put(username)
                self.total_user.append(username)
                tmp_user.append(username)
                print(Fore.RED + '新用户: %s' %username)

        mutex.acquire()
        for username in tmp_user:
            db.user.insert({
                'username': username
            })
            print(Fore.RED + '添加用户: %s' %username)
        for source in tmp_source:
            db.source.insert({
                 'source': source
            })
            print(Fore.GREEN + '添加链接: %s' %source)
        mutex.release()


    def run(self):
        while self.user_queue.not_empty:
            url = 'http://%s.tumblr.com/' %self.user_queue.get()
            self.download(url)
            time.sleep(2)

def main():
    parser = argparse.ArgumentParser('tumblr')
    parser.add_argument('-user', default='guodanpi', dest='user', help='开始爬取的用户名')
    arg = parser.parse_args()

    user_queue = queue.Queue()
    user_queue.put(arg.user)

    threads = []
    for i in range(10):
        tumblr = Tumblr(user_queue)
        tumblr.setDaemon(True)
        tumblr.start()
        threads.append(tumblr)

    while True:
        for i in threads:
            if not i.isAlive():
                break
        time.sleep(1)

if __name__ == '__main__':
    main()
