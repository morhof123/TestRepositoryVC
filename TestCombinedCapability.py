import sys
import socket
import os
import json
from threading import Thread
import virtualCapabilityServer as vcc
import guid
from enum import Enum

from time import sleep

class Status(Enum):
    NON_INITIALIZED = 0
    RUNNING = 1
    WAITING_FOR_EXECUTION= 100
    EXECUTING = 150
    WAITING_FOR_SUBCAP = 200
    STOPPED = 999



class VirtualCapability(Thread):
    def __init__(self, server:vcc.VirtualCapabilityServer):
        super().__init__()
        self.isStarted = False
        self.messages = dict()
        server.addVirtualCapability(self)
        self.server = server
        vcc.formatPrint(self,"initialized")
        self.Status = Status.NON_INITIALIZED

    def update(self,command):
        vcc.formatPrint(self, f"updated command: {command}")
        if command["type"] == "EXECUTE":
            sys.stderr.write("Try to Execute\n")
            self.isStarted = True
            returnValue = self.execute(command["value"])

            returner = dict()
            returner["callback"] = command["callback"]
            returner["value"] = returnValue
            returner["type"] = "RETURN"

            self.server.sendMessage(json.dumps(returner))

    def run(self) -> None:
        self.Status = Status.RUNNING
        self.server.start()
        vcc.formatPrint(self, "started")
        self.Status = Status.WAITING_FOR_EXECUTION

    def execute(self, values):
        sys.stderr.write("Executing now\n")
        self.Status = Status.EXECUTING

        mycallback = str(guid.guid.GUID())
        executeSubCap = {
            "type":"EXECUTE_CAP",
            "value": {
                "capability":"TestDeviceButtonCapability",
                "parameters":[]
            },
            "callback": mycallback
        }
        sleep(5)
        self.server.sendMessage(json.dumps(executeSubCap))
        self.Status = Status.WAITING_FOR_SUBCAP

        while (True):
            sleep(1)
            self.server.loop()
            sys.stderr.write(f"No Message found {self.server.receivedReturns}\n")
            breakMe = False
            for x in self.server.receivedReturns:
                if x["callback"] == mycallback:
                    breakMe = True
            if breakMe:
                sys.stderr.write("Breaking now\n")
                break

        sys.stderr.write("Finishing here\n")
        self.Status = Status.WAITING_FOR_EXECUTION
        return []

sys.stderr.write("Starting now\n")


connectionPort = int(os.getenv("CONNECTION_PORT"))

sys.stdout.write(f"Starting on Port {connectionPort}\n")

server = vcc.VirtualCapabilityServer(connectionPort)
vc = VirtualCapability(server)
sys.stderr.write("Trying to Start\n")
vc.start()
sleep(1)
while not vc.server.connected:
    sleep(1)
    sys.stderr.write("Nothing yet connected\n")

sys.stderr.write("Client connected\n")
sleep(1)
vc.server.sendMessage(
    json.dumps(
        {
            "type":"PING",
            "value":1,
            "callback":123
        }
    )
)

