import codecs
import re
import xml.etree.ElementTree as ET
import fileinput
import argparse
import sys

class Variable:
    def __init__(self, name):
        self.name = name
        self.type = None

    def typeVariable(self, type):
        self.type = type

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


    def checkArgType(self, type):
        return self.type.upper() == type

    def checkSymb(self):
        if self.type.upper() not in ["VAR", "STRING", "BOOL", "INT", "NIL"]:
            return False
        else:
            return True

class Instruction:
    def __init__(self, order, code):
        self.order = order
        self.code = code.upper()
        self.argdict = {}

    def addArgument(self, order, argument):
        if not re.match("arg[123]", order):
            sys.stderr.write("Instruction has maximum of 3 arguments, in format 'arg1', 'arg2', 'arg3' ")
            sys.exit(32)

        if order in self.argdict:
            sys.stderr.write("Two arguments have the same index")
            sys.exit(32)
        self.argdict.update({order: argument})

    def checkProperArgs(self, count):
        return len(self.argdict) == count;

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

    def setToFrame(self, variable, value):
        if variable.frame == "GF":
            if variable.value.name not in self.GF.keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            variable.value.typeVariable( value.type )
            self.GF.update({variable.value.name: value})
            print(variable.value.type)
            print(self.GF[variable.value.name].text)
        elif variable.frame == "TF":
            if self.TF == None:
                sys.stderr.write("Frame doesn't exist")
                sys.exit(55)
            if variable.value.name not in self.TF.keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            variable.value.typeVariable( value.type )
            self.TF.update({variable.value.name: value})
        else:
            if len(self.LF) == 0:
                sys.stderr.write("Frame doesn't exist")
                sys.exit(55)
            
            if variable.value.name not in self.LF[len(self.LF)-1].keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            variable.value.typeVariable( value.type )
            self.LF[len(self.LF)-1].update({variable.value.name: value})
            
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
            return value
    def interpretInst(self):
        self.sortlist()
        self.getLabels()
        i = 0
        while i < (len(self.instList)):
            instr = self.instList[i]
            #print(instr.code)
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
    def interpretZero(self, instruction, position):
        if instruction.code == "RETURN":
            if len(self.calls) == 0:
                sys.stderr.write("Call for this return doesn't exist")
                sys.exit(56)
            
            return self.calls.pop()
        elif instruction.code == "CREATEFRAME":
            self.TF = dict()
            return position
        elif instruction.code == "PUSHFRAME":
            if self.TF == None:
                sys.stderr.write("Frame doesn't exist")
                sys.exit(55)
            else:
                newFrame = self.TF
                self.LF.append(newFrame)
                self.TF = None
            return position
        elif instruction.code == "POPFRAME":
            if len(self.LF) == 0:
                sys.stderr.write("Frame for pop doesn't exist")
                sys.exit(55)
            else:
                self.TF = self.LF.pop()
            return position
        elif instruction.code == "BREAK":
            sys.stderr.write("TADY JE VYPIS ORDER, což je index v listu, počet vykonaných instrukcí a obsahe ramců")
            pass
        else:
            sys.stderr.write("Wrong number of arguments")
            sys.exit(32)

    def interpretOne(self, instruction, position):
        if not 'arg1' in instruction.argdict:
            sys.stderr.write("Cannot interpret instruction without first argument 'arg1' ")
            sys.exit(32)
        arg1 = instruction.argdict['arg1']

        if instruction.code == "DEFVAR":
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

        elif instruction.code == "LABEL":
            return position

        elif instruction.code == "PUSHS":
            if not arg1.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of argument")
                sys.exit(32)
            if arg1.checkArgType("VAR"):
                value = self.getFromFrame(arg1)
            else:
                value = arg1

            self.stack.append(value)
            return position
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

        elif instruction.code == "WRITE":
            if arg1.checkArgType("VAR"):
                string = self.getFromFrame(arg1)
                if string == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                if( string == "nil"):
                    print("", end="")
                else:
                    print(string,end="")
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
                    string = arg1.text

            string = string.replace('\\032', ' ')
            string = string.replace('\\092', ' \\')
            string = string.replace('\\010', '\n')
            string = string.replace('\\035', '#')
            print(string,end="")

            return position

        elif instruction.code == "JUMP":
            if not arg1.checkArgType("LABEL"):
                sys.stderr.write(f"Instruction {instruction.code} has bad type of argument")
                sys.exit(32)
            if arg1.text in self.labels.keys():
                return self.labels[arg1.text]
            else:
                sys.stderr.write("Non-existent Label")
                sys.exit(52)
        elif instruction.code == "EXIT":
            if not arg1.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of argument")
                sys.exit(32)
            if arg1.checkArgType("VAR"):
                code = self.getFromFrame(arg1)
            elif arg1.checkArgType("INT"):
                code = arg1.text
            else:
                sys.stderr.write("Cannot exit with this type")
                sys.exit(53)
            
            code = self.intConversion(code)
            if code <= 49 and code >= 0:
                sys.exit(code)
            else:
                sys.stderr.write("Cannot exit with this exit code")
                sys.exit(57)

        elif instruction.code == "DPRINT":
            if not arg1.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of argument")
                sys.exit(32)
            if arg1.checkArgType("VAR"):
                dprint = self.getFromFrame(arg1)
                sys.stderr.write(dprint)
            return position
        else:
            sys.stderr.write("Wrong number of arguments")
            sys.exit(32)

    def interpretTwo(self, instruction, position):
        arg1 = instruction.argdict['arg1']
        arg2 = instruction.argdict['arg2']
        if instruction.code == "READ":
            if not arg1.checkArgType("VAR") or not arg2.checkArgType("TYPE"):
                sys.stderr.write(f"Instruction {instruction.code} has bad type of arguments")
                sys.exit(32)
            
            if len(self.input) == 0:
                sys.stderr.write("Input is empty")
                sys.exit(54)
            
            
            for i, item in enumerate(self.input):
                if arg2.text == "bool":
                    if item.strip().upper() == "TRUE" or item.strip().upper() == "FALSE":
                        value = item.strip().lower()
                        self.input.pop(i)
                    else:
                        value = "false"
                        self.input.pop(i)
                    break
                elif arg2.text == "int":
                    try:
                        value = int(item.strip())
                        self.input.pop(i)
                        break
                    except ValueError:
                        value = "nil"
                        self.input.pop(i)
                        break
                elif arg2.text == "string":
                    value = item.strip()
                    self.input.pop(i)
                    break
                else:
                    value = "nil"
                    self.input.pop(i)
                    break

            var = Argument(arg2.text, value)
            
            self.setToFrame(arg1, var)
                
            return position
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
                sys.stderr(53)

            try:
                op1 = chr(op1)
            except ValueError as e:
                sys.stderr.write("Value cannot be converted to char")
                sys.exit(58)

            var = Argument(op1.type, op1.text)
            self.setToFrame(arg1, var)

            return position
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

            result = len(op1.text)

            var = Argument("int", result)

            self.setToFrame(arg1, var)
            return position

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
            var = Variable("bool", result)
            self.setToFrame(arg1, var)
            return position
        else:
            sys.stderr.write("Wrong number of arguments")
            sys.exit(32)

    def interpretThree(self, instruction, position):
        arg1 = instruction.argdict['arg1']
        arg2 = instruction.argdict['arg2']
        arg3 = instruction.argdict['arg3']
        if instruction.code == "ADD":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
            else:
                op1 = arg2

            if op1.argCheckType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
            else:
                op2 = arg3

            if op2.argCheckType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            result = self.intConversion(op1.text) + self.intConversion(op2.text)
            var = Argument("int", result)
            self.setToFrame(arg1, var)

            return position
        elif instruction.code == "SUB":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
            else:
                op1 = arg2

            if op1.argCheckType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
            else:
                op2 = arg3

            if op2.argCheckType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            result = self.intConversion(op1.text) - self.intConversion(op2.text)
            var = Argument("int", result)
            self.setToFrame(arg1, var)

            return position
        elif instruction.code == "MUL":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
            else:
                op1 = arg2

            if op1.argCheckType("INT"):
                sys.stderr.write("Cannot use MUL on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
            else:
                op2 = arg3

            if op2.argCheckType("INT"):
                sys.stderr.write("Cannot use Add on different type than int")
                sys.exit(53)

            result = self.intConversion(op1.text) * self.intConversion(op2.text)
            var = Argument("int", result)
            self.setToFrame(arg1, var)

            return position
        elif instruction.code == "IDIV":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
            else:
                op1 = arg2

            if op1.argCheckType("INT"):
                sys.stderr.write("Cannot use IDIV on different type than int")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
            else:
                op2 = arg3

            if op2.argCheckType("INT"):
                sys.stderr.write("Cannot use IDIV on different type than int")
                sys.exit(53)

            try:
                result = self.intConversion(op1) // self.intConversion(op2)
            except ZeroDivisionError as e:
                sys.stderr.write(f"ZeroDivisionError {e}")
                sys.exit(57)

            var = Argument("int", result)
            self.setToFrame(arg1, var)
            return position
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

            if op1.type == "nil" or op2.type == "nil":
                sys.stderr.write("Cannot use LT with nil")
                sys.exit(53)
            
            if op1.type == 'bool' and op2.type == 'bool':
                if op1.text == "true" and op2.text == "false":
                    result = 'false'
                elif op1.text == "false" and op2.text == "true":
                    result = 'true'
                else:
                    result = 'false'
            elif op1.type == 'int' and op2.type == 'int':
                    result = str(self.intConversion(op1.text) < self.intConversion(op2.text)).lower()
            elif op1.type == 'string' and op2.type == 'string':
                if op1.text == None and op2.text != None:
                    result = 'false'
                elif op1.text == None and op2.text != None:
                    result = 'true'
                else:
                    result = str(op1 < op2).lower()
            else:
                sys.stderr.write("Cannot use Getchar with different types")
                sys.exit(53)

            var = Argument(op1.type, result)
            self.setToFrame(arg1, var)

            return position
        elif instruction.code == "GT":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if (op1 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if (op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if op1.type == "nil" or op2.type == "nil":
                sys.stderr.write("Cannot use LT with nil")
                sys.exit(53)

            if op1.type == 'bool' and op2.type == 'bool':
                if op1.text == "true" and op2.text == "false":
                    result = 'false'
                elif op1.text == "false" and op2.text == "true":
                    result = 'true'
                else:
                    result = 'false'
            elif op1.type == 'int' and op2.type == 'int':
                result = str(self.intConversion(op1.text) < self.intConversion(op2.text)).lower()
            elif op1.type == 'string' and op2.type == 'string':
                if op1.text == None and op2.text != None:
                    result = 'false'
                elif op1.text == None and op2.text != None:
                    result = 'true'
                else:
                    result = str(op1 < op2).lower()
            else:
                sys.stderr.write("Cannot use Getchar with different types")
                sys.exit(53)

            var = Argument(op1.type, result)
            self.setToFrame(arg1, var)

            return position
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

            if op1.type == op2.type or op1.type == "nil" or op2.type == "nil":
                pass
            else:
                sys.stderr.write("Cannot use EQ with different types")
                sys.exit(53)
            
            if op1 == op2:
                var = Argument(op1.type, "true")
                self.setToFrame(arg1, var)
            else:
                var = Argument(op1.type, "false")
                self.setToFrame(arg1, var)

            return position
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

            if not op1.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            if op1 == "true" and op2 == "true":
                var = Argument("bool", "true")
                self.setToFrame(arg1, var)
            else:
                var = Argument("bool", "false")
                self.setToFrame(arg1, var)

            return position
        elif instruction.code == "OR":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if (op1 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op1 = arg2

            if not op1.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if (op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3

            if not op1.checkArgType("BOOL"):
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            if op1 == "true" or op2 == "true":
                var = Argument("bool", "true")
                self.setToFrame(arg1, var)
            else:
                var = Argument("bool", "false")
                self.setToFrame(arg1, var)
            
            return position
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
                op1 = arg2.text
            if not op1.checkArgType("STRING"):
                sys.stderr.write("Cannot use Stri2int with different type than int and string")
                sys.exit(53)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            else:
                op2 = arg3.text

            if not op2.checkArgType("INT"):
                sys.stderr.write("Cannot use Stri2int with different type than int and string")
                sys.exit(53)

            if self.intConversion(op2.text) < 0 or self.intConversion(op2.text) > len(op1.text) - 1:
                sys.stderr.write("Index out of range")
                sys.exit(58)

            result = ord(op1.text[self.intConversion(op2.text)])
            var = Argument("int", result)
            self.setToFrame(arg1, var)

            return position
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
            if not op1.checkArgType("STRING"):
                sys.stderr.write("Cannot use Concat on different type than string")
                sys.exit(53)

            if op1 == None:
                result = op2
            elif op2 == None:
                result = op1
            else:
                result = op1 + op2
            if( result == None ):
                result = ""

            var = Argument("string", result)
            self.setToFrame(arg1, var)

            return position

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

            try:
                if self.intConversion(op2) < 0:
                    sys.stderr.write("String index out of range")
                    sys.exit(58)
                    
                result = op1[self.intConversion(op2)]
            except IndexError as e:
                sys.stderr.write("String index out of range")
                sys.exit(58)

            var = Argument("string", result)
            self.setToFrame(arg1, var)
            
            return position
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

            if op1.text == op2.text:
                if arg1.text in self.labels.keys():
                    return self.labels[arg1.text]
                else:
                    sys.stderr.write("Label doesn't exist")
                    sys.exit(52)
                    
            return position
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
                
            if op1.text != op2.text:
                if arg1.text in self.labels.keys():
                    return self.labels[arg1.text]
                else:
                    sys.stderr.write("Label doesn't exist")
                    sys.exit(52)
            
            return position
        else:
            sys.stderr.write("Wrong number of arguments")
            sys.exit(32)

    def sortlist(self):
        def convertInstOrder( op ):
            try:
                op = int(op.lstrip('0'))
            except ValueError:
                raise ValueError("Order has to be number")

            if op <= 0:
                raise ValueError("Order has to be bigger than zero")
            return op

        try:
            self.instList.sort(key=lambda instr: convertInstOrder(instr.order))
        except ValueError as e:
            sys.stderr.write(str(e))
            sys.exit(32)

    def printList(self):
        for item in self.instList:
            print(item.order + " " + item.code + "")
            for arg, argitem in item.argdict.items():
                print(arg + " " + argitem.text)
        exit(0)
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

    interpreter = Interpreter(input_lines)

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
        "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ"]:
            sys.stderr.write("Neznámá nebo špatně zapsaná instrukce")
            sys.exit(32)

        for c in inst:
            if len(c.attrib) != 1:
                sys.stderr.write("Argument have more than 'type' ")
                sys.exit(32)
            try:
                new_arg = Argument(c.attrib['type'], c.text.strip())
            except Exception as ex:
                sys.stderr.write("Argument doesn't have type attribute")
                sys.exit(32)

            new_inst.addArgument(c.tag, new_arg)

        interpreter.instList.append(new_inst)

    interpreter.interpretInst()
