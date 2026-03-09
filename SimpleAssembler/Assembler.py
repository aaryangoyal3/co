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
        if line == "":
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

def parse_instruction(line, line_number):
    line = line.replace(",", " ")
    line = line.replace("(", " ")
    line = line.replace(")", " ")
    parts = line.split()
    if len(parts) == 0:
        print("Error: Empty instruction at line", line_number)
        sys.exit(1)
    opcode = parts[0]
    if opcode not in valid_opcodes:
        print("Error: Invalid opcode", opcode, "at line", line_number)
        sys.exit(1)
    operands = parts[1:]
    if len(operands) == 0:
        print("Error: Missing operands for", opcode, "at line", line_number)
        sys.exit(1)
    return opcode, operands

def parse_all():
    parsed = []
    for item in instructions:
        apc = item[0]
        line = item[1]
        line_number = item[2]
        opcode, operands = parse_instruction(line, line_number)
        parsed.append({
            "pc": apc,
            "opcode": opcode,
            "operands": operands,
            "line": line_number
        })
    return parsed

REGISTERS = {
    "zero":"00000","x0":"00000",
    "ra":"00001","x1":"00001",
    "sp":"00010","x2":"00010",
    "gp":"00011","x3":"00011",
    "tp":"00100","x4":"00100",
    "t0":"00101","x5":"00101",
    "t1":"00110","x6":"00110",
    "t2":"00111","x7":"00111",
    "s0":"01000","fp":"01000","x8":"01000",
    "s1":"01001","x9":"01001",
    "a0":"01010","x10":"01010",
    "a1":"01011","x11":"01011",
    "a2":"01100","x12":"01100",
    "a3":"01101","x13":"01101",
    "a4":"01110","x14":"01110",
    "a5":"01111","x15":"01111",
    "a6":"10000","x16":"10000",
    "a7":"10001","x17":"10001",
    "s2":"10010","x18":"10010",
    "s3":"10011","x19":"10011",
    "s4":"10100","x20":"10100",
    "s5":"10101","x21":"10101",
    "s6":"10110","x22":"10110",
    "s7":"10111","x23":"10111",
    "s8":"11000","x24":"11000",
    "s9":"11001","x25":"11001",
    "s10":"11010","x26":"11010",
    "s11":"11011","x27":"11011",
    "t3":"11100","x28":"11100",
    "t4":"11101","x29":"11101",
    "t5":"11110","x30":"11110",
    "t6":"11111","x31":"11111",
}

RTYPE = {
    "add": ("0110011","000","0000000"),
    "sub": ("0110011","000","0100000"),
    "sll": ("0110011","001","0000000"),
    "slt": ("0110011","010","0000000"),
    "sltu":("0110011","011","0000000"),
    "xor": ("0110011","100","0000000"),
    "srl": ("0110011","101","0000000"),
    "or":  ("0110011","110","0000000"),
    "and": ("0110011","111","0000000"),
}
ITYPE = {
    "lw":   ("0000011","010"),
    "addi": ("0010011","000"),
    "sltiu":("0010011","011"),
    "jalr": ("1100111","000"),
}
STYPE = {"sw": ("0100011","010")}
BTYPE = {
    "beq": ("1100011","000"),
    "bne": ("1100011","001"),
    "blt": ("1100011","100"),
    "bge": ("1100011","101"),
    "bltu":("1100011","110"),
    "bgeu":("1100011","111"),
}
UTYPE = {"lui":"0110111","auipc":"0010111"}
JTYPE = {"jal":"1101111"}

def get_reg(token, line_number):
    if token not in REGISTERS:
        print("Error: Invalid register", token, "at line", line_number)
        sys.exit(1)
    return REGISTERS[token]

def parse_imm(token, line_number):
    try:
        if token.lower().startswith("0x"):
            return int(token, 16)
        return int(token)
    except ValueError:
        print("Error: Invalid immediate", token, "at line", line_number)
        sys.exit(1)

def to_signed_bin(value, bits, line_number):
    if value < -(1 << (bits - 1)) or value >= (1 << (bits - 1)):
        print("Error: Immediate", value, "out of", bits, "bit signed range at line", line_number)
        sys.exit(1)
    if value < 0:
        value += (1 << bits)
    return format(value, "0{}b".format(bits))

