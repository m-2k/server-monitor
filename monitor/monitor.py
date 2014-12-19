import subprocess
import string
import logging
import threading
import time
from server import broadcast

def _shellquote(s):
    ''' Quotes a string so it can be passed as a shell parameter '''
    # This is highly unsafe and only works for simple strings!
    return "'" + s.replace("'", "'\\''") + "'"

class RemoteCommandException(Exception):
    def __init__(self, retcode, output):
        super(RemoteCommandException, self).__init__(output)

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
        command = ['ssh']
        command += ['-oBatchMode=yes']
        command += ['-p{}'.format(self.port)]

        hostspec = self.host if not self.username else '{}@{}'.format(self.username, self.host)
        command += [hostspec]
        command += [remoteCommand]

        # Executes the command and splits the output by lines
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RemoteCommandException(process.returncode, stderr)

        lines = stdout.strip().split('\n')
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

class BaseMonitor(threading.Thread):
    def __init__(self, server, monitorName, interval=2, numReads=10):
        super(BaseMonitor, self).__init__()

        self.server = server
        self.monitorName = monitorName
        self.lastValues = CircularList(numReads)
        self.interval = interval

    def run(self):
        while True:
            try:
                time.sleep(self.interval)

                '''logging.debug("Generating values for '{}.{}'".
                        format(self.server.name, self.monitorName))'''
                values = self.generateValues()

                '''logging.debug("Obtained values for '{}.{}'".
                        format(self.server.name, self.monitorName))'''
                self.lastValues.push(values)

                messageName = 'monitor-'+self.monitorName
                message = {
                    'server': self.server.name,
                    'lastValues': self.lastValues.values,
                    'values': values
                }
                broadcast(messageName, message)

                self.postProcess()
            except ValueError as e:
                logging.error('Found an error processing the command: {}'.format(e))
            except RemoteCommandException as e:
                logging.error('Unable to execute command: {}'.format(e))


    def generateValues(self):
        raise NotImplementedError('Abstract class')

    def postProcess(self):
        pass
