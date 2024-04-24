import socket as _socket
import json as _json
from threading import Thread as _Thread

from others.data import splitExtraData as _splitExtraData
from others.events import Events as _Events
from others.style import Print as _print, OnlyColorize as _col_str, Input as _input


class _RecvLoop(_Thread):
    def __init__(self, client):
        super().__init__()
        
        self._client = client
    
    def run(self):
        receivedData = ""
        
        while True:
            try:
                data = self._client._sock.recv(1024)
                if data == b"":
                    # _print("#lCLIENT## (#mdebug##): Server socket was closed and no data is to be received, raising Exception.")
                    raise ConnectionResetError()
            except ConnectionResetError as e:
                # _print(f"#lCLIENT## (#rerror##): #r{e}")
                # _print("#lCLIENT## (#rerror##): Disconnected from the server.")
                self._client.stop()
                break
            except ConnectionAbortedError as e:
                # _print(f"#lCLIENT## (#rerror##): #r{e}")
                # _print("#lCLIENT## (#rerror##): Disconnected from the server.")
                break
            else:
                # _print(f"#lCLIENT## (#binfo##): Received #g{data}## from the server.")
                
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
                    # _print("#lCLIENT## (#wevent##): Processing data #g{}##.".format(_json.loads(singleData)[0]))
                    self._client.events.onDataReceived._fire(_json.loads(singleData)[0])

class Client:
    _isOpen = False
    
    def __init__(self, serverAddr:tuple):
        self._sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        
        self.events = _Events("onDisconnected", "onDataReceived")
        self._recvLoop = _RecvLoop(self)
        
        self._sock.connect(serverAddr)
        
        # _print(f"#lCLIENT## (#binfo##): Connected to a server at #g{serverAddr}##.")
        self._uuid = self._sock.recv(37).decode("utf-8")
        # _print(f"#lCLIENT## (#binfo##): Got uuid #g{self._uuid}##.")
        
        self._isOpen = True
        
        self._recvLoop.start()
    
    def stop(self):
        if not self._isOpen:
            pass # _print("#lCLIENT## (#ywarn##): Trying to stop a not-running client.")
        
        # _print("#lCLIENT## (#binfo##): Stopping...")
        self._isOpen = False
        
        self._sock.close()
        # _print("#lCLIENT## (#wevent##): Disconnected from the server.")
        self.events.onDisconnected._fire()
        # _print("#lCLIENT## (#binfo##): Stopped successfully.")
    
    def sendData(self, data):
        assert self._isOpen, _col_str("#lCLIENT## (#ywarn##): Can`t send data from a not-running client.")
        
        finalData = _json.dumps([data]).encode("utf-8")
        
        # _print(f"#lCLIENT## (#binfo##): Sending #g{finalData}## to the server.")
        
        _Thread(target=self._sock.sendall, args=[finalData]).start()