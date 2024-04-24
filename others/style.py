from colorama import init, Fore
init()

_defaultCommand = "#"

colors = {
    _defaultCommand: Fore.RESET,
    "r": Fore.RED,
    "l": Fore.GREEN,
    "b": Fore.BLUE,
    "c": Fore.CYAN,
    "w": Fore.WHITE,
    "y": Fore.YELLOW,
    "m": Fore.MAGENTA,
    "g": Fore.LIGHTBLACK_EX
}

def _colorizeStr(line, command):
    for color in colors:
        line = line.replace(command + color, colors[color])
    
    line += Fore.RESET
    
    return line

def Print(line:str, command:str=_defaultCommand):
    if not (type(line) == str and type(command) == str):
        raise TypeError("Both line and command attributes must be string.")
    
    print(_colorizeStr(line, command))

def Input(line:str, command:str=_defaultCommand):
    if not (type(line) == str and type(command) == str):
        raise TypeError("Both line and command attributes must be string.")
    
    return input(_colorizeStr(line, command))

def OnlyColorize(line:str, command:str=_defaultCommand):
    if not (type(line) == str and type(command) == str):
        raise TypeError("Both line and command attributes must be string.")
    
    return _colorizeStr(line, command)