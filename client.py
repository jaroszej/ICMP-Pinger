from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8

def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)

        if whatReady[0] == []: # Timeout
            print("0: Destination Network Unreachable")
            return (None, None)

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        #Fill in start
        #Fetch the ICMP header from the IP packet
        icmp_header = recPacket[20:28]
        packet_type, code, checksum, packet_id, seq_num = struct.unpack("bbHHh", icmp_header)

        if packet_id == ID and packet_type == 0 and code == 0:
            packet_data = (packet_type, code, checksum, packet_id, seq_num, startedSelect)
            return packet_data
        #Fill in end

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            print("1: Destination Host Unreachable")
            return (None, None)

def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0

    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)
    
    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
    # Convert 16-bit integers from host to network byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str
    
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.

def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
   
    # SOCK_RAW is a powerful socket type. For more details: http://sock-raw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)
    
    myID = os.getpid() & 0xFFFF # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    result = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return result

def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    resps = []
    print("Pinging " + dest + " using Python:")
    print("")

    # Calculate vars values and return them
    # Send ping requests to a server separated by approximately one second
    for i in range(0,5):
        result = doOnePing(dest, timeout)
        resps.append(result)
        time.sleep(1) # one second

    return resps

if __name__ == '__main__':
    ping("google.co.il")
    ping("google.com")
    ping("localhost")
    ping("go.dev")