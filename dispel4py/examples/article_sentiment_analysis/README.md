## Sentiment Analyses for News Articles

[This workflow](./analysis_sentiment.py) uses two different approaches to analyse the sentiment of news articles (i.e. score the news article), and these sentiment scores are then grouped according to the location where they were published. Finally, the workflow will output the three happiest locations with their scores. 

The news articles used in this case are collected from a public Kaggle dataset [News Articles](https://www.kaggle.com/datasets/asad1m9a9h6mood/news-articles).This dataset contains news articles from 2015 related to business and sports with their heading, content, public location and date. As some of the data had missing fields and some of the articles contained a large number of nonsensical characters (e.g. <script>, `<br/>`), a Python script was developed for the project to pre-process the data. 

The first PE, "Read Articles", reads articles from an input file and then extracts the article content line by line. Every time a line is read and parsed, one data is generated and sent to two downstream PEs. PE "Sentiment AFINN" calculate the news article’s sentiment score by [AFINN lexicon](./AFINN-111.txt). PE "Tokenisation WD" and "Sentiment SWN3" tokenise the news article content and then calculate the sentiment score using the [SWN3](SentiWordNet_3.0.0_20130122.txt) lexicon. After that, data from both branches go to their respective "Find State" - "Happy State" - "Top 3 Happiest" PE chain. The three PEs find the location of each data, group the received data by location and finally display the three happiest (highest scoring) locations and their scores. The number of instances of the PE "Happy State" in the "SWN3" branch is set to 3 in order to reflect the stateful character.


## How to run the workflow with different mappings 

***Atention!!:** This workflow is a **statefull** workflow!! So only the **fixed workload mappings** and **hybrid** mapping could be used to run this workflow.

To run this test, the following two steps are required, namely the preparation of the data and the execution of the test script.

### Preparation of data
In order to run this test, you must first prepare the article data needed for the test. We collect some article data from http://aaa.com and saved as "Articles.csv" in this repository. Before running the test, you must first run "clean.py" in this directory to clean the data. 

To run the data cleaning program, first you need to install:
```shell
$ pip install pandas
``` 

Then, run the clean script:
```shell
$ python clean.py Articles.csv
``` 

After cleaning, a new file named "Articles_cleaned.csv" will occur by default. This file is the input of the next step. 

Note that you don't need to run the cleaning script again if you already have the cleaned data.


### Execution of the test script

To run the test script, first you need to install:
```shell
$ pip install nltk numpy 
``` 

In multiprocessing mode, parameter '-n' specify the number of processes. For executing it with the multiprocessing mode and assign 13 processes:
```
python -m dispel4py.new.processor multi  analysis_sentiment -n 13 -d "{"read" : [ {"input" : "Articles_cleaned.csv"} ]}"
OR 
dispel4py multi  analysis_sentiment -n 13 -d "{"read" : [ {"input" : "Articles_cleaned.csv"} ]}"
``` 

In hybrid mode, parameter '-n' specify the number of processes. For executing it with the multiprocessing mode and assign 13 processes:

----- REDIS ----
You need REDIS server running in a tab: 

```shell
conda activate py37_d4p
redis server
```

In another tab you can do the following run: 

```
python -m dispel4py.new.processor hybrid_redis analysis_sentiment -n 13 -d "{"read" : [ {"input" : "Articles_cleaned.csv"} ]}"
OR
dispel4py hybrid_redis analysis_sentiment -n 13 -d "{"read" : [ {"input" : "Articles_cleaned.csv"} ]}"
``` 

