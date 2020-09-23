Tutorial
==================


This guide can help you start working with pytwanalysis.


Initialize package
-------------------

Initialize package::

	>>> import pytwanalysis as ta
	

Set your mongoDB connection::

	>>> from pymongo import MongoClient		
	>>> mongoDBConnectionSTR = "mongodb://localhost:27017"
	>>> client = MongoClient(mongoDBConnectionSTR)
	>>> db = client.twitter_DB_API_test1 #choose your DB name here
	

Initialize your TwitterAnalysis object::

	>>> # Set up the folder path you want to save all of the output files
	>>> BASE_PATH = 'D:\\Data\\MyFiles'
	>>> # create object of type TwitterAnalysis
	>>> myAnalysis = ta.TwitterAnalysis(BASE_PATH, db)
	
	
	
Import Data
-------------------

Import data from json files into the mongoDB database::

	>>> # This is the folder path where all of your twitter json files should be
	>>> JSON_FILES_PATH = 'D:\\Data\\tests\\my_json_files'	
	
	>>> # Load json files into mongoDB
	>>> myAnalysis.loadDocFromFile(JSON_FILES_PATH)


Request data from Twitter's 7-day Search API::

	>>> # you authentication keys here - (you can retrive these from your Twitter's developer account)
	>>> consumer_key = '[your consumer_key]'
	>>> consumer_secret = '[yourconsumer_secret]'
	>>> access_token = '[your access_token]'
	>>> access_token_secret = '[your access_token_secret]'
	>>> query='term1 OR term2 OR term3'
	
	>>> # send the request to Twitter and save data into MongoDB
	>>> response = myAnalysis.search7dayapi(
	>>> 		consumer_key, 
	>>> 		consumer_secret, 
	>>> 		access_token, 
	>>> 		access_token_secret, 
	>>> 		query, 
	>>> 		result_type= 'mixed', 
	>>> 		max_count='100', 
	>>> 		lang='en')
	

Request data from Twitter's Premium Search API::

	>>> # options are "30day" or fullarchive
	>>> api_name = "fullarchive"

	>>> # the name of your dev environment  - (The one associate with your Twitter developer account)
	>>> dev_environment = "FullArchDev.json"

	>>> # your query
	>>> query = "(term1 OR term2 OR term3) lang:en"

	>>> # start and end date
	>>> date_start = "202002150000"
	>>> date_end = "202002160000"

	>>> # twitter bearear authentication - (this can be generated from your authentication keys)
	>>> twitter_bearer = '[your bearer authentication]'

	>>> # send the request to Twitter and save data into MongoDB
	>>> response, next_token = myAnalysis.searchPremiumAPI(
	>>> 		twitter_bearer, 
	>>> 		api_name, 
	>>> 		dev_environment, 
	>>> 		query, 
	>>> 		date_start, 
	>>> 		date_end, 
	>>> 		next_token = None, 
	>>> 		max_count='10')
	>>> print (next_token)
	eyJtYXhJZCI6MTIyODgzMTM1MTU1MTUxMjU3N30=
	



Create Collections
-------------------

Create database collections that will be used to analyze the data. (Depending on the size of your data, this could take a while).
After this step, you should see all collections in your MongoDB database. You cannot  go forward with your analysis without having this step complete::
	>>> # You can set the number of tweets to load at a time. 
	>>> # (Large number may cause out of memory errors; low number may take a long time to run)
	>>> step = 50000

	>>> # Build collections
	>>> myAnalysis.build_db_collections(step)



Create Edges
-------------------

