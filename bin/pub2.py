#!/usr/bin/env python

import zmq
import itertools
import time
from multiprocessing import Process

class publisher():
    def __init__(self):
        self.pub = Process(target=self.create_pub)
        self.addr = 'tcp://127.0.0.1:5555'
        self.pub.start()

    def create_pub(self):
        bind_to = self.addr
        all_topics = [
            'actions', 'circle', 'conf_gen', 'executor',
            'fullscreen', 'menu', 'remember_focused',
            'scratchpad'
        ]
        zmq_socket = zmq.Context().socket(zmq.PUB)
        zmq_socket.bind(bind_to)
        print(f'{all_topics}')
        try:
            for topic in itertools.cycle(all_topics):
                msg_body = str(f"{topic}lol").encode('utf-8')
                print(f'Topic: {topic}, msg:{msg_body}')
                zmq_socket.send_multipart([topic.encode('utf-8'), msg_body])
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    pp = publisher()
