#!/usr/bin/env python
"""
PyQt4 Graphic User Interface for BEST Receivers

Andrea Mattana

"""
from PyQt4 import QtCore, QtGui
import sys, time, struct, socket
from threading import Thread

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2018, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

box1_names = [["1N-1-1", "1N-1-2", "1N-1-3", "1N-1-4", "1N-2-1", "1N-2-2", "1N-2-3", "1N-2-4"],
			  ["1N-3-1", "1N-3-2", "1N-3-3", "1N-3-4", "1N-4-1", "1N-4-2", "1N-4-3", "1N-4-4"],
			  ["1N-5-1", "1N-5-2", "1N-5-3", "1N-5-4", "1N-6-1", "1N-6-2", "1N-6-3", "1N-6-4"],
			  ["1N-7-1", "1N-7-2", "1N-7-3", "1N-7-4", "1N-8-1", "1N-8-2", "1N-8-3", "1N-8-4"]]
N_BOXES = 4
N_CARRIER = 8
CARRIER_ETH_PORT = 5002

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


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


def clickable(widget):
    class Filter(QtCore.QObject):
        clicked = QtCore.pyqtSignal()
        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QtCore.QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        return True
            return False
    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked


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

def create_carrier(frame_box, x, y, w, h, serial_id, name):
	carrier = {}
	carrier['frame_antenna'] = QtGui.QFrame(frame_box)
	carrier['frame_antenna'].setGeometry(QtCore.QRect(x, y, w, h))
	carrier['frame_antenna'].setFrameShape(QtGui.QFrame.Box)
	carrier['frame_antenna'].setFrameShadow(QtGui.QFrame.Plain)

	carrier['level'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['level'].setGeometry(QtCore.QRect(0, 0, 148, 40))
	font = QtGui.QFont()
	font.setPointSize(14)
	font.setBold(True)
	font.setWeight(75)
	carrier['level'].setFont(font)
	carrier['level'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 255);"))
	carrier['level'].setFrameShape(QtGui.QFrame.Box)
	carrier['level'].setAlignment(QtCore.Qt.AlignCenter)

	carrier['flag_rf'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['flag_rf'].setGeometry(QtCore.QRect(0, 39, 50, 30))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	carrier['flag_rf'].setFont(font)
	carrier['flag_rf'].setStyleSheet(_fromUtf8("background-color: rgb(181, 181, 181); color: rgb(0, 0, 0);"))
	carrier['flag_rf'].setFrameShape(QtGui.QFrame.Box)
	carrier['flag_rf'].setAlignment(QtCore.Qt.AlignCenter)
	carrier['flag_rf'].setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

	carrier['flag_ol'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['flag_ol'].setGeometry(QtCore.QRect(0, 68, 50, 30))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	carrier['flag_ol'].setFont(font)
	carrier['flag_ol'].setStyleSheet(_fromUtf8("background-color: rgb(181, 181, 181); color: rgb(0, 0, 0);"))
	carrier['flag_ol'].setFrameShape(QtGui.QFrame.Box)
	carrier['flag_ol'].setAlignment(QtCore.Qt.AlignCenter)
	carrier['flag_ol'].setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

	carrier['flag_dsa'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['flag_dsa'].setGeometry(QtCore.QRect(0, 97, 50, 30))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	carrier['flag_dsa'].setFont(font)
	carrier['flag_dsa'].setStyleSheet(_fromUtf8("background-color: rgb(181, 181, 181); color: rgb(0, 0, 0);"))
	carrier['flag_dsa'].setFrameShape(QtGui.QFrame.Box)
	carrier['flag_dsa'].setAlignment(QtCore.Qt.AlignCenter)
	carrier['flag_dsa'].setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

	carrier['flag_if1'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['flag_if1'].setGeometry(QtCore.QRect(49, 39, 50, 30))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	carrier['flag_if1'].setFont(font)
	carrier['flag_if1'].setStyleSheet(_fromUtf8("background-color: rgb(181, 181, 181); color: rgb(0, 0, 0);"))
	carrier['flag_if1'].setFrameShape(QtGui.QFrame.Box)
	carrier['flag_if1'].setAlignment(QtCore.Qt.AlignCenter)
	carrier['flag_if1'].setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

	carrier['flag_if2'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['flag_if2'].setGeometry(QtCore.QRect(98, 39, 50, 30))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	carrier['flag_if2'].setFont(font)
	carrier['flag_if2'].setStyleSheet(_fromUtf8("background-color: rgb(181, 181, 181); color: rgb(0, 0, 0);"))
	carrier['flag_if2'].setFrameShape(QtGui.QFrame.Box)
	carrier['flag_if2'].setAlignment(QtCore.Qt.AlignCenter)
	carrier['flag_if2'].setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

	carrier['dsa_value'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['dsa_value'].setGeometry(QtCore.QRect(49, 97, 99, 30))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	carrier['dsa_value'].setFont(font)
	carrier['dsa_value'].setStyleSheet(_fromUtf8("background-color: rgb(181, 181, 181); color: rgb(0, 0, 0);"))
	carrier['dsa_value'].setFrameShape(QtGui.QFrame.Box)
	carrier['dsa_value'].setAlignment(QtCore.Qt.AlignCenter)
	carrier['dsa_value'].setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

	carrier['flag_if3'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['flag_if3'].setGeometry(QtCore.QRect(49, 68, 50, 30))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	carrier['flag_if3'].setFont(font)
	carrier['flag_if3'].setStyleSheet(_fromUtf8("background-color: rgb(181, 181, 181); color: rgb(0, 0, 0);"))
	carrier['flag_if3'].setFrameShape(QtGui.QFrame.Box)
	carrier['flag_if3'].setAlignment(QtCore.Qt.AlignCenter)
	carrier['flag_if3'].setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

	carrier['flag_if4'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['flag_if4'].setGeometry(QtCore.QRect(98, 68, 50, 30))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	carrier['flag_if4'].setFont(font)
	carrier['flag_if4'].setStyleSheet(_fromUtf8("background-color: rgb(181, 181, 181); color: rgb(0, 0, 0);"))
	carrier['flag_if4'].setFrameShape(QtGui.QFrame.Box)
	carrier['flag_if4'].setAlignment(QtCore.Qt.AlignCenter)
	carrier['flag_if4'].setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

	carrier['slave_id'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['slave_id'].setGeometry(QtCore.QRect(0, 126, 148, 36))
	font = QtGui.QFont()
	font.setPointSize(14)
	font.setBold(True)
	font.setWeight(75)
	carrier['slave_id'].setFont(font)
	carrier['slave_id'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 255); color: rgb(0, 0, 0);"))
	carrier['slave_id'].setFrameShape(QtGui.QFrame.Box)
	carrier['slave_id'].setAlignment(QtCore.Qt.AlignCenter)

	carrier['ant_name'] = QtGui.QLabel(carrier['frame_antenna'])
	carrier['ant_name'].setGeometry(QtCore.QRect(0, 160, 148, 36))
	font = QtGui.QFont()
	font.setPointSize(14)
	font.setBold(True)
	font.setWeight(75)
	carrier['ant_name'].setFont(font)
	carrier['ant_name'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 255); color: rgb(0, 0, 0);"))
	carrier['ant_name'].setFrameShape(QtGui.QFrame.Box)
	carrier['ant_name'].setAlignment(QtCore.Qt.AlignCenter)

	carrier['level'].setText("---")
	carrier['flag_rf'].setText("RF")
	carrier['flag_ol'].setText("OL")
	carrier['flag_dsa'].setText("DSA")
	carrier['flag_if1'].setText("IF 1")
	carrier['flag_if2'].setText("IF 2")
	carrier['dsa_value'].setText("0.0")
	carrier['flag_if3'].setText("IF 3")
	carrier['flag_if4'].setText("IF 4")
	carrier['slave_id'].setText("serial id: "+str(int(serial_id)))
	carrier['ant_name'].setText(name)

	return carrier

def create_eth_carrier(frame_box, x, y, w, h, ip):
	eth = {}

	eth['frame_box_eth'] = QtGui.QFrame(frame_box)
	eth['frame_box_eth'].setGeometry(QtCore.QRect(x, y, w, h))
	eth['frame_box_eth'].setFrameShape(QtGui.QFrame.Box)
	eth['frame_box_eth'].setFrameShadow(QtGui.QFrame.Plain)

	eth['label_ip'] = QtGui.QLabel(eth['frame_box_eth'])
	eth['label_ip'].setGeometry(QtCore.QRect(0, 40, 181, 38))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	eth['label_ip'].setFont(font)
	eth['label_ip'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 255); color: rgb(0, 0, 0);"))
	eth['label_ip'].setFrameShape(QtGui.QFrame.Box)
	eth['label_ip'].setAlignment(QtCore.Qt.AlignCenter)

	eth['label_box'] = QtGui.QLabel(eth['frame_box_eth'])
	eth['label_box'].setGeometry(QtCore.QRect(0, 4, 181, 38))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	eth['label_box'].setFont(font)
	eth['label_box'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 255);"))
	eth['label_box'].setFrameShape(QtGui.QFrame.Box)
	eth['label_box'].setAlignment(QtCore.Qt.AlignCenter)

	eth['label_ver'] = QtGui.QLabel(eth['frame_box_eth'])
	eth['label_ver'].setGeometry(QtCore.QRect(0, 118, 181, 38))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	eth['label_ver'].setFont(font)
	eth['label_ver'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 255);"))
	eth['label_ver'].setFrameShape(QtGui.QFrame.Box)
	eth['label_ver'].setAlignment(QtCore.Qt.AlignCenter)

	eth['label_carrier'] = QtGui.QLabel(eth['frame_box_eth'])
	eth['label_carrier'].setGeometry(QtCore.QRect(0, 155, 181, 36))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	eth['label_carrier'].setFont(font)
	eth['label_carrier'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 255);"))
	eth['label_carrier'].setFrameShape(QtGui.QFrame.Box)
	eth['label_carrier'].setAlignment(QtCore.Qt.AlignCenter)

	eth['label_port'] = QtGui.QLabel(eth['frame_box_eth'])
	eth['label_port'].setGeometry(QtCore.QRect(0, 76, 181, 38))
	font = QtGui.QFont()
	font.setPointSize(12)
	font.setBold(True)
	font.setWeight(75)
	eth['label_port'].setFont(font)
	eth['label_port'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 255);"))
	eth['label_port'].setFrameShape(QtGui.QFrame.Box)
	eth['label_port'].setAlignment(QtCore.Qt.AlignCenter)

	eth['label_ip'].setText(ip)
	eth['label_box'].setText("Box IP")
	eth['label_ver'].setText("Version")
	eth['label_carrier'].setText("Carrier 2017")
	eth['label_port'].setText("5200")

	return eth

def create_box_carrier(wid_rx, x, y, w, h, ip, names):
	bb = {}
	bb['frame_box'] = QtGui.QFrame(wid_rx)
	#frame_box.setGeometry(QtCore.QRect(20, 80, 1591, 216))
	bb['frame_box'].setGeometry(QtCore.QRect(x, y, w, h))
	bb['frame_box'].setFrameShape(QtGui.QFrame.Box)
	bb['frame_box'].setFrameShadow(QtGui.QFrame.Plain)
	bb['frame_box'].setLineWidth(1)

	bb['box_eth'] = create_eth_carrier(bb['frame_box'], 20, 10, 181, 196, ip)
	bb['carriers'] = []
	for i in range(8):
		bb['carriers'] += [create_carrier(bb['frame_box'], 230+(170*i), 10, 148, 196, i+1, names[i])]
	bb['sock'] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print "Connecting to", ip, CARRIER_ETH_PORT, "...",
	bb['sock'].connect((ip, CARRIER_ETH_PORT))
	print "done!"
	return bb


class MyDialog(QtGui.QDialog):

	# Signal for Slots
	poll_signal = QtCore.pyqtSignal()

	def __init__(self, parent=None):
		super(MyDialog, self).__init__(parent)

		self.resize(1660, 900)

		self.gridLayout = QtGui.QGridLayout(self) # Main Grid Layout Start
		self.tabWidget = QtGui.QTabWidget(self)
		self.tab_conf = QtGui.QWidget()
		self.tabWidget.addTab(self.tab_conf, "Configuration")

		rack = range(N_BOXES)
		rconf = {}
		rconf['tabName'] = "Receivers"
		rconf['box'] = []
		for box in rack:
			rconf['box'] += [{}]
			rconf['box'][box]['ip'] = "192.168.69."+str(5+box)

		self.create_rack(rconf)

		# Add SLOTS
		for box in rack:
			for rx in range(N_CARRIER):
				clickable(self.bb[box]['carriers'][rx]['flag_rf']).connect(lambda b=box, r=rx: self.set_rf(b,r))
				clickable(self.bb[box]['carriers'][rx]['flag_ol']).connect(lambda b=box, r=rx: self.set_ol(b, r))
				clickable(self.bb[box]['carriers'][rx]['flag_dsa']).connect(lambda b=box, r=rx: self.set_dsa(b, r))
				clickable(self.bb[box]['carriers'][rx]['flag_if1']).connect(lambda b=box, r=rx: self.set_if1(b, r))
				clickable(self.bb[box]['carriers'][rx]['flag_if2']).connect(lambda b=box, r=rx: self.set_if2(b, r))
				clickable(self.bb[box]['carriers'][rx]['flag_if3']).connect(lambda b=box, r=rx: self.set_if3(b, r))
				clickable(self.bb[box]['carriers'][rx]['flag_if4']).connect(lambda b=box, r=rx: self.set_if4(b, r))

		self.ctrl_enabled = False
		clickable(self.label_en_controls).connect(self.enable_controls)

		self.tabWidget.setCurrentIndex(1)

		self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)  # Main Grid Layout End

		self.stopThreads = False
		self.busy = False
		self.process_poll = Thread(target=self.read_boxes)
		self.active_box = 0
		time.sleep(1)
		if not self.process_poll.isAlive():
			print "\nStarted Polling Boxes..."
			self.process_poll.start()

	def closeEvent(self, event):
		result = QtGui.QMessageBox.question(self,
											"Confirm Exit...",
											"Are you sure you want to exit ?",
											QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		event.ignore()

		if result == QtGui.QMessageBox.Yes:
			event.accept()
			self.stopThreads = True
			self.close_rx_connections()
			print "Stopping Threads"
			time.sleep(0.1)

	def create_rack(self, rconf):
		self.border_tab_rx = QtGui.QWidget()

		self.tab_rx = QtGui.QWidget(self.border_tab_rx)
		self.tab_rx .setGeometry(QtCore.QRect(0, 0, 1640, 860))

		self.subctrl = QtGui.QWidget(self.tab_rx)
		self.subctrl.setGeometry(QtCore.QRect(0, 0, 1640, 70))

		self.subtab_rx = QtGui.QWidget(self.tab_rx)
		self.subtab_rx.setGeometry(QtCore.QRect(0, 80, 1640, 760))

		self.gridLayout_tab_rx = QtGui.QGridLayout(self.subtab_rx)
		self.scrollArea = QtGui.QScrollArea(self.subtab_rx)
		self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.scrollArea.setWidgetResizable(False)
		self.scrollAreaWidgetContents = QtGui.QWidget()
		self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1600, 226 * N_BOXES))
		self.gridLayout_box_carrier = QtGui.QGridLayout(self.scrollAreaWidgetContents)

		self.frame_ctrl = QtGui.QFrame(self.subctrl)
		self.frame_ctrl.setGeometry(QtCore.QRect(10, 10, 1600, 60))
		self.frame_ctrl.setFrameShape(QtGui.QFrame.Box)
		self.frame_ctrl.setFrameShadow(QtGui.QFrame.Plain)

		self.frame_eq = QtGui.QFrame(self.frame_ctrl)
		self.frame_eq.setGeometry(QtCore.QRect(10, 10, 520, 41))
		self.frame_eq.setFrameShape(QtGui.QFrame.Box)
		self.frame_eq.setFrameShadow(QtGui.QFrame.Plain)
		self.label = QtGui.QLabel(self.frame_eq)
		self.label.setGeometry(QtCore.QRect(10, 10, 291, 21))
		font = QtGui.QFont()
		font.setPointSize(12)
		self.label.setFont(font)
		self.label.setText("Amplitude Equalization to Level (dBm):")
		self.lineEdit = QtGui.QLineEdit(self.frame_eq)
		self.lineEdit.setGeometry(QtCore.QRect(310, 5, 91, 31))
		font = QtGui.QFont()
		font.setPointSize(14)
		self.lineEdit.setFont(font)
		self.lineEdit.setAlignment(QtCore.Qt.AlignCenter)
		self.lineEdit.setText("-5")
		self.eq_apply = QtGui.QPushButton(self.frame_eq)
		self.eq_apply.setGeometry(QtCore.QRect(420, 5, 94, 31))
		self.eq_apply.setAutoDefault(False)
		self.eq_apply.setText("Apply")

		self.frame_ant_layout = QtGui.QFrame(self.frame_ctrl)
		self.frame_ant_layout.setGeometry(QtCore.QRect(550, 10, 320, 41))
		self.frame_ant_layout.setFrameShape(QtGui.QFrame.Box)
		self.frame_ant_layout.setFrameShadow(QtGui.QFrame.Plain)
		self.label_3 = QtGui.QLabel(self.frame_ant_layout)
		self.label_3.setGeometry(QtCore.QRect(20, 10, 131, 21))
		font = QtGui.QFont()
		font.setPointSize(12)
		self.label_3.setFont(font)
		self.cb_layout = QtGui.QComboBox(self.frame_ant_layout)
		self.cb_layout.setGeometry(QtCore.QRect(150, 5, 150, 31))
		font = QtGui.QFont()
		font.setBold(True)
		font.setWeight(75)
		self.cb_layout.setFont(font)
		self.cb_layout.addItem(_fromUtf8(""))
		self.cb_layout.addItem(_fromUtf8(""))
		self.cb_layout.addItem(_fromUtf8(""))

		self.frame_rx_ctrl = QtGui.QFrame(self.frame_ctrl)
		self.frame_rx_ctrl.setGeometry(QtCore.QRect(890, 10, 680, 41))
		self.frame_rx_ctrl.setFrameShape(QtGui.QFrame.Box)
		self.frame_rx_ctrl.setFrameShadow(QtGui.QFrame.Plain)
		self.label_en_controls = QtGui.QLabel(self.frame_rx_ctrl)
		self.label_en_controls.setGeometry(QtCore.QRect(235, 7, 171, 26))
		font = QtGui.QFont()
		font.setPointSize(11)
		font.setBold(True)
		font.setWeight(75)
		self.label_en_controls.setFont(font)
		self.label_en_controls.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
		self.label_en_controls.setStyleSheet(_fromUtf8("background-color: rgb(255, 0, 0);\ncolor: rgb(255, 255, 0);"))
		self.label_en_controls.setAlignment(QtCore.Qt.AlignCenter)
		self.label_save_rx_conf = QtGui.QLabel(self.frame_rx_ctrl)
		self.label_save_rx_conf.setGeometry(QtCore.QRect(440, 7, 211, 26))
		font = QtGui.QFont()
		font.setFamily(_fromUtf8("Cantarell"))
		font.setPointSize(11)
		font.setBold(True)
		font.setWeight(75)
		self.label_save_rx_conf.setFont(font)
		self.label_save_rx_conf.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
		self.label_save_rx_conf.setStyleSheet(_fromUtf8("background-color: rgb(0, 85, 255);\ncolor: rgb(255, 255, 0);"))
		self.label_save_rx_conf.setAlignment(QtCore.Qt.AlignCenter)
		self.label_connect_all = QtGui.QLabel(self.frame_rx_ctrl)
		self.label_connect_all.setGeometry(QtCore.QRect(30, 7, 171, 26))
		font = QtGui.QFont()
		font.setFamily(_fromUtf8("Cantarell"))
		font.setPointSize(11)
		font.setBold(True)
		font.setWeight(75)
		self.label_connect_all.setFont(font)
		self.label_connect_all.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
		self.label_connect_all.setStyleSheet(_fromUtf8("background-color: rgb(0, 85, 255);\ncolor: rgb(255, 255, 0);"))
		self.label_connect_all.setAlignment(QtCore.Qt.AlignCenter)

		self.label.setText("Amplitude Equalization to Level (dBm):")
		self.lineEdit.setText("-5")
		self.eq_apply.setText("Apply")
		self.label_3.setText("Change Layout:")
		self.cb_layout.setItemText(0, "RX Controls")
		self.cb_layout.setItemText(1, "Bar Plot")
		self.cb_layout.setItemText(2, "Spectra Plot")
		self.label_en_controls.setText("ENABLE CONTROLS")
		self.label_save_rx_conf.setText("SAVE RX CONF")
		self.label_connect_all.setText("CONNECT ALL")

		self.bb = []
		for i in range(N_BOXES):
			self.bb.append(create_box_carrier(self.scrollAreaWidgetContents, 20, 80, 1591, 216, rconf['box'][i]['ip'], box1_names[i]))
			self.gridLayout_box_carrier.addWidget(self.bb[i]['frame_box'], i, 0, 1, 1)

		self.scrollArea.setWidget(self.scrollAreaWidgetContents)
		self.gridLayout_tab_rx.addWidget(self.scrollArea, 0, 0, 1, 1)

		self.tabWidget.addTab(self.border_tab_rx, rconf['tabName'])

	def enable_controls(self):
		if self.ctrl_enabled == False:
			self.ctrl_enabled = True
			self.label_en_controls.setStyleSheet(_fromUtf8("background-color: rgb(85, 255, 0); color: rgb(0, 0, 0);"))
		else:
			self.ctrl_enabled = False
			self.label_en_controls.setStyleSheet(_fromUtf8("background-color: rgb(255, 0, 0); color: rgb(255, 255, 0);"))

	def set_rf(self, box, slave):
		#print "Received cmd RF for Box %i and Rx #%i"%(box,slave),
		if self.ctrl_enabled:
			self.busy = True
			vr = get_vr_value(self.bb[box]['sock'], slave+1)
			#print "Old value was:", vr,
			if not ((vr & 16) == 16):
				vr += 16
			else:
				vr -= 16
			#print "New value is:", vr, "BOX",box, "SLAVE", slave
			set_vr_value(self.bb[box]['sock'], slave+1, vr)
			self.updateBox(box)
			self.busy = False


	def set_ol(self, box, slave):
		#print "Received cmd OL for Box %i and Rx #%i" % (box, slave)
		if self.ctrl_enabled:
			self.busy = True
			vr = get_vr_value(self.bb[box]['sock'], slave + 1)
			# print "Old value was:", vr,
			if not ((vr & 128) == 128):
				vr += 128
			else:
				vr -= 128
			# print "New value is:", vr, "BOX",box, "SLAVE", slave
			set_vr_value(self.bb[box]['sock'], slave + 1, vr)
			self.updateBox(box)
			self.busy = False

	def set_dsa(self, box, slave):
		#print "Received cmd DSA for Box %i and Rx #%i" % (box, slave)
		if self.ctrl_enabled:
			self.busy = True
			vr = get_vr_value(self.bb[box]['sock'], slave + 1)
			# print "Old value was:", vr,
			if not ((vr & 32) == 32):
				vr += 32
			else:
				vr -= 32
			# print "New value is:", vr, "BOX",box, "SLAVE", slave
			set_vr_value(self.bb[box]['sock'], slave + 1, vr)
			self.updateBox(box)
			self.busy = False

	def set_if1(self, box, slave):
		# print "Received cmd IF1 for Box %i and Rx #%i" % (box, slave)
		if self.ctrl_enabled:
			self.busy = True
			vr = get_vr_value(self.bb[box]['sock'], slave + 1)
			# print "Old value was:", vr,
			if not ((vr & 4) == 4):
				vr += 4
			else:
				vr -= 4
			# print "New value is:", vr, "BOX",box, "SLAVE", slave
			set_vr_value(self.bb[box]['sock'], slave + 1, vr)
			self.updateBox(box)
			self.busy = False

	def set_if2(self, box, slave):
		# print "Received cmd IF2 for Box %i and Rx #%i" % (box, slave)
		if self.ctrl_enabled:
			self.busy = True
			vr = get_vr_value(self.bb[box]['sock'], slave + 1)
			# print "Old value was:", vr,
			if not ((vr & 1) == 1):
				vr += 1
			else:
				vr -= 1
			# print "New value is:", vr, "BOX",box, "SLAVE", slave
			set_vr_value(self.bb[box]['sock'], slave + 1, vr)
			self.updateBox(box)
			self.busy = False

	def set_if3(self, box, slave):
		# print "Received cmd IF3 for Box %i and Rx #%i" % (box, slave)
		if self.ctrl_enabled:
			self.busy = True
			vr = get_vr_value(self.bb[box]['sock'], slave + 1)
			# print "Old value was:", vr,
			if not ((vr & 2) == 2):
				vr += 2
			else:
				vr -= 2
			# print "New value is:", vr, "BOX",box, "SLAVE", slave
			set_vr_value(self.bb[box]['sock'], slave + 1, vr)
			self.updateBox(box)
			self.busy = False

	def set_if4(self, box, slave):
		# print "Received cmd IF4 for Box %i and Rx #%i" % (box, slave)
		if self.ctrl_enabled:
			self.busy = True
			vr = get_vr_value(self.bb[box]['sock'], slave + 1)
			# print "Old value was:", vr,
			if not ((vr & 8) == 8):
				vr += 8
			else:
				vr -= 8
			# print "New value is:", vr, "BOX",box, "SLAVE", slave
			set_vr_value(self.bb[box]['sock'], slave + 1, vr)
			self.updateBox(box)
			self.busy = False

	def read_boxes(self):
		while True:
			#print "READ BOXES"
			time.sleep(1)
			if not self.busy:
				self.poll_signal.emit()
			cycle = 0
			while cycle < 9 and not self.stopThreads:
				time.sleep(0.5)
				cycle += 0.5
			if self.stopThreads:
				break

	def updateDialog(self):
		for x in range(len(self.bb)):
			self.busy_box = x
			self.updateBox(x)
		self.busy_box = -1

	def updateBox(self, x):
		#print "Polling Box: %s..."%(self.bb[x]['box_eth']['label_ip'].text()),
		for i in range(8):
			#print i+1,
			#print "%3.1f"%(float(att_val[i])), x, i, self.bb[x]['carriers'][i]['dsa_value'].text()
			self.bb[x]['carriers'][i]['dsa_value'].setText("%3.1f"%(float(get_att_value(self.bb[x]['sock'], i+1))))
			self.bb[x]['carriers'][i]['dsa_value'].setStyleSheet(_fromUtf8(
					"background-color: rgb(255, 255, 255); color: rgb(0, 0, 0);"))

			vr = get_vr_value(self.bb[x]['sock'], i+1)
			# IF AMP 1
			if (vr & 4) == 4:
				self.bb[x]['carriers'][i]['flag_if1'].setStyleSheet(_fromUtf8(
					"background-color: rgb(85, 255, 0); color: rgb(0, 0, 0);"))
			else:
				self.bb[x]['carriers'][i]['flag_if1'].setStyleSheet(_fromUtf8(
					"background-color: rgb(255, 0, 0); color: rgb(0, 0, 0);"))

			# IF AMP 2
			if (vr & 1) == 1:
				self.bb[x]['carriers'][i]['flag_if2'].setStyleSheet(_fromUtf8(
					"background-color: rgb(85, 255, 0); color: rgb(0, 0, 0);"))
			else:
				self.bb[x]['carriers'][i]['flag_if2'].setStyleSheet(_fromUtf8(
					"background-color: rgb(255, 0, 0); color: rgb(0, 0, 0);"))

			# IF AMP 3
			if (vr & 2) == 2:
				self.bb[x]['carriers'][i]['flag_if3'].setStyleSheet(_fromUtf8(
					"background-color: rgb(85, 255, 0); color: rgb(0, 0, 0);"))
			else:
				self.bb[x]['carriers'][i]['flag_if3'].setStyleSheet(_fromUtf8(
					"background-color: rgb(255, 0, 0); color: rgb(0, 0, 0);"))

			# IF AMP 4
			if (vr & 8) == 8:
				self.bb[x]['carriers'][i]['flag_if4'].setStyleSheet(_fromUtf8(
					"background-color: rgb(85, 255, 0); color: rgb(0, 0, 0);"))
			else:
				self.bb[x]['carriers'][i]['flag_if4'].setStyleSheet(_fromUtf8(
					"background-color: rgb(255, 0, 0); color: rgb(0, 0, 0);"))

			# RF AMP
			if (vr & 16) == 16:
				self.bb[x]['carriers'][i]['flag_rf'].setStyleSheet(_fromUtf8(
					"background-color: rgb(85, 255, 0); color: rgb(0, 0, 0);"))
			else:
				self.bb[x]['carriers'][i]['flag_rf'].setStyleSheet(_fromUtf8(
					"background-color: rgb(255, 0, 0); color: rgb(0, 0, 0);"))

			# OL AMP
			if (vr & 128) == 128:
				self.bb[x]['carriers'][i]['flag_ol'].setStyleSheet(_fromUtf8(
					"background-color: rgb(85, 255, 0); color: rgb(0, 0, 0);"))
			else:
				self.bb[x]['carriers'][i]['flag_ol'].setStyleSheet(_fromUtf8(
					"background-color: rgb(255, 0, 0); color: rgb(0, 0, 0);"))

			# DSA REGULATOR
			if (vr & 32) == 32:
				self.bb[x]['carriers'][i]['flag_dsa'].setStyleSheet(_fromUtf8(
					"background-color: rgb(85, 255, 0); color: rgb(0, 0, 0);"))
			else:
				self.bb[x]['carriers'][i]['flag_dsa'].setStyleSheet(_fromUtf8(
					"background-color: rgb(255, 0, 0); color: rgb(0, 0, 0);"))

	def close_rx_connections(self):
		for i in range(len(self.bb)):
			print "Closing connection with Box:",self.bb[i]['box_eth']['label_ip'].text(),"...",
			self.bb[i]['sock'].close()
			print "done!"


if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	dialog = MyDialog()
	dialog.poll_signal.connect(dialog.updateDialog)

	dialog.show()
	sys.exit(app.exec_())
