import 'dart:html';
import 'dart:convert';

class ServerHandler
{
    String name;
    DivElement memoryDiv;
    DivElement diskDiv;
    
    ServerHandler(this.name)
    {
        print("New server ${this.name}");
        DivElement serverDiv = new DivElement()
            ..id = this.name
            ..text = this.name
            ..classes.add('server')
        ;
        
        this.memoryDiv = serverDiv.append(new DivElement()
            ..id = 'memory'
        );
        
        this.diskDiv = serverDiv.append(new DivElement()
            ..id = 'disk'
        );
        
        document.querySelector("#server-list").children.add(serverDiv);
    }
    
    void update(Map message)
    {
        String type = message['message'];
        List lastValues = message['contents']['lastValues'];
        
        switch (type) {
        case 'monitor-memory':
            this.updateMemory(lastValues[lastValues.length-1]);
            break;
        case 'monitor-disk':
            this.updateDisk(lastValues[lastValues.length-1]);
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
        this.diskDiv.children.clear();
        this.diskDiv
            ..append(new ProgressElement()
                ..max = values['totalAvailable']+values['totalUsed']
                ..value = values['totalUsed']
            )
            /*..append(new BRElement())
            ..append(new SpanElement()
                ..text = "Available ${values['available']} of ${values['total']} MB"
            )*/
        ;
    }
}

Map<String, ServerHandler> serverHandlers = new Map();

void main() {
    var serverList = document.querySelector("#server-list");

    var ws = new WebSocket('ws://localhost:8000/monitor_socket')
            ..onOpen.listen((Event e) => print("Conectado!"))
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
