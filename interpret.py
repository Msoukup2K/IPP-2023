##
#   Author: Martin Soukup, xsouku15
#   Project: Interpret jazyka IPPcode2023
##
import re
import xml.etree.ElementTree as ET
import argparse
import sys

# Class variable defines value and type of variable defined by DEFVAR
class Variable:
    def __init__(self, name):
        self.name = name
        self.type = None

    def typeVariable(self, type):
        self.type = type

# Class argument defines argument text and type of an argument
# If argument has a type VAR, class encapsulates Variable as an instance of class Argument variable
class Argument:
    def __init__(self, argtype, text):
        if argtype.upper() == "VAR":
            frame_value = text.split("@")
            self.frame = frame_value[0]
            self.value = Variable(name=frame_value[1])
        else:
            self.frame = None
            self.value = None
        self.type = argtype
        self.text = text

    # Function checks if Argument is the right type
    def checkArgType(self, type):
        return self.type.upper() == type
    
    # Symb is a special case of type, checks if it is one of the right types for Symb
    def checkSymb(self):
        if self.type.upper() not in ["VAR", "STRING", "BOOL", "INT", "NIL"]:
            return False
        else:
            return True

# Class Instruction defines order and code, also a dictionary of arguments
# Dictionary added by function addArgument
class Instruction:
    def __init__(self, order, code):
        self.order = order
        self.code = code.upper()
        self.argdict = {}

    # Dictionary added by function addArgument looks then like {'arg1': Argument_object}
    def addArgument(self, order, argument):
        if not re.match("arg[123]", order):
            sys.stderr.write("Instruction has maximum of 3 arguments, in format 'arg1', 'arg2', 'arg3' ")
            sys.exit(32)

        if order in self.argdict:
            sys.stderr.write("Two arguments have the same index")
            sys.exit(32)
        self.argdict.update({order: argument})

    # Function checks if instruction has right count of arguments
    def checkProperArgs(self, count):
        return len(self.argdict) == count;

