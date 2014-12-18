import subprocess
import string
import logging
import gevent
from server import broadcast

def _shellquote(s):
    ''' Quotes a string so it can be passed as a shell parameter '''
    # This is highly unsafe and only works for simple strings!
    return "'" + s.replace("'", "'\\''") + "'"

class Server(object):
    def __init__(self, name, host, description, port=22, username=''):
        self.name = name
        self.host = host
        self.description = description
        self.port = port
        self.username = username

    def connect(self):
        pass

    def executeCommand(self, remoteCommand):
        localCommand = 'ssh -oBatchMode=yes '
        localCommand += '-p %i ' % self.port
        if self.username:
            localCommand += self.username + '@'
        localCommand += self.host + ' '
        localCommand += _shellquote(remoteCommand)

        # Executes the command and splits the output by lines
        output = subprocess.check_output(localCommand, shell=True).strip()
        lines = string.split(output, '\n')

        return lines

# Helper class, list that only stores the last n elements. Maybe "circular list"
# is not the best name, but meh.
class CircularList(object):
    def __init__(self, capacity):
        self.capacity = capacity
        self.values = []

    def push(self, elem):
        self.values.append(elem)
        if len(self.values) > self.capacity:
            self.values = self.values[-self.capacity:]

class BaseMonitor(object):
    def __init__(self, server, monitorName, interval=2, numReads=10):
        self.server = server
        self.monitorName = monitorName
        self.lastValues = CircularList(numReads)
        self.interval = interval

    def monitorLoop(self):
        while True:
            try:
                gevent.sleep(self.interval)

                values = self.generateValues()
                self.lastValues.push(values)

                messageName = 'monitor-'+self.monitorName
                message = {
                    'server': self.server.name,
                    'lastValues': self.lastValues.values,
                    'values': values
                }
                broadcast(messageName, message)

                self.postProcess()
            except subprocess.CalledProcessError as e:
                logging.error('Unable to execute command: {}'.format(e))


    def generateValues(self):
        raise NotImplementedError('Abstract class')

    def postProcess(self):
        pass
