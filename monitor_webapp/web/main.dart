import 'dart:html';
import 'dart:convert';
import 'dart:async';

/*****************************************************************************/
void assignStatusClass(Element element, num currentValue, num maxValue, [num warningThresholdPC = 50, num criticalThresholdPC = 80])
{
    num percent = currentValue*100.0/maxValue;
    element.classes.remove("bg-warning");
    element.classes.remove("bg-danger");

    if (percent >= warningThresholdPC && percent < criticalThresholdPC) {
        element.classes.add("bg-warning");
    } else if (percent >= criticalThresholdPC) {
        element.classes.add("bg-danger");
    }
}

/*****************************************************************************/
abstract class MonitorDisplay
{
    DivElement displayDiv;
    Timer timeoutTimer;

    MonitorDisplay(this.displayDiv)
    {
        this.startTimeout();
    }

    void _doShow(var data);

    void show(var data)
    {
        this.resetTimeout();
        this._doShow(data);
    }

    void startTimeout()
    {
        Duration timeout = new Duration(minutes: 1);
        //Duration timeout = new Duration(seconds: 3);
        this.timeoutTimer = new Timer(timeout,
                () => this.displayDiv.classes.add("timeout")
        );
    }

    void resetTimeout()
    {
        this.timeoutTimer.cancel();
        this.displayDiv.classes.remove("timeout");
        this.startTimeout();
    }
}

/*****************************************************************************/
class MemoryDisplay extends MonitorDisplay
{
    MemoryDisplay(DivElement div) : super(div) {}

    void _doShow(var data)
    {
        num available = data['available'];
        num total = data['total'];
        num used = total-available;
        double percentAvailable = available*100.0/total;

        this.displayDiv.children.clear();
        this.displayDiv
            ..append(new ProgressElement()
                ..max = total
                ..value = used
            )
            ..append(new BRElement())
            ..append(new SpanElement()
                ..text = "Available $available of $total MB"
            )
        ;

        assignStatusClass(this.displayDiv, used, total);
    }
}

/*****************************************************************************/
class DisksDisplay extends MonitorDisplay
{
    DisksDisplay(DivElement div) : super(div) {}

    void _doShow(var data)
    {
        this.displayDiv.children.clear();

        for (Map disk in data['disks']) {
            num available = disk['available'];
            num used = disk['used'];
            num total = available+used;

            // Parse the filesystem
            String filesystem = disk["filesystem"]
                .replaceFirst(new RegExp(r"/dev/"), "")
                .replaceFirst(new RegExp(r"disk/by-uuid/"), "");
            // Only last 4 chars
            filesystem = filesystem.substring(filesystem.length-4);


            DivElement diskDiv = new DivElement()
                ..classes.add("disk")
                ..append(new SpanElement()
                    ..text = filesystem
                )
                ..append(new ProgressElement()
                    ..max = total
                    ..value = used
                );

            assignStatusClass(diskDiv, used, total);

            this.displayDiv.append(diskDiv);
        }
    }
}

/*****************************************************************************/
class ProcDisplay extends MonitorDisplay
{
    ProcDisplay(DivElement div) : super(div) {}

    void _doShow(var data)
    {
        this.displayDiv.children.clear();

        TableElement table = new TableElement();

        TableSectionElement head = table.createTHead();
        TableRowElement header = head.insertRow(-1);
        header.insertCell(0).text = 'PID';
        header.insertCell(1).text = 'Name';
        header.insertCell(2).text = '%CPU';
        header.insertCell(3).text = '%mem';

        TableSectionElement body = table.createTBody();

        for (Map process in data) {
            TableRowElement processRow = body.insertRow(-1);
            processRow.insertCell(0).text = "${process['pid']}";
            processRow.insertCell(1).text = "${process['name']}";
            TableCellElement perccpuElem = processRow.insertCell(2)
                ..text = "${process['perccpu']}%";
            TableCellElement percmemElem = processRow.insertCell(3)
                ..text = "${process['percmem']}%";

            assignStatusClass(perccpuElem, process['perccpu'], 100);
            assignStatusClass(percmemElem, process['percmem'], 100);
        }

        this.displayDiv.append(table);
    }
}

/*****************************************************************************/
class ServerHandler
{
    String name;
    MemoryDisplay memoryDisplay;
    DisksDisplay disksDisplay;
    ProcDisplay procDisplay;

    ServerHandler(this.name)
    {
        print("New server ${this.name}");
        DivElement serverDiv = new DivElement()
            ..id = this.name
            ..classes.add('server')
        ;

        serverDiv.append(new DivElement()
            ..text = this.name
            ..classes.add("bg-primary")
            ..id = "name"
        );

        DivElement memoryDiv = serverDiv.append(new DivElement()
            ..id = "memory"
        );
        this.memoryDisplay = new MemoryDisplay(memoryDiv);

        DivElement disksDiv = serverDiv.append(new DivElement()
            ..id = "disks"
        );
        this.disksDisplay = new DisksDisplay(disksDiv);

        DivElement procDiv = serverDiv.append(new DivElement()
            ..id = "proccpu"
        );
        this.procDisplay = new ProcDisplay(procDiv);

        document.querySelector("#server-list").children.add(serverDiv);
    }

    void update(Map message)
    {
        String type = message['message'];
        List lastValues = message['contents']['lastValues'];
        var lastValue = lastValues[lastValues.length-1];

        switch (type) {
        case 'monitor-memory':
            this.memoryDisplay.show(lastValue);
            break;
        case 'monitor-disk':
            this.disksDisplay.show(lastValue);
            break;
        case 'monitor-proccpu':
            this.procDisplay.show(lastValue);
            break;
        }
    }
}

/*****************************************************************************/
void setStatus(String message)
{
    Element statusElement = document.querySelector('#status-message');
    if (statusElement != null) {
        statusElement.text = message;
    }
    print(message);
}

/*****************************************************************************/
Map<String, ServerHandler> serverHandlers = new Map();
WebSocket webSocket;

void connectSocket()
{
    bool hasError = false;
    
    setStatus("Connecting to socket...");
    webSocket = new WebSocket('ws://localhost:9000/monitor_socket')
        ..onOpen.listen((Event e) => setStatus("Connected to socket"));
    
    webSocket.onMessage.listen((MessageEvent e) {
        Map message = JSON.decode(e.data);
        String server = message['contents']['server'];

        if (!serverHandlers.containsKey(server)) {
            serverHandlers[server] = new ServerHandler(server);
        }

        serverHandlers[server].update(message);
    });
    
    const Duration reconnectTimeout = const Duration(seconds: 10);
    
    webSocket.onClose.listen((CloseEvent e) {
        setStatus("Socket closed. Retrying in 10 seconds.");
        if (!hasError) {
            new Timer(reconnectTimeout, connectSocket);
        }
        hasError = true;
    });
    
    webSocket.onError.listen((Event e) {
        setStatus("Socket error: ${e.toString()}. Retrying in 10 seconds.");
        if (!hasError) {
            new Timer(reconnectTimeout, connectSocket);
        }
        hasError = true;
    });
}

void main()
{
    connectSocket();
}
