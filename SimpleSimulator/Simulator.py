from py_compile import main
import sys

MEMORY_BASE = 0x00010000
MEMORY_WORDS = 32
WORD_MASK = 0xFFFFFFFF
HALT = "00000000000000000000000001100011"
MAX_STEPS =   10**6
MAXS = 10**9

class SimulationError(Exception):
    def __init__(self, message, partial=None):
        super().__init__(message)
        self.partial =   partial or[]
def wrapToUnsigned32(val):

    
    return val  &   WORD_MASK
def interpretAsSigned32(val):
        val &= WORD_MASK
        return val - (1 << 32) if val & 0x80000000 else val

def stretchSignBits(val,  bits):
    sign = 1 <<  (bits - 1)
    return (val & (sign - 1)) - (val & sign)

def checkProgramValidity(program):
    if not program:
        raise SimulationError("Empty program")
    for i, line in enumerate(program):
        if len(line) != 32 or any(c not in '01' for c in line):
            raise SimulationError(f"Invalid instruction format at line {i+1}")


def prepareFreshMemory():
    return {MEMORY_BASE + i * 4: 0 for i in  range(MEMORY_WORDS)}

def addressLooksValid(addr):
    return addr % 4 == 0

def buildTraceLine(pc, regs):
    return " ".join([f"0b{pc:032b}"] + [f"0b{r:032b}" for r in regs]) + " \n"

def collectMemorySnapshot(mem):
    out = []
    for i in range(MEMORY_WORDS):
        addr = MEMORY_BASE + i * 4
        out.append(f"0x{addr:08X}:0b{mem.get(addr,0):032b}\n")
    return out

