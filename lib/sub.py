from multiprocessing import Process
import zmq

class subscriber():
    def __init__(self):
        self.sub = Process(target=self.create_sub)
        self.addr = 'tcp://127.0.0.1:5555'
        self.sub.start()

    def create_sub(self, topics):
        connect_to = self.addr
        zmq_ctx = zmq.Context()
        zmq_socket = zmq_ctx.socket(zmq.SUB)
        zmq_socket.connect(connect_to)
        # manage subscriptions
        if not topics:
            zmq_socket.setsockopt(zmq.SUBSCRIBE, b'')
        else:
            for t in topics:
                zmq_socket.setsockopt(zmq.SUBSCRIBE, t.encode('utf-8'))
        try:
            while True:
                topic, msg = zmq_socket.recv_multipart()
                print(f"Topic: {topic.decode('utf-8')}, msg:{msg.decode('utf-8')}")
        except KeyboardInterrupt:
            pass
