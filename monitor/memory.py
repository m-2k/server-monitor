import string
from . import BaseMonitor
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches
import os
import pylab

class MemoryMonitor(BaseMonitor):
    def __init__(self, socketio, server, interval=1):
        super(self.__class__, self).__init__(socketio, server, 'memory', interval)

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

    def postProcess(self):
        ''' Generate the chart with the free memory '''
        filename = self.server.name + '-' + self.monitorName + '.png'
        currdir = os.path.dirname(os.path.realpath(__file__))
        destdir = os.path.join(currdir, '../static')
        destfile = os.path.join(destdir, filename)

        width, height, dpi = 500, 100, 72.0
        fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi)

        available = np.array([v['available'] for v in self.lastValues.values])
        total = np.array([v['total'] for v in self.lastValues.values])

        x = np.arange(len(available))
        y = np.row_stack((total-available, available))

        colors = ['#aa0000', '#00aa00']

        plt.stackplot(x, total-available, available, colors=colors)
        plt.xticks([])
        plt.autoscale(tight=True)

        pylab.savefig(destfile, dpi=dpi)
        plt.close(fig)

        message = {
            'server': self.server.name,
            'image': filename
        }
        self.socketio.emit('monitor-memory-image', message)

