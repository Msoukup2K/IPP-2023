import codecs
import re
import xml.etree.ElementTree as ET
import fileinput
import argparse
import sys

class Variable:
    def __init__(self, name):
        self.value = None
        self.name = name

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

    def setToFrame(self, variable, value=None, resultval=None):
        if variable.frame == "GF":
            if variable.value.name not in self.GF.keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)

            self.GF.update({variable.value.name: value.text if value != None else resultval})
        elif variable.frame == "TF":
            if self.TF == None:
                sys.stderr.write("Frame doesn't exist")
                sys.exit(55)
            if variable.value.name not in self.TF.keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            self.TF.update({variable.value.name: value.text if value != None else resultval})
        else:
            if len(self.LF) == 0:
                sys.stderr.write("Frame doesn't exist")
                sys.exit(55)
            
            if variable.value.name not in self.LF[len(self.LF)-1].keys():
                sys.stderr.write("Variable doesn't exist")
                sys.exit(54)
            self.LF[len(self.LF)-1].update({variable.value.name: value.text if value != None else resultval})
            
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
                value = arg1.text

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

            self.setToFrame(variable=arg1, resultval=stack_var)
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

            string = codecs.decode(string, 'unicode_escape')
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

    #TODO předělat před odevzdáním ty kontroly xml
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
            
            self.setToFrame(variable=arg1, resultval=value)
                
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
                op1 = arg2.text

            op1 = self.intConversion(op1)
            
            try:
                op1 = chr(op1)
            except ValueError as e:
                sys.stderr.write("Value cannot be converted to char")
                sys.exit(58)

            self.setToFrame(variable=arg1, resultval=op1)

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
            elif arg2.checkArgType("STRING"):
                op1 = arg2.text
            else:
                sys.stderr.write("Cannot use Strlen on different type than string")
                sys.exit(53)
            
            result = len(op1)
            
            self.setToFrame(arg1, resultval=result)
            return position

        elif instruction.code == "TYPE":
            if not arg1.checkArgType("VAR") and not arg2.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad type of arguments")
                sys.exit(32)

            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    op1 = "nil"
                if op1 == "nil":
                    type1 = "nil"
                else:
                    try:
                        int(op1)
                        type1 = "int"
                    except ValueError:
                        type1 = 'string'
                        try:
                            if op1.upper() == "TRUE" or op1.upper() == "FALSE":
                                type1 = 'bool'
                        except ValueError:
                            pass

            else:
                op1 = arg2.text
                type1 = arg2.type
            
            self.setToFrame(arg1, resultval=type1)

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
                self.setToFrame(arg1, resultval=op2)
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
            #TODO dodělat do variable types které se přiřazují do proměnné buďto v rámci rámce nebo v rámci variable objektu
            elif arg2.checkArgType("BOOL"):
                op1 = arg2.text
            else:
                sys.stderr.write("Cannot use Not on different type than bool")
                sys.exit(53)

            if op1.upper() == "TRUE":
                result = "false"
            elif op1.upper() == "FALSE":
                result = "true"
            else:
                sys.stderr.write("Cannot use Not on different type than bool")
                sys.exit(53)
 
            self.setToFrame(arg1,resultval=str(result).lower())    

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
                op1 = self.intConversion(self.getFromFrame(arg2))
            elif arg2.checkArgType("INT"):
                op1 = self.intConversion(arg2.text)
            else:
                sys.stderr.write("Cannot use Add on diffent type than int")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.intConversion(self.getFromFrame(arg3))
            elif arg3.checkArgType("INT"):
                op2 = self.intConversion(arg3.text)
            else:
                sys.stderr.write("Cannot use Add on diffent type than int")
                sys.exit(53)

            result = op1 + op2

            self.setToFrame(arg1, resultval=result)

            return position
        elif instruction.code == "SUB":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
            if arg2.checkArgType("VAR"):
                op1 = self.intConversion(self.getFromFrame(arg2))
            elif arg2.checkArgType("INT"):
                op1 = self.intConversion(arg2.text)
            else:
                sys.stderr.write("Cannot use Sub on diffent type than int")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.intConversion(self.getFromFrame(arg3))
            elif arg3.checkArgType("INT"):
                op2 = self.intConversion(arg3.text)
            else:
                sys.stderr.write("Cannot use Sub on diffent type than int")
                sys.exit(53)

            result = op1 - op2

            self.setToFrame(arg1, resultval=result)

            return position
        elif instruction.code == "MUL":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
            if arg2.checkArgType("VAR"):
                op1 = self.intConversion(self.getFromFrame(arg2))
            elif arg2.checkArgType("INT"):
                op1 = self.intConversion(arg2.text)
            else:
                sys.stderr.write("Cannot use Mul on diffent type than int")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.intConversion(self.getFromFrame(arg3))
            elif arg3.checkArgType("INT"):
                op2 = self.intConversion(arg3.text)
            else:
                sys.stderr.write("Cannot use Mul on diffent type than int")
                sys.exit(53)

            result = op1 * op2

            self.setToFrame(arg1, resultval=result)

            return position
        elif instruction.code == "IDIV":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
            if arg2.checkArgType("VAR"):
                op1 = self.intConversion(self.getFromFrame(arg2))
            elif arg2.checkArgType("INT"):
                op1 = self.intConversion(arg2.text)
            else:
                sys.stderr.write("Cannot use Mul on diffent type than int")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.intConversion(self.getFromFrame(arg3))
            elif arg3.checkArgType("INT"):
                op2 = self.intConversion(arg3.text)
            else:
                sys.stderr.write("Cannot use Mul on diffent type than int")
                sys.exit(53)

            try:
                result = op1 // op2
            except ZeroDivisionError as e:
                sys.stderr.write(f"ZeroDivisionError {e}")
                sys.exit(57)
            self.setToFrame(arg1, resultval=result)
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
                if op1 == "nil":
                    type1 = "nil"
                else:
                    try:
                        int(op1)
                        type1 = "int"
                    except ValueError:
                        type1 = 'string'
                        try:
                            if op1.upper() == "TRUE" or op1.upper() == "FALSE":
                                type1 = 'bool'
                        except ValueError:
                            pass
            else:
                op1 = arg2.text
                type1 = arg2.type
            
   
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                if op2 == "nil":
                    type2 = 'nil'
                else:
                    try:
                        int(op2)
                        type2 = "int"
                    except ValueError:
                        type2 = 'string'
                        try:
                            if op2.upper() == "TRUE" or op2.upper() == "FALSE":
                                type2 = 'bool'
                        except ValueError:
                            pass
            else:
                op2 = arg3.text
                type2 = arg3.type

            if type1 == "nil" or type2 == "nil":
                sys.stderr.write("Cannot use GT with nil")
                sys.exit(53)
            
            if type1 == 'bool' and type2 == 'bool':
                if op1 == "true" and op2 == "false":
                    result = 'false'
                elif op1 == "false" and op2 == "true":
                    result = 'true'
                else:
                    result = 'false'
            elif type1 == 'int' and type2 == 'int':
                    result = str(op1 < op2).lower()
            elif type1 == 'string' and type2 == 'string':
                if op1 == None and op2 != None:
                    result = 'false'
                elif op2 == None and op1 != None:
                    result = 'true'
                else:
                    result = str(op1 < op2).lower()
            else:
                sys.stderr.write("Cannot use Getchar with different types")
                sys.exit(53)
            self.setToFrame(arg1, resultval=result)

            return position
        elif instruction.code == "GT":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if( op1 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                if op1 == "nil":
                    type1 = "nil"
                else:
                    try:
                        int(op1)
                        type1 = "int"
                    except ValueError:
                        type1 = 'string'
                        try:
                            if op1.upper() == "TRUE" or op1.upper() == "FALSE":
                                type1 = 'bool'
                        except ValueError:
                            pass
            else:
                op1 = arg2.text
                type1 = arg2.type
            
   
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                if op2 == "nil":
                    type2 = 'nil'
                else:
                    try:
                        int(op2)
                        type2 = "int"
                    except ValueError:
                        type2 = 'string'
                        try:
                            if op2.upper() == "TRUE" or op2.upper() == "FALSE":
                                type2 = 'bool'
                        except ValueError:
                            pass
            else:
                op2 = arg3.text
                type2 = arg3.type

            if type1 == "nil" or type2 == "nil":
                sys.stderr.write("Cannot use GT with nil")
                sys.exit(53)
            
            if type1 == 'bool' and type2 == 'bool':
                if op1 == "true" and op2 == "false":
                    result = 'true'
                elif op1 == "false" and op2 == "true":
                    result = 'false'
                else:
                    result = 'false'
            elif type1 == 'int' and type2 == 'int':
                    result = str(op1 > op2).lower()
            elif type1 == 'string' and type2 == 'string':
                if op1 == None and op2 != None:
                    result = 'false'
                elif op2 == None and op1 != None:
                    result = 'true'
                else:
                    result = str(op1 > op2).lower()
            else:
                sys.stderr.write("Cannot use Getchar with different types")
                sys.exit(53)
            self.setToFrame(arg1, resultval=result)

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
                if op1 == "nil":
                    type1 = "nil"
                else:
                    try:
                        int(op1)
                        type1 = "int"
                    except ValueError:
                        type1 = 'string'
                        try:
                            if op1.upper() == "TRUE" or op1.upper() == "FALSE":
                                type1 = 'bool'
                        except ValueError:
                            pass
            else:
                op1 = arg2.text
                type1 = arg2.type
            
   
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                if op2 == "nil":
                    type2 = 'nil'
                else:
                    try:
                        int(op2)
                        type2 = "int"
                    except ValueError:
                        type2 = 'string'
                        try:
                            if op2.upper() == "TRUE" or op2.upper() == "FALSE":
                                type2 = 'bool'
                        except ValueError:
                            pass
            else:
                op2 = arg3.text
                type2 = arg3.type

            if type1 == type2 or type1 == "nil" or type2 == "nil":
                pass
            else:
                sys.stderr.write("Cannot use EQ with different types")
                sys.exit(53)
            
            if op1 == op2:
                self.setToFrame(arg1, resultval="true")
            else:
                self.setToFrame(arg1, resultval="false")


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
            elif arg2.checkArgType("BOOL"):
                op1 = arg2.text
            else:
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            elif arg3.checkArgType("BOOL"):
                op2 = arg3.text
            else:
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            if op1 == "true" and op2 == "true":
                self.setToFrame(arg1, resultval="true")
            else:
                self.setToFrame(arg1, resultval="false")

            return position
        elif instruction.code == "OR":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if( op1 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            elif arg2.checkArgType("BOOL"):
                op1 = arg2.text
            else:
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if( op2 == None):
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            elif arg3.checkArgType("BOOL"):
                op2 = arg3.text
            else:
                sys.stderr.write("Cannot use And on different type than bool")
                sys.exit(53)

            if op1 == "true" or op2 == "true":
                self.setToFrame(arg1, resultval="true")
            else:
                self.setToFrame(arg1, resultval="false")
            
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
            elif arg2.checkArgType("STRING"):
                op1 = arg2.text
            else:
                sys.stderr.write("Cannot use Setchar with different type than int and string")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            elif arg3.checkArgType("INT"):
                op2 = arg3.text
            else:
                sys.stderr.write("Cannot use Setchar with different type than int and string")
                sys.exit(53)

            self.setToFrame(variable=arg1, resultval=op2)

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
            elif arg2.checkArgType("STRING"):
                op1 = arg2.text
            else:
                sys.stderr.write("Cannot use Concat on different type than string")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            elif arg3.checkArgType("STRING"):
                op2 = arg3.text
            else:
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

            self.setToFrame(arg1, resultval=result)

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
            elif arg2.checkArgType("STRING"):
                op1 = arg2.text
            else:
                sys.stderr.write("Cannot use Getchar on different type than string")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            elif arg3.checkArgType("INT"):
                op2 = arg3.text
            else:
                sys.stderr.write("Cannot use Getchar with different type than int")
                sys.exit(53)

            try:
                if self.intConversion(op2) < 0:
                    sys.stderr.write("String index out of range")
                    sys.exit(58)
                    
                result = op1[self.intConversion(op2)]
            except IndexError as e:
                sys.stderr.write("String index out of range")
                sys.exit(58)
                
            self.setToFrame(arg1, resultval=result)
            
            return position
        elif instruction.code == "SETCHAR":
            if not arg1.checkArgType("VAR") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
                
            op1 = self.getFromFrame(arg1)
            
            if arg2.checkArgType("VAR"):
                op2 = self.getFromFrame(arg2)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            elif arg2.checkArgType("INT"):
                op2 = arg2.text
            else:
                sys.stderr.write("Cannot use Setchar with different type than int and string")
                sys.exit(53)
            if arg3.checkArgType("VAR"):
                op3 = self.getFromFrame(arg3)
                if op3 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
            elif arg3.checkArgType("STRING"):
                op3 = arg3.text
            else:
                sys.stderr.write("Cannot use Setchar with different type than int and string")
                sys.exit(53)

            

            return position
        elif instruction.code == "JUMPIFEQ":
            if not arg1.checkArgType("LABEL") or not arg2.checkSymb() or not arg3.checkSymb():
                sys.stderr.write(f"Instruction {instruction.code} has bad arguments")
                sys.exit(32)
                
            
            if arg2.checkArgType("VAR"):
                op1 = self.getFromFrame(arg2)
                if op1 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                if op1 == "nil":
                    type1 = 'nil'
                else:
                    try:
                        op1 = int(op1)
                        type1 = "int"
                    except ValueError:
                        type1 = 'string'
                        try:
                            if op1.upper() == "TRUE" or op1.upper() == "FALSE":
                                type1 = 'bool'
                        except ValueError:
                            pass
            else:
                op1 = arg2.text
                type1 = arg2.type
                if type1 == "int":
                    op1 = int(op1)

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                if op2 == "nil":
                    type2 = 'nil'
                else:
                    try:
                        op2 = int(op2)
                        type2 = "int"
                    except ValueError:
                        type2 = 'string'
                        try:
                            if op2.upper() == "TRUE" or op2.upper() == "FALSE":
                                type2 = 'bool'
                        except ValueError:
                            pass
            else:
                op2 = arg3.text
                type2 = arg3.type
                if type2 == "int":
                    op2 = int(op2)

            if type1 != type2 and type1 != "nil" and type2 != "nil":
                sys.stderr.write("Cannot use Jumpifeq with different types")
                sys.exit(53)

            if op1 == op2:
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
                if op1 == "nil":
                    type1 = 'nil'
                else:
                    try:
                        int(op1)
                        type1 = "int"
                    except ValueError:
                        type1 = 'string'
                        try:
                            if op1.upper() == "TRUE" or op1.upper() == "FALSE":
                                type1 = 'bool'
                        except ValueError:
                            pass
            else:
                op1 = arg2.text
                type1 = arg2.type

            if arg3.checkArgType("VAR"):
                op2 = self.getFromFrame(arg3)
                if op2 == None:
                    sys.stderr.write("Missing value")
                    sys.exit(56)
                if op2 == "nil":
                    type2 = 'nil'
                else:
                    try:
                        int(op2)
                        type2 = "int"
                    except ValueError:
                        type2 = 'string'
                        try:
                            if op2.upper() == "TRUE" or op2.upper() == "FALSE":
                                type2 = 'bool'
                        except ValueError:
                            pass
            else:
                op2 = arg3.text
                type2 = arg3.type

            if type1 != type2 and type1 != "nil" and type2 != "nil":
                sys.stderr.write("Cannot use Jumpifneq with different types")
                sys.exit(53)
                
            if op1 != op2 or op1 == 'nil' or op2 == 'nil':
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
                new_arg = Argument(c.attrib['type'], c.text)
            except Exception as ex:
                sys.stderr.write("Argument doesn't have type attribute")
                sys.exit(32)

            new_inst.addArgument(c.tag, new_arg)

        interpreter.instList.append(new_inst)

    interpreter.interpretInst()
