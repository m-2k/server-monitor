import 'dart:html';
import 'dart:convert';

class ServerHandler
{
    String name;
    DivElement memoryDiv;
    DivElement disksDiv;
    DivElement proccpuDiv;

    ServerHandler(this.name)
    {
        print("New server ${this.name}");
        DivElement serverDiv = new DivElement()
            ..id = this.name
            ..classes.add('server')
        ;

        serverDiv.append(new DivElement()
            ..text = this.name
            ..id = "name"
        );

        this.memoryDiv = serverDiv.append(new DivElement()
            ..id = "memory"
        );

        this.disksDiv = serverDiv.append(new DivElement()
            ..id = "disks"
        );

        this.proccpuDiv = serverDiv.append(new DivElement()
            ..id = "proccpu"
        );

        document.querySelector("#server-list").children.add(serverDiv);
    }

    void update(Map message)
    {
        String type = message['message'];
        List lastValues = message['contents']['lastValues'];
        var lastValue = lastValues[lastValues.length-1];

        switch (type) {
        case 'monitor-memory':
            this.updateMemory(lastValue);
            break;
        case 'monitor-disk':
            this.updateDisk(lastValue);
            break;
        case 'monitor-proccpu':
            this.updateProccpu(lastValue);
            break;
        }
    }

    void updateMemory(Map values)
    {
        double percentAvailable = values['available']*100.0/values['total'];

        this.memoryDiv.children.clear();
        this.memoryDiv
            ..append(new ProgressElement()
                ..max = values['total']
                ..value = values['total']-values['available']
            )
            ..append(new BRElement())
            ..append(new SpanElement()
                ..text = "Available ${values['available']} of ${values['total']} MB"
            )
        ;
    }

    void updateDisk(Map values)
    {
        this.disksDiv.children.clear();

        for (Map disk in values['disks']) {
            num available = disk['available'];
            num used = disk['used'];
            num total = available+used;

            // Parse the filesystem
            String filesystem = disk["filesystem"]
                .replaceFirst(new RegExp(r"/dev/"), "")
                .replaceFirst(new RegExp(r"disk/by-uuid/"), "");


            DivElement diskDiv = new DivElement()
                ..classes.add("disk")
                ..append(new SpanElement()
                    ..text = filesystem
                )
                ..append(new ProgressElement()
                    ..max = total
                    ..value = used
                );

            double percentAvailable = (available/total)*100.0;
            if (percentAvailable < 50) {
                diskDiv.classes.add("warning");
            }

            this.disksDiv.append(diskDiv);
        }
    }

    void updateProccpu(List processes) {
        this.proccpuDiv.children.clear();

        TableElement table = new TableElement();

        TableSectionElement head = table.createTHead();
        TableRowElement header = head.insertRow(-1);
        header.insertCell(0).text = 'PID';
        header.insertCell(1).text = 'Name';
        header.insertCell(2).text = '%CPU';
        header.insertCell(3).text = '%mem';

        TableSectionElement body = table.createTBody();

        for (Map process in processes) {
            TableRowElement processRow = body.insertRow(-1);
            processRow.insertCell(0).text = "${process['pid']}";
            processRow.insertCell(1).text = "${process['name']}";
            processRow.insertCell(2).text = "${process['perccpu']}%";
            processRow.insertCell(3).text = "${process['percmem']}%";
        }

        this.proccpuDiv.append(table);
    }
}

Map<String, ServerHandler> serverHandlers = new Map();

void setStatus(String message)
{
    document.querySelector('#status-message').text = message;
}

void main() {
    var serverList = document.querySelector("#server-list");

    setStatus("Connecting to monitor socket...");
    var ws = new WebSocket('ws://localhost:9000/monitor_socket')
            ..onOpen.listen((Event e) => setStatus("Connected to socket"))
            ..onClose.listen((CloseEvent e) => setStatus("Socket closed"))
            ..onError.listen((Event e) => setStatus("Socket error: ${e.toString()}"))
    ;

    ws.onMessage.listen((MessageEvent e) {
        Map message = JSON.decode(e.data);
        String server = message['contents']['server'];

        if (!serverHandlers.containsKey(server)) {
            serverHandlers[server] = new ServerHandler(server);
        }

        serverHandlers[server].update(message);
    });
}