Export edges from MongoDB. This step will create edge files that will be used for graph analysis::

	>>> # Set up the periods you want to analyze  
	>>> # Set period_arr to None if you don't want to analyze separate periods
	>>> # Format: Period Name, Period Start Date, Period End Date
	>>> period_arr = [['P1', '10/08/2017 00:00:00', '10/15/2017 00:00:00'],             
	>>>               ['P2', '01/21/2018 00:00:00', '02/04/2018 00:00:00'],              
	>>>               ['P3', '02/04/2018 00:00:00', '02/18/2018 00:00:00'],
	>>>               ['P4', '02/18/2018 00:00:00', '03/04/2018 00:00:00']]


	>>> ## TYPE OF GRAPH EDGES
	>>> ########################################################
	>>> # You can export edges for one type, or for all
	>>> # Options: user_conn_all,       --All user connections
	>>> #          user_conn_mention,   --Only Mentions user connections
	>>> #          user_conn_retweet,   --Only Retweets user connections
	>>> #          user_conn_reply,     --Only Replies user connections
	>>> #          user_conn_quote,     --Only Quotes user connections
	>>> #          ht_conn              --Hashtag connects - (Hashtgs that were used together)
	>>> #          all                  --It will export all of the above options

	>>> TYPE_OF_GRAPH = 'all'

	>>> myAnalysis.export_mult_types_edges_for_input(period_arr=period_arr, type_of_graph=TYPE_OF_GRAPH)

	
EDA
-------------------
Create Exploratory Data Analysis Files. This will show you the summary information about your data::

	>>> myAnalysis.eda_analysis()
	
	
	
Create All Analysis Files
--------------------------

It creates all folders and analysis files based on your given settings.


IMPORTANT STEP: Choose your settings here before running the automation analysis.

These variables will help you decide what files you want to see and with which parameters 

Running the analysis step could take a long time. 
If you want to run piece by piece so you can see results soon, you can change the flags to 'Y' one at the time
	
	
Choose the type of graph to analyze::
	
	>>> ## TYPE OF GRAPH ANALYSIS
	>>> ########################################################
	>>> # Type of graph analysis
	>>> # Options: user_conn_all,       --All user connections
	>>> #          user_conn_mention,   --Only Mentions user connections
	>>> #          user_conn_retweet,   --Only Retweets user connections
	>>> #          user_conn_reply,     --Only Replies user connections
	>>> #          user_conn_quote,     --Only Quotes user connections
	>>> #          ht_conn              --Hashtag connects - (Hashtgs that were used together)
	
	>>> TYPE_OF_GRAPH = 'user_conn_all'
	>>> #------------------------------------------------------------
	
Decide the output path, periods to analyze, and bot settings
	
	>>> 	# Path where you want to save your output files
	>>> 	# It will use the path you already set previously, 
	>>> 	# but you can change here in case you want a new path
	>>> 	OUTPUT_PATH = BASE_PATH  

	>>> 	#Filter bots or not. Options: (None, '0', or '1')
	>>> 	IS_BOT_FILTER = None

	>>> 	# Same period array you already set previously. 
	>>> 	# You can change here in case you want something new, 
	>>> 	# just follow the same format as array in previous step
	>>> 	PERIOD_ARR =  [['P1', '10/08/2017 00:00:00', '10/15/2017 00:00:00'],             
	>>> 				  ['P2', '01/21/2018 00:00:00', '02/04/2018 00:00:00'],              
	>>> 				  ['P3', '02/04/2018 00:00:00', '02/18/2018 00:00:00'],
	>>> 				  ['P4', '02/18/2018 00:00:00', '03/04/2018 00:00:00']]     
	>>> 	#------------------------------------------------------------
	
	
