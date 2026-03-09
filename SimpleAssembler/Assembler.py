import sys

valid_opcodes = {
"add","sub","slt","sltu","xor","sll","srl","or","and",
"addi","lw","sltiu","jalr",
"sw","beq","bne","blt","bge","bltu","bgeu","lui","auipc","jal"
}

labels = {}
instructions = []
pc = 0

def read_assembly_file(filename):
    global pc
    with open(filename, "r") as file:
        lines = file.readlines()
    line_number = 1
    for line in lines:
        line = line.strip()
        if line ==   "" :
            line_number += 1
            continue
        if ":" in line:
            parts = line.split(":",1)
            label = parts[0].strip()
            if label in labels:
                print("Error: Duplicate label at line", line_number)
                sys.exit(1)
            labels[label] = pc
            if len(parts) > 1:
                line = parts[1].strip()
            else:
                line = ""
            if line == "":
                line_number += 1
                continue
        instructions.append((pc, line, line_number))
        pc += 4
        line_number += 1

def parse_instruction(line):
    line = line.replace(",", " ")
    line = line.replace("(", " ")
    line = line.replace(")", " ")
    parts = line.split()
    if len(parts) == 0:
        return None, None
    opcode = parts[0]
    operands = parts[1:]
    return opcode, operands

