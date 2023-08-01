import argparse
import copy
import types
import multiprocessing
import time
from multiprocessing import Process, Queue, TimeoutError, Pool, Value, Condition
# from dispel4py.new import processor

from dispel4py.new.processor import GenericWrapper, get_inputs


from queue import Empty

from dispel4py.core import GenericPE, WRITER

# from test_workflow import producer, graph
# from dispel4py.examples.internal_extinction.int_ext_graph import read, graph
# from internal_extinction.int_ext_graph import read, graph

from dispel4py.new.logger import logger, print_stack_trace

TIMEOUT_IN_SECONDS = 1
MAX_RETRIES = 5

MULTI_TIMEOUT = TIMEOUT_IN_SECONDS


def parse_args(args, namespace):
    parser = argparse.ArgumentParser(
        prog='dispel4py',
        description='Submit a dispel4py graph to zeromq multi processing')
    parser.add_argument('-ct', '--consumer-timeout',
                        help='stop consumers after timeout in ms',
                        type=int)
    parser.add_argument('-n', '--num', metavar='num_processes', required=True,
                        type=int, help='number of processes to run')
    
    result = parser.parse_args(args, namespace)
    return result


class GenericWriter:

    def __init__(self, queue, destinations):
        self.queue = queue
        self.destinations = destinations

    def write(self, data):

        if self.destinations:
            for dest_id, input_name in self.destinations:
                self.queue.put((dest_id, {input_name: data}))

def simpleLogger(instance, message):
        print(f"Instance ID: {instance.id}, Message: {message}")



class DynamicWrapper(object):

    def __init__(self, pe, provided_inputs):
        
        self.pe = pe
        self.provided_inputs = provided_inputs
        self.pe.wrapper = self
        self.id = pe.id
        self.inputconnections = pe.inputconnections
        self.outputconnections = pe.outputconnections
        # self.name = pe.name
        # self.pe.log = types.MethodType(simpleLogger, self.pe)
        # self.test_string = "test string"

        # self.pe.log = lambda msg: DynamicWrapper.simpleLogger(self.pe, msg)

        # self.pe.log = simpleLogger(self.pe)

        # logger.debug(f"self.pe = {self.pe!r}\n \
        #                 self.pe.wrapper = {self.pe.wrapper!r}\n \
        #                 self.provided_inputs = {self.provided_inputs!r}\n \
        #                 self.pe.outputconnections = {self.pe.outputconnections!r}")
        
    def process(self, data):

        # logger.debug(f"data = {data}")
        return self.pe.process(data)
    
    # @staticmethod
    # def simpleLogger(instance, message):
    #     print(f"Instance ID: {instance.id}, Message: {message}")


class DynamicWroker():

    def __init__(self, queue, cp_graph, rank):

        self.graph = cp_graph
        self.rank = rank
        self.queue = queue
        self.node_pe = {node.obj.id: {'node' : node, 'pe' : node.obj} for node in self.graph.nodes()}

    def process(self):
        """
        Function to process a worker in the workflow.
        """
        pass


    def _get_destination(self, node, output_name):

        """
        Function to get the destinations of a certain node in the graph.

        Args:
            node: The node for which we want to find the destinations.
            output_name: The name of the output.

        Returns:
            A set of destinations for the node.
        """
        destinations = set()

        pe_id = node.obj.id

        for edge in self.graph.edges(node, data=True):
            direction = edge[2]['DIRECTION']
            source, dest = direction

        # ensure it's the source and not the first PE
        if source.id == pe_id and output_name == edge[2]['FROM_CONNECTION']:
            dest_input = edge[2]['TO_CONNECTION']
            destinations.add((dest.id, dest_input))

        logger.debug(f"rank = {self.rank}, destinations = {destinations}")
        return destinations
    

class AutoDynamicWroker(DynamicWroker):

    def __init__(self, queue, cp_graph, rank):
        super().__init__(queue, cp_graph, rank)
        logger.info(f"self.rank = {self.rank}")


    def process(self):

        retries = 0
        while retries < MAX_RETRIES:
            try:
                # Initially, block until an item is available
                value = self.queue.get(timeout=MULTI_TIMEOUT)

                if value == 'STOP':
                    # self.queue.put('STOP')
                    break

                # logger.debug(f"here rank = {self.rank}, value = {value}")

                pe_id, data = value
                pe = self.node_pe[pe_id]['pe']
                node = self.node_pe[pe_id]['node']

                # logger.debug(f"rank = {self.rank}, pe_id = {pe_id}, pe = {pe}, node = {node}") 
                
                for output_name in pe.outputconnections:

                    destinations = self._get_destination(node, output_name)
                    pe.outputconnections[output_name][WRITER] = GenericWriter(self.queue, destinations)
                
                # logger.debug(f"outputconnections = {pe.outputconnections}")

                output = pe.process(data)
                # logger.debug(f"rank = {self.rank}, output = {output}")
                if output:
                    for output_name, output_value in output.items():
                        destinations = self._get_destination(node, output_name)
                        if destinations:
                            for dest_id, input_name in destinations:
                                self.queue.put((dest_id, {input_name: output_value}))
                
                # If everything goes smoothly, break out of the loop
                break
                        
            except Empty:

                retries += 1
                if retries == MAX_RETRIES:
                    
                    self.queue.put('STOP')
                    logger.error(f"Here lol Empty queue, timeout = {MULTI_TIMEOUT * MAX_RETRIES}")

                    return
                
            except Exception as e:
                logger.error(f"Exception = {e}")

                return
                

