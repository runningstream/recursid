import logging
from multiprocessing import Lock
from queue import Queue, Empty
import time
from typing import Optional, Iterable

from ..CommandQueueCommands import CQC_DIE, CQC_RES
from ..BaseObject import BaseObject

HANDLER_LOOP_SLEEP = .1

def command_queue_user(func):
    """
    Decorator for any commands that require processing of the command
    queue before they run
    """
    def internal(self, *args, **kwargs):
        self.handle_command_queue()
        return func(self, *args, **kwargs)
    return internal

class BaseModule:
    """
    Base class for the main module types - InputEndpointModule,
    OutputEndpointModule, ReemitterModule
    """
    # ReemitterModules and OutputEndpointModules must provide a list
    # of supported object classes here
    supported_objects = [BaseObject]

    def __init__(self, starting_ttl,
            recv_obj_queue: Queue,
            send_obj_queue: Queue,
            recv_cmd_queue: Queue,
            processing_lock: Lock):
        """
        recv_obj_queue:
            the queue via which the framework will send this module objects,
            and this module will receive them
        send_obj_queue:
            the queue via which this module will send the framework objects,
            and the framework will receive them
        recv_cmd_queue:
            the queue via which this module will receive commands
        processing_lock:
            A lock that is held whenever the module is processing data.
            When the framework needs to shutdown, it can hold this lock,
            causing modules to complete processing one object then stop before
            processing the next.  Then, if the input/output queues are empty,
            the framework can end without leaving things in the pipeline.

            Right now, this is not important for normal InputEndpointModules,
            because the framework only tries to exit elegantly when those
            modules have finished already.  This locking is built-in to
            modules using the handle_object interface.
        """
        self.recv_obj_queue = recv_obj_queue
        self.send_obj_queue = send_obj_queue
        self.recv_cmd_queue = recv_cmd_queue
        self.processing_lock = processing_lock

        self.CMD_HANDLERS = {
                CQC_DIE: self.command_die,
                CQC_RES: self.command_log_resources,
                }

        self.starting_ttl = starting_ttl
        self.time_to_die = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def command_log_resources(self) -> None:
        """
        Output, via logging, current resource usage, including queue sizes
        """
        self.logger.info("Queue sizes - recv obj {} send obj {} recv cmd {}"
                "".format(self.recv_obj_queue.qsize(),
                        self.send_obj_queue.qsize(),
                        self.recv_cmd_queue.qsize()
                        )
                )

    def command_die(self) -> None:
        """
        Command handler for the CQC_DIE command
        """
        self.time_to_die = True

    def handle_command_queue(self) -> None:
        """
        Handle all the commands received via the command queue.
        This should be called before doing anything relying on commands
        from the command queue.  It'll pull down the commands received,
        then run their appropriate handlers.  Handlers should be quick,
        probably just setting values on self for other functions to query.

        Use the @command_queue_user to automatically run this before
        a command querying function
        """
        while not self.recv_cmd_queue.empty():
            cmd = self.recv_cmd_queue.get(False)
            if cmd not in self.CMD_HANDLERS:
                self.logger.warn(
                        "Received cmd without handler: {}".format(cmd))
            else:
                self.CMD_HANDLERS[cmd]()

    @classmethod
    def can_handle_object(cls, obj: BaseObject) -> bool:
        for supported_cls in cls.supported_objects:
            if isinstance(obj, supported_cls):
                return True
        return False

    @command_queue_user
    def framework_still_running(self) -> bool:
        """
        Return True if we haven't received the die command yet
        """
        return not self.time_to_die

    def main(self, *args, **kwargs) -> None:
        """
        Override main with a function that contains your handler code,
        or handler loop
        ReemitterModule and OutputEndpointModule have default mains that
        call handle_object each time a new object is received
        """
        raise RuntimeError("Cannot call main on a base class")

class InputEndpointModule(BaseModule):
    """
    Base class for InputEndpointModules
    """
    def add_to_send_queue(self, obj: BaseObject) -> None:
        """
        Really only for the ReemitterInputEndpointModule...
        """
        self.send_obj_queue.put(obj)

    def emit(self, obj: BaseObject) -> None:
        """
        InputEndpointModules use emit to send an object to the framework
        """
        obj.ttl = self.starting_ttl
        obj.ancestors = ""
        self.add_to_send_queue(obj)
    
    @classmethod
    def can_handle_object(cls, *args, **kwargs) -> None:
        raise RuntimeError("Cannot call can_handle_object on "
                "InputEndpointModule")

class ReemitterModule(BaseModule):
    """
    Base class for ReemitterModules
    """
    def reemit(self, obj: BaseObject, parent: BaseObject) -> None:
        """
        ReemitterModules use reemit to send 
        obj: the object to emit
        parent: the object obj is based on
        """
        obj.ttl = parent.ttl-1
        obj.ancestors = str(parent)
        self.send_obj_queue.put(obj)

    def main(self, *args, **kwargs) -> None:
        """
        For ReemitterModules, by default, the main function calls
        handle_object on every object received.  The return value from
        handle_object should be an iterable - each object in the iterable
        gets reemitted
        """
        while self.framework_still_running():
            with self.processing_lock:
                while not self.recv_obj_queue.empty():
                    input_obj = self.recv_obj_queue.get()
                    new_objs = self.handle_object(input_obj, *args, **kwargs)
                    if new_objs:
                        [self.reemit(new_obj, input_obj)
                                for new_obj in new_objs]
            time.sleep(HANDLER_LOOP_SLEEP)

    def handle_object(self, input_obj: BaseObject, *args, **kwargs) \
            -> Iterable[BaseObject]:
        """
        handle_object gets called for every input object
        """
        raise RuntimeError("Attempted to execute handle_object on "
                "ReemitterModule base class")

class OutputEndpointModule(BaseModule):
    """
    Base class for OutputEndpointModules
    """
    def main(self, *args, **kwargs) -> None:
        """
        For OutputEndpointModule, by default, the main function calls
        handle_object on every object received.  The return value from
        handle_object should be None.
        """
        while self.framework_still_running():
            with self.processing_lock:
                while not self.recv_obj_queue.empty():
                    input_obj = self.recv_obj_queue.get()
                    new_objs = self.handle_object(input_obj, *args, **kwargs)
            time.sleep(HANDLER_LOOP_SLEEP)

    def handle_object(self, input_obj: BaseObject, *args, **kwargs) \
            -> Iterable[BaseObject]:
        """
        handle_object gets called for every input object
        """
        raise RuntimeError("Attempted to execute handle_object on "
                "OutputEndpointModule base class")
