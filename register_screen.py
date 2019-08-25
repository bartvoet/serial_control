from tkinter import Tk, Text, Scrollbar, Button, Label, Frame,LEFT,NONE, Entry
from tkinter.constants import INSERT
import serial

root = Tk()
root.wm_title("Console tool")

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
    
    def read(self):
        pass
        
    def write(self):
        pass
    
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
  
    def isWritable(self):
        return self.writable
    
    def isReadable(self):
        return self.readable
    
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


registers = {}

def addReg(newRegister):
    if newRegister.getRegId() in registers.keys():
        raise Exception("Double definition of register") 
    registers[newRegister.getRegId()] = newRegister
    return newRegister

def configureScreen():
    #Ha Bart, ik heb de registers niet meer 100% in volgorde staan, maar wel in 'blokjes' die wat bij elkaar passen
    #nu heb ik het in een naam geplaatst, (name="OUTPUT CONTROL: \n ctrl_mode") maar zou tof zijn als de blokken een titel zouden krijgen
    
    # Output control and setpoints:
    addReg(RegisterEditor(0x50, "Mc"
                          , regRange=zeroTo(8)
                          , defaultValue=0
                          , name="OUTPUT CONTROL: \n ctrl_mode"
                          , description="(0)=PWM; (1)=RPM; (2)=current; (3)=FOC"))
    addReg(RegisterEditor(0xD, "Sd"
                          , regRange=between(-2048, 2047)
                          , defaultValue=0
                          , name="Id_setpoint"
                          , description="setpoint direct current -50.0A to 50.0A"  # -50.0 A to + 50.0 A        (value * 40.95994)
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 40.95994)
                            , userToReg=lambda x: (x * 40.95994))))
    addReg(RegisterEditor(0xE, "Sq"
                          , regRange=between(-2048, 2047)
                          , defaultValue=0
                          , name="Iq_setpoint"
                          , description="setpoint quadrature current -50.0A to 50.0A"  # -50.0 A to + 50.0 A        (value * 40.95994)
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 40.95994)
                            , userToReg=lambda x: (x * 40.95994))))
    addReg(RegisterEditor(0xF, "Sp"
                          , regRange=zeroTo(2000)
                          , defaultValue=0
                          , name="PWM_setpoint"
                          , description="Set duty-cycle 0.0% to 100.0%"  # 0.0 % to 100.0 %        value * 20
                          , transformation=Transformation(
                            regToUser=lambda x: float(x) * 20
                            , userToReg=lambda x: (x*20))))
    
    addReg(RegisterEditor(0x13, "Sr"
                          , regRange=between(-30000, 30000)
                          , defaultValue=0
                          , name="RPM_setpoint"
                          , description="RPM setpoint (RPM)"))  # -30000 to 30000        value * 1
    
    addReg(RegisterEditor(0x15, "Sf"
                          , regRange=zeroTo(2000)
                          , defaultValue=1953
                          , name="ac_freq"
                          , description="Set frequency of the AC output"  # 0.0 % to 100.0 %        value * 20
                          , transformation=Transformation(
                            regToUser=lambda x: float(97656 / x)
                            , userToReg=lambda x: (97656 / x))))
    addReg(RegisterEditor(0x20, "Td"
                          , regRange=between(10, 100)
                          , defaultValue=32
                          , name="dead_time"
                          , description="set output dead time (ns)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x) * 10
                            , userToReg=lambda x: (x/10))))
    
    addReg(RegisterEditor(0x22, "Ts"
                          , regRange=zeroTo(10000)
                          , defaultValue=500
                          , name="slope"
                          , description="set PWM rate of change in % per us"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x) * 1 #not defined yet
                            , userToReg=lambda x: (x*1))))
    
    addReg(RegisterEditor(0x23, "Tp"
                          , regRange=between(-1023, 1023)
                          , defaultValue=32
                          , name="phase_shift"
                          , description="set phase-shift in degrees"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x) * 0.3515625
                            , userToReg=lambda x: (x / 0.3515625))))
    
    addReg(RegisterEditor(0xB, "Im"
                          , regRange=zeroTo(0xFFF)
                          , defaultValue=2457 # 10A
                          , name="Imax"
                          , description="Max current in PID-loop output for current control"
                          , transformation=Transformation(
                            regToUser=lambda x: float((x - 2048)) / 40.95994
                            , userToReg=lambda x: (x * 40.95994) + 2048)))
    
    addReg(RegisterEditor(0x30, "Lp"
                          , regRange=zeroTo(2047)
                          , defaultValue=60
                          , name="CONTROL LOOPS: \n P_gain_0"
                          , description="Kp in RPM control-loop (0 to 10)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 20.47)
                            , userToReg=lambda x: (x * 20.47))))
    
    addReg(RegisterEditor(0x31, "Li"
                          , regRange=zeroTo(2047)
                          , defaultValue=40
                          , name="I_gain_0"
                          , description="Ki in RPM control-loop (0 to 10)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 20.47)
                            , userToReg=lambda x: (x * 20.47))))
    
    addReg(RegisterEditor(0x32, "Ld"
                          , regRange=zeroTo(2047)
                          , defaultValue=0
                          , name="D_gain_0"
                          , description="Kd in RPM control-loop (0 to 10)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 20.47)
                            , userToReg=lambda x: (x * 20.47))))
    
    addReg(RegisterEditor(0x33, "Lf"
                          , regRange=between(125,6250000)
                          , defaultValue=62500 #1 kHz
                          , name="PID_0_f"
                          , description="RPM control loop frequency (Hz)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(62500000 / x )
                            , userToReg=lambda x: (62500000 / x))))
    
    addReg(RegisterEditor(0x34, "Lq"
                          , regRange=zeroTo(2047)
                          , defaultValue=60
                          , name="P_gain_1"
                          , description="Kp in current source control-loop (0 to 10)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 20.47)
                            , userToReg=lambda x: (x * 20.47))))
    
    addReg(RegisterEditor(0x35, "Lr"
                          , regRange=zeroTo(2047)
                          , defaultValue=40
                           , name="I_gain_1"
                          , description="Ki in current source control-loop (0 to 10)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 20.47)
                            , userToReg=lambda x: (x * 20.47))))
    
    addReg(RegisterEditor(0x36, "Ls"
                          , regRange=zeroTo(2047)
                          , defaultValue=0
                          , name="D_gain_1"
                          , description="Kd in current source control-loop (0 to 10)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 20.47)
                            , userToReg=lambda x: (x * 20.47))))
    
    addReg(RegisterEditor(0x37, "Lg"
                          , regRange=between(125,6250000)
                          , defaultValue=1250   # 50 kHz
                          , name="PID_1_f"
                          , description="current source control loop frequency (Hz)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(62500000 / x )
                            , userToReg=lambda x: (62500000 / x ))))
    
    # Limits and safety thresholds:
    addReg(RegisterEditor(0x42, "Et"
                          , regRange=zeroTo(2047)
                          , defaultValue=2344   # approx.105 deg C
                          , name="LIMITS: \n temp_limit"
                          , description="Temperature limit MOSFETs (deg C)"
                          , transformation=Transformation(
                            regToUser=lambda x: float((x - 1940) / 3.85333)
                            , userToReg=lambda x: ((x * 3.85333)+1940))))
    
    addReg(RegisterEditor(0xC, "Il"
                          , regRange=zeroTo(0xFFF)
                          , defaultValue=3276
                          , name="OC_lim_i"
                          , description="Over-current (input) protection  (A)"
                          # 0.5 A to 50 A    ± 30.0 A    (value * 40.95994) + 2048
                          , transformation=Transformation(
                            regToUser=lambda x: float((x - 2048)) / 40.95994
                            , userToReg=lambda x: (x * 40.95994) + 2048)))
    
    addReg(RegisterEditor(0x7, "Ia"
                          , regRange=zeroTo(0xFFF)
                          , defaultValue=4000
                          , name="OC_lim_o"
                          , description="Over-current (output) protection  (A)"
                          , transformation=Transformation(
                            regToUser=lambda x: float((x - 2048)) / 40.95994
                            , userToReg=lambda x: (x * 40.95994) + 2048)))
    
    addReg(RegisterEditor(0x4, "Vb"
                          , defaultValue=0
                          , regRange=zeroTo(0xFFF)
                          , name="Vs_under"
                          , description="under-voltage protection threshold (V)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 128.189)
                            , userToReg=lambda x: (x * 128.189))))
    
    addReg(RegisterEditor(0x6, "Vs"
                          , defaultValue=2047
                          , regRange=zeroTo(0xFFF)
                          , name="Vs_over"
                          , description="over-voltage protection threshold (V)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 128.189)
                            , userToReg=lambda x: (x * 128.189))))
    addReg(RegisterEditor(0x24, "Te"
                          , regRange=zeroTo(100000000)
                          , defaultValue=1000
                          , name="t_error"
                          , description="time before error detection (us)"
                          , transformation=Transformation(
                            regToUser=lambda x: float(x / 100000)
                            , userToReg=lambda x: (x * 100000))))
    
    # Oscilloscope and display controls:
    addReg(RegisterEditor(0x51, "Ms"
                          , regRange=zeroTo(8)
                          , defaultValue=0
                          , name="DISPLAYS: \n scp_mode"
                          , description="VGA_scope presets(0~8)"))
    addReg(RegisterEditor(0x14, "St"
                          , regRange=between(-2048, 2048)
                          , defaultValue=0
                          , name="scp_thresh"
                          , description="Threshold for VGA-oscilloscope"))
    addReg(RegisterEditor(0xEF, "D"
                          , regRange=zeroTo(15)
                          , defaultValue=11
                          , name="disp_sel"
                          , description="data switch for 7-segment display"))

configureScreen();

for reg in registers.values():
    frame = Frame(root)
    reg.draw(frame)
    frame.pack()

def restoreDefaults():
    serialCommander.writeCommand("r")

Button(root,text = "restore defaults",command = restoreDefaults).pack()


content_text.pack(expand='yes', fill='both')
scroll_bar = Scrollbar(content_text)
content_text.configure(yscrollcommand=scroll_bar.set)
scroll_bar.config(command=content_text.yview)
scroll_bar.pack(side='right', fill='y')

root.mainloop()

