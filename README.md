# dispel4py

dispel4py is a free and open-source Python library for describing abstract stream-based workflows for distributed data-intensive applications. It enables users to focus on their scientific methods, avoiding distracting details and retaining flexibility over the computing infrastructure they use.  It delivers mappings to diverse computing infrastructures, including cloud technologies, HPC architectures and  specialised data-intensive machines, to move seamlessly into production with large-scale data loads. The dispel4py system maps workflows dynamically onto multiple enactment systems, and supports parallel processing on distributed memory systems with MPI and shared memory systems with multiprocessing, without users having to modify their workflows.

## Dependencies

dispel4py has been tested with Python *2.7.6*, *2.7.5*, *2.7.2*, *2.6.6* and Python *3.4.3*, *3.6*, *3.7*.

The following Python packages are required to run dispel4py:

- networkx (https://networkx.github.io/)

If using the MPI mapping:

- mpi4py (http://mpi4py.scipy.org/)

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
cd dispel4py
python setup.py install
cp ../requirements_d4py.txt .
pip install -r requirements_d4py.txt
```

install a library for logging

```shell
conda install coloredlogs
```


## 5. Testing dynamic 

```
cd dispel4py/examples/internal_extinction
```
#### Testing dynamic mapping

```
python -m dispel4py.new.processor new_dyn int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```

#### Testing dynamic autoscaling mapping
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

#### Testing dynamic redis mapping
> this may not work
```shell
python -m dispel4py.new.processor new_dyn_redis int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```


#### Testing dynamic redis autoscaling mapping
```shell
python -m dispel4py.new.processor new_dyn_redis_auto int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```
## Docker

The Dockerfile in the dispel4py root directory builds a Debian Linux distribution and installs dispel4py and OpenMPI.

```
docker build . -t dare-dispel4py
```

Start a Docker container with the dispel4py image in interactive mode with a bash shell:

```
docker run -it dare-dispel4py /bin/bash
```

For the EPOS use cases obspy is included in a separate Dockerfile `Dockerfile.seismo`:

```
docker build . -f Dockerfile.seismo -t dare-dispel4py-seismo
```