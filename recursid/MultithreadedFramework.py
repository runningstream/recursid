import threading as thr
from queue import Queue
from typing import List, Tuple, Dict, Any, Optional

from .modules.BaseModules import BaseModule
from .BaseFramework import BaseFramework

class MultithreadedFramework(BaseFramework):
    """
    MultithreadedFramework instantiates the framework with a separate thread
    for each module and the framework base.
    """
    def start_module(self, mod: BaseModule, *args, **kwargs):
        send_obj_queue = Queue()
        recv_obj_queue = Queue()
        send_cmd_queue = Queue()
        processing_lock = thr.Lock()
        module = mod(self.start_ttl, 
                send_obj_queue, recv_obj_queue, send_cmd_queue,
                processing_lock)
        proc = thr.Thread(target=module.main, args=args, kwargs=kwargs,
                name="Thread-{}".format(mod.__name__))
        proc.start()
        return {
                "module": mod,
                "process": proc,
                "send_queue": send_obj_queue,
                "recv_queue": recv_obj_queue,
                "cmd_queue": send_cmd_queue,
                "proc_lock": processing_lock,
                }
