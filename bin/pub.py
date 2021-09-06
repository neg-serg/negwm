#!/usr/bin/env python3

import zmq
import sys
from multiprocessing import Process

class pub():
    def __init__(self):
        self.pub = Process(target=self.create_pub)
        self.addr = 'tcp://127.0.0.1:5555'
        self.pub.start()

    def create_pub(self):
        topic = sys.argv[1]
        cmd = sys.argv[2]
        target = sys.argv[3]
        bind_to = self.addr
        zmq_socket = zmq.Context().socket(zmq.PUB)
        zmq_socket.bind(bind_to)
        try:
            msg_body = str(f"{topic} {cmd} {target}").encode('utf-8')
            print(f'Topic: {topic} msg:{msg_body}')
            zmq_socket.send_multipart([topic.encode('utf-8'), msg_body])
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    pp = pub()
