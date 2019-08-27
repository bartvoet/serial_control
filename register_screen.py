from tkinter import Tk, Text, Scrollbar, Button, Label, Frame,LEFT,NONE, Entry, OptionMenu, StringVar
from tkinter.constants import INSERT
import serial.tools.list_ports

root = Tk()
root.wm_title("Console tool")

# Dictionary with options
serialChoice = StringVar(root)
choices = [v.name  for v in serial.tools.list_ports.comports()]
if len(choices) > 0:
    serialChoice.set(choices[0])

popupMenu = OptionMenu(root, serialChoice, *choices)

popupMenu.pack()


#Taak starten die gaat lezen - eventueel syncrhonizeren om conflict met write te vermijde

def UNLIMITED(val):
    return True

def between(a,b):
    return lambda x: x in range(a,b)

def zeroTo(until):
    return lambda x: x in range(0,until)

class Transformation:
    def __init__(self,regToUser = None,userToReg = None):
        self.reg_to_user = regToUser
        self.user_to_reg = userToReg
    
    def initRegToUser(self,fn):
        self.reg_to_user = fn
        
    def initUserToReg(self, fn):
        self.user_to_reg = fn
        
    def transformRegToUser(self,value):
        if self.reg_to_user == None:
            return value
        return self.reg_to_user(value)
    
    def transformUserToReg(self,value):
        if self.user_to_reg == None:
            return value
        return self.user_to_reg(value)

NO_TRANSFORMATION = Transformation()

content_text = Text(root, wrap='word')

class SerialCommander:
    
    def __init__(self):
        self.ser = serial.Serial(port="/dev/ttyACM0",
                                  baudrate=115200,
                                  bytesize=serial.EIGHTBITS,
                                  parity=serial.PARITY_NONE,
                                  stopbits=serial.STOPBITS_ONE,
                                  timeout=1,
                                  xonxoff=0,
                                  rtscts=0)

    def logCommand(self,command):
        content_text.insert(INSERT, "[COMMAND SEND]: " +  command + "\n")

    def writeCommand(self,command):
        self.logCommand(command)
        self.ser.write(command.encode())
    
serialCommander = SerialCommander()

class RegisterEditor:
    def __init__(self,registerId, identification, 
                 defaultValue = 0,
                 transformation = NO_TRANSFORMATION,
                 name = "NO NAME",
                 regRange = UNLIMITED,
                 description = "",
                 writable = True,
                 readable = True):
        self.transformation = transformation
        self.identification = identification
        self.default_value = defaultValue
        self.name = name
        self.regRange = regRange
        self.description = description
        self.reg_id = registerId
        self.writable = writable
        self.readable = readable
        self.serialCommander = serialCommander

    def getRegId(self):
        return self.reg_id
  
    def draw(self,container):
        Label(container,text=self.name).pack(side=LEFT, fill=NONE)
        self.entry = Entry(container)
        self.entry.pack(side=LEFT, fill=NONE)
        Button(container, text="write", command = self.write).pack(side=LEFT, fill=NONE)
        Label(container,text=self.description).pack(side=LEFT, fill=NONE)

    def write(self):
        regValue = self.entry.get()
        if regValue.isdigit():
            transformedRegValue = self.transformation.transformUserToReg(float(regValue))
            self.serialCommander.writeCommand(self.identification + str(int(transformedRegValue)) + "\n")


def restoreDefaults():
    serialCommander.writeCommand("r")


registers = {}

def addReg(newRegister):
    if newRegister.getRegId() in registers.keys():
        raise Exception("Double definition of register") 
    registers[newRegister.getRegId()] = newRegister
    return newRegister

def startRegisterScreen():
    for reg in registers.values():
        frame = Frame(root)
        reg.draw(frame)
        frame.pack()
    
    
    Button(root,text = "restore defaults",command = restoreDefaults).pack()
    
    
    content_text.pack(expand='yes', fill='both')
    scroll_bar = Scrollbar(content_text)
    content_text.configure(yscrollcommand=scroll_bar.set)
    scroll_bar.config(command=content_text.yview)
    scroll_bar.pack(side='right', fill='y')
    
    root.mainloop()

