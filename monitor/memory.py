import string
from monitor import BaseMonitor
from server import broadcast
import os

class MemoryMonitor(BaseMonitor):
    def __init__(self, server, interval=2):
        super(self.__class__, self).__init__(server, 'memory', interval)

    def generateValues(self):
        command = 'free -om | tail -n +2 | head -n 1 | awk \'{ print $2, $3, $4, $5, $6, $7 }\''
        lines = self.server.executeCommand(command)

        # This command returns only one line with the values.
        # Make sure to cast the values to int.
        total, used, free, shared, buffers, cached = [int(v) for v in string.split(lines[0])]

        # Some useful calculations
        usedMinusCache = used-(buffers+cached)
        available = total-usedMinusCache
        
        return {
            'total': total, 
            'used': used, 
            'free': free, 
            'shared': shared,
            'buffers': buffers,
            'cached': cached,
            'available': available
        }

