import threading
from queue import Queue

class Threadpool:
    """Represents a group of working threads
    
    Attributes:
        num_threads (int)
        task_queue (Queue): a queue where the tasks to be executedare gathered
        active (bool): a flag that terminates the threads if it is False
        """
    def __init__(self, num_threads: int):
        self.num_threads: int = num_threads
        self.task_queue: Queue = Queue()
        for _ in range(num_threads):
            thread = threading.Thread(target=self.wait, args=())
            thread.start()

    def wait(self):
        """Implements the wait state of each working thread
        
        When a task is inserted, a thread is assigned to execute it
        """
        while True: 
            current_task = self.task_queue.get(block=True)
            
            if current_task == None:
                break

            [func, args, kwargs] = current_task
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(e)

    def add_task(self, func: "function", args=(), kwargs={}):
        """Add a task to be executed
        
        Args:
            func (function): the function to be executed
            args (tuple): its arguments
            kwargs (dict): its keyword arguments"""
        task = (func, args, kwargs)
        self.task_queue.put(task)

    def terminate(self):
        """Waits for the task queue to empty and then terminates the poolthread"""
        for _ in range(self.num_threads):
            self.task_queue.put(None)

if __name__ == "__main__":
    threadpool = Threadpool(4)
    
    i = 0
    while True:
        threadpool.add_task(print, (i, ))
        if i > 50:
            threadpool.terminate()
            break
        i += 1
    threadpool.add_task(print, (1, ))
    


