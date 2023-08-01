## Internal Extinction of Galaxies 

[This workflow](./int_ext_graph.py) has been developed to calculate the extinction within the galaxies, representing the dust extinction within the galaxies used in measuring the optical luminosity. The first PE, "ReadRaDec", read the coordinator data for 1051 galaxies in an input file. Then, these data are used in the second PE "GetVOTable" as arguments to make an HTTP request to the Virtual Observatory website  and get the VOTable as the response. Finally, these VOTable go into PE "FilterColumns"


## How to run the workflow with different mappings
Activate the enviroment - if you had not created, go to the [README instructions](https://github.com/NoPuzzle/dispel4py_autoscaling/tree/main#2-create-a-new-python-37-environment) of this repository.


```
conda activate py37_d4p
```

To run the this test, first you need to install:
```shell
$ pip install requests
$ pip install astropy
``` 

Then, run the script. Example run commands for several other modes are listed below:

### Run with simple mode:
```shell
python -m dispel4py.new.processor simple int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}'
OR
dispel4py simple int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}'
```
The ‘coordinates.txt’ file is the workflow's input data with the coordinates of the galaxies.

### Run with multiprocessing mode:
```shell
python -m dispel4py.new.processor multi int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
OR
dispel4py multi int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10

``` 
 Parameter '-n' specify the number of processes.


#### Run with dynamic multi mapping 
``` 
python -m dispel4py.new.processor new_dyn int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
OR
dispel4py new_dyn int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```

#### Run with dynamic multi mapping autoscaling mapping 
```
python -m dispel4py.new.processor new_dyn_auto int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
OR
dispel4py new_dyn_auto int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```

----- REDIS ----
You need REDIS server running in a tab: 

```shell
conda activate py37_d4p
redis-server
``` 

In another tab you can do the following runs: 

#### Run with dynamic redis mapping 
```shell
python -m dispel4py.new.processor new_dyn_redis int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
OR
dispel4py new_dyn_redis int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```

#### Run with dynamic redis autoscaling mapping 
```shell 
python -m dispel4py.new.processor new_dyn_redis_auto int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
OR
dispel4py new_dyn_redis_auto int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```

#### Run with hybrid redis mapping 
```shell
python -m dispel4py.new.processor hybrid_redis int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
OR
dispel4py hybrid_redis int_ext_graph.py -d '{"read" : [ {"input" : "coordinates.txt"} ]}' -n 10
```