# Class Interpreter is the main class interpreting every instruction
class Interpreter:
    def __init__(self, input):
        self.input = input
        self.instList = []
        self.calls = list()
        self.TF = None
        self.GF = dict()
        self.LF = list()
        self.stack = list()
        self.labels = dict()

    # Checks for labels stored by LABEL before interpreting
    def getLabels(self):
        for i in range(len(self.instList)):
            instr = self.instList[i]
            if instr.code == "LABEL":
                if instr.argdict['arg1'].checkArgType("LABEL"):
                    if instr.argdict['arg1'].text in self.labels.keys():
                        sys.stderr.write("Multiple labels with a same name")
                        sys.exit(52)

                    self.labels.update({instr.argdict['arg1'].text: i})
                else:
                    sys.stderr.write(f"Instruction {instr.code} requires type label")
                    sys.exit(53)

    # Sets value to variable, in the right frame
    # Every frame is stored differently
    def setToFrame(self, variable, value):
        # Global frame is dictionary, storing {'variable_name' : Argument_object}
        if variable.frame == "GF":
            if variable.value.name not in self.GF.keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            variable.value.typeVariable( value.type )
            self.GF.update({variable.value.name: value})
        # Temporary frame is dictionary, storing {'variable_name' : Argument_object}
        elif variable.frame == "TF":
            if self.TF == None:
                sys.stderr.write("Frame doesn't exist")
                sys.exit(55)
            if variable.value.name not in self.TF.keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            variable.value.typeVariable( value.type )
            self.TF.update({variable.value.name: value})
        # Local frame is a list of Temporary frames
        elif variable.frame == "LF":
            if len(self.LF) == 0:
                sys.stderr.write("Frame doesn't exist")
                sys.exit(55)
            # Check for a variable in the last added Temporary Frame
            if variable.value.name not in self.LF[len(self.LF)-1].keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            variable.value.typeVariable( value.type )
            self.LF[len(self.LF)-1].update({variable.value.name: value})
        else:
            sys.stderr.write("Cannot use other frames then GF, TF and LF")
            sys.exit(52)
            
    # Function gets variable from frame by it's name
    # Every frame checks if value is inside. If yes, name of variable is also the key.
    def getFromFrame(self, variable):
        if variable.frame == "GF":
            if variable.value.name not in self.GF.keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            return self.GF.get(variable.value.name)
        elif variable.frame == "TF":
            if self.TF == None:
                sys.stderr.write("Frame doesn't exist")
                sys.exit(55)
            if variable.value.name not in self.TF.keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            return self.TF.get(variable.value.name)
        elif variable.frame == "LF":
            if len(self.LF) == 0:
                sys.stderr.write("Frame doesn't exist")
                sys.exit(55)
    
            if variable.value.name not in self.LF[len(self.LF)-1].keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            else:
                value = self.LF[len(self.LF)-1].get(variable.value.name)
        else:
            sys.stderr.write("Cannot use other frames then GF, TF and LF")
            sys.exit(52)        
        return value
    
    # Funkction interpreting instruction start with sorting by order
    # Stores labels from given source code and stores them in a dictionary
    def interpretInst(self):
        self.sortlist()
        self.getLabels()
        i = 0
        # Variable i for position in the code, makes jumps easy to handle
        # Interpret loops then through code and by number of arguments decide which group is instruction in
        # Every instruction after interpreting returns it's position
        while i < (len(self.instList)):
            instr = self.instList[i]
            if len(instr.argdict) == 0:
                i = self.interpretZero(instr, i)
            elif len(instr.argdict) == 1:
                i = self.interpretOne(instr, i)
            elif len(instr.argdict) == 2:
                i = self.interpretTwo(instr, i)
            elif len(instr.argdict) == 3:
                i = self.interpretThree(instr, i)
            else:
                sys.stderr.write("Wrong number of arguments")
                sys.exit(32)
            i += 1
    
    # Function converts operand to integer, if cannot be converted catches an error
    def intConversion(self, op):
        if( op == None):
            sys.stderr.write("Value error, variable is unset")
            sys.exit(56)
        try:
            op = int(op)
        except ValueError as e:
            sys.stderr.write(f"Value error {e}")
            sys.exit(53)
        return op
    
    # Function interprets instructions with zero arguments
    def interpretZero(self, instruction, position):
        
        if instruction.code == "CLEARS":
            self.stack.clear();
            return position;
        
        # Return checks number of calls and pops last given call from stack
        if instruction.code == "RETURN":
            if len(self.calls) == 0:
                sys.stderr.write("Call for this return doesn't exist")
                sys.exit(56)
            return self.calls.pop()
        
        # Createframe declares Temporary frame, so it's not None
        elif instruction.code == "CREATEFRAME":
            self.TF = dict()
            return position
        
        # Appending created Temporary frame
        elif instruction.code == "PUSHFRAME":
            if self.TF == None:
                sys.stderr.write("Frame doesn't exist")
                sys.exit(55)
            else:
                newFrame = self.TF
                self.LF.append(newFrame)
                self.TF = None
            return position
        
        # Popping last appended frame
        elif instruction.code == "POPFRAME":
            if len(self.LF) == 0:
                sys.stderr.write("Frame for pop doesn't exist")
                sys.exit(55)
            else:
                self.TF = self.LF.pop()
            return position
        
        # Break prints instruction order, actual position in code, and state of frames
        elif instruction.code == "BREAK":
            sys.stderr.write(f"Instruction order: {instruction.order}, actual position: {position}\nFrames - GF: {self.GF}\nTF: {self.TF}\nLF: {self.TF}")
            return position
        
        # Following instructions are for STACK extension, they're similar to normal instructions
        elif instruction.code == "NOTS":
            
            # Difference between normal and STACK instruction is arguments are popped from stack
            arg2 = self.stack.pop();
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2
            if not op1.checkArgType("BOOL"):
                sys.stderr.write("Cannot use Not on different type than bool")
                sys.exit(53)

            if op1.text.upper() == "TRUE":
                result = "false"
            elif op1.text.upper() == "FALSE":
                result = "true"
            else:
                sys.stderr.write("Bool have values true or false")
                sys.exit(53)
                
            var = Argument("bool", result)
            self.stack.append(var)
            return position
        
        elif instruction.code == "INT2CHARS":
                
            arg2 = self.stack.pop();

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2
            if not op1.checkArgType("INT"):
                sys.stderr.write("Cannot use Int2char with with other type than int")
                sys.exit(53)

            try:
                result = chr(self.intConversion(op1.text))
            except ValueError as e:
                sys.stderr.write("Value cannot be converted to char")
                sys.exit(58)

            var = Argument("string", result)
            self.stack.append(var)
            return position
        
        elif instruction.code == "STRI2INTS":
            
            arg3 = self.stack.pop();
            arg2 = self.stack.pop();

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2
            if not op1.checkArgType("STRING"):
                sys.stderr.write("Cannot use Stri2int with different type than int and string")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Stri2int with different type than int and string")
                sys.exit(53)

            if self.intConversion(op2.text) < 0 or self.intConversion(op2.text) > len(op1.text) - 1:
                sys.stderr.write("Index out of range")
                sys.exit(58)

            # Takes one character on given index and changes it to integer
            result = ord(op1.text[self.intConversion(op2.text)])
            var = Argument("int", result)
            self.stack.append(var)
            return position
        
        elif instruction.code == "ADDS":

            arg3 = self.stack.pop();
            arg2 = self.stack.pop();
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3
            

            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            try:
                int(op2.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)
            try:
                int(op1.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)
            
            result = self.intConversion(op1.text) + self.intConversion(op2.text)
            var = Argument("int", result)
            self.stack.append(var)
            return position
        
        elif instruction.code == "SUBS":
    
            arg3 = self.stack.pop();
            arg2 = self.stack.pop();
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3
    
            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            try:
                int(op2.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)
            try:
                int(op1.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)

            result = self.intConversion(op1.text) - self.intConversion(op2.text)
            var = Argument("int", result)
            self.stack.append(var)
            return position
        
        elif instruction.code == "MULS":
          
            arg3 = self.stack.pop();
            arg2 = self.stack.pop();
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("INT"):
                sys.stderr.write("Cannot use MUL on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3
                
            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            try:
                int(op2.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)
            try:
                int(op1.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)

            result = self.intConversion(op1.text) * self.intConversion(op2.text)
            var = Argument("int", result)
            self.stack.append(var)
            return position
        
        elif instruction.code == "IDIVS":
         
            arg3 = self.stack.pop();
            arg2 = self.stack.pop();

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("INT"):
                sys.stderr.write("Cannot use IDIV on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use IDIV on different type than int")
                sys.exit(53)

            try:
                int(op2.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)
            try:
                int(op1.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)

            try:
                result = self.intConversion(op1.text) // self.intConversion(op2.text)
            except ZeroDivisionError as e:
                sys.stderr.write(f"ZeroDivisionError {e}")
                sys.exit(57)

            var = Argument("int", result)
            self.stack.append(var)
            return position
        elif instruction.code == "LTS":
            
            arg3 = self.stack.pop();
            arg2 = self.stack.pop();
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if( op1 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2
   
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            # LT cannot have arguments with type of nil
            if op1.checkArgType("NIL") or op2.checkArgType("NIL"):
                sys.stderr.write("Cannot use LT with nil")
                sys.exit(53)
            
            # Result is given by type of the given value
            if op1.checkArgType("BOOL") and op2.checkArgType("BOOL"):
                if op1.text == "true" and op2.text == "false":
                    result = 'false'
                elif op1.text == "false" and op2.text == "true":
                    result = 'true'
                else:
                    result = 'false'
            elif op1.checkArgType("INT") and op2.checkArgType("INT") :
                    result = str(self.intConversion(op1.text) < self.intConversion(op2.text)).lower()
            elif op1.checkArgType("STRING") and op2.checkArgType("STRING"):
                if op1.text == None and op2.text != None:
                    result = 'true'
                elif op1.text != None and op2.text == None:
                    result = 'false'
                else:
                    result = str(op1.text < op2.text).lower()
            else:
                sys.stderr.write("Cannot use Getchar with different types")
                sys.exit(53)

            var = Argument("bool", result)
            self.stack.append(var)
            return position
        elif instruction.code == "GTS":

            arg3 = self.stack.pop();
            arg2 = self.stack.pop();
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if op1.checkArgType("NIL") or op2.checkArgType("NIL") == "nil":
                sys.stderr.write("Cannot use LT with nil")
                sys.exit(53)

            if op1.checkArgType("BOOL") and op2.checkArgType("BOOL"):
                if op1.text == "true" and op2.text == "false":
                    result = 'true'
                elif op1.text == "false" and op2.text == "true":
                    result = 'false'
                else:
                    result = 'false'
            elif op1.checkArgType("INT") and op2.checkArgType("INT") :
                result = str(self.intConversion(op1.text) > self.intConversion(op2.text)).lower()
            elif op1.checkArgType("STRING") and op2.checkArgType("STRING"):
                if op1.text == None and op2.text != None:
                    result = 'false'
                elif op1.text != None and op2.text == None:
                    result = 'true'
                else:
                    result = str(op1.text > op2.text).lower()
            else:
                sys.stderr.write("Cannot use Getchar with different types")
                sys.exit(53)

            var = Argument("bool", result)
            self.stack.append(var)
            return position
        
        elif instruction.code == "EQS":
    
            arg3 = self.stack.pop();
            arg2 = self.stack.pop();

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if( op1 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2


            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if op1.type == op2.type or op1.checkArgType("NIL") or op2.checkArgType("NIL"):
                pass
            else:
                sys.stderr.write("Cannot use EQ with different types")
                sys.exit(53)
            
            if op1.text == op2.text:
                var = Argument("bool", "true")
                self.stack.append(var)
            else:
                var = Argument("bool", "false")
                self.stack.append(var)
            return position
            
        elif instruction.code == "ANDS":
                
            arg3 = self.stack.pop();
            arg2 = self.stack.pop();

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if( op1 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if not op2.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            # If both operands have proper types, make logical AND
            if op1.text == "true" and op2.text == "true":
                var = Argument("bool", "true")
                self.stack.append(var)
            else:
                var = Argument("bool", "false")
                self.stack.append(var)
            return position
        
        elif instruction.code == "ORS":

            arg3 = self.stack.pop();
            arg2 = self.stack.pop();
                
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if not op2.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            # If both operands have proper types, make logical OR
            if op1.text == "true" or op2.text == "true":
                var = Argument("bool", "true")
                self.stack.append(var)
            else:
                var = Argument("bool", "false")
                self.stack.append(var)
            return position
        else:
            sys.stderr.write("Wrong number of arguments")
            sys.exit(32)
            
    # Interprets instruction with one argument
    def interpretOne(self, instruction, position):
        # Checks if argument has right text and then stores it in a variable, simplifies working with argument
        if not 'arg1' in instruction.argdict:
            sys.stderr.write("Cannot interpret instruction without first argument 'arg1' ")
            sys.exit(32)
        arg1 = instruction.argdict['arg1']

        if instruction.code == "JUMPIFEQS":
            if not arg1.checkArgType("LABEL"):
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
                
            arg3 = self.stack.pop()
            arg2 = self.stack.pop()
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3
            if op1.type != op2.type and op1.type != "nil" and op2.type != "nil":
                sys.stderr.write("Cannot use Jumpifeq with different types")
                sys.exit(53)   
                      
            #If types are both int, we need to convert both to make proper condition
            if op1.checkArgType("INT") and op2.checkArgType("INT"):
                operand1 = self.intConversion(op1.text)
                operand2 = self.intConversion(op2.text)
            else: 
                operand1 = op1.text
                operand2 = op2.text

            if arg1.text in self.labels.keys():
                    label = self.labels[arg1.text]
            else:
                sys.stderr.write("Label doesn't exist")
                sys.exit(52)
                            
            # Returns label if condition is met
            if operand1 == operand2:
                    return label
            return position
        
        elif instruction.code == "JUMPIFNEQS":
            if not arg1.checkArgType("LABEL"):
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            arg3 = self.stack.pop();
            arg2 = self.stack.pop();
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if op1.type != op2.type and op1.type != "nil" and op2.type != "nil":
                sys.stderr.write("Cannot use Jumpifneqs with different types")
                sys.exit(53)

            if op1.checkArgType("INT") and op2.checkArgType("INT"):
                operand1 = self.intConversion(op1.text)
                operand2 = self.intConversion(op2.text)
            else: 
                operand1 = op1.text
                operand2 = op2.text

            if arg1.text in self.labels.keys():
                label = self.labels[arg1.text]
            else:
                sys.stderr.write("Cannot jump to the label")
                sys.exit(52)
            
            # If condition is not met, returns label position
            if operand1 != operand2:
                return label
            return position     
    
        # Creates a Variable and stores it in a right Frame, because there's no value, there's no point in using setToFrame
        elif instruction.code == "DEFVAR":
            if not arg1.checkArgType("VAR"):
                sys.stderr.write(f"Instruction {instruction.code} requires type var")
                sys.exit(53)

            if arg1.frame == "GF":
                if arg1.value.name in self.GF.keys():
                    sys.stderr.write("Cannot redefine a variable")
                    sys.exit(52)
                self.GF.update({arg1.value.name: None})
            elif arg1.frame == "TF":
                if self.TF == None:
                    sys.stderr.write("Frame doesn't exist")
                    sys.exit(55)
                if arg1.value.name in self.TF.keys():
                    sys.stderr.write("Cannot redefine a variable")
                    sys.exit(52)
                self.TF.update({arg1.value.name: None})
            elif arg1.frame == "LF":
                if len(self.LF) == 0:
                    sys.stderr.write("No frames on stack")
                    sys.exit(55)                
                if arg1.value.name in self.LF[len(self.LF)-1]:
                    sys.stderr.write("Cannot redefine a variable")
                    sys.exit(52)
                self.LF[len(self.LF)-1].update({arg1.value.name: None})

            return position

        # All Labels were taken by function getLabels in a start of Interpreter
        elif instruction.code == "LABEL":
            return position

        # Pushes value of variable or just value into the stack
        elif instruction.code == "PUSHS":
            if not arg1.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of argument")
                sys.exit(32)
            if arg1.checkArgType("VAR"):
                value = self.getFromFrame(arg1)
                if value == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                value = arg1

            self.stack.append(value)
            return position
        
        # Pops value from stack and stores it in a variable
        elif instruction.code == "POPS":
            if not arg1.checkArgType("VAR"):
                sys.stderr.write(f"Instruction {instruction.code} has bad type of argument")
                sys.exit(32)
            try:
                stack_var = self.stack.pop()
            except Exception as e:
                sys.stderr.write("There's no value to be popped")
                sys.exit(56)

            self.setToFrame(arg1, stack_var)
            return position

        # Appends position of line in source code and jumps to label if existing 
        elif instruction.code == "CALL":
            if not arg1.checkArgType("LABEL"):
                sys.stderr.write(f"Instruction {instruction.code} require type label")
                sys.exit(53)
            self.calls.append(position)

            if arg1.text in self.labels:
                value = self.labels[arg1.text]
            else:
                sys.stderr.write("Non-existent Label")
                sys.exit(52)
            
            return value
        
        # Write's into the output with print() function, variables and special cases are printed right away
        elif instruction.code == "WRITE":
            if arg1.checkArgType("VAR"):
                val = self.getFromFrame(arg1)
                if val == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                if( val.type == "nil"):
                    print("", end="")
                else:
                    print(val.text,end="")
                return position
            else:
                if arg1.checkArgType("NIL"):
                    print("", end="")
                    return position
                elif arg1.checkArgType("BOOL"):
                    if arg1.text.upper() == 'TRUE':
                        string = "true"
                    else:
                        string = "false"
                else:
                    val = arg1
                    string = arg1.text
            # Last formating before printing the value
            string = string.replace('\\032', ' ')
            string = string.replace('\\092', ' \\')
            string = string.replace('\\010', '\n')
            string = string.replace('\\035', '#')
            print(string,end="")
            return position

        # Jumps to label by returning position of label from dictionary
        elif instruction.code == "JUMP":
            if not arg1.checkArgType("LABEL"):
                sys.stderr.write(f"Instruction {instruction.code} has bad type of argument")
                sys.exit(32)
            if arg1.text in self.labels.keys():
                return self.labels[arg1.text]
            else:
                sys.stderr.write("Non-existent Label")
                sys.exit(52)
                
        # Stops interpreting and exits with error code from variable or source code
        elif instruction.code == "EXIT":
            if not arg1.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of argument")
                sys.exit(32)
            if arg1.checkArgType("VAR"):
                code = self.getFromFrame(arg1)
                if code == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                code = arg1
            if not code.checkArgType("INT"):
                sys.stderr.write("Cannot exit with this type")
                sys.exit(53)
            
            code = self.intConversion(code.text)
            if code <= 49 and code >= 0:
                sys.exit(code)
            else:
                sys.stderr.write("Cannot exit with this exit code")
                sys.exit(57)

        # Prints value
        elif instruction.code == "DPRINT":
            if not arg1.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of argument")
                sys.exit(32)
            if arg1.checkArgType("VAR"):
                dprint = self.getFromFrame(arg1)
                if dprint == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                sys.stderr.write(dprint.text)
            return position
        else:
            sys.stderr.write("Wrong number of arguments")
            sys.exit(32)

    # Interprets instruction with two arguments
    def interpretTwo(self, instruction, position):
        if not 'arg1' in instruction.argdict and not 'arg2' in instruction.argdict:
            sys.stderr.write("Cannot interpret instruction without first argument 'arg1' ")
            sys.exit(32)
        arg1 = instruction.argdict['arg1']
        arg2 = instruction.argdict['arg2']
        
        # Reads from input file, if it can't read proper type in input, returns nil, otherwise stores read input into variable
        if instruction.code == "READ":
            if not arg1.checkArgType("VAR") or not arg2.checkArgType("TYPE"):
                sys.stderr.write(f"Instruction {instruction.code} has bad type of arguments")
                sys.exit(32)
            
            value = "nil"
            valtype = "nil"
            for i, item in enumerate(self.input):
                if arg2.text == "bool":
                    if item.strip().upper() == "TRUE" or item.strip().upper() == "FALSE":
                        value = item.strip().lower()
                        valtype = "bool"
                        self.input.pop(i)
                    else:
                        value = "false"
                        valtype = "bool"
                        self.input.pop(i)

                    break
                elif arg2.text == "int":
                    try:
                        value = int(item.strip())
                        valtype = "int"
                        self.input.pop(i)
                    except ValueError:
                        value = "nil"
                        valtype = "nil"
                        self.input.pop(i)
                    break
                elif arg2.text == "string":
                    value = item.strip()
                    valtype = "string"
                    self.input.pop(i)
                    break
                else:
                    self.input.pop(i)
                    break
            
            var = Argument(valtype, value)           
            self.setToFrame(arg1, var)              
            return position
        
        # Converts int to char if conversion can be done and stores value into variable
        elif instruction.code == "INT2CHAR":
            if not arg1.checkArgType("VAR") and not arg2.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2
            if not op1.checkArgType("INT"):
                sys.stderr.write("Cannot use Int2char with with other type than int")
                sys.exit(53)

            try:
                result = chr(self.intConversion(op1.text))
            except ValueError as e:
                sys.stderr.write("Value cannot be converted to char")
                sys.exit(58)

            var = Argument("string", result)
            self.setToFrame(arg1, var)
            return position
        
        # Stores length of string into variable
        elif instruction.code == "STRLEN":
            if not arg1.checkArgType("VAR") and not arg2.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of arguments")
                sys.exit(32)
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("STRING"):
                sys.stderr.write("Cannot use Strlen on different type than string")
                sys.exit(53)

            try:
                result = len(op1.text)
            except TypeError as e:
                result = 0

            var = Argument("int", result)
            self.setToFrame(arg1, var)
            return position

        # Type finds type of value from variable or just type of value from source and store type as string
        elif instruction.code == "TYPE":
            if not arg1.checkArgType("VAR") and not arg2.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)

            else:
                op1 = arg2

            var = Argument("string", "" if op1 == None else op1.type )
            self.setToFrame(arg1, var)
            return position

        # Sets value to variable, if Symb is also a variable it gets it's value
        elif instruction.code == "MOVE":
            if not arg1.checkArgType("VAR") and not arg2.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of arguments")
                sys.exit(32)
            
            if arg2.checkArgType("VAR"):
                op2 = self.getFromFrame(arg2)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                self.setToFrame(arg1,op2)
            else:
                self.setToFrame(arg1,arg2)
            return position
        
        # Stores bool value into the variable after logical NOT
        elif instruction.code == "NOT":
            if not arg1.checkArgType("VAR") and not arg2.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of arguments")
                sys.exit(32)
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2
            if not op1.checkArgType("BOOL"):
                sys.stderr.write("Cannot use Not on different type than bool")
                sys.exit(53)

            if op1.text.upper() == "TRUE":
                result = "false"
            elif op1.text.upper() == "FALSE":
                result = "true"
            else:
                sys.stderr.write("Bool have values true or false")
                sys.exit(53)
            var = Argument("bool", result)
            self.setToFrame(arg1, var)
            return position
        else:
            sys.stderr.write("Wrong number of arguments")
            sys.exit(32)

    # Interprets instruction with three arguments
    def interpretThree(self, instruction, position):
        if not 'arg1' in instruction.argdict or not 'arg2' in instruction.argdict or not 'arg3' in instruction.argdict:
            sys.stderr.write("Cannot interpret instruction without first argument 'arg1' ")
            sys.exit(32)
        arg1 = instruction.argdict['arg1']
        arg2 = instruction.argdict['arg2']
        arg3 = instruction.argdict['arg3']
        
        # Following 4 instruction will make arithmetic operations and store result into variable
        # Every symb given must be converted to integer, if that fails. throws error 32, so there's no need for using intConversion function
        
        # ADD symb + symb
        if instruction.code == "ADD":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3
            

            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            try:
                int(op2.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)
            try:
                int(op1.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)
            
            result = self.intConversion(op1.text) + self.intConversion(op2.text)
            var = Argument("int", result)
            self.setToFrame(arg1, var)
            return position
        
        # SUB symb - symb
        elif instruction.code == "SUB":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3
    
            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            try:
                int(op2.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)
            try:
                int(op1.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)

            result = self.intConversion(op1.text) - self.intConversion(op2.text)
            var = Argument("int", result)
            self.setToFrame(arg1, var)
            return position
        
        # MUL symb * symb
        elif instruction.code == "MUL":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("INT"):
                sys.stderr.write("Cannot use MUL on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3
                
            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            try:
                int(op2.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)
            try:
                int(op1.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)

            result = self.intConversion(op1.text) * self.intConversion(op2.text)
            var = Argument("int", result)
            self.setToFrame(arg1, var)
            return position
        
        # IDIV symb // symb
        elif instruction.code == "IDIV":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("INT"):
                sys.stderr.write("Cannot use IDIV on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use IDIV on different type than int")
                sys.exit(53)

            try:
                int(op2.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)
            try:
                int(op1.text)
            except ValueError as e:
                sys.stderr.write("Invalid int")
                sys.exit(32)

            try:
                result = self.intConversion(op1.text) // self.intConversion(op2.text)
            except ZeroDivisionError as e:
                sys.stderr.write(f"ZeroDivisionError {e}")
                sys.exit(57)

            var = Argument("int", result)
            self.setToFrame(arg1, var)
            return position
        
        # Lesser then checks if first symb is less than second symb, result is stored in a variable
        elif instruction.code == "LT":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if( op1 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2
   
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            # LT cannot have arguments with type of nil
            if op1.checkArgType("NIL") or op2.checkArgType("NIL"):
                sys.stderr.write("Cannot use LT with nil")
                sys.exit(53)
            
            # Result is given by type of the given value
            if op1.checkArgType("BOOL") and op2.checkArgType("BOOL"):
                if op1.text == "true" and op2.text == "false":
                    result = 'false'
                elif op1.text == "false" and op2.text == "true":
                    result = 'true'
                else:
                    result = 'false'
            elif op1.checkArgType("INT") and op2.checkArgType("INT") :
                    result = str(self.intConversion(op1.text) < self.intConversion(op2.text)).lower()
            elif op1.checkArgType("STRING") and op2.checkArgType("STRING"):
                if op1.text == None and op2.text != None:
                    result = 'true'
                elif op1.text != None and op2.text == None:
                    result = 'false'
                else:
                    result = str(op1.text < op2.text).lower()
            else:
                sys.stderr.write("Cannot use Getchar with different types")
                sys.exit(53)

            var = Argument("bool", result)
            self.setToFrame(arg1, var)
            return position
        
        # Same as LT, but first symb must be greater than second symb
        elif instruction.code == "GT":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if op1.checkArgType("NIL") or op2.checkArgType("NIL") == "nil":
                sys.stderr.write("Cannot use LT with nil")
                sys.exit(53)

            if op1.checkArgType("BOOL") and op2.checkArgType("BOOL"):
                if op1.text == "true" and op2.text == "false":
                    result = 'true'
                elif op1.text == "false" and op2.text == "true":
                    result = 'false'
                else:
                    result = 'false'
            elif op1.checkArgType("INT") and op2.checkArgType("INT") :
                result = str(self.intConversion(op1.text) > self.intConversion(op2.text)).lower()
            elif op1.checkArgType("STRING") and op2.checkArgType("STRING"):
                if op1.text == None and op2.text != None:
                    result = 'false'
                elif op1.text != None and op2.text == None:
                    result = 'true'
                else:
                    result = str(op1.text > op2.text).lower()
            else:
                sys.stderr.write("Cannot use Getchar with different types")
                sys.exit(53)

            var = Argument("bool", result)
            self.setToFrame(arg1, var)
            return position
        
        # first symb must be equal to second symb, by type and by value
        # because every value is stored as string, there's no need for conversions
        elif instruction.code == "EQ":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if( op1 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

   
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if op1.type == op2.type or op1.checkArgType("NIL") or op2.checkArgType("NIL"):
                pass
            else:
                sys.stderr.write("Cannot use EQ with different types")
                sys.exit(53)
            
            if op1.text == op2.text:
                var = Argument("bool", "true")
                self.setToFrame(arg1, var)
            else:
                var = Argument("bool", "false")
                self.setToFrame(arg1, var)
            return position
        
        # Logical AND
        elif instruction.code == "AND":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if( op1 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if not op2.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            # If both operands have proper types, make logical AND
            if op1.text == "true" and op2.text == "true":
                var = Argument("bool", "true")
                self.setToFrame(arg1, var)
            else:
                var = Argument("bool", "false")
                self.setToFrame(arg1, var)
            return position
        
        # Logical OR
        elif instruction.code == "OR":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if not op2.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            # If both operands have proper types, make logical OR
            if op1.text == "true" or op2.text == "true":
                var = Argument("bool", "true")
                self.setToFrame(arg1, var)
            else:
                var = Argument("bool", "false")
                self.setToFrame(arg1, var)     
            return position
        
        # Changes char from string to int
        elif instruction.code == "STRI2INT":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2
            if not op1.checkArgType("STRING"):
                sys.stderr.write("Cannot use Stri2int with different type than int and string")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Stri2int with different type than int and string")
                sys.exit(53)

            if self.intConversion(op2.text) < 0 or self.intConversion(op2.text) > len(op1.text) - 1:
                sys.stderr.write("Index out of range")
                sys.exit(58)

            # Takes one character on given index and changes it to integer
            result = ord(op1.text[self.intConversion(op2.text)])
            var = Argument("int", result)
            self.setToFrame(arg1, var)
            return position
        
        # Joins two strings
        elif instruction.code == "CONCAT":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2
            if not op1.checkArgType("STRING"):
                sys.stderr.write("Cannot use Concat on different type than string")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3
            if not op2.checkArgType("STRING"):
                sys.stderr.write("Cannot use Concat on different type than string")
                sys.exit(53)

            # If one of the values is empty String result will be the second given string
            if op1.text == None and op2.text == None:
                result = ""
            elif op2.text == None:
                result = op1.text
            elif op1.text == None :
                result = op2.text
            else:
                result = op1.text + op2.text
            
            var = Argument("string", result)
            self.setToFrame(arg1, var)
            return position

        # Gets char from string on given index
        elif instruction.code == "GETCHAR":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2
            if not op1.checkArgType("STRING"):
                sys.stderr.write("Cannot use Getchar on different type than string and int")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3
            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Getchar with different type than string int")
                sys.exit(53)

            # Catches exception when index is bigger then length of string
            try:
                if self.intConversion(op2.text) < 0:
                    sys.stderr.write("String index out of range")
                    sys.exit(58)
                
                result = op1.text[self.intConversion(op2.text)]
            except IndexError as e:
                sys.stderr.write("String index out of range")
                sys.exit(58)

            var = Argument("string", result)
            self.setToFrame(arg1, var)
            
            return position
        
        # Sets character into the string
        elif instruction.code == "SETCHAR":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)      
                  
            op1 = self.getFromFrame(arg1)
            if op1 == None:
                sys.stderr.write("Missing value")
                sys.exit(56)
                
            if not op1.checkArgType("STRING"):
                sys.stderr.write("Variable has to be string")
                sys.exit(53)
                
            if arg2.checkArgType("VAR"):
                op2 = self.getFromFrame(arg2)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg2
            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Setchar with different type than int and string")
                sys.exit(53)
                
            if arg3.checkArgType("VAR"):
                op3 = self.getFromFrame(arg3)
                if op3 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op3 = arg3
            if not op3.checkArgType("STRING"):
                sys.stderr.write("Cannot use Setchar with different type than int and string")
                sys.exit(53)  
                  
            if op3.text == None:
                sys.stderr.write("Cannot use Setchar without char")
                sys.exit(58)
            
            # Finds index in string, modifies string from variable and sets it back
            for i in range(len(op1.text)):
                if i == int(op2.text):
                    try:
                        result = op1.text[:i] + op3.text[0] + op1.text[i+1:]
                        var = Argument("string", result)
                        self.setToFrame(arg1, var)
                        return position
                    except IndexError as e:
                        sys.stderr.write("Index is out of range")
                        sys.exit(58)
            sys.stderr.write("Index is out of range")
            sys.exit(58)

        # Jumps if condition is met
        elif instruction.code == "JUMPIFEQ":
            if not arg1.checkArgType("LABEL") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)        
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3
            if op1.type != op2.type and op1.type != "nil" and op2.type != "nil":
                sys.stderr.write("Cannot use Jumpifeq with different types")
                sys.exit(53)   
                      
            #If types are both int, we need to convert both to make proper condition
            if op1.checkArgType("INT") and op2.checkArgType("INT"):
                operand1 = self.intConversion(op1.text)
                operand2 = self.intConversion(op2.text)
            else: 
                operand1 = op1.text
                operand2 = op2.text

            if arg1.text in self.labels.keys():
                    label = self.labels[arg1.text]
            else:
                sys.stderr.write("Label doesn't exist")
                sys.exit(52)
                            
            # Returns label if condition is met
            if operand1 == operand2:
                    return label
            return position
        
        # Jumps if condition is not met
        elif instruction.code == "JUMPIFNEQ":
            if not arg1.checkArgType("LABEL") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if op1.type != op2.type and op1.type != "nil" and op2.type != "nil":
                sys.stderr.write("Cannot use Jumpifneq with different types")
                sys.exit(53)

            if op1.checkArgType("INT") and op2.checkArgType("INT"):
                operand1 = self.intConversion(op1.text)
                operand2 = self.intConversion(op2.text)
            else: 
                operand1 = op1.text
                operand2 = op2.text

            if arg1.text in self.labels.keys():
                label = self.labels[arg1.text]
            else:
                sys.stderr.write("Cannot jump to the label")
                sys.exit(52)
            
            # If condition is not met, returns label position
            if operand1 != operand2:
                return label
            return position        
        else:
            sys.stderr.write("Wrong number of arguments")
            sys.exit(32)

    # Functions sorts list by order, strips order by leading characters and checks for proper order of instruction
    def sortlist(self):
        def convertInstOrder( op ):
            try:
                op = int(op.lstrip('0'))
            except ValueError:
                raise ValueError("Order has to be number")

            if op <= 0:
                raise ValueError("Order has to be bigger than zero")
            return op
        # Tries to sort list by converting order of instruction to integer
        try:
            self.instList.sort(key=lambda instr: convertInstOrder(instr.order))
        except ValueError as e:
            sys.stderr.write(str(e))
            sys.exit(32)

## MAIN function of program, uses Argparse for argument parsing and print a usage of help
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Argument parser for interpret.py", add_help=False)
    
    parser.add_argument("--help", help="Prints help for usage of interpret.py",
                        action="help", )
    parser.add_argument("--source", help="Source file with XML structure of parsed IppCode23",
                        action="store")
    parser.add_argument("--input", help="Input file with data to read",
                        action="store")
    args = parser.parse_args()

    if not args.source and not args.input:
        sys.stderr.write("Pleas provide either input file or a source file")
        sys.exit(10)

    # Parsing input
    if not args.input:
        input_lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            input_lines.append(line)
    else:
        with open(args.input, 'r') as f:
            input_lines = f.readlines()

    # Tries parsing XML source with XML Element Tree
    if not args.source:
        source_lines = ""
        while True:
            try:
                line = input()
            except EOFError:
                break
            source_lines += line

        try:
            root = ET.fromstring(source_lines)
        except ET.ParseError as e:
            sys.stderr.write("Error parsing XML")
            sys.exit(31)
    else:
        try:
            source_xml = ET.parse(args.source)
            root = source_xml.getroot()
        except ET.ParseError as e:
            sys.stderr.write("Error parsing XML")
            sys.exit(31)

    # Defines Interpreter
    interpreter = Interpreter(input_lines)

    # Checks for proper Xml source file
    if root.tag != 'program':
        sys.stderr.write("Missing header 'program' in XML")
        sys.exit(32)

    if not 'language' in root.attrib.keys():
        sys.stderr.write("Not specified language in header of XML")

    for atr in root.attrib.keys():
        if not atr in ['language', 'name', 'description']:
            sys.stderr.write("Unsupported attributes in header of XML")
            sys.exit(32)

    if root.attrib['language'].upper() != 'IPPCODE23':
        sys.stderr.write("Language not supported by this interpret")
        sys.exit(32)

    # Checking if instruction are not maliformed or doesn't exist
    order_dict = {}
    for inst in root:

        if inst.tag != 'instruction':
            sys.stderr.write("Every element has to be 'instruction'")
            sys.exit(32)

        for c in inst.attrib:
            if not c in ['opcode', 'order']:
                sys.stderr.write("Unsupported attribute in XML structure")
                sys.exit(32)

        try:
            # Creates new instruction object
            new_inst = Instruction(inst.attrib['order'], inst.attrib['opcode'])

        except Exception as ex:
            sys.stderr.write("Order or opcode is missing")
            sys.exit(32)


        if inst.attrib['order'] in order_dict:
            sys.stderr.write("Duplicate 'Order' attribute in XML")
            sys.exit(32)
        else:
            order_dict.update({inst.attrib['order'] : inst.attrib['opcode']})

        if not inst.attrib['opcode'].upper() in ["CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK",
            "DEFVAR", "POPS", "CALL", "LABEL", "JUMP", "PUSHS", "WRITE", "EXIT", "DPRINT",
            "MOVE", "INT2CHAR", "STRLEN", "TYPE", "READ", "NOT", "ADD", "SUB",
            "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "STRI2INT", "CONCAT",
            "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ", "MULS", "ADDS", "SUBS", "IDIVS", "CLEARS", "LTS", "GTS", "EQS", "ANDS",
            "ORS", "NOTS", "INT2CHARS", "STRI2INTS", "JUMPIFEQS", "JUMPIFNEQS"]:
            sys.stderr.write("Neznámá nebo špatně zapsaná instrukce")
            sys.exit(32)

        # Checks if arguments are not maliformed, then changes every escape sequence to character
        for c in inst:
            if len(c.attrib) != 1:
                sys.stderr.write("Argument have more than 'type' ")
                sys.exit(32)
            try:
                # Creates new Argument object
                new_arg = Argument(c.attrib['type'], re.sub(r'\\(\d{3})', lambda match: chr(int(match.group(1))),c.text.strip()) if c.text != None else c.text)
            except Exception as ex:
                print(ex)
                sys.stderr.write("Argument doesn't have type attribute")
                sys.exit(32)
                
        # Adds argument to created instruction
            new_inst.addArgument(c.tag, new_arg)
            
        # Adds instruction to instruction list for interpreter
        interpreter.instList.append(new_inst)
        
    # Starts process of interpreting
    interpreter.interpretInst()
