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
