#!/usr/bin/env python
# collect rssi scan samples from nl80211 (linux >3) supported
# wifi cards
#
# make sure to set the CAP_NET_ADMIN flag if not running as root:
#  setcap cap_net_admin=eip wifi-collect.py
# and to the python interpreter
#  setcap cap_net_admin=eip /usr/bin/python2.7

#from net_tools import all_interfaces, if_nametoindex
import rospy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue



from select import select
from subprocess import check_output, CalledProcessError
from sys import exit
import shlex
import re
from pprint import pformat

def publish(pub, info):
    diag = DiagnosticArray()
    diag.header.stamp = rospy.Time.now()
    status = DiagnosticStatus()
    status.hardware_id = "wifi"
    status.name = 'wifi_scan'
    status.level = status.OK
    status.message = pformat(info)
    
    for k,v in info.items():
        status.values.append(
            KeyValue(k,str(v)),
        )
    diag.status = [status]
    pub.publish(diag)

if __name__ == '__main__':
    rospy.init_node('wifiscanner')
    pub = rospy.Publisher('/wifiscanner', DiagnosticArray,
                          queue_size=10)

    # init
    interface = rospy.get_param('~iface', 'wlan0')
    interfaces = [interface]
    scan_ssid = rospy.get_param('~ssid', 'STRANDS')
#    rospy.loginfo("collecting rssi on %s",str(interfaces))

    # communication with tcpdump
    bcn_pattern = '.* (\d+) MHz.* (-\d+)dB signal .* BSSID:([0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]).* Beacon \((\S*)\) .*'
    rts_pattern = '.* (\d+) MHz.* (-\d+)dB .* TA:(%s).*'
    iwlist_pattern = '^.*Cell (\d+) - Address: ([0-9ABCDEF:]+).*\n.*Channel:(\d+)\n.*\n.*Quality=(\d+)/(\d+).*Signal level=(-[0-9]+).*\n.*\n.*ESSID:"(.+)".*$'    
    #cmdlines = [shlex.split("sudo /usr/sbin/tcpdump -eIi %s" % (i)) for i in interfaces]
    cmdlines = shlex.split("sudo iwlist %s scanning" % (interface)) 


    # we also keep a set of seen beacons and add them to the list to also
    # capture their RTS packets, further increasing the sampling rate
    parser = re.compile(iwlist_pattern, re.MULTILINE)
    bssids = {}

    while not rospy.is_shutdown():
        try:
            output=check_output(cmdlines)
            print output
            for match in parser.finditer(output):
                info = {}
                (info['cell'],
                 info['bssid'],
                 info['channel'],
                 info['quality'],
                 dummy,
                 info['signal'],
                 info['essid']) = match.groups()
                print info
                publish(pub, info)
                
        except CalledProcessError:
            rospy.logwarn('failed to get wifi scan')
#        if m is not None:
            #(freq, rssi, bssid, ssid) = m.groups()[:1]
#            (cell) = m.groups()[:1]
            #print cell
#                if ssid == scan_ssid:
#                    bssids[bssid]=[freq, rssi]
#                    publish(pub, dev, freq, rssi, bssid, ssid)
#                    print dev, freq, rssi, bssid, ssid
#                    print bssids
                #bssid = m.groups()[2]
                #if not bssid in bssids:
                #    bssids.add(bssid)
                #    parser = re.compile("|".join([bcn_pattern]+[rts_pattern%bssid for bssid in bssids]))

        rospy.sleep(5)
