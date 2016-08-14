import re
import subprocess
import sys
import os

def check_exit(exitCode):
    if exitCode:
        exit(exitCode)

# send a command to the shell and return the result
def cmd_exec_sync(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, exitOnFailure=True, env=os.environ.copy(), shell=True):
    """executes a given command in the system shell
    """
    proc = subprocess.Popen(shlex.split(cmd), stdin=stdin, stdout=stdout, stderr=stderr,env=env, shell=shell)
    return_code = proc.wait()
    return check_exit(return_code) if exitOnFailure else return_code

def cmd(cmd):
    """executes a given command in the system shell
    """
    return subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout.read().decode()

class WirelessDriver(object):
    def __new__(cls, *args, **kwargs):
        # try networksetup (Mac OS 10.10)
        response = cmd('which networksetup')
        if len(response) > 0 and 'not found' not in response:
            obj = object.__new__(NetworksetupDriver, *args, **kwargs)
            return obj
        raise Exception('Unable to find compatible wireless driver.')

    def __init__(self, interface=None):
        self.interface = interface

    def connect(self, ssid, password):
        raise NotImplementedError()

    @property
    def current_network(self):
        raise NotImplementedError()

    @property
    def interfaces(self):
        raise NotImplementedError()

    def enable(self):
        raise NotImplementedError()

    def disable(self):
        raise NotImplementedError()

    @property
    def is_enabled(self):
        raise NotImplementedError()
        

# OS X networksetup Driver
class NetworksetupDriver(WirelessDriver):

    def __init__(self, interface=None):
        WirelessDriver.__init__(self, interface=interface)
        # get the list of interfaces, pick Wi-Fi if available, otherwise pick first
        # TODO add check for empty interfaces list and raise
        self._hardware_port_to_interface_index = dict()
        interfaces = self.interfaces
        if "Wi-Fi" in self._hardware_port_to_interface_index:
            self.interface = interfaces[self._hardware_port_to_interface_index["Wi-Fi"]]
        else:
            self.interface = interfaces[0]

    def enable(self):    
        cmd('networksetup -setairportpower {} on'.format(self.interface))

    def disable(self):
        cmd('networksetup -setairportpower {} off'.format(self.interface))

    # connect to a network
    def connect(self, ssid, password):
        # attempt to connect
        response = cmd('networksetup -setairportnetwork {} {} {}'.format(
            self.interface, ssid, password))

        # parse response - assume success when there is no response
        return (len(response) == 0)

    # returned the ssid of the current network
    @property
    def current_network(self):
        # attempt to get current network
        response = cmd('networksetup -getairportnetwork {}'.format(
            self.interface))

        # parse response
        phrase = 'Current Wi-Fi Network: '
        if phrase in response:
            return response.replace('Current Wi-Fi Network: ', '').strip()
        else:
            return None

    # return a list of wireless adapters
    @property
    def interfaces(self):
        # grab list of interfaces
        response = cmd('networksetup -listallhardwareports')
        print response
        # parse response
        interfaces = []
        matches = re.findall("Hardware Port:\s+(.*?)\s+Device:\s+(.*?)\s+", response)
        print "current matches", matches
        for match in matches:
            print "match", match
            interfaces.append(match[1])
            self._hardware_port_to_interface_index[match[0]] = len(interfaces) - 1
            # return list
        return interfaces

    @property
    def is_enabled(self):
        response = cmd('networksetup -getairportpower {}'.format(
            self.interface))
        return 'On' in response  

