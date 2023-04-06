import re
import xml.etree.ElementTree as ET
import argparse
import sys

class Instruction:
    def instruction(self,order,code):
        order = order
        code = code

class Interpreter:
        def interpreter(self, args):
            args = args

class XMLInterpret:
    def interpret(self, xml_file):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for instruction_element in root.findall('instruction'):
            pass


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Argument parser for interpret.py")
    
    parser.add_argument("--help", help="Prints help for usage of interpret.py", default=sys.stdin, action="store")
    print(parser)
    print('HEEELP')
        
        