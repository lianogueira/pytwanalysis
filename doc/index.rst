.. pytwanalysis documentation master file, created by
   sphinx-quickstart on Tue Sep  1 14:38:26 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pytwanalysis's documentation!
========================================

A tool to gather, discover, and analyze Twitter data using a combination of graph-clustering and topic modeling techniques with the goal of semantically grouping tweet messages together.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   tutorial 
   reference
   datadictionary
   galery
   
   

*****************************************
Twitter Analysis
*****************************************

This package allows the user to load Twitter documents into a MongoDB database, process and analyze the data.

**Things you can do with this library:**
---------------------------------

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
     
     
**Data Management with mongoDB**:
---------------------------------
 + load json twitter files into mongoDB
 
     *The logic is setup so that you can run the same file multiple times. It won't load the same file twice. And if something fails, it starts from where it stopped.
     
 + create aggreation collections with data for EDA (e.g. tweetCountByFile, hashtagCount, tweetCountByLanguageAgg, tweetCountByPeriodAgg, tweetCountByUser)
 + break text into words
 + create collection with hashtags for each tweet
 + create collection with edges between users formed by replies, retweets, quotes and mentions
 + create collection with users info 
 + export data into \t delimeted files that can be opened as CSV files
 + run different topic model analysis for hashtags groups  
  
 
**Graph Analysis** 
---------------------------------

 + load a networkx file from node/edge files
 + print measurements from graph (Diameter, Radius, Extrema bounding, Centers with their degree, # Nodes, # Edges)
 + plot graph
 + plot graph with clusters (spectral clustering / Louvain Community)
 + contract nodes
 
  
**Topic Analysis** 
---------------------------------

 + train topic model
 + plot topic distribution
 + plot frequency lists (hashtags, word frequency)
 
 

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`





