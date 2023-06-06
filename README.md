# Easydags: DAGs made easy

This package was heavily inspired by this library: https://github.com/mindee/tawazi and a little bit by Airflow.

## Define a DAG

Maybe all of you already know what is a Directed Acyclic Graph (DAG)... but please think about this definition when using this library:


A DAG represents a collection of tasks you want to run, this is also organized to show relationships between tasks.

- Each node is a task (A,B) 
- Each edge represents a dependency, A->B means we can only execute B after A finishes.

## Double click to dependency 

The concept of dependency in general is preatty simple: A->B means that A needs to run before B.


But after we understand the concept of dependency we might need to complicate that concept a little bit with this two definitions.

Hard dependency:  B need the output of the process A… and the output of A is an actual argument of the function that executes B

Soft dependency:  B need the output of the process A… but the output is stored somewhere else, we just know that A have finished. As an example let's think about 2 queries where we need the table of the first query in the second one.

## Why do we need hard and soft dependencies

Basically i am a developer that works a lot with data pipelines, that means that i usually encounter the following scenario:

1. A query that creates: my_dataset.my_awesome_table
2. A second query that creates another table that depends on my_dataset.my_awesome_table

So what can we do in those cases? well, if we want to have the most recent version of the second table we will need to run the first query before!... but i do not need any result in memory! thats a soft dependency.

On the other hand i also had the following scenario:

1. i have a pre process function
2. i need to run model 1 to get prediction 1
3. i need to run model 2 to get my prediction 2
4. My final prediction will be the mean between prediction 1 and 2 (a simple ensamble)

Lest suppose that the first task leaves the resulting table in my_dataset.clean_data, that will create a soft dependency between the nodes 2,3 and node 1.

But lets suppose that we receive the predictions from model 1 and model 2 in the final node in memory? (something like a pandas dataframe)... that will create a hard dependency!

All hard dependencies can be re_writed as a soft dependency (using local files or databases) but there are some cases when it is easier/cheaper/faster to pass the data directly in memory... thats why we might encounter both kind of dependencies out in the wild!

This library will help you get through all those challenges if you use it wisely, i really hope that this helps someone with a real world problem. 


## Why do we need DAGs

This is a hard question... after all all your processes might be ok. But i will try to explain the main reason with one example:

![Motivation](resource_readme/concurrence_imp.png)
              

Unless you are using DAGs there is a high posibility that you are following the lineal DAG.. but thats inneficient, there is a high possibility that you have a lot of processes that can run in parallel thats why DAGs are so useful, they do not only give us one execution order, they also help us realize which task can be paralellized... and of course this library implements thats using threads (we can define the maximum number of threads with the paramater max_concurrency in the DAG constructor)




## How to use this library 

As we said in the definition a DAG is a list of tasks, and each node is a task with some dependencies (or none)... basically we can create a dag following that idea.

1. import the node clase (ExecNode)
2. import the DAG class
3. Create an empty list and start populating with nodes
4. Create nodes, specifiying their tasks (a python function) and define dependencies.
5. Create a DAG using the list of nodes

Here are some examples:

#### Defining a DAG with Soft Dependencies

```python
from easydags import  ExecNode, DAG #import some useful classes
import time

nodes = [] #start the empty list


def example0():
    # A dummy function... we just create some "timeout" to crearly show that f1 will run just after f0
    print('beginning 0')
    time.sleep(3)
    print('end 0')



nodes.append( ExecNode(id_= 'f0',# we set the id of the task... must be unique
              exec_function = example0 # we set the task
              ) )  


def example1():
     # A dummy function... this is just to show that f1 runs after f0
    print('beginning 1')
    print('end 1')

nodes.append( ExecNode(id_= 'f1',# we set the id of the task... must be unique
              exec_function = example1 ,# we set the task
              depends_on_soft= ['f0'] # Since we dont need the actual result from our dependency this is as soft one
              ) )   


dag = DAG(nodes,max_concurrency=2) #Create the DAG as the list of nodes

dag.execute() # execute the dag

```


#### Defining a DAG with Hard Dependencies

```python

from easydags import  ExecNode, DAG
import time

nodes = []


def example0():
    print('beginning 0')
    time.sleep(3)
    print('end 0')
    return 8



nodes.append( ExecNode(id_= 'f0',
              exec_function = example0,
              output_name = 'my_cool_varname' #we define how to retrieve this result in the following nodes with a hard dependency... if we do not define this the defaul name is {self.id_}_result
              ) )  


def example1(**kwargs):#result from previous nodes will be passed as kwargs 
    f0_result = kwargs['my_cool_varname'] #You just access to the variable that you want with the output name of the dedired node
    print('beginning 1')
    print('end 1')
    print(f0_result + 8 )

nodes.append( ExecNode(id_= 'f1',
              exec_function = example1 ,
              depends_on_hard= ['f0'],
              n_trials= 3
              ) )   

    
dag = DAG(nodes,max_concurrency=2) #Create the DAG as the list of nodes

dag.execute() # execute the dag

```


#### Defining the simple ensemble

``` python
from easydags import  ExecNode, DAG
import time

nodes = []


def prepro():
    print('beginning pre pro')
    time.sleep(3)
    print('end pre pro')
    return 'df with cool features'



nodes.append( ExecNode(id_= 'pre_process',
              exec_function = prepro,
              output_name = 'my_cool_df'
              ) )  


def model1(**kwargs):
    df = kwargs['my_cool_df']
    
    print(f'i am using {df} in model 1')
    time.sleep(3)
    print('finish training model1')
    
    return 'model 1 37803'

nodes.append( ExecNode(id_= 'model1',
              exec_function = model1 ,
              depends_on_hard= ['pre_process'],
              output_name = 'model1'
              ) )   



def model2(**kwargs):
    df = kwargs['my_cool_df']
    
    print(f'i am using {df} in model 2')
    time.sleep(3)
    print('finished training model2')
    
    return 'model 2 78373'

nodes.append( ExecNode(id_= 'model2',
              exec_function = model2 ,
              depends_on_hard= ['pre_process'],
              output_name = 'model2'
              ) )  



def ensemble(**kwargs):
    model1 = kwargs['model1']
    model2 = kwargs['model2']
    
    result = f'{model1} and {model2}'
    
    print(result)
    
    return result 

nodes.append( ExecNode(id_= 'ensemble',
              exec_function = ensemble ,
              depends_on_hard= ['model1','model2'],
              output_name = 'ensemble'
              ) )  



dag = DAG(nodes,name = 'Ensemble example',max_concurrency=3, debug = False)

dag.execute()
```
Please note that we can check the logs to verify that model 1 and model ran in paralallel

![Motivation](resource_readme/concurrence_check.png)



#### Checking the html output

One of the coolest features of airflow is that once you've built your DAG you can see it on their UI and you can also check the states of the latest run!

Well, my friend, we can do it here too.


When you create the dag object you can name the DAG as you want (by defaul the name is DAG) and easydags will create a html file name {self.name}_states_run.html you can see there the following:

1. The current structure
2. Datetime of last execution 
3. States of each node:
    - Green: ok
    - Red: It failed
    - Gray: Did not run because one of their dependencies failed


![Motivation](resource_readme/html_output.png)


#### One last cool feature: Number of trials

There are some cases where simply running your task again is enough... thats why we implemented this feature, We can set number of trials with the parameters n_trials in the creations of each node.

```python

node = ExecNode(id_= 'id',
              exec_function = function ,
              n_trials= 3 # set number of trials
              )
```





