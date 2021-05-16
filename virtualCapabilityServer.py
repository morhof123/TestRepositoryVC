from threading import Thread
import os
import socket
import json
import sys
from time import sleep

def formatPrint(c,string:str) -> None:
    """Prints the given string in a formatted way: [Classname] given string

    Parameters:
        c       (class)  : The class which should be written inside the braces
        string  (str)    : The String to be printed
    """
    sys.stderr.write(f"[{type(c).__name__}] {string}\n")

class CommandNotFoundException(Exception):
    pass
class WrongNumberOfArgumentsException(Exception):
    pass

class VirtualCapabilityServer(Thread):
    '''Server meant to be run inside of a docker container as a Thread.

    '''
    def __init__(self, connectionPort:int = None):
        super().__init__()
        self.connectionPort = connectionPort
        self.running = False
        self.connected = False
        self.messages = list()
        self.virtualCapabilities = list()
        self.sentMessages = dict()
        formatPrint(self, "initialized")
        self.receivedReturns = list()

    def run(self) -> None:
        formatPrint(self, "started")
        if self.connectionPort == None:
            self.connectionPort = os.getenv("CONNECTION_PORT")
            if self.connectionPort == None:
                self.connectionPort = 9999
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("0.0.0.0", self.connectionPort))
        self.socket.listen(1)
        self.sock, self.adr = self.socket.accept()
        self.connected = True
        formatPrint(self, f"connected on {str(self.sock)}")
        while self.running:
            self.loop()

    def loop(self) -> None:
        try:
            data = self.sock.recv(512)
            if data != b'':
                # print("[Server] received: " + str(data))
                try:
                    self.messageReceived(data.decode())
                except Exception as e:
                    returner = dict()
                    returner["type"] = "ERROR"
                    returner["value"] = repr(e)
                    returner["callback"] = -1
                    self.sendMessage(json.dumps(returner))
        except:
            pass
            # self.notify("NEW_CONNECTION")

    def messageReceived(self, msg):
        # Try to decode message and get coresponding values
        try:
            formatPrint(self, f"Received {msg}")
            receivedCommand = json.loads(msg)
            type, value, callback = receivedCommand["type"], receivedCommand["value"], receivedCommand["callback"]
        except Exception as e:
            formatPrint(self, f"There was an error: {repr(e)}")
            returner = dict()
            returner["type"] = "ERROR"
            returner["value"] = repr(e)
            returner["callback"] = -1

            self.sendMessage(json.dumps(returner))
            return

        try:
            if (type == "EXECUTE"):
                self.notify(receivedCommand)
                self.messages.append(receivedCommand)

            elif (type == "RETURN"):
                self.notify(receivedCommand)
                if (callback in self.sentMessages.keys()):
                    self.sentMessages.pop(callback)
                self.messages.append(receivedCommand)
                self.receivedReturns.append(receivedCommand)

            elif (type == "INFO"):
                returner = dict()
                returner["type"] = "RETURN"
                returner["value"] = f"{repr(os.environ)}"
                returner["callback"] = callback

                self.sendMessage(json.dumps(returner))

            elif (type == "PING"):
                returner = dict()
                returner["type"] = "PONG"
                returner["value"] = ""
                returner["callback"] = callback

                self.sendMessage(json.dumps(returner))

            elif (type == "PONG"):
                if (callback in self.sentMessages.keys()):
                    self.sentMessages.pop(callback)

            elif (type == "ECHO"):
                returner = dict()
                returner["type"] = "RETURN"
                returner["value"] = value
                returner["callback"] = callback
                self.sendMessage(json.dumps(returner))

            elif (type == "ERROR"):
                if callback in self.sentMessages.keys():
                    formatPrint(self, f"There was an error with the sent Message {self.sentMessages[callback]}")
                else:
                    formatPrint(self, f"There was an error {msg}")
            else:
                raise CommandNotFoundException(f"The Commandtype you send wasn't found {type}")


        except Exception as e:
            returner = dict()
            returner["type"] = "ERROR"
            returner["value"] = repr(e)
            returner["callback"] = callback
            self.sendMessage(json.dumps(returner))


    def sendMessage(self, msg):
        formatPrint(self, f"Sending {msg}")
        newmsg = json.loads(msg)
        self.sentMessages[newmsg["callback"]] = newmsg
        self.sock.send(msg.encode("UTF-8"))

    def addVirtualCapability(self, vc):
        self.virtualCapabilities.append(vc)

    def notify(self, msg):
        formatPrint(self, f"notifying: {msg}")
        for vc in self.virtualCapabilities:
            vc.update(msg)

