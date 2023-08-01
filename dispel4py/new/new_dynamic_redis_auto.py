# from internal_extinction.int_ext_graph import read, graph

from dispel4py.new.dyn_redis_config import connect, parse_args
from dispel4py.new.logger import logger

from multiprocessing import Process, Queue, TimeoutError, Pool, Value, Condition
import json

from dispel4py.new.processor import GenericWrapper, get_inputs
from dispel4py.core import GenericPE, WRITER



DISPEL4PY_REDIS_AUTO_PREFIX = "DISPEL4PY_DYN_AUTO"

MANAGER_KEY = DISPEL4PY_REDIS_AUTO_PREFIX + "_MANAGER"
MANAGER_TERMIATE_FIELD = "TERMINATE"

MANAGER_TERMIATE_YES = "YES"
MANAGER_TERMIATE_NO = "NO"

STREAM_KEY = DISPEL4PY_REDIS_AUTO_PREFIX + "_STREAM"
GROUP_NAME = DISPEL4PY_REDIS_AUTO_PREFIX + "_GROUP"
FIELD_KEY = "KEY"

TIMEOUT_IN_SECONDS = 1
MAX_RETRIES = 5

REDIS_TIMEOUT = TIMEOUT_IN_SECONDS * 1000




def reset_redis(redis):
    if redis.exists(STREAM_KEY):
        redis.delete(STREAM_KEY)
    if redis.exists(GROUP_NAME):
        redis.xgroup_destroy(STREAM_KEY, GROUP_NAME)

    redis.xgroup_create(STREAM_KEY, GROUP_NAME, mkstream=True)

def unpack_response(response): # -> (entry_id, pe_id, data)

    """
    response = [[key, [(entry_id, {FIELD_KEY: value})]]]
    """

    # logger.debug(f"response = {response}")


    key, msg = response[0]
    entry_id, payload = msg[0]
    value = json.loads(payload[FIELD_KEY])

    pe_id, data = value

    
    # # logger.debug(f"key = {key}")
    # # logger.debug(f"msg = {str(msg)}")
    # logger.debug(f"entry_id = {entry_id}")
    # # logger.debug(f"payload = {str(payload)}")
    # # logger.debug(f"value = {str(value)}")
    # logger.debug(f"pe_id = {pe_id}")
    # logger.debug(f"data = {data}")

    return entry_id, pe_id, data

class RedisWriter:

    def __init__(self, redis, destinations):

        self.redis = redis
        self.destinations = destinations

    def write(self, data):

        if self.destinations:
            for dest_id, input_name in self.destinations:
                payload = {FIELD_KEY : json.dumps((dest_id , {input_name: data}))}
                self.redis.xadd(STREAM_KEY, payload, "*")

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

        
    def process(self, data):

        # logger.debug(f"data = {data}")
        return self.pe.process(data)
    
    # @staticmethod
    # def simpleLogger(instance, message):
    #     print(f"Instance ID: {instance.id}, Message: {message}")


class DynamicRedisWroker():

    def __init__(self, cp_graph, rank):

        self.graph = cp_graph
        self.rank = rank
        # self.queue = queue
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

        # logger.debug(f"rank = {self.rank}, destinations = {destinations}")
        return destinations


class AutoDynamicRedisWorker(DynamicRedisWroker):
    
    def __init__(self, cp_graph, rank):
        super().__init__(cp_graph, rank)


    def process(self):
        
        try:
            worker_redis = connect(name=f"worker_{self.rank}")
            # logger.debug(f"worker_{self.rank} is processing")

            response = []
            retries = 0
            # timeout = REDIS_TIMEOUT

            while not response:

                response = worker_redis.xreadgroup(GROUP_NAME, f"worker_{self.rank}", {STREAM_KEY: '>'}, count=1, block=REDIS_TIMEOUT)

                if worker_redis.hget(MANAGER_KEY, MANAGER_TERMIATE_FIELD) == MANAGER_TERMIATE_YES:
                    logger.debug(f"worker_{self.rank} is exiting")

                    # return
                    break

                retries+=1
                if retries == MAX_RETRIES:
                    
                    worker_redis.hset(MANAGER_KEY, MANAGER_TERMIATE_FIELD, MANAGER_TERMIATE_YES)
                    # logger.debug(f"worker_{self.rank} is exiting and terminating the workflow")
                    # logger.debug(f"worker_{self.rank} is exiting")
                    logger.error(f"Empty queue, timeout = {REDIS_TIMEOUT * MAX_RETRIES}")

                    # worker_redis.xadd(STREAM_KEY, {'exit': "1"}, "*")
                    # return
                    break
                

            if response:

                entry_id, pe_id, data = unpack_response(response)
                pe = self.node_pe[pe_id]['pe']
                node = self.node_pe[pe_id]['node']

                for output_name in pe.outputconnections:
                    
                    destinations = self._get_destination(node, output_name)
                    pe.outputconnections[output_name][WRITER] = RedisWriter(worker_redis, destinations)

                output = pe.process(data)

                if output:
                    for output_name, output_value in output.items():
                        destinations = self._get_destination(node, output_name)
                        if destinations:
                            for dest_id, input_name in destinations:
                                payload = {FIELD_KEY : json.dumps((dest_id , {input_name: output_value}))}
                                worker_redis.xadd(STREAM_KEY, payload, "*")

                worker_redis.xack(STREAM_KEY, GROUP_NAME, entry_id)

            # else:
            
        except Exception as e:
            logger.error(f"Exception = {e}")

        # worker_redis.xgroup_delconsumer(STREAM_KEY, GROUP_NAME, f"worker_{self.rank}")
        # return 

    




