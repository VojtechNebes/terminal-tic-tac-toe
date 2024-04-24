import socket as _socket
import json as _json
from threading import Thread as _Thread
from uuid import uuid4 as _uuid4

from others.data import splitExtraData as _splitExtraData
from others.events import Events as _Events
from others.style import Print as _print, OnlyColorize as _col_str


class _ClientConn(_Thread):
    _isOpen = False
    
    def __init__(self, sock, server):
        super().__init__()
        
        self._server = server
        self._sock = sock
        self._uuid = str(_uuid4())
        
        self._sock.sendall(str(self._uuid).encode("utf-8"))
        
        self.start()
    
    def run(self):
        receivedData = ""
        
        while True:
            try:
                data = self._sock.recv(1024)
                if data == b"":
                    raise Exception()
            except ConnectionResetError as e:
                # _print(f"#cSERVER## (#rerror##): #r{e}")
                # _print(f"#cSERVER## (#binfo##): Client #g{self._uuid}## has disconnected.")
                self._close()
                break
            except ConnectionAbortedError as e:
                # _print(f"#cSERVER## (#rerror##): #r{e}")
                # _print(f"#cSERVER## (#binfo##): Client #g{self._uuid}## has disconnected.")
                break
            else:
                # _print(f"#cSERVER## (#mdebug##): Received #g{data}## from client #g{self._uuid}##.")
                
                receivedData += data.decode("utf-8")
                
                unpackedData, rest = _splitExtraData(receivedData, "][")
                # self._unprocessedData.extend(unpackedData)
                
                try:
                    _json.loads(rest)
                except _json.decoder.JSONDecodeError:
                    receivedData = rest
                else:
                    receivedData = ""
                    unpackedData.append(rest)
                
                for singleData in unpackedData:
                    # here fire onDataReceived event
                    # _print("#cSERVER## (#wevent##): Processing data #g{}##.".format({'uuid': self._uuid, 'data': _json.loads(singleData)[0]}))
                    self._server.events.onDataReceived._fire(_json.loads(singleData)[0], self._uuid)
    
    def _close(self):
        print("closing socket from client._close()")
        self._sock.close()
        self._server._clients.remove(self)
        # _print(f"#cSERVER## (#wevent##): Client #g{self._uuid}## has disconnected.")
        self._server.events.onClientRemoved._fire(self._uuid)

class _AcceptLoop(_Thread):
    def __init__(self, server):
        super().__init__()
        self._server = server
    
    def run(self):
        while self._server._isOpen:
            try:
                clientSock, clientAddr = self._server._sock.accept()
            except OSError as e:
                pass # _print(f"#cSERVER## (#rerror##): #r{e}")
            else:
                _Thread(target=self._newClient, args=[clientSock, clientAddr]).start()
    
    def _newClient(self, clientSock, clientAddr):
        if len(self._server._clients) < self._server._maxClients or self._server._maxClients == -1:
            newClient = _ClientConn(clientSock, self._server)
            self._server._clients.append(newClient)
            # _print(f"#cSERVER## (#binfo##): A client has connected from #g{clientAddr}##, got uuid #g{newClient._uuid}##.")
            # _print(f"#cSERVER## (#wevent##): A client has connected from #g{clientAddr}##, got uuid #g{newClient._uuid}##.")
            self._server.events.onClientAdded._fire(clientAddr, newClient._uuid)
        else:
            clientSock.close()

class Server:
    _isOpen = False
    
    def __init__(self, *, local:bool, maxClients:int):
        # _print("#cSERVER## (#binfo##): Initializing...")
        
        self._clients = []
        self._maxClients = maxClients
        
        self._sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        
        if local: self._sock.bind(("127.0.0.1", 0))
        else: self._sock.bind((_socket.gethostbyname(_socket.gethostname()), 0))
        
        self._sock.listen()
        
        self.events = _Events("onClientAdded", "onClientRemoved", "onDataReceived", "onStopped")
        self._acceptLoop = _AcceptLoop(self)
        
        self._isOpen = True
        
        #self._mainLoop.start()
        self._acceptLoop.start()
        
        # _print(f"#cSERVER## (#binfo##): Running at #g{self._sock.getsockname()}##.")
    
    def stop(self):
        assert self._isOpen, _col_str("#cSERVER## (#ywarn##): Tried to stop a not-running server.")
        
        # _print("#cSERVER## (#binfo##): Stopping...")
        
        self._isOpen = False
        for client in self._clients:
            client._close()
        
        self._sock.close()
        
        # _print("#cSERVER## (#wevent##): Server stopped.")
        self.events.onStopped._fire()
        # _print("#cSERVER## (#binfo##): Stopped successfully.")
    
    def sendData(self, data):
        assert self._isOpen, _col_str("#cSERVER## (#ywarn##): Can`t send data form a not-running server.")
        
        finalData = _json.dumps([data]).encode("utf-8")
        
        # _print(f"#cSERVER## (#binfo##): Sending #g{finalData}## to #g{len(self._clients)}## client(s).")
        
        for client in self._clients:
            _Thread(target=client._sock.sendall, args=[finalData]).start()
    
    def getAddr(self):
        assert self._isOpen, _col_str("#cSERVER## (#ywarn##): Can`t get addr of a not-running server.")
        
        return self._sock.getsockname()
    
    def getClients(self):
        assert self._isOpen, _col_str("#cSERVER## (#ywarn##): Server can`t have any clients when not open.")
        
        return [client._uuid for client in self._clients]
    
    def kickClient(self, clientUUID):
        for client in self._clients:
            if client._uuid == clientUUID:
                client._close()
                return