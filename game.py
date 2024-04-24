from server import Server as newServer
from client import Client as newClient
from others.style import OnlyColorize as colorizeString

import socket, random, os, time


X_MARK = "X"
O_MARK = "O"
GAMEBOARD_EMPTY = ""

def clearConsole():
    if os.name == "posix":
        os.system("clear")
    else:
        os.system("cls")

class Game:
    def __init__(self, *, maxClients=-1):
        self.server = newServer(local=False, maxClients=maxClients)
        
        self.server.events.onClientRemoved.connect(self.onClientRemoved)
        self.server.events.onClientAdded.connect(self.onClientAdded)
        
        self.running = True
        self.gameboard = [
            [GAMEBOARD_EMPTY, GAMEBOARD_EMPTY, GAMEBOARD_EMPTY],
            [GAMEBOARD_EMPTY, GAMEBOARD_EMPTY, GAMEBOARD_EMPTY],
            [GAMEBOARD_EMPTY, GAMEBOARD_EMPTY, GAMEBOARD_EMPTY]
        ]
    
    def onClientRemoved(self, clientUUID):
        self.server.sendData({"msgType": "notif", "data": "The other player has disconnected."})
        self.running = False
        # self.server.stop()
    
    def onClientAdded(self, clientSock, clientUUID):
        print("A client was added.")
        if len(self.server._clients) == 2:
            self.start()
        else:
            self.server.sendData({"msgType": "notif", "data": f"Waiting for the other player, ip and port are {self.server.getAddr()}."})
    
    def start(self):        
        self.server.events.onDataReceived.connect(self.onDataReceived)
        self.playerList = self.server.getClients()
        self.playerOnTurn = random.choice(self.server.getClients())
        
        self.sendGameData("ok")
    
    def onDataReceived(self, data, player):
        if data["msgType"] == "move" and player == self.playerOnTurn and self.running:
            self.updateGameboard({"player": player, "move": data["data"]})
    
    def updateGameboard(self, data):
        gameboardPos = (
            ["A", "B", "C"].index(data["move"][0]),
            ["1", "2", "3"].index(data["move"][1])
        )
        
        if self.gameboard[gameboardPos[0]][gameboardPos[1]] == GAMEBOARD_EMPTY:
            self.gameboard[gameboardPos[0]][gameboardPos[1]] = data["player"]
            
            playerListCopy = self.playerList.copy()
            playerListCopy.remove(data["player"])
            self.playerOnTurn = playerListCopy[0]
            
            self.sendGameData("ok")
        else:
            self.sendGameData("placeTaken")
    
    def sendGameData(self, lastMoveResult):
        self.server.sendData({
            "msgType": "gameUpdate",
            "data": {"playerOnTurn": self.playerOnTurn, "gameboard": self.gameboard, "marks": {GAMEBOARD_EMPTY: " ", self.playerList[0]: X_MARK, self.playerList[1]: O_MARK}, "winner": self.getWinner(), "lastMoveResult": lastMoveResult}
            # {
                # "playerOnTurn": self.playerOnTurn,
                # "gameboard": self.gameboard,
                # "marks": {None: " ", self.playerList[0]: "X", self.playerList[1]: "O"},
                # "winner": self.getWinner()
            # }
        })
    
    def getWinner(self):
        if self.gameboard[0][0] == self.gameboard[0][1] == self.gameboard[0][2] and not self.gameboard[0][0] == GAMEBOARD_EMPTY:
            return self.gameboard[0][0]
        
        if self.gameboard[1][0] == self.gameboard[1][1] == self.gameboard[1][2] and not self.gameboard[1][0] == GAMEBOARD_EMPTY:
            return self.gameboard[1][0]
        
        if self.gameboard[2][0] == self.gameboard[2][1] == self.gameboard[2][2] and not self.gameboard[2][0] == GAMEBOARD_EMPTY:
            return self.gameboard[2][0]
        
        if self.gameboard[0][0] == self.gameboard[1][0] == self.gameboard[2][0] and not self.gameboard[0][0] == GAMEBOARD_EMPTY:
            return self.gameboard[0][0]
        
        if self.gameboard[0][1] == self.gameboard[1][1] == self.gameboard[2][1] and not self.gameboard[0][1] == GAMEBOARD_EMPTY:
            return self.gameboard[0][1]
        
        if self.gameboard[0][2] == self.gameboard[1][2] == self.gameboard[2][2] and not self.gameboard[0][2] == GAMEBOARD_EMPTY:
            return self.gameboard[0][2]
        
        if self.gameboard[0][0] == self.gameboard[1][1] == self.gameboard[2][2] and not self.gameboard[0][0] == GAMEBOARD_EMPTY:
            return self.gameboard[0][0]
        
        if self.gameboard[0][2] == self.gameboard[1][1] == self.gameboard[2][0] and not self.gameboard[0][2] == GAMEBOARD_EMPTY:
            return self.gameboard[0][2]
        
        for row in self.gameboard:
            for mark in row:
                if mark == GAMEBOARD_EMPTY:
                    return None
        
        return "draw"

