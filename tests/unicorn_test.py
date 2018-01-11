
import unicorn
import unicorn.arm_const as ARM

import argparse
import time
import math
import sys

sys.path.append("..")
from assembler import parse as ASMparser
from bytecodeinterpreter import BCInterpreter
from procsimulator import Simulator


CODE_START_ADDR = 0x100000
regs_arm = [ARM.UC_ARM_REG_R0, ARM.UC_ARM_REG_R1, ARM.UC_ARM_REG_R2, ARM.UC_ARM_REG_R3,
            ARM.UC_ARM_REG_R4, ARM.UC_ARM_REG_R5, ARM.UC_ARM_REG_R6, ARM.UC_ARM_REG_R7,
            ARM.UC_ARM_REG_R8, ARM.UC_ARM_REG_R9, ARM.UC_ARM_REG_R10, ARM.UC_ARM_REG_R11,
            ARM.UC_ARM_REG_R12, ARM.UC_ARM_REG_R13, ARM.UC_ARM_REG_R14, ARM.UC_ARM_REG_R15]

class Context:
    mode2bits = {'User': 16, 'FIQ': 17, 'IRQ': 18, 'SVC': 19}       # Other modes are not supported
    bits2mode = {v:k for k,v in mode2bits.items()}
    
    def __init__(self, type_, sim, lengths):
        self.regs = [0 for i in range(16)]
        self.cpsr = 0
        self.spsr = None
        self.mem = None
        self.lengths = lengths
        self.sim = sim
        self.type = type_

        self.reason = {}

    def __eq__(self, other):
        self.reason = {}
        if self.regs != other.regs:
            self.reason["regs"] = [(i, self.regs[i], other.regs[i]) for i in range(16) if self.regs[i] != other.regs[i]]
        if self.cpsr != other.cpsr:
            self.reason["status"] = ("CPSR", self.cpsr, other.cpsr)
        if self.spsr != other.spsr:
            self.reason["status"] = ("SPSR", self.spsr, other.spsr)
        if self.mem != other.mem:
            self.reason["mem"] = 0
            
        if len(self.reason) > 0:
            return False
        return True

    def update(self):
        if self.type == "qemu":
            self.from_qemu()
        else:
            self.from_simulator()

    def from_qemu(self):
        self.regs = [self.sim.reg_read(reg) for reg in regs_arm]
        self.cpsr = self.sim.reg_read(ARM.UC_ARM_REG_CPSR)
        self.spsr = self.sim.reg_read(ARM.UC_ARM_REG_SPSR)
        self.mem = {"INTVEC": self.sim.mem_read(CODE_START_ADDR, self.lengths["INTVEC"]),
                    "CODE": self.sim.mem_read(CODE_START_ADDR + 0x80, self.lengths["CODE"]),
                    "DATA": self.sim.mem_read(CODE_START_ADDR + 4096, self.lengths["DATA"])}

    def from_simulator(self):
        self.regsStr = self.sim.getRegisters()['User']
        self.regs = []
        for i in range(16):
            self.regs.append(self.regsStr["R"+str(i)])
        self.regs[15] -= 8
        self.cpsr = self.sim.sim.regs.getCPSR().val
        self.spsr = 0 # self.sim.sim.regs.getSPSR()
        self.mem = {"INTVEC": self.sim.sim.mem.data["INTVEC"],
                    "CODE": self.sim.sim.mem.data["CODE"],
                    "DATA": self.sim.sim.mem.data["DATA"]}

    def __str__(self):
        s = " " + "_"*88 + " " + "\n"
        if self.type == "qemu":
            s += "|{:^88}|".format("QEMU REFERENCE EMULATOR") + "\n"
        else:
            s += "|{:^88}|".format("EPATER EMULATOR") + "\n"
        s += "|" + "-"*88 + "|" + "\n"
        s += "| " + " |".join(["{:^9}".format("R"+str(i)) for i in range(8)]) + " |" + "\n"
        s += "| " + " |".join(["{:>9}".format(self.regs[i]) for i in range(8)]) + " |" + "\n"
        s += "| " + " |".join(["{:>9}".format(hex(self.regs[i])) for i in range(8)]) + " |" + "\n"
        s += "|" + "-"*88 + "|" + "\n"
        s += "| " + " |".join(["{:^9}".format("R"+str(i)) for i in range(8, 16)]) + " |" + "\n"
        s += "| " + " |".join(["{:>9}".format(self.regs[i]) for i in range(8,16)]) + " |" + "\n"
        s += "| " + " |".join(["{:>9}".format(hex(self.regs[i])) for i in range(8,16)]) + " |" + "\n"
        s += "|" + "-"*88 + "|" + "\n"
        cpsr = "| CPSR : {} (N={}, Z={}, C={}, V={}) / Mode = {}".format(hex(self.cpsr), 
                                                                        int(self.cpsr>>31), 
                                                                        int(self.cpsr>>30&0x1), 
                                                                        int(self.cpsr>>29&0x1), 
                                                                        int(self.cpsr>>28&0x1),
                                                                        self.bits2mode[self.cpsr & 0x1F])
        s += "{:<89}".format(cpsr) + "|\n"
        s += "|" + "-"*88 + "|" + "\n"
        return s


