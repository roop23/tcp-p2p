#! /usr/local/bin/python
import os
import sys
import time
import platform
import threading
from socket import *
from os import listdir
from datetime import datetime
from os.path import isfile, join

server_name = gethostname()
server_port = 7734
client_name_bind = gethostname()
client_name = gethostname()
client_p2p_version = 'P2P-CI/1.0'

valid_methods = {'ADD':'ADD', 'LOOKUP':'LOOKUP', 'LIST':'LIST', 'REGISTER':'REGISTER', 'GET':'GET'}
valid_headers = {
                    'Host:':'Host:', 'Port:':'Port:', 'Title:':'Title:','ALL':'ALL',
                    'OS:':'OS:','Date:':'Date:','Last-Modified:':'Last-Modified:',
                    'Content-Length:':'Content-Length:', 'Content-Type:':'Content-Type:',
                }
status_phrases = {'OK':'OK', 'Bad_Request':'Bad_Request', 'Not_Found':'Not_Found', 'P2P-CI_Version_Not_Supported':'P2P-CI_Version_Not_Supported'}
status_codes = {'OK':'200', 'Bad_Request':'400', 'Not_Found':'404', 'P2P-CI_Version_Not_Supported':'505'}
method_token_count = {'ADD':9, 'LOOKUP':9, 'LIST':7, 'REGISTER':6}

rfc_directory = 'rfc'
space = ' '
crlf = '\r\n'

def get_os_version():
    if platform.system() == 'Darwin':
        import subprocess
        text = subprocess.check_output(["system_profiler", "SPSoftwareDataType"])
        text = text.split('\n')
        l =  [x for x in text if x != '']
        os_version = l[2].strip()
        os_version = os_version[(os_version.find('System Version: ') + len('System Version: ')):]
        os_version = os_version[:os_version.find(' (')]
        return os_version
    else:
        return platform.system()

def validate_rfc_directory():
    if os.path.isdir(rfc_directory):
        return 1
    else:
        return 0

def validate_file(file):
    if os.path.isfile(file):
        return 1
    else:
        return 0

def validate_input(text):
    if text == '':
        print "Invalid input"
        return 0
    else:
        return 1

def handle_error(function, code, phrase):
    print "**** Attention ****"
    print "error in function: " + function + " with code: " + code + " with phrase: " + phrase
    print "**** Attention ****"
    print

def handle_p2s_failure():
    print "Error connecting with server!. Please restart the program."

def handle_p2p_failure():
    print "Error connecting with Peer!. Please check."

def sync_rfcs(client_port):
    rfc_files = [ file for file in listdir(rfc_directory) if validate_file(join(rfc_directory,file)) and not file.startswith('.') ]
    for rfc in rfc_files:
        if space in rfc:
            print "Filename invalid. Contains space."
        else:
            add_request(rfc, client_port)

def add_request(rfc, client_port):
    filename = rfc_directory + '/' + rfc
    valid_file = validate_file(filename)
    if not valid_file:
        print "Error! The file " + rfc + " is not present."
        return
    with open(filename) as f:
        content = f.read()
        f.close()
    title = ''
    if content != '':
        title = content.split('\n')[0]
        title = title.replace(' ', '_')
    header = valid_methods['ADD'] + space + rfc + space + client_p2p_version + crlf
    message_body = valid_headers['Host:'] + space + client_name + crlf
    message_body = message_body + valid_headers['Port:'] + space + str(client_port) + crlf
    message_body = message_body + valid_headers['Title:'] + space + title + crlf
    message = header + message_body + crlf
    reply = send_server(message)
    reply_token = reply.split()
    if reply_token[1] != status_codes['OK']:
        handle_error(valid_methods['ADD'], reply_token[1], reply_token[2])

