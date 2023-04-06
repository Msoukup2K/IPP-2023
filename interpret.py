import re
import xml.etree.ElementTree as ET
import fileinput
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
    
    parser = argparse.ArgumentParser(description="Argument parser for interpret.py", add_help=False)
    
    parser.add_argument("--help", help="Prints help for usage of interpret.py",
                        action="help", )
    parser.add_argument("--source", help="Source file with XML structure of parsed IppCode23",
                        action="store")
    parser.add_argument("--input", help="Input file with data to read",
                        action="store")
    args = parser.parse_args()

    if not args.source and not args.input:
        print("Pleas provide either input file or a source file")
        sys.exit(52)

    if not args.input:
        print("input: ")

    if not args.source:
        print("sauce: ")

