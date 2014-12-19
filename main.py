#!/usr/bin/env python
import gevent
from monitor.server import broadcast, startMonitorServer
from monitor import Server, memory, disk, processes
import logging

'''SERVERS = [
    Server('marcelo', 'mottalli.ddns.net', 'Casa Marcelo', 8000, 'marcelo'),
    Server('git', 'git.grandata.com', 'Git server', 22, 'marcelo'),
#    Server('borges', 'borges', 'Borges', 22, 'sun-sm')
]'''

SERVERS = [
    Server('adams', 'adams', 'adams', 2222, 'sun-im'),
    Server('asimov', 'asimov', 'asimov', 2222, 'sun-im'),
    Server('mann', 'mann', 'mann', 2222, 'sun-im'),
    Server('tolkien', 'tolkien', 'tolkien', 2222, 'sun-im'),
    Server('martin', 'martin', 'martin', 22, 'sun-im'),
    Server('borges', 'borges', 'borges', 22, 'sun-im'),
]

def startMonitoringThreads(server):
    logging.info("Starting monitor threads for server {}...".format(server.name))

    monitorClasses = [memory.MemoryMonitor, disk.DiskMonitor, processes.CPUMonitor]
    for monitorClass in monitorClasses:
        monitor = monitorClass(server)
        monitor.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    for server in SERVERS:
        startMonitoringThreads(server)

    startMonitorServer()