def registeropcodemapping(inst, inst_pc, line_number):
    opcode   = inst[0]
    operands = inst[1:]

    if opcode in RTYPE:
        oc, f3, f7 = RTYPE[opcode]
        rd  = get_reg(operands[0], line_number)
        rs1 = get_reg(operands[1], line_number)
        rs2 = get_reg(operands[2], line_number)
        return f7 + rs2 + rs1 + f3 + rd + oc

    if opcode in ITYPE:
        oc, f3 = ITYPE[opcode]
        rd = get_reg(operands[0], line_number)
        if operands[1] in REGISTERS:
            rs1 = get_reg(operands[1], line_number)
            imm = parse_imm(operands[2], line_number)
        else:
            imm = parse_imm(operands[1], line_number)
            rs1 = get_reg(operands[2], line_number)
        imm_bin = to_signed_bin(imm, 12, line_number)
        return imm_bin + rs1 + f3 + rd + oc

    if opcode in STYPE:
        oc, f3 = STYPE[opcode]
        rs2 = get_reg(operands[0], line_number)
        if operands[1] in REGISTERS:
            rs1 = get_reg(operands[1], line_number)
            imm = parse_imm(operands[2], line_number)
        else:
            imm = parse_imm(operands[1], line_number)
            rs1 = get_reg(operands[2], line_number)
        imm_bin = to_signed_bin(imm, 12, line_number)
        return imm_bin[0:7] + rs2 + rs1 + f3 + imm_bin[7:12] + oc

    if opcode in BTYPE:
        oc, f3 = BTYPE[opcode]
        rs1 = get_reg(operands[0], line_number)
        rs2 = get_reg(operands[1], line_number)
        if operands[2] in labels:
            imm = labels[operands[2]] - inst_pc
        else:
            imm = parse_imm(operands[2], line_number)
        imm_bin = to_signed_bin(imm, 13, line_number)
        b12   = imm_bin[0]
        b11   = imm_bin[1]
        b10_5 = imm_bin[2:8]
        b4_1  = imm_bin[8:12]
        return b12 + b10_5 + rs2 + rs1 + f3 + b4_1 + b11 + oc

    if opcode in UTYPE:
        oc = UTYPE[opcode]
        rd  = get_reg(operands[0], line_number)
        imm = parse_imm(operands[1], line_number)
        imm_bin = to_signed_bin(imm, 20, line_number)
        return imm_bin + rd + oc

    if opcode in JTYPE:
        oc = JTYPE[opcode]
        rd = get_reg(operands[0], line_number)
        if operands[1] in labels:
            imm = labels[operands[1]] - inst_pc
        else:
            imm = parse_imm(operands[1], line_number)
        imm_bin = to_signed_bin(imm, 21, line_number)
        b20    = imm_bin[0]
        b19_12 = imm_bin[1:9]
        b11    = imm_bin[9]
        b10_1  = imm_bin[10:20]
        return b20 + b10_1 + b11 + b19_12 + rd + oc

    print("Invalid Instruction:", opcode)
    sys.exit(1)

def is_virtual_halt(opcode, operands):
    if opcode != "beq" or len(operands) != 3:
        return False
    if operands[0] not in ("zero","x0") or operands[1] not in ("zero","x0"):
        return False
    try:
        val = int(operands[2], 16) if operands[2].lower().startswith("0x") else int(operands[2])
        return val == 0
    except ValueError:
        return False

def check_virtual_halt(parsed):
    if not parsed:
        print("Error: No instructions found")
        sys.exit(1)
    found = any(is_virtual_halt(i["opcode"], i["operands"]) for i in parsed)
    if not found:
        print("Error: Missing Virtual Halt instruction (beq zero,zero,0)")
        sys.exit(1)
    last = parsed[-1]
    if not is_virtual_halt(last["opcode"], last["operands"]):
        print("Error: Virtual Halt must be the last instruction at line", last["line"])
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: python Assembler.py <input.asm> <output.bin>")
        sys.exit(1)

    input_file  = sys.argv[1]
    output_file = sys.argv[2]

    read_assembly_file(input_file)
    parsed = parse_all()
    check_virtual_halt(parsed)

    binary_lines = []
    for inst in parsed:
        instruction = [inst["opcode"]] + inst["operands"]
        bits = registeropcodemapping(instruction, inst["pc"], inst["line"])
        binary_lines.append(bits)

    with open(output_file, "w") as f:
        for line in binary_lines:
            f.write(line + "\n")

main()
