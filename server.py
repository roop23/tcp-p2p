#! /usr/local/bin/python
import time
import threading
from socket import *

server_port = 7734
server_name = gethostname()
server_p2p_version = 'P2P-CI/1.0'
valid_methods = {'ADD':'ADD', 'LOOKUP':'LOOKUP', 'LIST':'LIST', 'REGISTER':'REGISTER'}
valid_headers = {'Host:':'Host:', 'Port:':'Port:', 'Title:':'Title:'}
status_phrases = {'OK':'OK', 'Bad_Request':'Bad_Request', 'Not_Found':'Not_Found', 'P2P-CI_Version_Not_Supported':'P2P-CI_Version_Not_Supported'}
status_codes = {'OK':'200', 'Bad_Request':'400', 'Not_Found':'404', 'P2P-CI_Version_Not_Supported':'505'}
method_token_count = {'ADD':9, 'LOOKUP':9, 'LIST':7, 'REGISTER':6}
space = ' '
crlf = '\r\n'

def add_peer(active_peers, lock, hostname, port):
    # ************** #
    lock.acquire()
    if hostname not in active_peers:
        active_peers[hostname] = port
    lock.release()
    # ************** #

def remove_peer(active_peers, lock, host):
    # ************** #
    lock.acquire()
    if host in active_peers:
        del active_peers[host]
    lock.release()
    # ************** #

def remove_rfcs(rfc_index, lock, hostname):
    # ************** #
    lock.acquire()
    for rfc in rfc_index:
        for pair in rfc_index[rfc]:
            if pair[0] == hostname:
                rfc_index[rfc].remove(pair)
    if hostname in rfc_index:
        del rfc_index[host]
    lock.release()
    # ************** #
    

def validate_message(message, method_name):
    message_token = message.split()
    if len(message_token) == method_token_count[method_name]:
        return 1
    else:
        return 0

def handle_broken_connection(active_peers, rfc_index, lock, hostname):
    remove_peer(active_peers, lock, hostname)
    remove_rfcs(rfc_index, lock, hostname)

def handle_error(connectionSocket, error):
    header = server_p2p_version + space + status_codes[error] + space + status_phrases[error] + crlf
    reply_body = ''
    reply_message = header + reply_body + crlf
    connectionSocket.send(header)

def handle_register(message, connectionSocket, lock, active_peers, rfc_index):
    message_token = message.split()
    hostname = message_token[3]
    port = message_token[5]
    add_peer(active_peers, lock, hostname, port)
    header = server_p2p_version + space + status_codes['OK'] + space + status_phrases['OK'] + crlf
    reply_body = ''
    reply_message = header + crlf + reply_body + crlf
    connectionSocket.send(reply_message)
    return hostname
    
def handle_list(message, connectionSocket, lock, active_peers, rfc_index):
    reply_body = ''
    # ************** #
    lock.acquire()
    for rfc_item in rfc_index:
        for pair in rfc_index[rfc_item]:
            rfc = rfc_item
            rfc_hostname = pair[0]
            rfc_title = pair[1]
            rfc_host_upload_port = active_peers[rfc_hostname]
            reply_body = reply_body + rfc + space + rfc_title + space + rfc_hostname + space + rfc_host_upload_port + crlf
    lock.release()
    # ************** #
    header = server_p2p_version + space + status_codes['OK'] + space + status_phrases['OK'] + crlf
    reply_message = header + crlf + reply_body + crlf
    connectionSocket.send(reply_message)

def handle_add(message, connectionSocket, lock, active_peers, rfc_index):
    message_token = message.split()
    rfc = message_token[1]
    hostname = message_token[4]
    port = message_token[6]
    rfc_title = message_token[8]
    reply_body = ''
    # ************** #
    lock.acquire()
    pair = (hostname, rfc_title)
    if rfc in rfc_index:
        if pair not in rfc_index[rfc]:
            rfc_index[rfc].append(pair)
    else:
        rfc_index[rfc] = [pair]
    lock.release()
    # ************** #
    header = server_p2p_version + space + status_codes['OK'] + space + status_phrases['OK'] + crlf
    reply_body = rfc + space + rfc_title + space + hostname + space + port + crlf
    reply_message = header + crlf + reply_body + crlf
    connectionSocket.send(reply_message)

def handle_lookup(message, connectionSocket, lock, active_peers, rfc_index):
    message_token = message.split()
    rfc_lookup = message_token[1]
    hostname = message_token[4]
    port = message_token[6]
    rfc_lookup_title = message_token[8]
    reply_body = ''
    rfc_not_found = 1
    # ************** #
    lock.acquire()
    if rfc_lookup in rfc_index:
        for pair in rfc_index[rfc_lookup]:
            rfc_title = pair[1]
            if rfc_title == rfc_lookup_title:
                rfc_not_found = 0
                rfc_hostname = pair[0]
                rfc_host_upload_port = active_peers[rfc_hostname]
                reply_body = reply_body + rfc_lookup + space + rfc_title + space + rfc_hostname + space + rfc_host_upload_port + crlf
    lock.release()
    # ************** #
    if rfc_not_found:
        handle_error(connectionSocket, status_phrases['Not_Found'])
    else:
        header = server_p2p_version + space + status_codes['OK'] + space + status_phrases['OK'] + crlf
        reply_message = header + crlf + reply_body + crlf
        connectionSocket.send(reply_message)

def handle_peer(connectionSocket, lock, active_peers, rfc_index):
    hostname = ''
    while True:
        message = connectionSocket.recv(1024)
        if not message:
            if hostname != '':
                handle_broken_connection(active_peers, rfc_index, lock, hostname)
                print 'Lost connection'
            break
        print "--> Incoming"
        print message
        method = message.split()[0]
        valid = 1
        if method not in valid_methods:
            handle_error(connectionSocket, status_phrases['Bad_Request'])
        elif method == valid_methods['LIST']:
            valid = validate_message(message, valid_methods['LIST'])
            if valid:
                handle_list(message, connectionSocket, lock, active_peers, rfc_index)
        elif method == valid_methods['LOOKUP']:
            valid = validate_message(message, valid_methods['LOOKUP'])
            if valid:
                handle_lookup(message, connectionSocket, lock, active_peers, rfc_index)
        elif method == valid_methods['ADD']:
            valid = validate_message(message, valid_methods['ADD'])
            if valid:
                handle_add(message, connectionSocket, lock, active_peers, rfc_index)
        elif method == valid_methods['REGISTER']:
            valid = validate_message(message, valid_methods['REGISTER'])
            if valid:   
                hostname = handle_register(message, connectionSocket, lock, active_peers, rfc_index)
        if not valid:
            handle_error(connectionSocket, status_phrases['Bad_Request'])

def main():
    # set up data structures
    active_peers = {}
    rfc_index = {}
    serverSocket = socket(AF_INET,SOCK_STREAM)
    serverSocket.bind((server_name,server_port))
    serverSocket.listen(1)
    lock = threading.Lock()
    print 'The server is ready to receive connection.'
    while True:
        connectionSocket, addr = serverSocket.accept()
        print 'Received connection'
        try:
            t = threading.Thread(target = handle_peer, args = (connectionSocket, lock, active_peers, rfc_index))
            t.daemon = True
            t.start()
        except:
            print "Error: unable to start thread"
    
main()
