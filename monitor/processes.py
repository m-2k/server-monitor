from monitor import BaseMonitor

class CPUMonitor(BaseMonitor):
    def __init__(self, server, interval=2):
        super(self.__class__, self).__init__(server, 'proccpu', interval)

    def generateValues(self):
        #command = 'ps -o pid,comm,%cpu,%mem,ruser -ax | tail -n +2'
        command = "top -b -n1 | tail -n +8 | awk '{ print $1, $12, $9, $10, $2 }'"
        lines = self.server.executeCommand(command)

        processes = []
        for line in lines:

            try:
                (pid, command, cpu, mem, user) = line.split()
            except ValueError:
                # SOMETIMES we cannot unpack the values
                pass
            
            pid = int(pid)
            cpu = float(cpu.replace(',', '.'))
            mem = float(mem.replace(',', '.'))
            processes.append((pid, command, cpu, mem, user))
        
        # Filter processes without CPU or RAM usage
        processes = [p for p in processes if p[2] > 0 or p[3] > 0]

        # Sort by RAM usage in REVERSE order
        processes.sort(key=lambda process: -process[3])

        # Select only the top 5
        processes = processes[0:5]

        result = []
        for process in processes:
            result.append({
                'pid': process[0],
                'name': process[1],
                'perccpu': process[2],
                'percmem': process[3],
                'user': process[4],
            })

        return result