def list_request(client_port):
    header = valid_methods['LIST'] + space + valid_headers['ALL'] + space + client_p2p_version + crlf
    message_body = valid_headers['Host:'] + space + client_name + crlf
    message_body = message_body + valid_headers['Port:'] + space + str(client_port) + crlf
    message = header + message_body + crlf
    reply = send_server(message)
    reply_token = reply.split()
    if reply_token[1] != status_codes['OK']:
        handle_error(valid_methods['LIST'], reply_token[1], reply_token[2])

def lookup_request(rfc, title, client_port):
    header = valid_methods['LOOKUP'] + space + str(rfc) + space + client_p2p_version + crlf
    message_body = valid_headers['Host:'] + space + client_name + crlf
    message_body = message_body + valid_headers['Port:'] + space + str(client_port) + crlf
    message_body = message_body + valid_headers['Title:'] + space + title + crlf
    message = header + message_body + crlf
    reply = send_server(message)
    reply_token = reply.split()
    if reply_token[1] != status_codes['OK']:
        handle_error(valid_methods['LOOKUP'], reply_token[1], reply_token[2])

def send_get_request(connection_details, client_port, rfc):
    try:
        p2p_socket = socket(AF_INET, SOCK_STREAM)
        p2p_socket.connect(connection_details)
    except:
        handle_p2p_failure()
        return
    header = valid_methods['GET'] + space + str(rfc) + space + client_p2p_version + crlf
    message_body = valid_headers['Host:'] + space + client_name + crlf
    message_body = message_body + valid_headers['OS:'] + space + send_get_request.os_version + crlf
    message = header + message_body + crlf
    reply = send_peer(p2p_socket, message)
    reply_token = reply.split()
    p2p_socket.close()
    if reply_token[1] != status_codes['OK']:
        handle_error(valid_methods['GET'], reply_token[1], reply_token[2])
    else:
        handle_get_reply(client_port, reply, rfc)
    
def handle_get_reply(client_port, message, rfc):
    token = 'Content-Type: text/text\r\n'
    if token not in message:
        print "Invalid reply from get"
        return
    rfc_content = message[(message.find(token) + len(token)):]
    print '*********'
    print rfc_content
    print '*********'
    filename = rfc_directory + '/' + rfc
    with open(filename, 'w') as f:
        f.write(rfc_content)
        f.close()
    add_request(rfc, client_port)

def handle_get_request(connection_socket, rfc):
    filename = rfc_directory + '/' + rfc
    valid_file = validate_file(filename)
    if not valid_file:
        print "Error! The file " + rfc + " is not present."
        handle_p2p_error(connection_socket, status_phrases['Not_Found'])
        return
    with open(filename) as f:
        rfc_content = f.read()
        f.close()
    req_date = datetime.now().strftime("%a, %d %b %Y %T ") + str(time.tzname[time.daylight])
    lm_time = datetime.fromtimestamp(os.path.getmtime(filename))
    lm_time = lm_time.strftime("%a, %d %b %Y %T ") + str(time.tzname[time.daylight])
    content_length = str(os.path.getsize(filename))
    content_type = 'text/text'
    
    header = client_p2p_version + space + status_codes['OK'] + space + status_phrases['OK'] + crlf
    message_body = valid_headers['Date:'] + space + req_date + crlf
    message_body = message_body + valid_headers['OS:'] + space + handle_get_request.os_version + crlf
    message_body = message_body + valid_headers['Last-Modified:'] + space + lm_time + crlf
    message_body = message_body + valid_headers['Content-Length:'] + space + content_length + crlf
    message_body = message_body + valid_headers['Content-Type:'] + space + content_type + crlf
    message_body = message_body + rfc_content
    message = header + message_body
    send_peer(connection_socket, message)

def handle_p2p_error(connection_socket, error):
    header = client_p2p_version + space + status_codes[error] + space + status_phrases[error] + crlf
    reply_body = ''
    reply_message = header + reply_body + crlf
    connection_socket.send(header)

