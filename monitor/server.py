import json
from gevent import monkey; monkey.patch_all()
from flask import Flask, render_template, app
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
import logging

flask_app = Flask(__name__)
flask_app.debug = True

ALL_CLIENTS = {}

def broadcast(message, contents):
    envelope = {
        'message': message,
        'contents': contents
    }
    encodedEnvelope = json.dumps(envelope)

    for client in ALL_CLIENTS.values():
        client.ws.send(encodedEnvelope)

class MonitorSocket(WebSocketApplication):
    def on_open(self):
        client = self.ws.handler.active_client
        logging.info("Client connected! Registering with address {}".format(client.address))
        ALL_CLIENTS[client.address] = client

    def on_message(self, message):
        pass

    def on_close(self, reason=None):
        client = self.ws.handler.active_client
        del ALL_CLIENTS[client.address]

@flask_app.route('/')
def index():
    return render_template('index.html')

def startMonitorServer():
    WebSocketServer(
        ('0.0.0.0', 8000),

        Resource({
            '^/monitor_socket': MonitorSocket,
            '^/.*': flask_app
        }),

        debug=False
    ).serve_forever()
