#!/usr/bin/env python
'''
from flask import Flask, url_for
from flask.ext.socketio import SocketIO, send, emit
from string import split
import subprocess
import re
import gevent
from pprint import pprint
import logging
import pylab
import numpy as np
import matplotlib.pyplot as plt

SERVER_CONFIG = {
#    'borges': {
#        'username': 'sun-sm',
#        'hostname': 'borges',
#        'descrption': 'Borges'
#    },
    'casa': {
        'username': 'marcelo',
        'port': 8000,
        'hostname': 'localhost',
        'descrption': 'local'
    }
}

COMMANDS = {
    # Disk usage: device, mount point, used bytes, total bytes, percent usage
    'disk': 'df -Pm | tail -n +2 | awk \'{ print $1, $6, $3, $4, $5+0 }\'',

    # Processes by CPU usage: PID, short command, %CPU, %RAM
    'procpu': 'ps -eo pid,comm,pcpu,pmem --sort -pcpu | tail -n +2 | head -n 5 | awk \'{ print $1, $2, $3, $4 }\'',

    # Processes by RAM usage: PID, short command, %CPU, %RAM
   # 'procpu': 'ps -eo pid,comm,pcpu,pmem --sort -pmem | tail -n +2 | head -n 5 | awk \'{ print $1, $2, $3, $4 }\''

    # Memory usage: Total, used, free, shared, buffers, cached
    'memory': 'free -om | tail -n +2 | head -n 1 | awk \'{ print $2, $3, $4, $5, $6, $7 }\''
}

class CommandException(Exception):
    pass

def commandOutput(command):
    """ Executes a command and returns the output splitted by words and lines """
    # TODO: Error checking
    output = subprocess.check_output(command, shell=True).strip()
    lines = split(output, '\n')
    words = [split(line) for line in lines]
    return words

def sshCommand(server, commandName):
    if server not in SERVER_CONFIG:
        raise Exception("Invalid server name: "+server)

    # Build the ssh command
    config = SERVER_CONFIG[server]
    command = 'ssh -oBatchMode=yes '
    if 'port' in config:
        command += '-p %i ' % config['port']

    if 'username' in config:
        command += config['username'] + '@'
    command += config['hostname'] + ' ' + COMMANDS[commandName]

    return commandOutput(command)

def getDiskUsage(host):
    usage = sshCommand(host, 'disk')

    # Select only the entries associated to a filesystem
    diskre = re.compile(r'^/dev/sd(.)([0-9]*)$')
    usage = filter(lambda u: diskre.match(u[0]), usage)
    diskUsage = {}
    for (dev, mountpoint, used, total, percent) in usage:
        res = diskre.match(dev)
        disk = res.group(1)
        partition = res.group(2)

        used, total, percent = int(used), int(total), int(percent)

        if partition != '':
            if disk not in diskUsage:
                diskUsage[disk] = {}

            partition = int(partition)
            diskUsage[disk][partition] = {'used': used, 'total': total, 'percent': percent}
        else:
            diskUsage[disk] = {'used': used, 'total': total, 'percent': percent}

    return diskUsage

def getProcesses(host):
    processes = sshCommand(host, 'procpu')

    result = []
    for (pid, command, perccpu, percmem) in processes:
        result.append({
            'pid': int(pid),
            'command': command,
            'perccpu': float(perccpu),
            'percmem': float(percmem)
            })

    return result

def getMemory(host):
    memory = sshCommand(host, 'memory') 
    memory = memory[0]  # Note that the memory command returns a single line

    # Cast every value to an integer
    memory = [int(m) for m in memory]
    (total, used, free, shared, buffers, cached) = memory

    return {'total': total, 'used': used, 'free': free, 'shared': shared, 'buffers': buffers, 'cached': cached }

app = Flask('python-monitor')
app.config['SECRET_KEY'] = 'Ks36B9IJ9pYXfziaw9p3'
app.debug = True
socketio = SocketIO(app)

@socketio.on('client_connected')
def client_connected(message):
    logging.info('Client connected')

# Helper class, list that only stores the last n elements. Maybe "circular list"
# is not the best name, but meh.
class CircularList(object):
    def __init__(self, capacity):
        self.capacity = capacity
        self.elements = []

    def push(self, elem):
        self.elements.append(elem)
        if len(self.elements) > self.capacity:
            self.elements = self.elements[-self.capacity:]

def memoryThread(server):
    filename = server + '-' + 'memory.png'
    lastReadings = CircularList(10)

    width, height = 500, 200
    dpi = 72.0

    while True:
        status = getMemory(server)
        lastReadings.push(status)

        # Generate the graphs
        used = np.array([r['used'] for r in lastReadings.elements])
        free = np.array([r['free'] for r in lastReadings.elements])
        cached = np.array([r['cached'] for r in lastReadings.elements])
        x = np.arange(len(used))
        y = np.row_stack((used, free, cached))
        fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi)
        plt.stackplot(x, y, label=['Used', 'Free', 'Cached'])

        pylab.savefig('static/'+filename, dpi=dpi)
        plt.close(fig)

        gevent.sleep(2)

def spawnThreads(server):
    gevent.spawn(memoryThread, server)

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # Spawn a monitor thread for each server
    for server in SERVER_CONFIG:
        spawnThreads(server)

    socketio.run(app)
'''

'''from flask import Flask
from flask.ext.socketio import SocketIO
from monitor import memory
import logging
import monitor
import gevent

app = Flask('python-monitor')
app.config['SECRET_KEY'] = 'Ks36B9IJ9pYXfziaw9p3'
app.debug = True
socketio = SocketIO(app)

@socketio.on('client_connected')
def client_connected(message):
    logging.info('Client connected')

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    local = monitor.Server('local', 'localhost', 'Servidor local')
    memoryMonitor = memory.MemoryMonitor(socketio, local)
    gevent.spawn(memory.MemoryMonitor.monitorLoop, memoryMonitor)

    socketio.run(app)
'''

import gevent
from monitor.server import broadcast, startMonitorServer
from monitor import Server, memory, disk
import logging

SERVERS = [
    Server('marcelo', 'mottalli.ddns.net', 'Casa Marcelo', 8000, 'marcelo'),
    Server('borges', 'borges', 'Borges', 22, 'sun-sm')
]

def startMonitoringThreads(server):
    logging.info("Starting monitor threads for server {}...".format(server.name))

    memoryMonitor = memory.MemoryMonitor(server)
    gevent.spawn(memory.MemoryMonitor.monitorLoop, memoryMonitor)

    diskMonitor = disk.DiskMonitor(server)
    gevent.spawn(disk.DiskMonitor.monitorLoop, diskMonitor)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    for server in SERVERS:
        startMonitoringThreads(server)

    startMonitorServer()
