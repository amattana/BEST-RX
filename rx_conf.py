#!/usr/bin/env python3

import socket,sys,os
import struct
#import mad_conf_parse

#TCP_PORT = 5002
#TCP_IP = '192.168.69.1'

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
        print("Cmd returned an error!!!")

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
        print("Cmd returned an error!!!")

def stampa_conf(ip, rx_id, att_val, vrval):
    print("\n\nBox IP: %s"%(ip), end='')
    for i in rx_id:
        print("\tRx-%d"%(i), end='')
    print("")
    print("-----------------------", end='')
    for i in rx_id:
        print("--------", end='')
    print("")

    print("DSA dB Val:\t", end='')
    for i in att_val:
        print("\t%3.1f"%(i), end='')
    print("")

    print("IF AMP 1:\t", end='')
    for i in vrval:
        if ((i & 4) == 4):
            print("\tON", end='')
        else:
            print("\tOFF", end='')
    print("")

    print("IF AMP 2:\t", end='')
    for i in vrval:
        if ((i & 1) == 1):
            print("\tON", end='')
        else:
            print("\tOFF", end='')
    print("")

    print("IF AMP 3:\t", end='')
    for i in vrval:
        if ((i & 2) == 2):
            print("\tON", end='')
        else:
            print("\tOFF", end='')
    print("")

    print("IF AMP 4:\t", end='')
    for i in vrval:
        if ((i & 8) == 8):
            print("\tON", end='')
        else:
            print("\tOFF", end='')
    print("")

    print("RF AMP:\t\t", end='')
    for i in vrval:
        if ((i & 16) == 16):
            print("\tON", end='')
        else:
            print("\tOFF", end='')
    print("")

    print("OL AMP:\t\t", end='')
    for i in vrval:
        if ((i & 128) == 128):
            print("\tON", end='')
        else:
            print("\tOFF", end='')
    print("")

    print("DSA Regulator:\t", end='')
    for i in vrval:
        if ((i & 32) == 32):
            print("\tON", end='')
        else:
            print("\tOFF", end='')
    print("")


if __name__ == '__main__':

    from optparse import OptionParser
    p = OptionParser()
    p.set_usage('rx_conf.py [options]')
    p.set_description(__doc__)
    p.add_option("-b", "--box_ip", dest="box_ip", type='str', default="192.168.69.5", help="IP of the box [default: 192.168.69.5]")
    p.add_option("-r", "--receiver", dest="receiver", type='int', default=-1, help="Select the receiver.")
    p.add_option("-n", "--new_value", dest="value", type='float', default=-1, help="Set the attenuation factor, if not given just read the current value")
    p.add_option("-v", "--verbose", dest="verbose", action='store_true', default=False, help="More info")

    p.add_option("--IF_AMP1", dest="if_amp1", type='int', default=-1, help="Enable IF GALI First Amp   [0: OFF,1: ON]")
    p.add_option("--IF_AMP2", dest="if_amp2", type='int', default=-1, help="Enable IF GALI Second Amp  [0: OFF,1: ON]")
    p.add_option("--IF_AMP3", dest="if_amp3", type='int', default=-1, help="Enable IF GALI Third Amp   [0: OFF,1: ON]")
    p.add_option("--IF_AMP4", dest="if_amp4", type='int', default=-1, help="Enable IF GALI Fourth Amp  [0: OFF,1: ON]")

    p.add_option("--RF_AMP", dest="rf_amp", type='int', default=-1,   help="Enable RF GALI Amp         [0: OFF,1: ON]")
    p.add_option("--OL_AMP", dest="ol_amp", type='int', default=-1,   help="Enable OL GALI Amp         [0: OFF,1: ON]")
    p.add_option("--DSA", dest="dsa", type='int', default=-1,         help="Enable DSA power regulator [0: OFF,1: ON]")
    p.add_option("--ALL", dest="all", type='int', default=-1,         help="Enable ALL amplifiers and DSA power regulator [0: OFF,1: ON]")

    opts, args = p.parse_args(sys.argv[:])
    rx_ip = opts.box_ip
    if opts.receiver==-1:
        rx_id = range(1,9)
    else:
        rx_id = [opts.receiver]
    verbose = opts.verbose
    value = opts.value

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((rx_ip, 5002))

    att = []
    vr_val = []
    for i in rx_id:
        att += [get_att_value(s,i)]
        vr_val += [get_vr_value(s,i)]

    stampa_conf(rx_ip, rx_id, att, vr_val)
    print("")

    if not ((opts.if_amp1==-1) and (opts.if_amp2==-1) and (opts.if_amp3==-1) and (opts.if_amp4==-1)
            and (opts.rf_amp==-1) and (opts.ol_amp==-1) and (opts.dsa==-1) and (value==-1) and (opts.all==-1)):

        for i in range(len(rx_id)):

            if not opts.if_amp1==-1:
                vr_val[i] = vr_val[i] & 0b11111011
                if opts.if_amp1:
                    vr_val[i] = vr_val[i] | 4
            if not opts.if_amp2 == -1:
                vr_val[i] = vr_val[i] & 0b11111110
                if opts.if_amp2:
                    vr_val[i] = vr_val[i] | 1
            if not opts.if_amp3 == -1:
                vr_val[i] = vr_val[i] & 0b11111101
                if opts.if_amp3:
                    vr_val[i] = vr_val[i] | 2
            if not opts.if_amp4 == -1:
                vr_val[i] = vr_val[i] & 0b11110111
                if opts.if_amp4:
                    vr_val[i] = vr_val[i] | 8
            if not opts.rf_amp == -1:
                vr_val[i] = vr_val[i] & 0b11101111
                if opts.rf_amp:
                    vr_val[i] = vr_val[i] | 16
            if not opts.dsa == -1:
                vr_val[i] = vr_val[i] & 0b11011111
                if opts.dsa:
                    vr_val[i] = vr_val[i] | 32
            if not opts.ol_amp == -1:
                vr_val[i] = vr_val[i] & 0b01111111
                if opts.ol_amp:
                    vr_val[i] = vr_val[i] | 128

            if not opts.all == -1:
                if opts.all:
                    vr_val[i] = vr_val[i] | 0b10111111
                else:
                    vr_val[i] = vr_val[i] & 0b01000000

            set_vr_value(s,rx_id[i],vr_val[i])
            if not value==-1:
                set_att_value(s,rx_id[i],value)

        print("\n\nSetting new configuration...done!  ...Reading again...")

        att = []
        vr_val = []
        for i in rx_id:
            att += [get_att_value(s, i)]
            vr_val += [get_vr_value(s, i)]
        stampa_conf(rx_ip, rx_id, att, vr_val)
        print("")


    s.close()
    print("")

