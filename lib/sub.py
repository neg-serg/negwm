from multiprocessing import Process
import zmq

class sub():
    def __init__(self):
        self.addr = 'tcp://127.0.0.1:5555'
        self.topic = self.__class__.__name__
        self.sub = Process(target=self.create_sub)
        self.sub.start()

    def create_sub(self):
        zmq_ctx = zmq.Context()
        zmq_socket = zmq_ctx.socket(zmq.SUB)
        zmq_socket.connect(self.addr)
        zmq_socket.setsockopt(
            zmq.SUBSCRIBE, self.topic.encode('utf-8')
        )
        try:
            print(f'Begin to listen for {self.topic}')
            while True:
                topic, msg = zmq_socket.recv_multipart()
                print(f"Topic {topic.decode('utf-8')}, msg {msg.decode('utf-8')}")
        except KeyboardInterrupt:
            pass