class AutoScaler():

    def __init__(self, queue, max_pool_size, initial_actice_size):

        self.max_pool_size = max_pool_size
        self.pool =Pool(processes=self.max_pool_size)

        self.queue = queue
        #  synchronization primitive allow for further extedning multiple auto scalers 
        self.active_size = Value('i', initial_actice_size)
        self.active_count = Value('i', 0)
        # self.task_counter = Value('i', 0)
        self.condition = Condition()
    
    def shrink(self, size_to_shrink):
        with self.active_size.get_lock():
            self.active_size.value = max(1, self.active_size.value - size_to_shrink)

        logger.debug(f"Shrink: active size = {self.active_size.value}")
    
    def grow(self, size_to_grow):
        with self.active_size.get_lock():
            self.active_size.value = min(self.max_pool_size, self.active_size.value + size_to_grow) 

        logger.debug(f"Grow: active size = {self.active_size.value}")  

    def process(self, graph):

        # logger.debug(f"dir(node.obj) = {dir(node.obj.pe)}")

        # for node in graph.nodes():

        #     logger.debug(f"dir(node.obj) = {type(node.obj.pe)}")
        #     provided_inputs = None
        #     node.obj = DynamicWrapper(node.obj, provided_inputs)

        results = []
        total_workers_spawned = 0
        while True:

            self.auto_scale()
            if self.queue.empty() and self.active_count.value == 0:
                
                # print("queue is empty")
                task_results = [result.get() for result in results]
                break

            else:
                cp_graph = copy.deepcopy(graph)
                worker = AutoDynamicWroker(self.queue, cp_graph, total_workers_spawned)
                total_workers_spawned += 1
                # self.start(self.queue.get())
                
                results.append(self.start(worker.process, args=[]))


                # logger.debug(f"here1")
                # self.start(worker.process, args=[]).get()

                logger.debug(f"queue.size = {self.queue.qsize()}, self.active_count.value = {self.active_count.value}")

                # break

            if self.active_count.value == self.active_size.value:

                [result.get() for result in results]
                results = []


    def auto_scale(self):

        if self.queue.qsize() > 10:
            logger.debug(f"queue size = {self.queue.qsize()}, active size = {self.active_size.value}")
            self.grow(1)

        elif self.queue.qsize() < 5 and self.active_count.value > 0:
            logger.debug(f"queue size = {self.queue.qsize()}, active size = {self.active_size.value}")
            self.shrink(1)
        

    def start(self, task_func, args=None):

        with self.condition:
            while self.active_count.value >= self.active_size.value:
                self.condition.wait()

            with self.active_count.get_lock():
                self.active_count.value += 1
        
        # logger.debug(f"Start: active count = {self.active_count.value}")
        return self.pool.apply_async(task_func, args=args, callback=self.done)
    
    def done(self, result):
        with self.condition:
            self.active_count.value -= 1
            self.condition.notify_all()
        
        # logger.debug(f"Done: active count = {self.active_count.value}")


# def test_process(workflow, inputs=None, args=None):
def process(workflow, inputs=None, args=None):
    # logger.debug(f"workflow = {workflow}, dir(workflow) = {dir(workflow)})")
    queue = multiprocessing.Manager().Queue()

    graph = workflow.graph

    size = args.num-1

    for node in graph.nodes():

        provided_inputs = get_inputs(node.obj, inputs)
        
        node.obj = DynamicWrapper(node.obj, provided_inputs)
        # logger.debug(f"dir(node.obj) = {dir(node.obj.pe)}")
        if provided_inputs:

            # logger.debug(f"provided_inputs = {provided_inputs}")

            if isinstance(provided_inputs, int):
                for i in range(provided_inputs):
                    queue.put((node.obj.id, {}))
            else:
                for d in provided_inputs:
                    queue.put((node.obj.id, d))

    auto_scaler = AutoScaler(queue, size, 4)
    
    auto_scaler.process(graph)



        

# def process(workflow, inputs=None, args=None):

#     logger.info(f"workflow = {workflow}, dir(workflow) = {dir(workflow)})")
#     start_time = time.time()
#     size = args.num-1
#     graph = workflow.graph
#     queue = multiprocessing.Manager().Queue()

#     # pes = {node.getContainedObject().id: node.getContainedObject() for node in workflow.graph.nodes()}
#     # nodes = {node.getContainedObject().id: node for node in workflow.graph.nodes()}

#     for node in graph.nodes():

#         provided_inputs = get_inputs(node.obj, inputs)
#         # logger.debug(f"dir(node.obj) = {dir(node.obj)}")
#         node.obj = DynamicWrapper(node.obj, provided_inputs)
#         # logger.debug(f"dir(node.obj) = {dir(node.obj.pe)}")

#         if provided_inputs:

#             logger.debug(f"provided_inputs = {provided_inputs}")

#             if isinstance(provided_inputs, int):
#                 for i in range(provided_inputs):
#                     queue.put((node.obj.id, {}))
#             else:
#                 for d in provided_inputs:
#                     queue.put((node.obj.id, d))

#     workers = []
#     for rank in range(size):
#         cp_graph = copy.deepcopy(graph)
#         worker = AutoDynamicWroker(queue, cp_graph, rank)
#         proc = multiprocessing.Process(target=worker.process)
#         workers.append(proc)
        
#     print('Starting %s workers communicating' % (len(workers)))

#     for worker in workers:
#         worker.start()
#     for worker in workers:
#         worker.join()

#     print ("ELAPSED TIME: "+str(time.time()-start_time))

# args = parse_args(["-n", "10"], None)

# logger.debug(f"args = {args}")

# print(args)
# process(graph, {read: [ {"input" : "internal_extinction/coordinates.txt"} ]}, args)

# test_process(graph, {read: [ {"input" : "internal_extinction/coordinates.txt"} ]}, args)