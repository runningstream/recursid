import multiprocessing as mp
from typing import List, Tuple, Dict, Any, Optional

from .modules.BaseModules import BaseModule
from .BaseFramework import BaseFramework

class MultiprocessFramework(BaseFramework):
    """
    MultiprocessFramework instantiates the framework with a separate process
    for each module and the framework base.
    """
    def start_module(self, mod: BaseModule, *args, **kwargs):
        send_obj_queue = mp.Queue()
        recv_obj_queue = mp.Queue()
        send_cmd_queue = mp.Queue()
        processing_lock = mp.Lock()
        module = mod(self.start_ttl, 
                send_obj_queue, recv_obj_queue, send_cmd_queue,
                processing_lock)
        proc = mp.Process(target=module.main, args=args, kwargs=kwargs,
                name="Process-{}".format(mod.__name__))
        proc.start()
        return {
                "module": mod,
                "process": proc,
                "send_queue": send_obj_queue,
                "recv_queue": recv_obj_queue,
                "cmd_queue": send_cmd_queue,
                "proc_lock": processing_lock,
                }