Decide what types of files to create and with what options::

	>>> # Creates a separate folder for the top degree nodes
	>>> #------------------------------------------------------------
	>>> CREATE_TOP_NODES_FILES_FLAG = 'Y'
	>>> # IF you chose CREATE_TOP_NODES_FILES_FLAG='Y', you can also set these settings
	>>> # We will create subfolder for the top degree nodes based on these number
	>>> TOP_DEGREE_START = 1   
	>>> TOP_DEGREE_END = 25
	>>> # We will create subfolders for the top degree nodes 
	>>> # for each period based on these numbers
	>>> PERIOD_TOP_DEGREE_START = 1
	>>> PERIOD_TOP_DEGREE_END = 10

	>>> # Creates files with the edges of each folder 
	>>> # and a list of nodes and their degree
	>>> #------------------------------------------------------------
	>>> CREATE_NODES_EDGES_FILES_FLAG = 'Y'

	>>> # Creates the graph visualization files
	>>> #------------------------------------------------------------
	>>> CREATE_GRAPHS_FILES_FLAG = 'Y'

	>>> # Creates files for topic discovery
	>>> #------------------------------------------------------------
	>>> # Tweet texts for that folder, word cloud, and LDA Model Visualization
	>>> CREATE_TOPIC_MODEL_FILES_FLAG = 'Y'
	>>> # If you chose CREATE_TOPIC_MODEL_FILES_FLAG='Y', you can also set this setting
	>>> # This is the number of topics to send as input to LDA model (Default is 4)
	>>> NUM_OF_TOPICS = 4

	>>> # Creates files with ht frequency
	>>> #------------------------------------------------------------
	>>> # Text files with all hashtags used, wordcloud, and barchart
	>>> CREATE_HT_FREQUENCY_FILES_FLAG = 'Y'	


	>>> # Creates files with word frequency
	>>> #------------------------------------------------------------
	>>> # Text files with all hashtags used, wordcloud, and barchart
	>>> CREATE_WORDS_FREQUENCY_FILES_FLAG = 'Y'
	>>> # If you answer yes to CREATE_WORDS_FREQUENCY_FILES_FLAG, then you can choose
	>>> # how many words you want to see in your list file.
	>>> # The number of words to save on the frequency word list file. (Default=5000)
	>>> TOP_NO_WORD_FILTER = 5000   


	>>> # Creates files with time series data
	>>> #------------------------------------------------------------
	>>> CREATE_TIMESERIES_FILES_FLAG = 'Y'


	>>> # Creates graphs with hashtag information
	>>> #------------------------------------------------------------
	>>> # This can be used when you're analyzing user connections, 
	>>> # but still want to see the hashtag connection graph for that group of users
	>>> CREATE_HT_CONN_FILES_FLAG = 'Y'
	>>> # IF you chose CREATE_HT_CONN_FILES_FLAG = 'Y', you can also set this setting
	>>> # This is to ignore the top hashtags in the visualization
	>>> # Sometimes ignoring the main hashtag can be helpful in visualization to
	>>> # discovery other important structures within the graph
	>>> TOP_HT_TO_IGNORE = 2


	>>> # Creates louvain communities folder and files
	>>> #------------------------------------------------------------
	>>> CREATE_COMMUNITY_FILES_FLAG = 'N'
	>>> # If set CREATE_COMMUNITY_FILES_FLAG = 'Y', then you can
	>>> # set a cutoff number of edges to identify when a folder should be created
	>>> # If the commty has less edges than this number, it won't create a new folder
	>>> # Default is 200
	>>> COMMTY_EDGE_SIZE_CUTOFF = 200 
	>>> #------------------------------------------------------------

	>>> ## GRAPH OPTIONS #######################################
	>>> ########################################################

	>>> # In case you want to print full graph, with no reduction, and without node scale
	>>> CREATE_GRAPH_WITHOUT_NODE_SCALE_FLAG = 'Y'
	>>> # In case you want to print full graph, with no reduction, but with node scale
	>>> CREATE_GRAPH_WITH_NODE_SCALE_FLAG = 'Y'
	>>> # In case you want to print reduced graph
	>>> CREATE_REDUCED_GRAPH_FLAG = 'Y'
	
	>>> # This is the cutoff number of edges to decide if we will print 
	>>> # the graph or not. The logic will remove nodes until it can get 
	>>> # to this max number of edges to plot
	>>> # If you choose a large number it may take a long time to run. 
	>>> # If you choose a small number it may contract nodes too much or not print the graph at all
	>>> GRAPH_PLOT_CUTOFF_NO_NODES = 3000
	>>> GRAPH_PLOT_CUTOFF_NO_EDGES = 10000

	>>> # Reduced Graph settings
	>>> #------------------------------------------------------------
	>>> # This is a percentage number used to remove nodes
	>>> # so we can be able to plot large graphs. 
	>>> # You can run this logic multiple times with different percentages. 
	>>> # Each time the logic will save the graph file with a different name 
	>>> # according to the parameter given
	>>> REDUCED_GRAPH_COMTY_PER = 90
	
	>>> # Reduce graph by removing edges with weight less than this number
	>>> # None if you don't want to use this reduction method
	>>> REDUCED_GRAPH_REMOVE_EDGE_WEIGHT = None   
	
	>>> # Continuously reduce graph until it gets to the GRAPH_PLOT_CUTOFF numbers or to 0
	>>> REDUCED_GRAPH_REMOVE_EDGES_UNTIL_CUTOFF_FLAG = 'Y'
	>>> #------------------------------------------------------------


