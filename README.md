tcp-p2p
=======
The programs can be executed using the following commands:

Server: python server.py
Clients: python client.py

Requirements:

Python 2.7.5 (tested on this version of Python)

Assumptions:

1. Either the client creates a directory by the name "rfc" in the pwd or by running the client program, the directory is created automatically. This directory contains all the RFCs that are sent to the server and that are received from other clients.
2. The name of the rfc file should not contain any spaces.