def handle_peer(connection_socket):
    message = connection_socket.recv(1024)
    if not message:
        return
    message_token = message.split()
    method = message_token[0]
    if method == valid_methods['GET']:
        rfc = message_token[1]
        handle_get_request(connection_socket, rfc)
    else:
        send_error(connection_socket, status_phrases['Bad_Request'])

def register(client_port):
    header = valid_methods['REGISTER'] + space + client_p2p_version + crlf
    message_body = valid_headers['Host:'] + space + client_name + crlf
    message_body = message_body + valid_headers['Port:'] + space + str(client_port) + crlf
    message = header + message_body + crlf
    reply = send_server(message)
    reply_token = reply.split()
    if reply_token[1] != status_codes['OK']:
        handle_error(valid_methods['REGISTER'], reply_token[1], reply_token[2])
    else:
        sync_rfcs(client_port)

def send_peer(connection_socket, message):
    print '--> Outgoing'
    print message
    connection_socket.send(message)
    message = connection_socket.recv(1024)
    if not message:
        print "Peer connection lost"
    else:
        print '--> Incoming peer request'
        print message                
        return message
    
def send_server(message):
    print '--> Outgoing'
    print message
    send_server.p2s_socket.send(message)
    message = send_server.p2s_socket.recv(1024)
    if not message:
        handle_p2s_failure()
    else:
        print '--> Incoming'
        print message                
        return message

def setup_server_connection(client_port):
    try:
        p2s_socket = socket(AF_INET, SOCK_STREAM)
        p2s_socket.connect((server_name,server_port))
    except:
        handle_p2s_failure()
        return 0
    os_version = get_os_version()
    send_get_request.os_version = os_version
    handle_get_request.os_version = os_version
    send_server.p2s_socket = p2s_socket
    register(client_port)
    return 1

def handle_user_input(client_port):
    while True:
        user_input = raw_input("Please enter 1 to LIST, 2 to LOOKUP, 3 to ADD, 4 to GET, 5 to EXIT --> ")
        if user_input == str(1):
            list_request(client_port)
        elif user_input == str(2):
            rfc = raw_input("Please enter the rfc numer --> ")
            if validate_input(rfc):
                rfc = rfc.replace(' ', '_')
                title = raw_input("Please enter the rfc title --> ")
                if validate_input(title):
                    title = title.replace(' ', '_')
                    lookup_request(rfc, title, client_port)
        elif user_input == str(3):
            rfc = raw_input("Please enter the rfc numer --> ")
            if validate_input(rfc):
                rfc = rfc.replace(' ', '_')
                add_request(rfc, client_port)
        elif user_input == str(4):
            rfc_host = raw_input("Please enter the hostname of the peer --> ")
            if validate_input(rfc_host):
                rfc_port = raw_input("Please enter the upload port of the peer --> ")
                if validate_input(rfc_port):
                    rfc_port = int(rfc_port)
                    connection_details = (rfc_host, rfc_port)
                    rfc = raw_input("Please enter the rfc numer --> ")
                    if validate_input(rfc):
                        send_get_request(connection_details, client_port, rfc)
        elif user_input == str(5):
            print "Stopping program. Please press cntl + c to exit."
            sys.exit(0)
        else:
            print "Please enter a valid input" 
def main():
    valid = validate_rfc_directory()
    if not valid:
        os.makedirs(rfc_directory)
    client_socket = socket(AF_INET,SOCK_STREAM)
    client_socket.bind((client_name_bind,0))
    client_port = client_socket.getsockname()[1]
    client_socket.listen(1)
    setup = setup_server_connection(client_port)
    if not setup:
        sys.exit(0)
    try:
        t = threading.Thread(target = handle_user_input, args = (client_port,))
        t.daemon = True
        t.start()
    except:
        print "Error: unable to start thread"        
    while True:
        connection_socket, addr = client_socket.accept()
        print 'Received p2p connection'
        try:
            t = threading.Thread(target = handle_peer, args = (connection_socket,))
            t.daemon = True
            t.start()
        except:
            print "Error: unable to start thread"        
main()