def concatenateReports(r1, r2):
    r = ""
    for l1, l2 in zip(r1.split("\n"), r2.split("\n")):
        r += l1 + "   " + l2 + "\n"
    return r

def initializeQemu(machine):
    for reg in regs_arm[:-1]:     # Not the last, because we want to preserve the value of PC!
        machine.reg_write(reg, 0)
    machine.reg_write(ARM.UC_ARM_REG_CPSR, 0x10)        # User-mode



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='EPATER simulator test suite')
    parser.add_argument('inputfile', help="Fichier assembleur")
    parser.add_argument('-c', "--count", default=10, type=int, help="Number of steps")
    args = parser.parse_args()

    with open(args.inputfile) as f:
        bytecode, bcinfos, assertInfos, errors, _ = ASMparser(f, memLayout="test")
    
    # Setting up the QEMU reference ARM simulator
    armRef = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)

    armRef.mem_map(CODE_START_ADDR, 1024*(4 + 2 + 1))       # 4 KB for code, 2 KB for data, 1 KB buffer (just in case)
    contiguousMem = bytearray([0]) * (1024*(4 + 2))
    contiguousMem[0:len(bytecode['INTVEC'])] = bytecode['INTVEC']
    contiguousMem[0x80:0x80+len(bytecode['CODE'])] = bytecode['CODE']
    contiguousMem[4096:4096+len(bytecode['DATA'])] = bytecode['DATA']
    armRef.mem_write(CODE_START_ADDR, bytes(contiguousMem))
    initializeQemu(armRef)

    # Setting up epater simulator
    armEpater = BCInterpreter(bytecode, bcinfos, assertInfos)
    armEpater.setRegisters({15: CODE_START_ADDR+8})      # Set PC at the entrypoint
    armEpater.sim.fetchAndDecode()                       # Fetch the first instruction

    memLengths = {"INTVEC": len(bytecode['INTVEC']), "CODE": len(bytecode['CODE']), "DATA": len(bytecode['DATA'])}
    contextRef = Context("qemu", armRef, memLengths)
    contextEpater = Context("epater", armEpater, memLengths)

    cycle = 0
    pcRef = CODE_START_ADDR
    while cycle < args.count:
        # One step on the reference emulator
        armRef.emu_start(pcRef, CODE_START_ADDR+4096, count=1)
        pcRef = armRef.reg_read(ARM.UC_ARM_REG_R15)

        # One step on epater
        armEpater.step("into")

        # Update contexts
        contextRef.update()
        contextEpater.update()

        if contextRef != contextEpater:
            print(concatenateReports(str(contextRef), str(contextEpater)))
            print(contextRef.reason)
        cycle += 1
    