class AutoScaler():
    
    def __init__(self, max_pool_size, initial_actice_size, redis):
        

        self.master_redis = redis

        self.max_pool_size = max_pool_size
        self.pool =Pool(processes=self.max_pool_size)

        #  synchronization primitive allow for further extedning multiple auto scalers 
        self.active_size = Value('i', initial_actice_size)
        
        self.active_count = Value('i', 0)
        # self.task_counter = Value('i', 0)

        self.total_workers_spawned = 0
        self.current_workers_spawned = 0


        self.condition = Condition()
    
    def shrink(self, size_to_shrink):
        with self.active_size.get_lock():
            self.active_size.value = max(1, self.active_size.value - size_to_shrink)

        logger.debug(f"Shrink: active size = {self.active_size.value}")
    
    def grow(self, size_to_grow):
        with self.active_size.get_lock():
            self.active_size.value = min(self.max_pool_size, self.active_size.value + size_to_grow) 

        logger.debug(f"Grow: active size = {self.active_size.value}")



    def is_finished(self):

        # a = self.master_redis.hget(MANAGER_KEY, MANAGER_TERMIATE_FIELD)
        
        # logger.debug(f"a = {a}")
        # group_info = self.master_redis.xinfo_groups(STREAM_KEY)

        # logger.debug(f"group_info = {group_info}")

        # if(group_info[0]['pending'] ==  0 and group_info[0]['last-delivered-id'] != '0-0'):

        if self.master_redis.hget(MANAGER_KEY, MANAGER_TERMIATE_FIELD) == MANAGER_TERMIATE_YES:

            return True


        # return False



    def process(self, graph):

        self.master_redis.hset(MANAGER_KEY, MANAGER_TERMIATE_FIELD, MANAGER_TERMIATE_NO)
        results = []

        while True:
            
            self.auto_scale()

            if self.is_finished() and self.active_count.value == 0:

                logger.info("All tasks are finished")
                break
            
            else:

                cp_graph = graph.copy()
                # worker = AutoDynamicRedisWorker(cp_graph, self.current_workers_spawned)
                
                # self.current_workers_spawned += 1


                worker = AutoDynamicRedisWorker(cp_graph, self.active_count.value)


                results.append(self.start(worker.process, args=[]))

            
            if self.active_count.value == self.active_size.value:

                [result.get() for result in results]
                results = []

                # self.current_workers_spawned = 0

    def auto_scale(self):


        # pendding could be used
        group_info = self.master_redis.xinfo_consumers(STREAM_KEY, GROUP_NAME) 

        logger.debug(f"group_info = {group_info}")

        total_idle_for_active_workers = 0
        for i, consumer in enumerate(group_info):

            # if i >= self.current_workers_spawned:
            if i >= self.active_count.value:
                break

            total_idle_for_active_workers += consumer['idle']
        logger.debug(f"total_idle_for_active_workers = {total_idle_for_active_workers}")
        if total_idle_for_active_workers > 5000:
            self.shrink(1)
        elif total_idle_for_active_workers < 1000:
            self.grow(10)
        
        # # self.total_workers_spawned 
        # for i in range(self.current_workers_spawned):
        #     total_idle_for_active_workers += group_info[i]['idle']
        # pass

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



    

def process(workflow, inputs=None, args=None):

    # logger.info(f"workflow = {workflow}, dir(workflow) = {dir(workflow)})")

    size = args.num-1
    graph = workflow.graph

    
    redis = connect(name="master")
    reset_redis(redis)

    for node in graph.nodes():

        # logger.debug(f"node = {node.obj}, dir(node) = {dir(node.obj)}")
        provided_inputs = get_inputs(node.obj, inputs)

        if provided_inputs:

            if isinstance(provided_inputs, int):
                for _ in range(provided_inputs):

                    payload = {FIELD_KEY : json.dumps((node.obj.id , {}))}
                    redis.xadd(STREAM_KEY, payload, "*")
            
            else:
                for d in provided_inputs:
                    payload = {FIELD_KEY : json.dumps((node.obj.id , d))}
                    redis.xadd(STREAM_KEY, payload, "*")

    auto_scaler = AutoScaler(size, 10, redis)
    auto_scaler.process(graph)
    



# args = parse_args(["-n", "20"], None)

# process(graph, {read: [ {"input" : "internal_extinction/coordinates.txt"} ]}, args)