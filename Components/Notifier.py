class Notifier:
    def __init__(self):
        self.listeners = {}

    # Update anything listening for updates
    def addListener(self, listener, callback):
        self.listeners[listener] = callback

    def removeListener(self, listener):
        del self.listeners[listener]

    def notifyListeners(self, changeData):
        for listener, callback in self.listeners.items():
            callback({**{"sender": self}, **changeData})