def runProgram(program):
    checkProgramValidity(program)

    regs = [0] * 32
    regs[2] = 380
    mem =prepareFreshMemory()
    pc = 0
    trace =[]
    steps  =  0

    instructions = [int(x, 2) for x in program]

    while True:
        if pc % 4 != 0:
            raise SimulationError(f"Misaligned PC: {pc}", trace)

        idx = pc // 4
        if not (0 <= idx < len(instructions)):
            break
        if steps > MAX_STEPS:
            raise SimulationError("Infinite loop detected", trace)
        try:
            inst = instructions[idx]
            raw = program[idx]
            opcode = inst & 0x7F
            rd = (inst >> 7) & 0x1F
            funct3 = (inst >> 12) & 0x7
            rs1 = (inst >> 15) & 0x1F
            rs2 = (inst >> 20) & 0x1F
            funct7 = (inst >> 25) & 0x7F

            next_pc = pc  +  4


            if opcode == 0x33:
                a = regs[rs1]
                b = regs[rs2]

                if funct3 == 0x0:
                    val = a + b if funct7 == 0x00 else a - b
                elif funct3 == 0x1:
                    val = a << (b & 0x1F)
                elif funct3 == 0x2:
                    val = 1 if interpretAsSigned32(a) < interpretAsSigned32(b) else 0
                elif funct3 == 0x3:
                    val = 1 if a < b else 0
                elif funct3 == 0x4:
                    val = a ^ b
                elif funct3 == 0x5:
                    val = (interpretAsSigned32(a) >> (b & 0x1F)) if funct7 == 0x20 else (a >> (b & 0x1F))
                elif funct3 == 0x6:
                    val = a | b
                elif funct3 == 0x7:
                    val = a & b
                else:
                    raise SimulationError("Unsupported R-type", trace)


                if rd != 0:
                    regs[rd] = wrapToUnsigned32(val)

            elif opcode == 0x13:
                imm = stretchSignBits((inst >> 20) & 0xFFF, 12)

                if funct3 == 0x0:  # ADDI
                    val =regs[rs1] +  imm
                elif funct3 == 0x7:  # ANDI
                    val = regs[rs1] & imm
                elif funct3 == 0x6:  # ori
                    val = regs[rs1] | imm
                elif funct3 == 0x4:  # XORI
                    val = regs[rs1] ^ imm
                elif funct3 == 0x2:  # SLTI
                    val = 1 if interpretAsSigned32(regs[rs1]) < imm else 0
                elif funct3 == 0x3:  # SLTIU
                    val = 1 if regs[rs1] < (imm & WORD_MASK) else 0
                else:
                    raise SimulationError("Unsupported I-type", trace)

                if rd != 0:
                    regs[rd] = wrapToUnsigned32(val)
            elif opcode == 0x03:
                imm = stretchSignBits((inst >> 20) & 0xFFF, 12)
                addr = wrapToUnsigned32(regs[rs1] + imm)

                if not addressLooksValid(addr):
                    raise SimulationError(f"Unaligned load at {addr}", trace)
                if rd != 0:
                    regs[rd] = mem.get(addr, 0)
            elif opcode == 0x23:
                imm = ((inst >> 25) << 5) | ((inst >> 7) & 0x1F)
                imm = stretchSignBits(imm, 12)
                addr = wrapToUnsigned32(regs[rs1] + imm)

                if not addressLooksValid(addr):
                    raise  SimulationError(f"Unaligned store at {addr}", trace)
                mem[addr] =  regs[rs2]
            elif opcode == 0x63:
                imm = ((inst >> 31) << 12) | (((inst >> 7) & 1) << 11) | (((inst >> 25) & 0x3F) << 5) | (((inst >> 8) & 0xF) << 1)
                imm = stretchSignBits(imm, 13)

                a = regs[rs1]
                b = regs[rs2]
                take = False
                if funct3 == 0x0: take = (a == b)
                elif funct3 == 0x1: take = (a != b)
                elif funct3 == 0x4: take = interpretAsSigned32(a) < interpretAsSigned32(b)
                elif funct3 == 0x5: take = interpretAsSigned32(a) >= interpretAsSigned32(b)
                elif funct3 == 0x6: take = a < b
                elif funct3 == 0x7: take = a >= b
                else:
                    raise SimulationError("Unsupported branch", trace)
                if take:
                    next_pc = pc +  imm
            elif opcode == 0x6F:
                imm = ((inst >> 31) << 20) | (((inst >> 12) & 0xFF) << 12) | (((inst >> 20) & 1) << 11) | (((inst >> 21) & 0x3FF) << 1)
                imm = stretchSignBits(imm, 21)

                if rd !=0:
                    regs[rd] = wrapToUnsigned32(pc + 4)
                next_pc = pc + imm
            elif opcode == 0x67:
                imm = stretchSignBits((inst >> 20) & 0xFFF, 12)
                target = (regs[rs1] + imm) & ~1

                if rd != 0:
                    regs[rd] = wrapToUnsigned32(pc + 4)

                next_pc = wrapToUnsigned32(target)
            elif opcode == 0x37:  # LUI
                if rd != 0:
                    regs[rd] = inst & 0xFFFFF000

            elif opcode == 0x17:  # AUIPC
                if rd != 0:
                    regs[rd] = wrapToUnsigned32(pc + (inst & 0xFFFFF000))
 
            else:
                raise SimulationError("Unsupported oPcode", trace)

            regs[0] =   0
            pc = wrapToUnsigned32(next_pc)
            trace.append(buildTraceLine(pc, regs))
            if raw ==  HALT:
                break
            steps = steps + 1
        except SimulationError:
            raise
        except Exception as e:
            raise SimulationError(str(e), trace)

    trace.extend(collectMemorySnapshot(mem))
    return trace
def main():

    if len(sys.argv) < 3:
        print("usage: python sim.py input.txt output.txt")
        return
    try:
        with open(sys.argv[1]) as f:
            program = [line.strip() for line in f if line.strip()]
    except:
        print("error: Cannot read input file")

        return

    try:
        output = runProgram(program)
        with open(sys.argv[2], "w") as f:
            f.writelines(output)
    except SimulationError as e:
        if e.partial:
            with open(sys.argv[2], "w") as f:
                f.writelines(e.partial)
        print("Simulation Error:", e)
if __name__ == "__main__":
    main()
