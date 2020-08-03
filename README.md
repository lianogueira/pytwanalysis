# pyTwitterAnalysis
A tool to gather, discover, and analyze Twitter data using a combinations of graph-clustering and topic modeling techniques with the goal of semantically grouping tweet messages together. 

#### **Installation**

```
pip install pyTwitterAnalysis
```

#### **Initializing an object**
```
import pyTwitterAnalysis as ta
```

```
#set up your mongoDB connection here
mongoDBConnectionSTR = "mongodb://localhost:27017"
client = MongoClient(mongoDBConnectionSTR)
db = client.yourDB #chose your DB name here
```

```
BASE_PATH = '[youFolderPath]' #path where you want to save your files
```

```
x = ta.tw_analysis(BASE_PATH, db)
```


#### **Requirements:**
1. Python 3.7

2. **Database**: MongoDB - (Version: 4.0+)

3. **Libraries:**
 + pymongo 
 + NLTK  
 + numpy  
 + networkx 2.3 
 + matplotlib 3.2.1 
 + gensim
 + sklearn    
 + python-louvain
 + scipy  
 + seaborn
 + pandas
 + wordcloud
 + Pyphen

 
##### **Pre-requisites installation** 
```
 pip install pymongo
 pip install nltk
 pip install numpy
 pip install networkx==2.3
 pip install matplotlib==3.2.1
 pip install gensim
 pip install -U scikit-learn 
 pip install python-louvain 
 pip install scipy 
 pip install seaborn 
 pip install pandas 
 pip install wordcloud
 pip install Pyphen
```
 
 #### **Things you can do with this library:**
 + Use mongoDB to store and process your Twitter data
 + Export edges created based on user connections 
 + create graphs, timeseries analysis, topic analysis, and graph analysis of you Twitter data
 + create folder structure to save all files (by period or not)
 + create the following files for each folder and sub folder
     + nodes with degrees 
     + edges
     + texts for topics
     + graph with lda model
     + graph plot
     + graph plot with contracted nodes
     + hashtag & words frequency list
     + hashtags & words barChart
     + timeseries plot (tweet count & hashtag count(
     + wordclouds (high degree nodes, high frequency hashtags, high frequency words)
     
     

#### **Data Management with mongoDB**:
 + load json twitter files into mongoDB
 
     *The logic is setup so that you can run the same file multiple times. It won't load the same file twice. And if something fails, it starts from where it stopped.
     
 + create aggreation collections with data for EDA (e.g. tweetCountByFile, hashtagCount, tweetCountByLanguageAgg, tweetCountByPeriodAgg, tweetCountByUser)
 + break text into words
 + create collection with hashtags for each tweet
 + create collection with edges between users formed by replies, retweets, quotes and mentions
 + create collection with users info 
 + export data into \t delimeted files that can be opened as CSV files
 + run different topic model analysis for hashtags groups  
  
 
#### **Graph Analysis** 

 + load a networkx file from node/edge files
 + print measurements from graph (Diameter, Radius, Extrema bounding, Centers with their degree, # Nodes, # Edges)
 + plot graph
 + plot graph with clusters (spectral clustering / Louvain Community)
 + contract nodes
 
  
#### **Topic Analysis** 

 + train topic model
 + plot topic distribution
 + plot frequency lists (hashtags, word frequency)
 
 
