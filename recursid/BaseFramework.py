import itertools as it
import logging
import time
import multiprocessing as mp
import threading as thr
from queue import Queue
from typing import List, Tuple, Dict, Any, Optional, Union

from .CommandQueueCommands import DIE as CQC_DIE
from .BuiltinObjects import DeathLog
from .modules.BuiltinInputEndpointModules import ReemitInputEndpointModule
from .modules import all_iems, all_rems, all_oems
from .modules.BaseModules import BaseModule

DEFAULT_START_TTL = 5
PROCESSING_LOOP_SLEEP = .1

class BaseFramework:
    """
    BaseFramework instantiates the framework with a separate thread
    for each module and the framework base.

    Properties that get defined on this instance are:
    self.iems: List[
                Dict[str,
                  Union[InputEndpointModule, mp.Process, thr.Thread, Queue,
                            Queue, Queue]
                    ]
                ]
    self.rems: List[
                Dict[str,
                  Union[ReemitterModule, mp.Process, thr.Thread, Queue,
                            Queue, Queue]
                    ]
                ]
    self.oems: List[
                Dict[str,
                  Union[OutputEndpointModule, mp.Process, thr.Thread, Queue,
                            Queue, Queue]
                    ]
                ]
    self.reemitter: 
                Dict[str,
                  Union[OutputEndpointModule, mp.Process, thr.Thread, Queue,
                            Queue, Queue]
                    ]
    """
    def __init__(self,
            iems: List[Tuple[str, Dict[str, Any]]],
            rems: List[Tuple[str, Dict[str, Any]]],
            oems: List[Tuple[str, Dict[str, Any]]],
            start_ttl: Optional[int] = None,
            ):
        """
        iems, rems, and oems:
            Each is a list of 2-tuples specifying the name of a module
            followed by a dictionary of keyword arguments for it.
            iems, rems, oems specify InputEndpointModules,
            ReemitterModules, and OutputEndpointModules respectively
        start_ttl:
            The maximum times an object may be reemitted after initial ingest
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.start_ttl = start_ttl if start_ttl is not None else \
                DEFAULT_START_TTL

        # Recover the actual module classes from each module name
        # Errors will be raised here if a module doesn't exist/isn't registed
        try:
            iem_mods = [(all_iems[mod_name], kwargs)
                    for mod_name, kwargs in iems]
        except KeyError as e:
            self.logger.critical("Input endpoint module not found: {}"
                    "".format(e))
            exit(1)

        try:
            rem_mods = [(all_rems[mod_name], kwargs)
                    for mod_name, kwargs in rems]
        except KeyError as e:
            self.logger.critical("Reemiter module not found: {}"
                    "".format(e))
            exit(1)

        try:
            oem_mods = [(all_oems[mod_name], kwargs)
                    for mod_name, kwargs in oems]
        except KeyError as e:
            self.logger.critical("Output endpoint module not found: {}"
                    "".format(e))
            exit(1)

        # Now that config is parsed a bit, start up the modules
        self.iems = []
        self.rems = []
        self.oems = []
        self.reemitter = None
        try:
            self.reemitter = self.start_module(ReemitInputEndpointModule)

            # Start each module with its args, and setup the structures needed
            self.iems = [self.start_module(mod, **kwargs)
                    for mod, kwargs in iem_mods]
            self.rems = [self.start_module(mod, **kwargs)
                    for mod, kwargs in rem_mods]
            self.oems = [self.start_module(mod, **kwargs)
                    for mod, kwargs in oem_mods]
        except:
            # If modules errored out, kill them all and die
            for em in it.chain(self.iems, self.rems, self.oems,
                    [self.reemitter]):
                try:
                    em["process"].kill()
                except BaseException as e:
                    self.logger.error("Exception when killing all modules "
                            "after startup error:")
                    self.logger.exception(e)
            raise

        self.time_to_die = False

    def start_module(self, mod: BaseModule, *args, **kwargs) -> \
            Dict[str, Union[BaseModule, mp.Process, thr.Thread,
                mp.Queue, Queue, mp.Lock, thr.Lock]]:
        raise RuntimeError("Tried to run start_module on framework base")

    def __command_death(self, modules):
        for em in modules:
            em["cmd_queue"].put(CQC_DIE)

    def command_die(self) -> None:
        """
        Tell all modules to die, and command this base to die
        """
        self.time_to_die = True
        self.__command_death(
                it.chain(self.iems, self.rems, self.oems, [self.reemitter])
                )

    def command_iems_to_die(self) -> None:
        """
        Tell just the iems to die
        """
        self.__command_death(self.iems)

    def main(self) -> None:
        """
        Continuously loop, handling objects, until death
        After death, join all the modules
        """
        iems_still_available = True
        while iems_still_available and not self.time_to_die:
            objs_handled_last_time = True
            while objs_handled_last_time:
                objs_handled_last_time = self.processing_iteration()
            time.sleep(PROCESSING_LOOP_SLEEP)

            # If all the iems have exited, it's time to die
            iems_live = (iem["process"].is_alive() for iem in self.iems)
            if not any(iems_live):
                self.logger.debug("All IEMs found dead")
                iems_still_available = False

        # Tell any remaining iems to die - for instance, if we initiated
        # shutdown for any reason other than all the iems dying
        self.logger.debug("Commanding IEMs to die")
        self.command_iems_to_die()

        # Before dying, we need to have no modules processing data and
        # all queues empty, or data will die in the pipeline prematurely
        queues_empty = False
        while not queues_empty:
            # Hold the lock on all modules - modules only release the
            # lock when they're not processing, so this essentially
            # waits until all processing is stopped
            rem_oem_reem_locks = [em["proc_lock"]
                    for em in it.chain(self.rems, self.oems, [self.reemitter])]
            self.logger.debug(
                    "Attempting to hold REM OEM REEM locks for shutdown")
            [lock.acquire() for lock in rem_oem_reem_locks]

            # Then, see if all the queues are empty
            # Only check queues for alive modules, because dead modules, 
            # like those that crashed, can never empty their queues
            self.logger.debug("Looking for any data in queues")
            queues = ((em["send_queue"], em["recv_queue"])
                    for em in it.chain(self.rems, self.oems, [self.reemitter])
                    if em["process"].is_alive())
            if all(queue.empty() for queue in it.chain.from_iterable(queues)):
                break

            self.logger.debug("Releasing REM OEM REEM locks for another "
                    "go-round")
            [lock.release() for lock in rem_oem_reem_locks]

            # Do another processing iteration to hopefully wrap things up
            objs_handled_last_time = self.processing_iteration()
            # Let the locks try to get picked up...
            time.sleep(.1)

        self.command_die()
        self.logger.debug("Releasing REM OEM REEM locks for death")
        [lock.release() for lock in rem_oem_reem_locks]

        # At the end of the program, join all the modules
        for em in it.chain(self.iems, self.rems, self.oems, [self.reemitter]):
            em["process"].join()

        self.logger.debug("Framework has died gracefully")

    def processing_iteration(self) -> bool:
        """
        Run one round of reading from the sources and sending to the sinks
        returns: True if any objects were handled
        """
        some_object_handled = False
        # Check each InputEndpointModules for one input object
        iem_recv = (iem["recv_queue"]
                for iem in (self.iems + [self.reemitter])
                )
        iem_inputs = (queue.get()
                for queue in iem_recv if not queue.empty()
                )
        # Send any input objects to all supporting Reemitter & OutputEndpoints
        for obj in iem_inputs:
            some_object_handled = True
            this_object_handled = False
            if obj.ttl < 0:
                """
                self.logger.debug("Object died from low TTL: {}".format(obj))
                """
                obj = DeathLog(obj)
                self.reemitter["send_queue"].put(obj)
                continue

            for em in it.chain(self.rems, self.oems):
                if em["module"].can_handle_object(obj):
                    """
                    self.logger.debug(
                            "Object had handler {}: {}".format(
                                em["module"].__name__,
                                obj)
                            )
                    """
                    this_object_handled = True
                    em["send_queue"].put(obj)

            # Handle the case where no module could handle an object
            if not this_object_handled:
                self.logger.debug("Object had no handler: {}".format(obj))
                obj_death = DeathLog(obj)
                self.reemitter["send_queue"].put(obj_death)


        # Check each reemitter for an input object
        rem_recv_and_empty = ((rem["recv_queue"], rem["recv_queue"].empty())
                for rem in self.rems)
        rem_inputs = (queue.get()
                for (queue, empty) in rem_recv_and_empty if not empty
                )
        # Send all inputs to the ReemitInputEndpointModule
        for obj in rem_inputs:
            some_object_handled = True
            self.reemitter["send_queue"].put(obj)

        return some_object_handled