Set configuration with your choices::

	>>> # Set configurations
	>>> myAnalysis.setConfigs(type_of_graph=TYPE_OF_GRAPH,
	>>>             is_bot_Filter=IS_BOT_FILTER,
	>>>             period_arr=PERIOD_ARR,
	>>>             create_nodes_edges_files_flag=CREATE_NODES_EDGES_FILES_FLAG, 
	>>>             create_graphs_files_flag=CREATE_GRAPHS_FILES_FLAG,
	>>>             create_topic_model_files_flag=CREATE_TOPIC_MODEL_FILES_FLAG,
	>>>             create_ht_frequency_files_flag=CREATE_HT_FREQUENCY_FILES_FLAG,
	>>>             create_words_frequency_files_flag=CREATE_WORDS_FREQUENCY_FILES_FLAG,
	>>>             create_timeseries_files_flag=CREATE_TIMESERIES_FILES_FLAG,
	>>>             create_top_nodes_files_flag=CREATE_TOP_NODES_FILES_FLAG, 
	>>>             create_community_files_flag=CREATE_COMMUNITY_FILES_FLAG,
	>>>             create_ht_conn_files_flag=CREATE_HT_CONN_FILES_FLAG,
	>>>             num_of_topics=NUM_OF_TOPICS, 
	>>>             top_no_word_filter=TOP_NO_WORD_FILTER, 
	>>>             top_ht_to_ignore=TOP_HT_TO_IGNORE,
	>>>             graph_plot_cutoff_no_nodes=GRAPH_PLOT_CUTOFF_NO_NODES, 
	>>>             graph_plot_cutoff_no_edges=GRAPH_PLOT_CUTOFF_NO_EDGES,
	>>>             create_graph_without_node_scale_flag=CREATE_GRAPH_WITHOUT_NODE_SCALE_FLAG, 
	>>>             create_graph_with_node_scale_flag=CREATE_GRAPH_WITH_NODE_SCALE_FLAG, 
	>>>             create_reduced_graph_flag=CREATE_REDUCED_GRAPH_FLAG,
	>>>             reduced_graph_comty_contract_per=REDUCED_GRAPH_COMTY_PER,
	>>>             reduced_graph_remove_edge_weight=REDUCED_GRAPH_REMOVE_EDGE_WEIGHT, 
	>>>             reduced_graph_remove_edges=REDUCED_GRAPH_REMOVE_EDGES_UNTIL_CUTOFF_FLAG,                            
	>>>             top_degree_start=TOP_DEGREE_START, 
	>>>             top_degree_end=TOP_DEGREE_END, 
	>>>             period_top_degree_start=PERIOD_TOP_DEGREE_START, 
	>>>             period_top_degree_end=PERIOD_TOP_DEGREE_END, 
	>>>             commty_edge_size_cutoff=COMMTY_EDGE_SIZE_CUTOFF
	>>>             )

	
Create all folders and files based on your choices::

	>>> myAnalysis.edge_files_analysis(output_path=OUTPUT_PATH)



The following is a list of the possible analysis files that will get created in each folder:

+ **G_Measures-(All).txt:** Some metrics of the graph. (e.g. total number of nodes and edges).

+ **G_Measures-(LargestCC).txt:** Some metrics of the  largest connected component of the graph. (e.g. total number of nodes and edges).

+ **G_Edges.txt:** List of edges and their respective weight.

+ **G_NodesWithDegree.txt:** List of all nodes with their respective degrees.

+ **G_Nodes_WordCloud.png:** Word cloud representing the nodes in the graph, weighted by the node's degree

+ **G_Graph.png:** Plot of the full graph without any reduction. The size of the nodes are scaled based on the node's degree.

+ **G_Graph(WithoutScale).png:** Plot of the full graph without any reduction and without any scale for the node size.

+ **G_Graph-(ReducedGraph)[%Parameters].png:** Plot of the graph after reduction. The parameters used for reduction will appear in the file name inside brackets.

