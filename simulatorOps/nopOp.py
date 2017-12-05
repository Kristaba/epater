import operator
import struct
from enum import Enum
from collections import defaultdict, namedtuple, deque 

import simulatorOps.utils as utils
from simulatorOps.abstractOp import AbstractOp, ExecutionException

class NopOp(AbstractOp):
    saveStateKeys = frozenset(("condition",))

    def __init__(self):
        super().__init__()
        self._type = utils.InstrType.swap

    def decode(self):
        instrInt = self.instrInt
        if not (utils.checkMask(instrInt, (25, 24, 21), (27, 26, 23, 22, 20, 19, 18, 17, 16))):
            raise ExecutionException("masque de décodage invalide pour une instruction de type NOP", 
                                        internalError=True)

        # Retrieve the condition field
        self._decodeCondition()
        
        # Nothing to do, it's a NOP...

    def explain(self, simulatorContext):
        bank = simulatorContext.regs.mode
        simulatorContext.regs.deactivateBreakpoints()
        
        self._nextInstrAddr = -1
        
        disassembly = ""
        description = "<ol>\n"
        disCond, descCond = self._explainCondition()
        description += descCond

        disassembly = "NOP" + disCond
        description += "<li>Ne rien faire</li><li>Nonon, vraiment, juste rien</li>"

        description += "</ol>"
        simulatorContext.regs.reactivateBreakpoints()
        return disassembly, description
    
    def execute(self, simulatorContext):
        # Whatever happens, a NOP instruction does nothing
        return
