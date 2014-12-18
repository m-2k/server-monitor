from monitor import BaseMonitor
from server import broadcast
import string

class DiskMonitor(BaseMonitor):
    def __init__(self, server, interval=2):
        super(self.__class__, self).__init__(server, 'disk', interval)

    def generateValues(self):
        ''' We want only the "real" filesystems (the ones of type ext[2,3,4]). The same
        partition may be mounted more than once (e.g. chroots) so we do an unique too '''
        command = 'df -Pm -t ext2 -t ext3 -t ext4 | tail -n +2 | awk \'{ print $1, $3, $4 }\' | sort -nu -k2 | sort -n'
        lines = self.server.executeCommand(command)

        disks = []

        totalUsed = 0
        totalAvailable = 0

        for line in lines:
            filesystem, used, available = string.split(line)
            used = int(used)
            available = int(available)

            totalUsed += used
            totalAvailable += available

            disks.append({
                'filesystem': filesystem,
                'used': used,
                'available': available
            })

        return {
            'disks': disks,
            'totalUsed': totalUsed,
            'totalAvailable': totalAvailable
        }
