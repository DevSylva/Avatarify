Skip to content
Search or jump to…

Pull requests
Issues
Marketplace
Explore
 
@KKiohd 
Learn Git and GitHub without any code!
Using the Hello World guide, you’ll start a branch, write comments, and open a pull request.


mynameisfiber
/
avatarify
forked from alievk/avatarify
0
01.2k
Code
Pull requests
Actions
Projects
Wiki
Security
Insights
avatarify/predictor_remote.py /
@mynameisfiber
mynameisfiber reduce communications overhead and add compression flag
Latest commit 69dac33 on 19 Apr
 History
 1 contributor
88 lines (71 sloc)  2.5 KB
  
from predictor_local import PredictorLocal
from arguments import opt

import zmq
import blosc
import msgpack
import msgpack_numpy as m
m.patch()


DEFAULT_PORT = 5556


if opt.compress:
    def pack_message(msg):
        return blosc.compress(msgpack.packb(msg), typesize=8)
    
    def unpack_message(msg):
        return msgpack.unpackb(blosc.decompress(msg))
else:
    def pack_message(msg):
        return msgpack.packb(msg)
    
    def unpack_message(msg):
        return msgpack.unpackb(msg)


class PredictorRemote:
    def __init__(self, *args, worker_host='localhost', worker_port=DEFAULT_PORT, **kwargs):
        self.worker_host = worker_host
        self.worker_port = worker_port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect(f"tcp://{worker_host}:{worker_port}")
        print(f"Connected to {worker_host}:{worker_port}")
        self.predictor_args = (args, kwargs)
        self.init_worker()

    def init_worker(self):
        msg = (
            '__init__',
            *self.predictor_args,
        )
        return self._send_recv_msg(msg)

    def __getattr__(self, item):
        return lambda *args, **kwargs: self._send_recv_msg((item, args, kwargs))

    def _send_recv_msg(self, msg):
        self.socket.send(pack_message(msg), copy=False)
        response = self.socket.recv()
        return unpack_message(response)


def message_handler(port):
    print("Creating socket")
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.bind("tcp://*:%s" % port)
    predictor = None
    predictor_args = ()

    print("Listening for messages on port:", port)
    while True:
        msg_raw = socket.recv()
        try:
            msg = unpack_message(msg_raw)
        except ValueError:
            print("Invalid Message")
            continue
        method = msg[0]
        if method == "__init__":
            predictor_args_new = msg[1:]
            if predictor_args_new == predictor_args:
                print("Same config as before... reusing previous predictor")
            else:
                del predictor
                predictor_args = predictor_args_new
                predictor = PredictorLocal(*predictor_args[0], **predictor_args[1])
                print("Initialized predictor with:", predictor_args)
            result = True
        else:
            result = getattr(predictor, method)(*msg[1], **msg[2])
        socket.send(pack_message(result), copy=False)


def run_worker(port):
    message_handler(port)
© 2020 GitHub, Inc.
Terms
Privacy
Security
Status
Help
Contact GitHub
Pricing
API
Training
Blog
About
