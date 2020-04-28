import time
import queue

import server

def test(send_queue, device_queue, signal_queue):
    time.sleep(10)
    signal_queue.put(1)
    print("Signal sent")



def main(send_queue:queue.Queue, device_queue:queue.Queue, signal_queue:queue.Queue):
    test(send_queue, device_queue, signal_queue)

if __name__ == "__main__":
    main(None, None, None)