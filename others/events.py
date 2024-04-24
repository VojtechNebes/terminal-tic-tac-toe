from threading import Thread as _Thread

class _connection:
    def __init__(self, func, remove):
        self._func, self._remove = func, remove
    
    def disconnect(self):
        self._remove(self)

class _event:
    def __init__(self):
        self._connections = []
    
    def connect(self, func):
        newConnection = _connection(func, self._connections.remove)
        self._connections.append(newConnection)
        return newConnection
    
    def _fire(self, *args, **kwargs):
        for connection in self._connections:
            _Thread(target=connection._func, args=args, kwargs=kwargs).start()

class Events:
    def __init__(self, *eventNames):
        self.__dict__ = {name: _event() for name in eventNames}