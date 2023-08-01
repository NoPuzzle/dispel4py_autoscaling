# dispel4py

dispel4py is a free and open-source Python library for describing abstract stream-based workflows for distributed data-intensive applications. It enables users to focus on their scientific methods, avoiding distracting details and retaining flexibility over the computing infrastructure they use.  It delivers mappings to diverse computing infrastructures, including cloud technologies, HPC architectures and  specialised data-intensive machines, to move seamlessly into production with large-scale data loads. The dispel4py system maps workflows dynamically onto multiple enactment systems, and supports parallel processing on distributed memory systems with MPI and shared memory systems with multiprocessing, without users having to modify their workflows.

## Dependencies

dispel4py has been tested with Python *2.7.6*, *2.7.5*, *2.7.2*, *2.6.6* and Python *3.4.3*, *3.6*, *3.7*.

The following Python packages are required to run dispel4py, no need to manually install, see the [installation](#installation):

- PyJWT == 2.6.0
- flake8 == 5.0.0
- httpsproxy-urllib2 == 1.0
- ipython == 7.34.0
- lxml == 4.8.0
- matplotlib == 3.5.1
- msgpack == 0.6.2
- networkx == 2.6.3
- nltk == 3.7
- nose == 1.3.7
- numpy == 1.21.5
- pandas == 1.3.5
- pyzmq == 23.2.0
- redis == 4.4.2
- requests == 2.28.1
- scipy == 1.7.3
- seaborn == 0.12.2
- setuptools == 54.2.0
- six == 1.16.0
- storm == 0.25
- thrift == 0.16.0
- ujson == 5.2.0


The following Python packages are optional depending the mapping or workflow to run (**Recommend to install**):
- astropy == 4.3.1
- coloredlogs == 15.0.1
- zipp == 3.12.1

## Introduction of Mappings

The mappings of dispel4py refer to the connections between the processing elements (PEs) in a dataflow graph. Dispel4py is a Python library used for specifying and executing data-intensive workflows. In a dataflow graph, each PE represents a processing step, and the mappings define how data flows between the PEs during execution. These mappings ensure that data is correctly routed and processed through the dataflow, enabling efficient and parallel execution of tasks.

We currently support the following ones:
- Sequential
  - "simple": it executes dataflow graphs sequentially on a single process, suitable for small-scale data processing tasks. 
- Parallel:  
  -  Fixed fixed workload distribution - support stateful and stateless PEs: 
    - "mpi": it distributes dataflow graph computations across multiple nodes (distributed memory) using the Message Passing Interface (MPI). 
    - "storm": it enables the execution of dataflow graphs on distributed real-time data processing systems, leveraging Apache Storm for scalable and fault-tolerant processing.
    - "multi": it runs multiple instances of a dataflow graph concurrently using **multiprocessing Python library**, offering parallel processing on a single machine. 
    - "zmq_multi": it runs multiple instances of a dataflow graph concurrently using **ZMQ library**, offering parallel processing on a single machine.
  - Dynamic workfload distribution -  support only stateless PEs 
    - "dyn_multi": it runs multiple instances of a dataflow graph concurrently using **multiprocessing Python library**. Worload assigned dynamically (but no autoscaling). 
    - "dyn_auto_multi": same as above, but allows autoscaling. 
    - "dyn_redis": it runs multiple instances of a dataflow graph concurrently using **Redis library**. Worload assigned dynamically (but no autocasling). 
    - "dyn_auto_redis": same as above, but allows autoscaling.
  - Hybrid workload distribution - supports stateful and stateless PEs 
    - "hybrid_redis": it runs multiple instances of a dataflow graph concurrently using **Redis library**. Hybrid approach for workloads: Stafeless PEs assigned dynamically, while Stateful PEs are assigned from the begining.

## Installation


## 1. Prepare your directory

```shell
mkdir dispel4py_autoscaling
cd dispel4py_autoscaling
```

## 2. Create a new python 3.7 environment

```shell
conda create --name py37_d4p python=3.7
conda activate py37_d4p
```


## 3. Clone Github Repo 

using https 
```shell
git clone https://github.com/NoPuzzle/dispel4py_autoscaling.git
```

or ssh
```shell
git clone git@github.com:NoPuzzle/dispel4py_autoscaling.git
```


## 4. Install dispel4py
```shell
python setup.py install
pip install -r requirements_d4py.txt
```

Optional but recommand to install
```shell
conda install coloredlogs
conda install -c conda-forge astropy
conda install -c conda-forge zipp
```


## 5. Testing dynamic multi mapping

```
cd dispel4py/examples/internal_extinction
```
#### Testing dynamic multi mapping with a stateless workflow
```
python -m dispel4py.new.processor new_dyn int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```

#### Testing dynamic multi autoscaling mapping with a statless workflow
```
python -m dispel4py.new.processor new_dyn_auto int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```

##  6. Testing dynamic Redis

> Go to another terminal for following command line

```shell
conda activate py37_d4p
redis-server
```

> Go back to previous terminal

#### Testing dynamic redis mapping with a stateless workflow 
```shell
python -m dispel4py.new.processor new_dyn_redis int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```

#### Testing dynamic redis autoscaling mapping with a stateless workflow
```shell
python -m dispel4py.new.processor new_dyn_redis_auto int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```


#### Testing hybrid redis mapping for a stateless workflow
```shell
python -m dispel4py.new.processor hybrid_redis int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```

#### Testing hybrid redis mapping for a stateful workflow
```shell
cd ../graph_testing 
python -m dispel4py.new.processor hybrid_redis split_merge.py -i 100 -n 10
python -m dispel4py.new.processor hybrid_redis grouping_alltoone_stateful.py -i 100 -n 10
```
