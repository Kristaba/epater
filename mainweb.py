import argparse
import time
import math
import asyncio
import json
import collections
from itertools import repeat

import websockets

from assembler import parse as ASMparser
from bytecodeinterpreter import BCInterpreter
from procsimulator import Simulator


interpreters = {}
connected = set()


async def producer(data_list):
    # Simuler des interruptions externes
    while True:
        await asyncio.sleep(0.1)
        if data_list:
            return json.dumps(data_list.pop(0))


async def handler(websocket, path):
    print("User {} connected.".format(websocket))
    connected.add(websocket)
    to_send = []
    received = []
    try:
        while True:
            if not websocket.open:
                break
            listener_task = asyncio.ensure_future(websocket.recv())
            producer_task = asyncio.ensure_future(producer(to_send))
            done, pending = await asyncio.wait(
                [listener_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED)

            if listener_task in done:
                try:
                    message = listener_task.result()
                except websockets.exceptions.ConnectionClosed:
                    break
                if message:
                    received.append(message)
            else:
                listener_task.cancel()

            if producer_task in done:
                message = producer_task.result()
                await websocket.send(message)
            else:
                producer_task.cancel()

            # TODO: Try là-dessus?
            data = process(websocket, received)
            if data:
                to_send.extend(data)
    finally:
        if websocket in interpreters:
            del interpreters[websocket]
        connected.remove(websocket)
        print("User {} disconnected.".format(websocket))


def process(ws, msg_in):
    """
    Output: List of messages to send.
    """
    retval = []
    for msg in msg_in:
        data = json.loads(msg)
        if data[0] == 'assemble':
            # TODO: Afficher les erreurs à l'écran
            bytecode, bcinfos = ASMparser(data[1].split("\n"))
            interpreters[ws] = BCInterpreter(bytecode, bcinfos)

            # TODO: Reset interface
            # Memory View
            cols = {"c{}".format(i): "00" for i in range(9)}
            vallist = []
            for i in range(10):
                vallist.append({"id": i, "values": cols})
            retval.append(["mem", vallist])
        elif data[0] == 'stepinto':
            interpreters[ws].stepinto()
        elif data[0] == 'stepforward':
            pass
        elif data[0] == 'stepout':
            pass
        elif data[0] == 'reset':
            interpreters[ws].reset()
        elif data[0] == 'setbreakinst':
            pass
        elif data[0] == 'setbreakmem':
            pass
        elif data[0] == 'run':
            pass
        elif data[0] == 'animate':
            # Faire step into à chaque intervalle
            pass
        elif data[0] == 'update':
            pass
        elif data[0] == 'breakpoints':
            pass
        else:
            print("Unknown message: ", data)
    del msg_in[:]
    return retval


if __name__ == '__main__':
    start_server = websockets.serve(handler, '127.0.0.1', 31415)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()