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
    file = open(filename, "r")
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
                sys.exit()

            labels[label] = pc

            if len(parts) > 1:
                line = parts[1].strip()
            else:
                line = ""

            if line== "":
                line_number += 1
                continue
        instructions.append((pc, line, line_number))

        pc += 4
        line_number += 1
def parse_instruction(line,line_number):

    line = line.replace(","," ")
    line = line.replace("("," ")
    line = line.replace(")"," ")

    parts = line.split()

    opcode = parts[0]

    operands = parts[1:]

    return opcode,operands


def parse_all():

    parsed = []

    for item in instructions:

        apc = item[0]
        line = item[1]
        line_number = item[2]

        opcode,operands = parse_instruction(line,line_number)

        parsed.append({
            "pc":apc,
            "opcode":opcode,
            "operands":operands,
            "line":line_number
        })

    return parsed
def registeropcodemapping(inst):
    #registermapping
    registerset1={"zero":"00000","ra":"00001","sp":"00010","gp":"00011","tp":"00100"}
    temporary={"t0":"00101","t1":"00110","t2":"00111","t3":"11100","t4":"11101","t5":"11110","t6":"11111"}
    argument={"a0":"01010","a1":"01011","a2":"01100","a3":"01101","a4":"01110","a5":"01111","a6":"10000","a7":"10001"}
    savedregister={"s0":"01000","s1":"01001","s2":"10010","s3":"10011","s4":"10100","s5":"10101","s6":"10110","s7":"10111","s8":"11000","s9":"11001","s10":"11010","s11":"11011"}

    #opcodefuct3funct7mapping
    rtype = {
    "add":{"opcode":"0110011","funct3":"000","funct7":"0000000"},
    "sub":{"opcode":"0110011","funct3":"000","funct7":"0100000"},
    "sll":{"opcode":"0110011","funct3":"001","funct7":"0000000"},
    "slt":{"opcode":"0110011","funct3":"010","funct7":"0000000"},
    "sltu":{"opcode":"0110011","funct3":"011","funct7":"0000000"},
    "xor":{"opcode":"0110011","funct3":"100","funct7":"0000000"},
    "srl":{"opcode":"0110011","funct3":"101","funct7":"0000000"},
    "or":{"opcode":"0110011","funct3":"110","funct7":"0000000"},
    "and":{"opcode":"0110011","funct3":"111","funct7":"0000000"} 
    }

    itype = {
    "lw":{"opcode":"0000011","funct3":"010"},
    "addi":{"opcode":"0010011","funct3":"000"},
    "sltiu":{"opcode":"0010011","funct3":"011"},
    "jalr":{"opcode":"1100111","funct3":"000"}
    }

    stype = {"sw":{"opcode":"0100011","funct3":"010"}}

    btype = {
    "beq":{"opcode":"1100011","funct3":"000"},
    "bne":{"opcode":"1100011","funct3":"001"},
    "blt":{"opcode":"1100011","funct3":"100"},
    "bge":{"opcode":"1100011","funct3":"101"},
    "bltu":{"opcode":"1100011","funct3":"110"},
    "bgeu":{"opcode":"1100011","funct3":"111"}
    }

    utype = {
    "lui":{"opcode":"0110111"},
    "auipc":{"opcode":"0010111"}
    }

    jtype = {"jal":{"opcode":"1101111"}}

    instruction = inst[0]

    main={}
    if instruction in rtype:
        main = rtype[instruction]
    elif instruction in itype:
        main = itype[instruction]
    elif instruction in stype:
        main = stype[instruction]
    elif instruction in btype:
        main = btype[instruction]
    elif instruction in utype:
        main = utype[instruction]
    elif instruction in jtype:
        main = jtype[instruction]
    else:
        print("Invalid Instruction")
        return

    opcode = main["opcode"]
    funct3 = main.get("funct3","")
    funct7 = main.get("funct7","")

    registers=[]
    immediate=0

    for i in inst[1:]:

        if i in registerset1:
            registers.append(registerset1[i])

        elif i in temporary:
            registers.append(temporary[i])

        elif i in argument:
            registers.append(argument[i])

        elif i in savedregister:
            registers.append(savedregister[i])

        else:
            try:
                immediate = immediate + int(i)
            except:
                print("Error: Invalid operand", i)
                sys.exit()

    return opcode,funct3,funct7,registers,immediate

def to_signed_bin(value,bits):

    if value < 0:
        value = value + (1 << bits)

    val = value & ((1 << bits) - 1)

    return format(val, '0' + str(bits) + 'b')


def encode_instruction(opcode,funct3,funct7,registers,immediate,current_pc,line_number):

    opcode_lookup={
    "0110011":"rtype",
    "0000011":"itype","0010011":"itype","1100111":"itype",
    "0100011":"stype",
    "1100011":"btype",
    "0110111":"utype","0010111":"utype",
    "1101111":"jtype"
    }

    kind = opcode_lookup.get(opcode,"")

    if kind == "rtype":

        rd  = registers[0]
        rs1 = registers[1]
        rs2 = registers[2]

        return funct7 + rs2 + rs1 + funct3 + rd + opcode

    elif kind == "itype":

        rd  = registers[0]
        rs1 = registers[1]

        imm_bits = to_signed_bin(immediate,12)

        return imm_bits + rs1 + funct3 + rd + opcode

    elif kind == "stype":

        rs2 = registers[0]
        rs1 = registers[1]

        imm_bits = to_signed_bin(immediate,12)

        return imm_bits[0:7] + rs2 + rs1 + funct3 + imm_bits[7:12] + opcode

    elif kind == "btype":

        rs1 = registers[0]
        rs2 = registers[1]

        imm_bits = to_signed_bin(immediate >> 1,13)

        return imm_bits[0] + imm_bits[2:8] + rs2 + rs1 + funct3 + imm_bits[8:12] + imm_bits[1] + opcode

    elif kind=="utype":

        rd = registers[0]

        imm_bits = to_signed_bin(immediate,32)

        return imm_bits[0:20] + rd + opcode

    elif kind =="jtype":

        rd = registers[0]

        imm_bits = to_signed_bin(immediate >> 1,21)

        return imm_bits[0] + imm_bits[10:20] + imm_bits[9] + imm_bits[1:9] + rd + opcode


