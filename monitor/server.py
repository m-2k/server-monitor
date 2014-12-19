import json
#from gevent import monkey; monkey.patch_all()
from flask import Flask, render_template, app
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource, WebSocketError
import logging
import os

flask_app = Flask(__name__, 
    static_url_path='', 
    static_folder=os.path.join(os.getcwd(), 'monitor_webapp/build/web')
)

flask_app.debug = True

ALL_CLIENTS = {}

def broadcast(message, contents):
    envelope = {
        'message': message,
        'contents': contents
    }
    encodedEnvelope = json.dumps(envelope)

    for client in ALL_CLIENTS.values():
        try:
            client.ws.send(encodedEnvelope)
        except WebSocketError:
            pass

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
    return flask_app.send_static_file('index.html')

def startMonitorServer(port=9000):
    logging.info("Starting monitor server in port {}".format(port))
    WebSocketServer(
        ('0.0.0.0', port),

        Resource({
            '^/monitor_socket': MonitorSocket,
            '^/.*': flask_app
        }),

        debug=False
    ).serve_forever()
