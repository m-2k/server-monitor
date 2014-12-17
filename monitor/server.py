from gevent import monkey; monkey.patch_all()
from ws4py.websocket import WebSocket
from ws4py.manager import WebSocketManager
import json

_ALL_CLIENTS = WebSocketManager()
_ENCODER = json.JSONEncoder()

class _SelfRegisteringSocket(WebSocket):
    ''' A server socket that registers and unregisters itself with the WebSocketManager '''

    def __init__(self, *args, **kwargs):
        self.alreadyRegisterd = False
        WebSocket.__init__(*args, **kwargs)

    def opened(self):
        # THIS IS A HACK! WebSocketManger() is implemented for clients
        # (for some reason) but it works just as well for servers. If
        # we don't add this check, it will enter in an infinite recursion.
        if not self.alreadyRegistered:
            self.alreadyRegistered = True
            _ALL_CLIENTS.add(self)

    def closed(self, code, reason):
        _ALL_CLIENTS.remove(self)

def broadcast(message, values):
    envelope = { 'message': message, 'values': values }
    _ALL_CLIENTS.broadcast(_ENCODER.encode(envelope))