class Player:
    def __init__(self, serverAddr):
        self.client = newClient(serverAddr)
        
        self.client.events.onDisconnected.connect(self.onDisconnected)
        self.client.events.onDataReceived.connect(self.onDataReceived)
    
    def onDisconnected(self):
        self.printGameFrame(None, "notif", "Disconnected from the server.")
    
    def onDataReceived(self, data):
        if data["msgType"] == "notif":
            self.printGameFrame(None, "notif", data["data"])
        elif data["msgType"] == "gameUpdate":
            if data["data"]["winner"] == self.client._uuid:
                self.printGameFrame(data, "won")
            elif data["data"]["winner"] == "draw":
                self.printGameFrame(data, "draw")
            elif not data["data"]["winner"] == None:
                self.printGameFrame(data, "lost")
            else:
                if data["data"]["playerOnTurn"] == self.client._uuid:                    
                    self.sendNextMove(data)
                else:
                    self.printGameFrame(data, "notYourTurn")
    
    def sendNextMove(self, gameData):
        if gameData["data"]["lastMoveResult"] == "ok":
            self.printGameFrame(gameData, "yourTurn", "Your turn!")
        elif gameData["data"]["lastMoveResult"] == "placeTaken":
            self.printGameFrame(gameData, "yourTurn", "That place is taken, try again.")
        
        move = input("What will be your next move? (eg. A2): ").upper()
        
        while not move in ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']:
            self.printGameFrame(gameData, "yourTurn", "Invalid input, try again.")
            move = input("What will be your next move? (eg. A2): ").upper()
        
        self.client.sendData({"msgType": "move", "data": move})
    
    def printGameFrame(self, gameData, scene, notif=""):
        clearConsole()
        
        # print(scene)
        
        if scene == "notYourTurn":
            self.printGameboard(gameData["data"])
            
            print(notif)
            print("Other player`s turn...")
        elif scene == "yourTurn":
            self.printGameboard(gameData["data"])
            
            print(notif)
        elif scene == "won":
            self.printGameboard(gameData["data"])
            
            print(notif)
            print("You won!")
        elif scene == "lost":
            self.printGameboard(gameData["data"])
            
            print(notif)
            print("You lost.")
        elif scene == "draw":
            self.printGameboard(gameData["data"])
            
            print(notif)
            print("Draw.")
        elif scene == "notif":
            print(notif)
    
    def printGameboard(self, gameData):
        # print(gameData["marks"], gameData["gameboard"])
        
        print('\n     1   2   3  ')
        print('   ┌───┬───┬───┐')
        print(f' A │ {self.coloredMark(gameData["marks"][gameData["gameboard"][0][0]])} │ {self.coloredMark(gameData["marks"][gameData["gameboard"][0][1]])} │ {self.coloredMark(gameData["marks"][gameData["gameboard"][0][2]])} │')
        print('   ├───┼───┼───┤')
        print(f' B │ {self.coloredMark(gameData["marks"][gameData["gameboard"][1][0]])} │ {self.coloredMark(gameData["marks"][gameData["gameboard"][1][1]])} │ {self.coloredMark(gameData["marks"][gameData["gameboard"][1][2]])} │')
        print('   ├───┼───┼───┤')
        print(f' C │ {self.coloredMark(gameData["marks"][gameData["gameboard"][2][0]])} │ {self.coloredMark(gameData["marks"][gameData["gameboard"][2][1]])} │ {self.coloredMark(gameData["marks"][gameData["gameboard"][2][2]])} │')
        print('   └───┴───┴───┘')
        print(f"\nYou play as '{self.coloredMark(gameData['marks'][self.client._uuid])}'\n")
        
        # print(gameData["gameboard"][0][0], gameData["gameboard"][0][1], gameData["gameboard"][0][2])
        # print(gameData["gameboard"][1][0], gameData["gameboard"][1][1], gameData["gameboard"][1][2])
        # print(gameData["gameboard"][2][0], gameData["gameboard"][2][1], gameData["gameboard"][2][2])
    
    def coloredMark(self, mark):
        if mark == X_MARK:
            return colorizeString(f"#r{mark}")
        
        if mark == O_MARK:
            return colorizeString(f"#b{mark}")
        
        return colorizeString(f"#g{mark}")

if __name__ == "__main__":
    choice = input("'H' to host a game, 'J' to join a game: ").upper()
    
    if choice == "H":
        game = Game(maxClients=2)
        
        print(f"The game is running on LAN on port {game.server.getAddr()[1]}.")
        
        player = Player(game.server.getAddr())
    elif choice == "J":
        ip = input("Enter the server ip address: ")
        
        port = None
        
        while port == None:
            try:
                port = int(input("Enter the server port: "))
            except ValueError:
                print("Invalid input.\nPort must be a number between 1024 and 65535.\nTry again.")
        
        player = Player((ip, port))