+ **T_tweetTextsForTopics.txt:** Tweet texts excluding some special characters, stop words, hashtags, and mentions 

+ **Topics-(LDA model).png:** Topic discovery plot using LDA model 

+ **T_HT_FrequencyList.txt:** A list of all hashtags and the number of times they were used 

+ **T_HT_Top30_BarChart.png:** A Bar Chart showing the top 30 hashtags 

+ **T_HT_Top30_BarChart-(Excluding Top1).png:** A Bar Chart showing the top hashtags, excluding the top 1 

+ **T_HT_Top30_BarChart-(Excluding Top2).png:** A Bar Chart showing the top hashtags, excluding the top 2 

+ **T_HT_WordCloud.png:** Word cloud representing the hashtags used, weighted by their frequency 

+ **T_Words_FrequencyList.txt:** A list of the top words used and the number of times they were used. 

+ **T_Words_Top30_BarChart.png:** A Bar Chart showing the top 30 words 

+ **T_Words_WordCloud.png:** Word cloud representing the words used, weighted by their frequency. 

+ **TS_TweetCount.png**: Timeseries graph showing the tweet count by day.

+ **TS_TweetCountByHT[1-5]:** Timeseries graph showing the hash count by day of the the top 5 hashtags.

+ **ht_edges.txt:** List of hashtag edges created based on the connections made by two hashtags being used on the same tweet. This files is used to create the hashtag connections graph.

+ **HTG_G_Graph.png:** Hashtag connection graph.

+ **HTG_G_Graph-(ReducedGraph)[%Parameters].png**: Reduced hashtag connection graph. The parameters used for reduction will appear in the file name inside brackets.



Even though the files can be generated automatically, you can also run separate steps manually. 


Manual Analysis Examples
-------------------------

Some example of how to use the individual methods of this library in case you don't want to use the automation to create all files.


Create LDA Analysis files::
	>>> myAnalysis.lda_analysis_files(
	>>> 	'D:\\Data\\MyFiles', 
	>>> 	startDate_filter='09/20/2020 00:00:00', 
	>>> 	endDate_filter='03/04/2021 00:00:00')
	
	
Create hashtag frequency Analysis files::
	>>> myAnalysis.ht_analysis_files(
	>>> 	'D:\\Data\\MyFiles', 
	>>> 	startDate_filter='09/20/2020 00:00:00', 
	>>> 	endDate_filter='03/04/2021 00:00:00')
	
Create word frequency Analysis files::
	>>> myAnalysis.words_analysis_files(
	>>> 	'D:\\Data\\MyFiles', 
	>>> 	startDate_filter='09/20/2020 00:00:00', 
	>>> 	endDate_filter='03/04/2021 00:00:00')

Create timeseries frequency Analysis files::
	>>> ...
	
Create nodes and edges Analysis files::
	>>> ...
	
Create networkx graph from edge file::
	>>> edge_file_path = 'C:\\MyPath\\edges.txt'
	G = myAnalysis.loadGraphFromFile(edge_file_path)
	
Plot graph given networkx graph G::
	>>> ...
	
Plot graph given networkx graph G::
	>>> ...
	
Calculate louvain_clustering::
	>>> G2, labels, k = myAnalysis.calculate_louvain_clustering(G)
	
Calculate spectral_clustering::
	>>> G2, labels, k = myAnalysis.calculate_spectral_clustering(G, k=5)	
	
Print clustering metrics for community_louvain clustering method::
	>>> myAnalysis.print_commty_cluster_metrics(
	>>> 	G, 
	>>> 	comm_att = 'community_louvain', 
	>>> 	ignore_cmmty_lt=100, 
	>>> 	acc_node_size_cutoff=30000)

Print clustering metrics for the top 25 nodes clusters::
	>>> myAnalysis.print_top_nodes_cluster_metrics(
	>>> 	G, 
	>>> 	25, 
	>>> 	acc_node_size_cutoff=30000)
	
Compress graphs::
	>>> ... 
	
Get Largest Connected Component::
	>>> ...	
		
Plot Community Distribution::
	>>> ...	
	
	
There are many other options of manual analysis you can do. Explore the methods available on the Reference section of this documentation for more.