#!/usr/bin/env python

'''

	Equalize levels of TPM inputs to given dBm level

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2018, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import sys
import numpy as np
sys.path.append("../board")
sys.path.append("../rf_jig")
sys.path.append("../config")
sys.path.append("../repo_utils")
from tpm_utils import *
from bsp.tpm import *
DEVNULL = open(os.devnull,'w')

from gui_utils import *
from rf_jig import *
from rfjig_bsp import *
from ip_scan import *
from optparse import OptionParser
import datetime

RXPKT_HEAD   = 1
#slave  = 5
RXPKT_MASTER = 124
#RXPKT_CMD    = 99 # ask version
#RXPKT_CMD    = 108 # get port
#RXPKT_CMD = 110 # get_data
RXPKT_CMD = 111 # set_data
RXPKT_COUNT  = 1
#RXPKT_DATA_TYPE = 12 # U16
RXPKT_DATA_TYPE = 8 # U8
RXPKT_PORT_TYPE = 4 # DIO
#RXPKT_PORT_NUMBER = 108 # 00_15
#RXPKT_PORT_NUMBER = 96 # 00_07
RXPKT_PORT_NUMBER = 97 # 08_15 # Attenuation


def bit2att(val):
    attenuazione  = ((val&2**0)>>0) * 0.5
    attenuazione += ((val&2**1)>>1) * 16
    attenuazione += ((val&2**2)>>2) * 1
    attenuazione += ((val&2**3)>>3) * 8
    attenuazione += ((val&2**4)>>4) * 2
    attenuazione += ((val&2**5)>>5) * 4
    return attenuazione

def att2bit(val):
    #print("\natt2bit(",val,")\tBin:",bin(val),
    val = int(val*2)
    #print val,")\tBin:",bin(val),
    attenuazione  = ((val&2**0)>>0) * 1
    attenuazione += ((val&2**1)>>1) * 4
    attenuazione += ((val&2**2)>>2) * 16
    attenuazione += ((val&2**3)>>3) * 32
    attenuazione += ((val&2**4)>>4) * 8
    attenuazione += ((val&2**5)>>5) * 2
    #print attenuazione,bin(attenuazione)
    return attenuazione

def get_att_value(s,slave):
    RXPKT_CMD = 110 # get_data
    RXPKT_PORT_NUMBER = 97 # 08_15 # Attenuation
    msg = struct.pack('>BBBBBBBBB', RXPKT_HEAD, slave, RXPKT_MASTER, RXPKT_CMD, RXPKT_COUNT, 3, RXPKT_DATA_TYPE, RXPKT_PORT_TYPE, RXPKT_PORT_NUMBER)
    s.send(msg)
    a=s.recv(32)
    if struct.unpack('>'+str(len(a))+'B',a)[5]==0:
        att=bit2att(struct.unpack('>'+str(len(a))+'B',a)[10])
    else:
        att=-1
    return att

def set_att_value(s,slave,value):
    value=round(value*2)/2  # 0.5 dB is the step for attenuation
    RXPKT_CMD = 111 # set_data
    RXPKT_PORT_NUMBER = 97 # 08_15 # Attenuation
    msg = struct.pack('>BBBBBBBBBB', RXPKT_HEAD, slave, RXPKT_MASTER, RXPKT_CMD, RXPKT_COUNT, 4, RXPKT_DATA_TYPE, RXPKT_PORT_TYPE, RXPKT_PORT_NUMBER,att2bit(value))
    s.send(msg)
    a=s.recv(32)
    if struct.unpack('>'+str(len(a))+'B',a)[5]!=0:
        print "Cmd returned an error!!!"

def get_vr_value(s,slave):
    RXPKT_CMD = 110 # get_data
    RXPKT_PORT_NUMBER = 96  # 00_07
    msg = struct.pack('>BBBBBBBBB', RXPKT_HEAD, slave, RXPKT_MASTER, RXPKT_CMD, RXPKT_COUNT, 3, RXPKT_DATA_TYPE, RXPKT_PORT_TYPE, RXPKT_PORT_NUMBER)
    s.send(msg)
    a=s.recv(32)
    if struct.unpack('>'+str(len(a))+'B',a)[5]==0:
        #print("\n\n\n",struct.unpack('>'+str(len(a))+'B',a),"\n\n\n"
        val=struct.unpack('>'+str(len(a))+'B',a)[10]
    else:
        val=-1
    return val

def set_vr_value(s,slave,value):
    RXPKT_CMD = 111 # set_data
    RXPKT_PORT_NUMBER = 96  # 00_07
    #print("Setting val:",value
    msg = struct.pack('>BBBBBBBBBB', RXPKT_HEAD, slave, RXPKT_MASTER, RXPKT_CMD, RXPKT_COUNT, 4, RXPKT_DATA_TYPE, RXPKT_PORT_TYPE, RXPKT_PORT_NUMBER,value)
    s.send(msg)
    a=s.recv(32)
    if struct.unpack('>'+str(len(a))+'B',a)[5]!=0:
        print "Cmd returned an error!!!"

def stampa_conf(ip, rx_id, att_val, vrval):
    print "\n\nBox IP: %s"%(ip),
    for i in rx_id:
        print "\tRx-%d"%(i),
    print ""
    print "-----------------------",
    for i in rx_id:
        print "--------",
    print ""

    print "DSA dB Val:\t",
    for i in att_val:
        print "\t%3.1f"%(i),
    print ""

    print "IF AMP 1:\t",
    for i in vrval:
        if ((i & 4) == 4):
            print "\tON",
        else:
            print "\tOFF",
    print ""

    print "IF AMP 2:\t",
    for i in vrval:
        if ((i & 1) == 1):
            print "\tON",
        else:
            print "\tOFF",
    print ""

    print "IF AMP 3:\t",
    for i in vrval:
        if ((i & 2) == 2):
            print "\tON",
        else:
            print "\tOFF",
    print ""

    print "IF AMP 4:\t",
    for i in vrval:
        if ((i & 8) == 8):
            print "\tON",
        else:
            print "\tOFF",
    print ""

    print "RF AMP:\t\t",
    for i in vrval:
        if ((i & 16) == 16):
            print "\tON",
        else:
            print "\tOFF",
    print ""

    print "OL AMP:\t\t",
    for i in vrval:
        if ((i & 128) == 128):
            print "\tON",
        else:
            print "\tOFF",
    print ""

    print "DSA Regulator:\t",
    for i in vrval:
        if ((i & 32) == 32):
            print "\tON",
        else:
            print "\tOFF",
    print ""

def open_rx_connections(rx_ip_list):
	s = []
	for i in range(len(rx_ip_list)):
		s += [socket.socket(socket.AF_INET, socket.SOCK_STREAM)]
		s[i].connect((rx_ip_list[i], 5002))
	return s

def close_rx_connections(s):
	for i in range(len(s)):
		s[i].close()

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-t", "--time",
					  dest="time",
					  default=5,
					  help="Time interval in seconds")

	parser.add_option("-b", "--board_ip",
					  dest="board_ip",
					  default="",
					  help="TPM Board IP")

	parser.add_option('-e', '--eqvalue',
					  dest='eqvalue',
					  type='float',
					  default='-50',
					  help='Equalization Value (Default: -50 which means do not equalize)')

	(options, args) = parser.parse_args()

	print "\n######################################################"
	print "\n\nTPM Input Levels"

	# Search for TPMs
	# TPMs = ip_scan()
	TPMs = [options.board_ip]
	data = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y/%m/%d")
	ora = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%H:%M:%S")
	print "\nStart Reading on " + data + " at " + ora + "\n\n"
	# TPMs = ['10.0.10.{0}'.format(i+1) for i in xrange(16)]

	remap = [1, 0, 3, 2, 5, 4, 7, 6, 30, 31, 28, 29, 26, 27, 24, 25, 9, 8, 11, 10, 13, 12, 15, 14, 22, 23, 20, 21, 18, 19,
			 16, 17]

	rx_ip_list = ["192.168.69.5", "192.168.69.6", "192.168.69.7", "192.168.69.8"]
	best_rx = [	["2N-3-1", 1, 1],
				["2N-3-2", 1, 2],
				["2N-3-3", 1, 3],
				["2N-3-4", 1, 4],
				["2N-4-1", 1, 5],
				["2N-4-2", 1, 6],
				["2N-4-3", 1, 7],
				["2N-4-4", 1, 8],
				["2N-5-1", 2, 1],
				["2N-5-2", 2, 2],
				["2N-5-3", 2, 3],
				["2N-5-4", 2, 4],
				["unused", 0, 1],
				["unused", 0, 2],
				["unused", 0, 3],
				["unused", 0, 4],
				["2N-6-1", 2, 5],
				["2N-6-2", 2, 6],
				["2N-6-3", 2, 7],
				["2N-6-4", 2, 8],
				["2N-7-1", 3, 1],
				["2N-7-2", 3, 2],
				["2N-7-3", 3, 3],
				["2N-7-4", 3, 4],
				["2N-8-1", 3, 5],
				["2N-8-2", 3, 6],
				["2N-8-3", 3, 7],
				["2N-8-4", 3, 8],
				["unused", 0, 5],
				["unused", 0, 6],
				["unused", 0, 7],
				["unused", 0, 8]]
	try:

		sock = open_rx_connections(rx_ip_list)

		ora = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y-%m-%d %H:%M:%S")
		rms_map = []
		print "\nMeasurement: " + ora + "\n"
		for i in TPMs:
			tpm = int(i.split(".")[-1])
			freqs, spettro, rawdata, rms, rfpower = get_raw_meas(i)
		print "   RxBoxIP   \tCarrier\t  DSA\tANTENNA\t input\tLEVEL"
		print "\t\t  id\t   dB\t BEST\t   #\t dBm "
		print "-------------------------------------------------------------------------"
		for k in xrange(len(rfpower)):
			rx_att = get_att_value(sock[best_rx[k][1]], best_rx[k][2])
			print " %s\t   %s\t  %3.1f\t%s\t   %02d\t %3.1f " % (rx_ip_list[best_rx[k][1]], best_rx[k][2], rx_att, best_rx[k][0], k, rfpower[remap[k]]),
			if not options.eqvalue == -50:
				diff = float(options.eqvalue) - rfpower[remap[k]]
				if diff < 0:
					print "\t--> diff is + %3.1f" % (np.clip([abs(diff)], 0, 31.5)[0])
					# set_att_value(s, antennas[i][2], antennas[i][3], numpy.clip([rx_att_A + abs(diffA)], 0, 31.5)[0])
				else:
					print "\t--> diff is - %3.1f" % (np.clip([diff], 0, 31.5)[0])
			else:
				print

		if not options.eqvalue == -50:
			print "\n\nSignal Equalization:"
			time.sleep(0.3)
			for k in xrange(len(rfpower)):
				diff = float(options.eqvalue) - rfpower[remap[k]]
				rx_att = get_att_value(sock[best_rx[k][1]], best_rx[k][2])
				if diff < 0:
					new_att = np.clip([rx_att + abs(diff)], 0, 31.5)[0]
				else:
					new_att = np.clip([rx_att - diff], 0, 31.5)[0]
				print "  TPM/ADU input %02d:  %s:%d  DSA  from %3.1f dB   to   %3.1f dB"%(k, rx_ip_list[best_rx[k][1]],  best_rx[k][2], rx_att, round(new_att*2)/2)
				set_att_value(sock[best_rx[k][1]], best_rx[k][2], new_att)
			print "\n\nEqualization Completed!\n\n...Reading again...\n\n"
			time.sleep(0.3)

			for i in TPMs:
				tpm = int(i.split(".")[-1])
				freqs, spettro, rawdata, rms, rfpower = get_raw_meas(i)
			print "   RxBoxIP   \tCarrier\t  DSA\tANTENNA\t input\tLEVEL"
			print "\t\t  id\t   dB\t BEST\t   #\t dBm "
			print "-------------------------------------------------------------------------"
			for k in xrange(len(rfpower)):
				rx_att = get_att_value(sock[best_rx[k][1]], best_rx[k][2])
				print " %s\t   %s\t  %3.1f\t%s\t   %02d\t %3.1f " % (rx_ip_list[best_rx[k][1]], best_rx[k][2], rx_att, best_rx[k][0], k, rfpower[remap[k]]),
				if not options.eqvalue == -50:
					diff = float(options.eqvalue) - rfpower[remap[k]]
					if diff < 0:
						print "\t--> diff is + %3.1f" % (np.clip([abs(diff)], 0, 31.5)[0])
						# set_att_value(s, antennas[i][2], antennas[i][3], numpy.clip([rx_att_A + abs(diffA)], 0, 31.5)[0])
					else:
						print "\t--> diff is - %3.1f" % (np.clip([diff], 0, 31.5)[0])
				else:
					print
	
		close_rx_connections(sock)
		print
	except KeyboardInterrupt:

		print "\nExiting...\n\n"
