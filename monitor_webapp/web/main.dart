import 'dart:html';

void main() {
    var serverList = document.querySelector("#server-list");

    var button = new ButtonElement()
        ..id = 'sarasa'
        ..text = 'Hola mundo';

    serverList.append(button);

    var ws = new WebSocket('ws://localhost:9000')
            ..onOpen.listen((e) => print("Conectado!"))
            ..onMessage.listen((e) => print("Got message '${e.data}'"))
    ;

    ws.onOpen.listen((e){
        ws.send("Hola mundo!");
    });

}
