import unittest
import threading
import queue
import time
import sys

sys.path.append("./functions")

import windows

class Streamer:

    def __init__(self):
        self.buffer = queue.Queue(maxsize=2)

    def post(self, item):
        if self.buffer.full():
            #print("waiting")
            self.buffer.join()
        #print("post item")
        self.buffer.put(item)
        time.sleep(0.1)

    def stream(self):
        while True:
            try:
                yield self.buffer.get(timeout=1)
                self.buffer.task_done()
            except queue.Empty:
                return


class MyTestCase(unittest.TestCase):


    def test_streaming(self):
        streamer = Streamer()

        def post(count):
            for i in range(count):
                streamer.post("%d"%i)

        thread = threading.Thread(target=post,args=[9])
        thread.start()

        for w in windows.discrete_window_text(streamer.stream()):
            print(w)

        thread.join()



if __name__ == '__main__':
    unittest.main()
