
from pytwanalysis.py_twitter_db import TwitterDB
from pytwanalysis.py_twitter_graphs import TwitterGraphs
from pytwanalysis.py_twitter_topics import TwitterTopics

#from pyTwitterGraphAnalysis import tw_graph
#from pyTwitterDB import tw_database
#from pyTwitterTopics import tw_topics


from pymongo import MongoClient
import networkx as nx
import numpy as np
import os
import datetime
import csv
import pandas as pd
import matplotlib.pyplot as plt
import time

import warnings
warnings.filterwarnings("ignore")


MIN_NO_OF_NODES_TO_REDUCE_GRAPH = 100


class TwitterAnalysis(TwitterGraphs, TwitterDB, TwitterTopics):
    """
    Main class - It inherits TwitterGraphs, TwitterDB, and TwitterTopics classes.    
    """
    def __init__(
            self, 
            base_folder_path, 
            mongoDB_database):
        
        TwitterGraphs.__init__(self, base_folder_path)
        TwitterDB.__init__(self, mongoDB_database)
        TwitterTopics.__init__(self, base_folder_path, mongoDB_database)

        self.type_of_graph = 'user_conn_all'
        self.is_bot_Filter = None
        self.period_arr = None
        self.create_nodes_edges_files_flag = 'Y'
        self.create_graphs_files_flag ='Y' 
        self.create_topic_model_files_flag = 'Y' 
        self.create_ht_frequency_files_flag = 'Y' 
        self.create_words_frequency_files_flag = 'Y'
        self.create_timeseries_files_flag = 'Y'
        self.create_top_nodes_files_flag = 'Y' 
        self.create_community_files_flag = 'N'
        self.create_ht_conn_files_flag = 'Y'
        self.num_of_topics = 4
        self.top_no_word_filter = None
        self.top_ht_to_ignore = None
        self.graph_plot_cutoff_no_nodes = 500
        self.graph_plot_cutoff_no_edges = 2000
        self.create_graph_without_node_scale_flag = 'N'
        self.create_graph_with_node_scale_flag = 'Y'
        self.create_reduced_graph_flag = 'Y'
        self.reduced_graph_comty_contract_per = 90 
        self.reduced_graph_remove_edge_weight = None
        self.reduced_graph_remove_edges = 'Y'
        self.top_degree_start = 1
        self.top_degree_end = 10
        self.period_top_degree_start = 1
        self.period_top_degree_end = 5
        self.commty_edge_size_cutoff = 200
        self.user_conn_filter = None
        self.edge_prefix_str = 'UserConnections_'
        

        
    #####################################
    # Method: setConfigs
    # Description: Configure objects settings
    def setConfigs(
            self,
            type_of_graph='user_conn_all', 
            is_bot_Filter=None, 
            period_arr=None, 
            create_nodes_edges_files_flag='Y', 
            create_graphs_files_flag='Y', 
            create_topic_model_files_flag='Y', 
            create_ht_frequency_files_flag='Y', 
            create_words_frequency_files_flag='Y', 
            create_timeseries_files_flag='Y',   
            create_top_nodes_files_flag = 'Y', 
            create_community_files_flag = 'N', 
            create_ht_conn_files_flag='Y',
            num_of_topics=4, 
            top_no_word_filter=None, 
            top_ht_to_ignore=None, 
            graph_plot_cutoff_no_nodes=500, 
            graph_plot_cutoff_no_edges=2000,
            create_graph_without_node_scale_flag='N', 
            create_graph_with_node_scale_flag='Y', 
            create_reduced_graph_flag='Y',
            reduced_graph_comty_contract_per=90,  
            reduced_graph_remove_edge_weight=None, 
            reduced_graph_remove_edges='Y',                            
            top_degree_start=1, 
            top_degree_end=10, 
            period_top_degree_start=1, 
            period_top_degree_end=5, 
            commty_edge_size_cutoff=200):
            
        """
        Configure the current object settings to drive the automation of the analysis files
                
        Parameters
        ----------               
        type_of_graph : (Optional)
            This setting defines the type of graph to analyze. Six different options are available: user_conn_all, user_conn_retweet, user_conn_quote, user_conn_reply, user_conn_mention, and ht_conn.
            (Default='user_conn_all')
        
        is_bot_Filter : (Default=None)
        
        period_arr : (Optional)
            An array of start and end dates can be set so that the pipeline creates a separate analysis folder for each of the periods in the array. (Default=None)
        
        create_nodes_edges_files_flag : (Optional)
            If this setting is set to 'Y', the pipeline will create two files for each graph and sub-graph. One file with the edge list, and one with the node list and their respective degree.(Default='Y') 
        
        create_graphs_files_flag : (Optional)
            If this setting is set to 'Y', the pipeline will plot the graph showing all the connections.
            (Default='Y')
        
        create_topic_model_files_flag : (Optional)
            If this setting is set to 'Y', the pipeline will create topic discovery related files for each folder. It will create a text file with all the tweets that are part of that folder, it will also train a LDA model based on the tweets texts and plot a graph with the results.
            (Default='Y')
        
        create_ht_frequency_files_flag : (Optional)
            If this setting is set to 'Y', the pipeline will create hashtag frequency files for each folder. It will create a text file with the full list of hashtags and their frequency, a wordcloud showing the most frequently used hashtags, and barcharts showing the top 30 hashtags.
            (Default='y')'
        
        create_words_frequency_files_flag : (Optional)
            If this setting is set to 'Y', the pipeline will create word frequency files for each folder. It will create a text file with a list of words and their frequency, a wordcloud showing the most frequently used words, and barcharts showing the top 30 words.
            (Default='Y') 
        
        create_timeseries_files_flag : (Optional)
            If this setting is set to 'Y', the pipeline will create timeseries graphs for each folder representing the tweet count by day, and the top hashtags frequency count by day.
            (Default='Y')    
        
        create_top_nodes_files_flag : (Optional)
            If this setting is set to 'Y', the pipeline will create separate analysis folders for all the top degree nodes.
            (Default='Y') 
        
        create_community_files_flag : (Optional)
            If this setting is set to 'Y', the pipeline will use the louvain method to assign each node to a community. A separate folder for each of the communities will be created with all the analysis files.
            (Default='N') 
        
        create_ht_conn_files_flag : (Optional)
            If this setting is set to 'Y', the pipeline will plot hashtag connections graphs. This can be used when user connections are being analyzed, but it could still be interesting to see the hashtags connections made by that group of users.
            (Default='Y') 
        
        num_of_topics : (Optional)
            If the setting *CREATE_TOPIC_MODEL_FILES_FLAG* was set to 'Y', then this number will be used to send as input to the LDA model. If no number is given, the pipeline will use 4 as the default value.
            (Default=4) 
        
        top_no_word_filter : (Optional)
            If the setting *CREATE_WORDS_FREQUENCY_FILES_FLAG* was set to 'Y', then this number will be used to decide how many words will be saved in the word frequency list text file. If no number is given, the pipeline will use 5000 as the default value.
            (Default=None)
        
        top_ht_to_ignore : (Optional)
            If the setting *CREATE_HT_CONN_FILES_FLAG* was set to 'Y', then this number will be used to choose how many top hashtags can be ignored. Sometimes ignoring the main hashtag can be helpful in visualizations to discovery other interesting structures within the graph.
            (Default=None)
        
        graph_plot_cutoff_no_nodes : (Optional)
            Used with the graph_plot_cutoff_no_edges parameter. For each graph created, these numbers will be used as cutoff values to decide if a graph is too large to be plot or not. Choosing a large number can result in having the graph to take a long time to run. Choosing a small number can result in graphs that are too reduced and with little value or even graphs that can't be printed at all because they can't be reduce further. 
            (Default=500) 
        
        graph_plot_cutoff_no_edges : (Optional) 
            Used with the graph_plot_cutoff_no_nodes parameter. For each graph created, these numbers will be used as cutoff values to decide if a graph is too large to be plot or not. Choosing a large number can result in having the graph to take a long time to run. Choosing a small number can result in graphs that are too reduced and with little value or even graphs that can't be printed at all because they can't be reduce further. 
            (Default=2000)
        
        create_graph_without_node_scale_flag : (Optional)
            For each graph created, if this setting is set to 'Y', the pipeline will try to plot the full graph with no reduction and without any logic for scaling the node size.
            (Default='N') 
        
        create_graph_with_node_scale_flag : (Optional)
            For each graph created, if this setting is set to 'Y', the pipeline will try to plot the full graph with no reduction, but with additional logic for scaling the node size.
            (Default='Y') 
        
        create_reduced_graph_flag : (Optional)
            For each graph created, if this setting is set to 'Y', the pipeline will try to plot the reduced form of the graph.
            (Default='Y') 
        
        reduced_graph_comty_contract_per : (Optional)
            If the setting *CREATE_REDUCED_GRAPH_FLAG* was set to 'Y', then this number will be used to reduce the graphs by removing a percentage of each community found in that particular graph. The logic can be run multiple times with different percentages. For each time, a new graph file will be saved with a different name according to the parameter given.
            (Default=90) 
        
        reduced_graph_remove_edge_weight : (Optional)
            If the setting *CREATE_REDUCED_GRAPH_FLAG* was set to 'Y', then this number will be used to reduce the graphs by removing edges that have weights smaller then this number. The logic can be run multiple times with different percentages. For each time, a new graph file will be saved with a different name according to the parameter given.
            (Default=None)
        
        reduced_graph_remove_edges : (Optional)
            If this setting is set to 'Y', and the setting *CREATE_REDUCED_GRAPH_FLAG was set to 'Y', then the pipeline will continuously try to reduce the graphs by removing edges of nodes with degrees smaller than this number. It will stop the graph reduction once it hits the the values set int the GRAPH_PLOT_CUTOFF parameters.
            (Default='Y')     
        
        top_degree_start : (Optional)
            If the setting  *CREATE_TOP_NODES_FILES_FLAG* was set to 'Y', then these numbers will define how many top degree node sub-folders to create.
            (Default=1) 
        
        top_degree_end : (Optional)
            If the setting  *CREATE_TOP_NODES_FILES_FLAG* was set to 'Y', then these numbers will define how many top degree node sub-folders to create.
            (Default=10) 
        
        period_top_degree_start : (Optional)
            If the setting  *CREATE_TOP_NODES_FILES_FLAG* was set to 'Y', then these numbers will define how many top degree node sub-folders for each period to create.
            (Default=1) 
        
        period_top_degree_end : (Optional)
            If the setting  *CREATE_TOP_NODES_FILES_FLAG* was set to 'Y', then these numbers will define how many top degree node sub-folders for each period to create.
            (Default=5) 
        
        commty_edge_size_cutoff : (Optional)
            If the setting textit{CREATE_COMMUNITY_FILES_FLAG} was set to 'Y', then this number will be used as the community size cutoff number. Any communities that have less nodes then this number will be ignored. If no number is given, the pipeline will use 200 as the default value.
            (Default=200)                 
        
        Examples
        --------          
        ...:
        
            >>> setConfigs(type_of_graph=TYPE_OF_GRAPH,
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
            
        """
                
        self.type_of_graph = type_of_graph
        self.is_bot_Filter = is_bot_Filter
        self.period_arr = period_arr
        self.create_nodes_edges_files_flag = create_nodes_edges_files_flag
        self.create_graphs_files_flag = create_graphs_files_flag
        self.create_topic_model_files_flag = create_topic_model_files_flag
        self.create_ht_frequency_files_flag = create_ht_frequency_files_flag
        self.create_words_frequency_files_flag = create_words_frequency_files_flag
        self.create_timeseries_files_flag = create_timeseries_files_flag
        self.create_top_nodes_files_flag = create_top_nodes_files_flag
        self.create_community_files_flag = create_community_files_flag
        self.create_ht_conn_files_flag = create_ht_conn_files_flag
        self.num_of_topics = num_of_topics
        self.top_no_word_filter = top_no_word_filter
        self.top_ht_to_ignore = top_ht_to_ignore
        self.graph_plot_cutoff_no_nodes = graph_plot_cutoff_no_nodes
        self.graph_plot_cutoff_no_edges = graph_plot_cutoff_no_edges
        self.create_graph_without_node_scale_flag = create_graph_without_node_scale_flag
        self.create_graph_with_node_scale_flag = create_graph_with_node_scale_flag
        self.create_reduced_graph_flag = create_reduced_graph_flag
        self.reduced_graph_comty_contract_per = reduced_graph_comty_contract_per
        self.reduced_graph_remove_edge_weight = reduced_graph_remove_edge_weight
        self.reduced_graph_remove_edges = reduced_graph_remove_edges
        self.top_degree_start = top_degree_start
        self.top_degree_end = top_degree_end
        self.period_top_degree_start = period_top_degree_start
        self.period_top_degree_end = period_top_degree_end
        self.commty_edge_size_cutoff = commty_edge_size_cutoff
                
        if self.type_of_graph == 'user_conn_all':
            self.edge_prefix_str = 'UserConnections_'                
        elif self.type_of_graph == 'user_conn_mention':
            self.edge_prefix_str = 'MentionUserConnections_'
            self.user_conn_filter = 'mention'
        elif self.type_of_graph == 'user_conn_retweet':
            self.edge_prefix_str = 'RetweetUserConnections_'
            self.user_conn_filter = 'retweet'
        elif self.type_of_graph == 'user_conn_reply':
            self.edge_prefix_str = 'ReplyUserConnections_'
            self.user_conn_filter = 'reply'
        elif self.type_of_graph == 'user_conn_quote':
            self.edge_prefix_str = 'QuoteUserConnections_'
            self.user_conn_filter = 'quote'
        elif self.type_of_graph == 'ht_conn':
            self.edge_prefix_str = 'HTConnection_'
            self.export_type = 'ht_edges'
        
        
    #####################################
    # Method: create_path
    # Description: creates a path to add the files for this node        
    def create_path(self, path):       
        if not os.path.exists(path):
            os.makedirs(path)
            
    #####################################
    # Method: get_now_dt
    # Description: returns formated current timestamp to be printed
    def get_now_dt(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #####################################
    # Method: concat_edges
    # Description: aux function to concatenate edges to help filter in mongoDB
    def concat_edges(self, G):
        """
        Aux function to concatenate edges to help filter in mongoDB
                
        Parameters
        ----------               
        G : 
            undirected networkx graph created from the Twitter data                               
        
        Returns
        -------
        arr_edges
            the array with the concatenatd edges            
    
        Examples
        --------          
        Create an array of concatenated edges from a networkx graph:
        
            >>> arr_edges = concat_edges(G)
        """
        
        arr_edges = []                        
        for u,v,a in G.edges(data=True):
            arr_edges.append(u.lower() + '-' +v.lower())
            arr_edges.append(v.lower() + '-' +u.lower())
                                    
        return arr_edges

    #####################################
    # Method: build_db_collections
    # Description: Call methods to create all collections in mongoDB
    def build_db_collections(self, inc=100000, bots_ids_list_file=None):
        """
        This method is in charge of extracting, cleaning, and loading the data 
        into all the collections in MongoDB. 
       
        Parameters
        ----------               
        inc : (Optional)
            used to determine how many tweets will be processed at a time - (Default=100000).
            A large number may cause out of memory errors, and a low number may take a long time to run, 
            so the decision of what number to use should be made based on the hardware specification.
              
        bots_ids_list_file : (Optional)
            a file that contains a list of user ids that are bots. 
            It creates flags in the MongoDB collection to indentify 
            which tweets and user are in the bots list. - (Default=None)
                 
    
        Examples
        --------          
        Load all data into all collections in MongoDB:
            
            >>> inc = 50000
            >>> build_db_collections(inc)
        """
                
        ### Loading Focused Data into MongoDB
        self.loadFocusedData(inc)
        
        ### Loading user information to collection
        # Loading user information for the actual tweet document
        self.loadUsersData(inc, 'tweet')
        # Loading user information for the original tweet in case of retweets
        self.loadUsersData(inc, 'retweet')
        # Loading user information for the quoted tweet
        self.loadUsersData(inc, 'quote')
        # Loading user information for replies - 
        # (in this case we we don't have full information about the user. Only screen_name and user_id)
        self.loadUsersData(inc, 'reply')
        # Loading user information for mention - 
        # (in this case we we don't have full information about the user. Only screen_name and sometimes user_id)
        self.loadUsersData(inc, 'mention')
        
        ### Breaking tweets into Words        
        self.loadWordsData(inc)
        
        ### Loading tweet connections - 
        # These are the edges formed between users by replies, retweets, quotes and mentions
        self.loadTweetConnections(inc) 
                                
        ### Loading tweet hashtag connections - 
        # These are the edges formed between hash tags being used together in the same tweet        
        self.loadTweetHTConnections(inc) 
        
        #####
        ### loading aggregate collections
        self.loadAggregations('tweetCountByFile')
        self.loadAggregations('tweetCountByLanguageAgg')
        self.loadAggregations('tweetCountByMonthAgg')

        
        # Loading bots list from file - (List of user ids that are bots)
        # SKIP this step if you don't have a bots list        
        if bots_ids_list_file is not None:
            bots_list_id_str = []
            with open(bots_ids_list_file,'r') as f:
                for line in f:
                    line = line.rstrip("\n")
                    bots_list_id_str.append(line)

            self.set_bot_flag_based_on_arr(bots_list_id_str, 10000) 

        


                            
    #####################################
    # Method: plot_graph_contracted_nodes
    # Description: aux function to plot graph. 
    # This steps repets in different parts of this code, so creating a function to avoid repetition
    def plot_graph_contracted_nodes(self, G, file):
        """
        Method to compress and plot graph based on the graph reduction 
        settings that can be updated using the *setConfigs* method.                
                
        Parameters
        ----------               
        G : 
            undirected networkx graph created from the Twitter data
        file :
            the path and name of the graph you want to save
                
        Example
        --------                          
            >>> plot_graph_contracted_nodes(G, 'c:\\Data\\MyGraph.png')
        """

        G2 = G.copy()   
        
        if len(G2.nodes()) > MIN_NO_OF_NODES_TO_REDUCE_GRAPH:                    
                    
            contraction_name = ''

            print("Graph to plot before changes: nodes=" + str(len(G2.nodes)) + " edges=" + str(len(G2.edges)))
            
            
            #in case we want to reduce the graph with edges of weight less than a cutoff number 
            if self.reduced_graph_remove_edge_weight is not None:               
                #find list of edges that have that weigh cutoff
                edges_to_remove = [edge for edge in list(G2.edges(data=True)) if edge[2]['weight'] <= self.reduced_graph_remove_edge_weight]                
                #remove edges for the list
                G2.remove_edges_from(edges_to_remove)                
                #get the largest connected component
                G2 = self.largest_component_no_self_loops(G2)                
                contraction_name = contraction_name + "[RemEdgeWeightLessThan" + str(self.reduced_graph_remove_edge_weight) + "]"
            

            #reduce graph based on a percentage of the nodes for each community
            if self.reduced_graph_comty_contract_per is not None and len(G2.nodes()) > MIN_NO_OF_NODES_TO_REDUCE_GRAPH:
                att = 'community_louvain'                
                G2 = self.contract_nodes_commty_per(G2, self.reduced_graph_comty_contract_per, att)                
                G2 = self.largest_component_no_self_loops(G2)                
                contraction_name = contraction_name + "[RemPercOfComty=" + str(self.reduced_graph_comty_contract_per) + "]"

                
            #In case we want to continue to remove until we get to a cutoff number, another level of contraction
            if self.reduced_graph_remove_edges == 'Y' and len(G2.nodes()) > MIN_NO_OF_NODES_TO_REDUCE_GRAPH:                                
                if len(G2.edges()) > 100000:
                    cutoff_no = 3
                    G2 = self.remove_edges_eithernode(G2, cutoff_no)
                    contraction_name = contraction_name + '[RemEdgeEitherNodeDegCutoff=' + str(cutoff_no) +  ']'
                                    
                cutoff_no = 5
                if (len(G2.nodes()) > self.graph_plot_cutoff_no_nodes) or (len(G2.edges()) > self.graph_plot_cutoff_no_edges):
                    while (len(G2.nodes()) > self.graph_plot_cutoff_no_nodes) or (len(G2.edges()) > self.graph_plot_cutoff_no_edges):
                        
                        G2 = self.remove_edges(G2, cutoff_no)
                        if len(G2.nodes()) > 0:
                            G2 = self.largest_component_no_self_loops(G2)

                        if cutoff_no < 150:
                            cutoff_no += 10
                        elif cutoff_no < 1000:
                            cutoff_no += 100
                        elif cutoff_no < 10000:
                            cutoff_no += 500
                        else:
                            cutoff_no += 1000
                             
                    contraction_name = contraction_name + '[RemEdgeBothNodesDegLessThan=' + str(cutoff_no) +  ']'

            #set up final file name with reduction parameters
            file = file.replace('.', contraction_name + '.')
                

            #get largest connected component after all removals
            if len(G2.edges()) > 0:
                G2 = self.largest_component_no_self_loops(G2)


            #find best settings for the graphs depending on size. You can change these to get better graphs
            if len(G2.edges()) < 450:
                v_scale = 0.01; v_k =0.7; v_iterations=50; v_node_size=2
            elif len(G2.edges()) < 5000:
                v_scale = 2; v_k = 0.6; v_iterations=200; v_node_size=0.8
            elif len(G2.edges()) < 10000:
                v_scale = 1; v_k = 0.1; v_iterations=200; v_node_size=0.6
            elif len(G2.edges()) >= 10000:
                v_scale = 1; v_k = 0.05; v_iterations=500; v_node_size=0.6

            print("Graph to plot after changes: nodes=" + str(len(G2.nodes)) + " edges=" + str(len(G2.edges)))

            
            if (len(G2.nodes()) < self.graph_plot_cutoff_no_nodes and len(G2.edges()) < self.graph_plot_cutoff_no_edges) and len(G2.edges()) != 0:                
                if not os.path.exists(file):
                    G_to_plot, labels2, k = self.calculate_louvain_clustering(G2)                    
                    self.plotSpringLayoutGraph(G_to_plot, 
                                               file, 
                                               v_scale, 
                                               v_k, 
                                               v_iterations, 
                                               cluster_fl='Y', 
                                               v_labels=list(list(labels2)), 
                                               replace_existing_file=False) 



    #####################################
    # Method: export_mult_types_edges_for_input
    # Description: export edges that will be used to create graphs
    # User can choose only one type of graph to export the edges, or export them all
    def export_mult_types_edges_for_input(self, period_arr=None, bot_filter_fl='N', type_of_graph='all'):
        """
        This method will export edges from mongoDB data that can be used to create graphs.
        The user can choose only one type of graph to export the edges, or export them all
                
        Parameters
        ----------
        period_arr : (Optional)
            An array with showing the different periods to be analyzed separatly in the data.
            (Default = None)
            
        bot_filter_fl : (Optional)
            A flag to identify if you want to create extra edge files separating tweets by bots or not.
            This option is only available when the bot flag was updated in mongoDB using method set_bot_flag_based_on_arr.
            (Default='N')
            
        type_of_graph : (Optional)
            the type of graph to export the edges for. 
            Available options: user_conn_all, user_conn_mention, 
            user_conn_retweet, user_conn_reply, user_conn_quote, ht_conn, or all
            (Default='all')
                
        Example
        --------                          
            >>> # Set up the periods you want to analyse 
            >>> # Set period_arr to None if you don't want to analyze separate periods
            >>> # Format: Period Name, Period Start Date, Period End Date
            >>> period_arr = [['P1', '10/08/2017 00:00:00', '10/15/2017 00:00:00'],             
            >>>               ['P2', '01/21/2018 00:00:00', '02/04/2018 00:00:00'],              
            >>>               ['P3', '02/04/2018 00:00:00', '02/18/2018 00:00:00'],
            >>>               ['P4', '02/18/2018 00:00:00', '03/04/2018 00:00:00']]
            >>> 
            >>> 
            >>> ## TYPE OF GRAPH EDGES
            >>> ########################################################
            >>> # You can export edges for one type, or for all
            >>> # Options: user_conn_all,       --All user connections
            >>> #          user_conn_mention,   --Only Mentions user connections
            >>> #          user_conn_retweet,   --Only Retweets user connections
            >>> #          user_conn_reply,     --Only Replies user connections
            >>> #          user_conn_quote,     --Only Quotes user connections
            >>> #          ht_conn              --Hashtag connects - (Hashtgs that wereused together)
            >>> #          all                  --It will export all of the above options
            >>> 
            >>> TYPE_OF_GRAPH = 'all'
            >>> 
            >>> export_mult_types_edges_for_input(period_arr=period_arr, type_of_graph=TYPE_OF_GRAPH)
        """
        
        if type_of_graph == 'all' or type_of_graph == 'user_conn_all':
            self.export_all_edges_for_input(period_arr, bot_filter_fl, type_of_graph='user_conn_all')
        if type_of_graph == 'all' or type_of_graph == 'user_conn_mention':
            self.export_all_edges_for_input(period_arr, bot_filter_fl, type_of_graph='user_conn_mention')
        if type_of_graph == 'all' or type_of_graph == 'user_conn_retweet':
            self.export_all_edges_for_input(period_arr, bot_filter_fl, type_of_graph='user_conn_retweet')
        if type_of_graph == 'all' or type_of_graph == 'user_conn_reply':
            self.export_all_edges_for_input(period_arr, bot_filter_fl, type_of_graph='user_conn_reply')
        if type_of_graph == 'all' or type_of_graph == 'user_conn_quote':
            self.export_all_edges_for_input(period_arr, bot_filter_fl, type_of_graph='user_conn_quote')
        if type_of_graph == 'all' or type_of_graph == 'ht_conn':
            self.export_all_edges_for_input(period_arr, bot_filter_fl, type_of_graph='ht_conn')


        
    #####################################
    # Method: export_all_edges_for_input
    # Description: export edges that will be used to create graphs
    def export_all_edges_for_input(self, period_arr=None, bot_filter_fl='N', type_of_graph='user_conn_all'):
                                
        # Creates path to add the edge files to be used as input
        input_files_path = self.folder_path + '\\data_input_files'
        self.create_path(input_files_path)                    
        
        # 
        edge_prefix_str = ''
        user_conn_filter = None
        export_type = 'edges'
        if type_of_graph == 'user_conn_all':
            edge_prefix_str = 'UserConnections_'                
        elif type_of_graph == 'user_conn_mention':
            edge_prefix_str = 'MentionUserConnections_'
            user_conn_filter = 'mention'
        elif type_of_graph == 'user_conn_retweet':
            edge_prefix_str = 'RetweetUserConnections_'
            user_conn_filter = 'retweet'
        elif type_of_graph == 'user_conn_reply':
            edge_prefix_str = 'ReplyUserConnections_'
            user_conn_filter = 'reply'
        elif type_of_graph == 'user_conn_quote':
            edge_prefix_str = 'QuoteUserConnections_'
            user_conn_filter = 'quote'
        elif type_of_graph == 'ht_conn':
            edge_prefix_str = 'HTConnection_'
            export_type = 'ht_edges'                    

        print("** exporting edges - Graph type=" + type_of_graph )        

        # Export ALL edges for ALL periods
        print("**   exporting edges for AllPeriods " + self.get_now_dt())
        self.exportData(export_type, 
                        input_files_path + '\\' + edge_prefix_str + 'AllPeriods_', 
                        0, 
                        user_conn_filter=user_conn_filter, 
                        replace_existing_file=False)        
                
            
        if bot_filter_fl == 'Y':
            # Export edges for ALL periods, excluding edges associated with bots
            print("**   exporting edges for AllPeriods_ExcludingBots - " + self.get_now_dt())
            self.exportData(export_type, 
                            input_files_path + '\\' + edge_prefix_str + 'AllPeriods_ExcludingBots_',
                            0, 
                            is_bot_Filter = '0', 
                            user_conn_filter=user_conn_filter, 
                            replace_existing_file=False)

            # Export edges for ALL periods, only edges associated with bots
            print("**   exporting edges for AllPeriods_BotsOnly - " + self.get_now_dt())
            self.exportData(export_type, 
                            input_files_path + '\\' + edge_prefix_str + 'AllPeriods_BotsOnly_', 
                            0, 
                            is_bot_Filter = '1', 
                            user_conn_filter=user_conn_filter, 
                            replace_existing_file=False)                        


        # Export edges by period using the dates set on array period_arr
        if period_arr is not None:

            for idx, period in enumerate(period_arr):

                # Export ALL edges for this period    
                print("**   exporting edges for " + period[0] + " - "  + self.get_now_dt())
                edges = self.exportData(export_type, 
                                        input_files_path + '\\' + edge_prefix_str + '' + period[0] + '_', 0, 
                                        startDate_filter=period[1], 
                                        endDate_filter=period[2], 
                                        is_bot_Filter=None, 
                                        user_conn_filter=user_conn_filter, 
                                        replace_existing_file=False)

                if bot_filter_fl == 'Y':
                    # Export edges for this period, excluding edges associated with bots
                    print("**   exporting edges for " + period[0] + "_ExcludingBots - "  + self.get_now_dt())
                    edges = self.exportData(export_type, 
                                            input_files_path + '\\' + edge_prefix_str + '' + period[0] + '_ExcludingBots_', 0, 
                                            startDate_filter=period[1], 
                                            endDate_filter=period[2], 
                                            is_bot_Filter='0', 
                                            user_conn_filter=user_conn_filter, 
                                            replace_existing_file=False) 

                    # Export edges for this period, only edges associated with bots        
                    print("**   exporting edges for " + period[0] + "_BotsOnly - "  + self.get_now_dt())
                    edges = self.exportData(export_type, 
                                            input_files_path + '\\' + edge_prefix_str + '' + period[0] + '_BotsOnly_', 
                                            0, 
                                            startDate_filter=period[1], 
                                            endDate_filter=period[2], 
                                            is_bot_Filter='1', 
                                            user_conn_filter=user_conn_filter, 
                                            replace_existing_file=False)
                        
        print("** exporting edges - END *** - " + self.get_now_dt())


        
        
    #####################################
    # Method: nodes_edges_analysis_files
    # Description: creates nodes and edges files       
    def nodes_edges_analysis_files(self, G, path): 
        """
        Given a graph G, it exports nodes with they degree, edges with their weight, 
        and word clouds representing the nodes scaled  by their degree
                
        Parameters
        ----------               
        G : 
            undirected networkx graph created from the Twitter data                               
        path :
            the path where the files should be saved
    
        Examples
        --------          
            Saved node and edges files into path:
        
            >>> nodes_edges_analysis_files(G, 'C:\\Data\\MyFilePath')
        """            
        
        print("****** Exporting nodes and edges to file - " + self.get_now_dt())
        self.export_nodes_edges_to_file(G, path + "\\G_NodesWithDegree.txt", path + "\\G_Edges.txt")

        print("****** Ploting Nodes Wordcloud - " + self.get_now_dt())        
        node_file_name = path + '\\G_NodesWithDegree.txt'
        df = self.read_freq_list_file(node_file_name,' ')    
        self.plot_word_cloud(df, file=path +'\\G_Nodes_WordCloud.png')
        print("\n")
        
    #####################################
    # Method: lda_analysis_files
    # Description: creates topic model files
    # tweet texts, lda model visualization
    def lda_analysis_files(self, path, startDate_filter=None, endDate_filter=None, arr_edges=None, arr_ht_edges=None):            
        """
        Creates topic model files. Export a files with tweet texts and a lda model visualization.
        The data comes from the mongoDB database and is filtered based on the parameters.
                
        Parameters
        ----------                                       
        path :
            the path where the files should be saved
        
        startDate_filter : (Optional)
            filter by a certain start date
            
        endDate_filter : (Optional)
            filter by a certain end date
        
        arr_edges : (Optional)
            and array of concatenated edges that will be used to filter certain connection only.
            the method concat_edges can be used to create that array.
        
        arr_ht_edges : (Optional)
            and array of concatenated hashtag edges that will be used to filter certain ht connection only.
            the method concat_edges can be used to create that array. 
    
        Examples
        --------          
            Save lda analysis files into path:
        
            >>> lda_analysis_files(
            >>>     'D:\\Data\\MyFiles', 
            >>>     startDate_filter='09/20/2020 19:00:00', 
            >>>     endDate_filter='03/04/2021 00:00:00')
        """ 
        
        #export text for topic analysis
        print("****** Exporting text for topic analysis - " + self.get_now_dt())    
        self.exportData('text_for_topics', 
                        path + "\\" , 0, 
                        startDate_filter, 
                        endDate_filter, 
                        self.is_bot_Filter, 
                        arr_edges, 
                        arr_ht_edges=arr_ht_edges, 
                        replace_existing_file=False)

        # Train LDA models and print topics
        print("****** Topic discovery analysis (lda model) ****** - " + self.get_now_dt())        
        model_name = "Topics"
        topics_file_name = path + '\\T_tweetTextsForTopics.txt'
        if not os.path.exists(path + '\\Topics-(LDA model).png'):
            self.train_model_from_file(topics_file_name, self.num_of_topics, model_name, model_type='lda')
            self.plot_topics(path + '\\Topics-(LDA model).png', self.num_of_topics, 'lda', replace_existing_file=False)
        


    #####################################
    # Method: ht_analysis_files
    # Description: creates hashtag frequency files
    # frequency file text, wordcloud, and barcharts
    def ht_analysis_files(self, path, startDate_filter=None, endDate_filter=None, arr_edges=None, arr_ht_edges=None):        
        """
        Creates hashtag frequency files. Frequency text file, wordcloud, and barcharts.
        The data comes from the mongoDB database and is filtered based on the parameters.
                
        Parameters
        ----------                                       
        path :
            the path where the files should be saved
        
        startDate_filter : (Optional)
            filter by a certain start date
            
        endDate_filter : (Optional)
            filter by a certain end date
        
        arr_edges : (Optional)
            and array of concatenated edges that will be used to filter certain connection only.
            the method concat_edges can be used to create that array.
        
        arr_ht_edges : (Optional)
            and array of concatenated hashtag edges that will be used to filter certain ht connection only.
            the method concat_edges can be used to create that array.
    
        Examples
        --------          
            Save hashtag frequency files into path:
        
            >>> ht_analysis_files(
            >>>     'D:\\Data\\MyFiles', 
            >>>     startDate_filter='09/20/2020 19:00:00', 
            >>>     endDate_filter='03/04/2021 00:00:00')
        """
        
        #export ht frequency list         
        print("\n****** Exporting ht frequency list - " + self.get_now_dt())
        self.exportData('ht_frequency_list', 
                        path + "\\" , 0, 
                        startDate_filter, 
                        endDate_filter, 
                        self.is_bot_Filter, 
                        arr_edges, 
                        arr_ht_edges=arr_ht_edges, 
                        replace_existing_file=False)        
        
        print("****** Ploting HashTags Barchart and Wordcloud - " + self.get_now_dt())                   
        ht_file_name = path + '\\T_HT_FrequencyList.txt'
        
        if os.stat(ht_file_name).st_size != 0:                        
            df = self.read_freq_list_file(ht_file_name)            
            self.plot_top_freq_list(df, 30, 'HashTag', exclude_top_no=0, file=path + '\\T_HT_Top30_BarChart.png', replace_existing_file=False)
            self.plot_top_freq_list(df, 30, 'HashTag', exclude_top_no=1, file=path + '\\T_HT_Top30_BarChart-(Excluding Top1).png', replace_existing_file=False)
            self.plot_top_freq_list(df, 30, 'HashTag', exclude_top_no=2, file=path + '\\T_HT_Top30_BarChart-(Excluding Top2).png', replace_existing_file=False)
            self.plot_word_cloud(df, file=path + '\\T_HT_WordCloud.png', replace_existing_file=False)
        
        
    #####################################
    # Method: words_analysis_files
    # Description: creates words frequency files
    # frequency file text, wordcloud, and barcharts
    def words_analysis_files(self, path, startDate_filter=None, endDate_filter=None, arr_edges=None, arr_ht_edges=None):        
        """
        Creates words frequency files. Frequency text file, wordcloud, and barcharts.
        The data comes from the mongoDB database and is filtered based on the parameters.
                
        Parameters
        ----------                                       
        path :
            the path where the files should be saved
        
        startDate_filter : (Optional)
            filter by a certain start date
            
        endDate_filter : (Optional)
            filter by a certain end date
        
        arr_edges : (Optional)
            and array of concatenated edges that will be used to filter certain connection only.
            the method concat_edges can be used to create that array.
        
        arr_ht_edges : (Optional)
            and array of concatenated hashtag edges that will be used to filter certain ht connection only.
            the method concat_edges can be used to create that array.
    
        Examples
        --------          
            Save words frequency files into path:
        
            >>> words_analysis_files(
            >>>     'D:\\Data\\MyFiles', 
            >>>     startDate_filter='09/20/2020 19:00:00', 
            >>>     endDate_filter='03/04/2021 00:00:00')
            
        """                
        #export words frequency list 
        print("\n****** Exporting words frequency list - " + self.get_now_dt())        
        self.exportData('word_frequency_list', 
                        path + "\\" , 0, 
                        startDate_filter, 
                        endDate_filter, 
                        self.is_bot_Filter, 
                        arr_edges, 
                        arr_ht_edges, 
                        self.top_no_word_filter, 
                        replace_existing_file=False)
                        

        print("****** Ploting Word Barchart and Wordcloud - " + self.get_now_dt())                   
        word_file_name = path + '\\T_Words_FrequencyList.txt'
        if os.stat(word_file_name).st_size != 0:
            df = self.read_freq_list_file(word_file_name)
            self.plot_top_freq_list(df, 30, 'Word', exclude_top_no=0, file=path+'\\T_Words_Top30_BarChart.png', replace_existing_file=False)
            self.plot_word_cloud(df, file=path+'\\T_Words_WordCloud.png', replace_existing_file=False)
        

    #####################################
    # Method: time_series_files
    # Description: creates time frequency files    
    def time_series_files(self, path, startDate_filter=None, endDate_filter=None, arr_edges=None, arr_ht_edges=None):        
        """
        Creates timeseries frequency files. Tweet count by day and hashcount count by day.
        The data comes from the mongoDB database and is filtered based on the parameters.
                
        Parameters
        ----------                                       
        path :
            the path where the files should be saved
        
        startDate_filter : (Optional)
            filter by a certain start date
            
        endDate_filter : (Optional)
            filter by a certain end date
        
        arr_edges : (Optional)
            and array of concatenated edges that will be used to filter certain connection only.
            the method concat_edges can be used to create that array.
        
        arr_ht_edges : (Optional)
            and array of concatenated hashtag edges that will be used to filter certain ht connection only.
            the method concat_edges can be used to create that array.
    
        Examples
        --------          
            Save timeseries frequency files into path:
        
            >>> time_series_files(
            >>>    'D:\\Data\\MyFiles', 
            >>>    startDate_filter='09/20/2020 19:00:00', 
            >>>    endDate_filter='03/04/2021 00:00:00')
        """  
        
                          
        print("****** Exporting time series files - " + self.get_now_dt())           
        tweet_df = self.get_time_series_df(startDate_filter=startDate_filter, endDate_filter=endDate_filter, arr_edges=arr_edges, arr_ht_edges=arr_ht_edges)
        
        #plot time series for all tweets
        if not os.path.exists(path + '\\TS_TweetCount.png'):
            self.plot_timeseries(tweet_df, ['tweet', 'tweet_created_at'], path + '\\TS_TweetCount.png')   
        
        #plot time series for top hashtags [1-5]
        if not os.path.exists(path + '\\TS_TweetCountByHT[1-5].png'):
            self.plot_top_ht_timeseries(top_no_start=1, top_no_end=5, file = path + '\\TS_TweetCountByHT[1-5].png', 
                                        startDate_filter=startDate_filter, endDate_filter=endDate_filter, arr_edges=arr_edges, arr_ht_edges=arr_ht_edges)
            
        #plot time series for top hashtags [3-10]
        if not os.path.exists(path + '\\TS_TweetCountByHT[3-10].png'):
            self.plot_top_ht_timeseries(top_no_start=3, top_no_end=10, file = path + '\\TS_TweetCountByHT[3-10].png', 
                                        startDate_filter=startDate_filter, endDate_filter=endDate_filter, arr_edges=arr_edges, arr_ht_edges=arr_ht_edges)
    
        
    #####################################
    # Method: ht_connection_files
    # Description: creates hashags graph connections files
    def ht_connection_files(self, path, startDate_filter=None, endDate_filter=None, arr_edges=None):
                                                                       
        print("****** Exporting ht connection files - " + self.get_now_dt())        
    
        #create file with ht edges
        self.exportData('ht_edges', path + "\\" , 0, startDate_filter, endDate_filter, self.is_bot_Filter, arr_edges)                
        edge_file_path = path + "\\ht_edges.txt" 
        G = self.loadGraphFromFile(edge_file_path)
        if len(G.edges) > 0:
            if len(G.edges) > 1000:
                G = self.largest_component_no_self_loops(G)
            else:
                G.remove_edges_from(nx.selfloop_edges(G))    
                for node in list(nx.isolates(G)):
                    G.remove_node(node)
            print("HT graph # of Nodes " + str(len(G.nodes())))
            print("HT graph # of Edges " + str(len(G.edges())))
            self.graph_analysis_files(G, path, gr_prefix_nm = 'HTG_') 


        #remove top hashtags if we want to ignore the top hashtags
        if self.top_ht_to_ignore is not None:
            G2 = G.copy()
            remove_name = '[WITHOUT('
            arr_nodes = sorted(G2.degree(), key=lambda x: x[1], reverse=True)
            for ht, degree in arr_nodes[0:self.top_ht_to_ignore]:            
                remove_name = remove_name + '-' + ht
                G2.remove_node(ht)
            remove_name = remove_name + ')]'

            if len(G2.edges) > 0:
                if len(G2.edges) > 1000:
                    G2 = self.largest_component_no_self_loops(G2)
                else:
                    G2.remove_edges_from(nx.selfloop_edges(G2))    
                    for node in list(nx.isolates(G2)):
                        G2.remove_node(node)  
                print("HT graph # of Nodes " + str(len(G2.nodes())))
                print("HT graph # of Edges " + str(len(G2.edges())))
                self.graph_analysis_files(G2, path, gr_prefix_nm = 'HTG_' + remove_name + '_')                                                                


    #####################################
    # Method: graph_analysis_files
    # Description: creates graphs files
    def graph_analysis_files(self, G, path, gr_prefix_nm=''):
        """
        Plot graph analysis files for a given graph G. 
        It uses the configuration set on the setConfigs method.
                
        Parameters
        ----------               
        G : 
            undirected networkx graph created from the Twitter data                               
        path :
            the path where the files should be saved
        
        gr_prefix_nm: (Optional)
            a prefix to add to the graph name. (Default='')
            
        Examples
        --------          
        Create graph visualization files
        
            >>> graph_analysis_files(G, 'C:\\Data\\MyAnalysis\\', 'MyNameTest')
        """      
        
        if len(G.nodes()) > 0 and len(G.edges()) > 0:
        
            #plot graph
            print("\n****** Ploting graphs... *********** - " + self.get_now_dt())                

            # if not os.path.exists(path + '\\' + gr_prefix_nm + 'G_Graph.png') 
            # and not os.path.exists(path + '\\' + gr_prefix_nm + 'G_Graph(WithoutScale).png'):                        
            if ((len(G.nodes()) <= self.graph_plot_cutoff_no_nodes \
                 or len(G.edges()) <= self.graph_plot_cutoff_no_edges) \
                 and len(G.edges()) != 0) \
                 or len(G.nodes()) <= MIN_NO_OF_NODES_TO_REDUCE_GRAPH:

                if len(G.edges()) < 450:
                    v_scale = 0.01; v_k =0.7; v_iterations=100; v_node_size=2
                elif len(G.edges()) < 5000:
                    v_scale = 2; v_k = 0.6; v_iterations=200; v_node_size=0.8
                elif len(G.edges()) < 10000:
                    v_scale = 1; v_k = 0.1; v_iterations=200; v_node_size=0.6
                elif len(G.edges()) >= 10000:
                    v_scale = 1; v_k = 0.05; v_iterations=500; v_node_size=0.6

                if self.create_graph_with_node_scale_flag == 'Y':
                    G_to_plot, labels2, k = self.calculate_louvain_clustering(G)
                    self.plotSpringLayoutGraph(G_to_plot, 
                                               path + '\\' + gr_prefix_nm + 'G_Graph.png', 
                                               v_scale, 
                                               v_k, 
                                               v_iterations, 
                                               cluster_fl='Y', 
                                               v_labels=list(list(labels2)), 
                                               replace_existing_file=False)

                if self.create_graph_without_node_scale_flag == 'Y':
                    self.plotSpringLayoutGraph(G, 
                                               path + '\\' + gr_prefix_nm + 'G_Graph(WithoutScale).png',
                                               v_scale, 
                                               v_k, 
                                               v_iterations, 
                                               cluster_fl='N', 
                                               v_alpha=1, 
                                               scale_node_size_fl='N', 
                                               replace_existing_file=False)


            #plot reduced graph
            if self.create_reduced_graph_flag == 'Y':
                self.plot_graph_contracted_nodes(G, path + '\\' + gr_prefix_nm + 'G_Graph-(ReducedGraph).png')
            print("\n")
                        
            
    #####################################
    # Method: edge_files_analysis
    # Description: load graph from edge files and call methods to create all analysis 
    # files for the main graph and for the graph of each period
    def edge_files_analysis(self, output_path): 
        """
        Automated way to generate all analysis files. 
        It creates all folders, edge files, and any other files based on given settings. 
        The setting of what files are interesting or not, should be set using the setConfigs method.
        
        Parameters
        ----------                                       
        output_path :
            the path where the files should be saved        
    
        Examples
        --------          
            Create all analysis files and folder based on the configurations set on setConfigs:
        
            >>> edge_files_analysis('D:\\Data\\MyFiles') 
        """      
                
        case_ht_str = ''
        if self.type_of_graph == 'ht_conn':
            case_ht_str = 'ht_'            

        #Get the right edges file to import
        if self.is_bot_Filter is None:
            parent_path = output_path + '\\' + self.edge_prefix_str + 'All'
            edge_file_path = self.folder_path + '\\data_input_files\\' + self.edge_prefix_str + 'AllPeriods_' + case_ht_str + 'edges.txt'
            if not os.path.exists(edge_file_path): self.export_all_edges_for_input(period_arr=self.period_arr, type_of_graph=self.type_of_graph)
        elif self.is_bot_Filter == '0':
            parent_path = output_path + '\\' + self.edge_prefix_str + 'ExcludingBots'
            edge_file_path = self.folder_path + '\\data_input_files\\' + self.edge_prefix_str +'AllPeriods_ExcludingBots_' + case_ht_str + 'edges.txt'            
            if not os.path.exists(edge_file_path): self.export_all_edges_for_input(period_arr=self.period_arr, bot_filter_fl='Y', type_of_graph=self.type_of_graph)
        elif self.is_bot_Filter == '1':
            parent_path = output_path + '\\' + self.edge_prefix_str + 'Bots_Edges_Only'
            edge_file_path = self.folder_path + '\\data_input_files\\' + self.edge_prefix_str + 'AllPeriods_BotsOnly_' + case_ht_str + 'edges.txt'            
            if not os.path.exists(edge_file_path): self.export_all_edges_for_input(period_arr=self.period_arr, bot_filter_fl='Y', type_of_graph=self.type_of_graph)
            
        print(edge_file_path)
        self.create_path(output_path)
            
        # Load graph from edge file
        G = self.loadGraphFromFile(edge_file_path)
                
        # Call method to print all analysis files
        self.all_analysis_file(G, parent_path, startDate_filter=None, endDate_filter=None)                
                                       
          
        # Run analysis by period using the dates set on array period_arr
        if self.period_arr is not None:                                    
            
            # Creates a text file with the period information. 
            # This is just so that whoever is looking at these folder can know what dates we used for each period
            myFile = open(output_path + '\\PeriodsInfo.txt', 'w', encoding="utf-8")
            with myFile:
                writer = csv.writer(myFile, delimiter='\t', lineterminator='\n')
                writer.writerows(self.period_arr)
                    
            for idx, period in enumerate(self.period_arr):                    

                # Set the period information variables
                period_name = period[0]
                period_start_date = period[1]
                period_end_date = period[2]

                print("\n**********************************************************")
                print("************************** " + period_name + " ****************************\n" ) 

                # Edge file path 
                if self.is_bot_Filter is None:
                    parent_path = output_path + "\\" + self.edge_prefix_str + "All_By_Period\\" + period_name
                    edge_file_path = output_path + "\\data_input_files\\" + self.edge_prefix_str + period_name +"_" + case_ht_str + "edges.txt"                        
                    if not os.path.exists(edge_file_path): self.export_all_edges_for_input(period_arr=self.period_arr, type_of_graph=self.type_of_graph)
                elif self.is_bot_Filter  == '0':
                    parent_path = output_path + "\\" + self.edge_prefix_str + "Excluding_Bots_By_Period\\" + period_name
                    edge_file_path = output_path + "\\data_input_files\\" + self.edge_prefix_str + period_name + "_ExcludingBots_" + case_ht_str + "edges.txt"                    
                    if not os.path.exists(edge_file_path): self.export_all_edges_for_input(period_arr=self.period_arr, bot_filter_fl='Y', type_of_graph=self.type_of_graph)
                elif self.is_bot_Filter  == '1':
                    parent_path = output_path + "\\" + self.edge_prefix_str + "Bots_Edges_Only_By_Period\\" + period_name                    
                    edge_file_path = output_path + "\\data_input_files\\" + self.edge_prefix_str + period_name +"_BotsOnly_" + case_ht_str + "edges.txt"                    
                    if not os.path.exists(edge_file_path): self.export_all_edges_for_input(period_arr=self.period_arr, bot_filter_fl='Y', type_of_graph=self.type_of_graph)

                # Create new path if it doesn't exist
                self.create_path(parent_path)

                #load graph from edge file
                G = self.loadGraphFromFile(edge_file_path)                
                
                #call function to genrate all files for this graph
                self.all_analysis_file(G, parent_path, startDate_filter=period_start_date, endDate_filter=period_end_date)
                                        
        

    #####################################
    # Method: all_analysis_file
    # Description: Calls method to create all files for full dataset, for top degree nodes, and for community graphs
    def all_analysis_file(self, G, output_path, startDate_filter=None, endDate_filter=None):
                                
        #files for the main graph
        self.create_analysis_file(G, output_path, startDate_filter=startDate_filter, endDate_filter=endDate_filter)
                                        
        #files for the top nodes
        if self.create_top_nodes_files_flag == 'Y':            
            self.top_nodes_analysis(G, output_path, startDate_filter=startDate_filter, endDate_filter=endDate_filter)        
        
        #files for community nodes
        if self.create_community_files_flag == 'Y':
            self.commty_analysis_files(G, output_path, startDate_filter=startDate_filter,  endDate_filter=endDate_filter)                                

            
            
    #####################################
    # Method: create_analysis_file
    # Description: calls individual methods to create files on the settings             
    def create_analysis_file(
            self, 
            G, 
            output_path, 
            startDate_filter=None, 
            endDate_filter=None, 
            arr_edges=None):
                                
        #export file with measures
        print("****** Graph Measures - " + self.get_now_dt())
        self.print_Measures(G, fileName_to_print = output_path + "\\G_Measures-(All).txt")
        print("\n")
        
        arr_ht_edges = None
        if self.type_of_graph == 'ht_conn':
            arr_ht_edges = arr_edges
            arr_edges = None            

        if len(G.edges()) != 0:
            #get largest connected component and export file with measures
            G = self.largest_component_no_self_loops(G)
            print("****** Largest Component Graph Measures - " + self.get_now_dt())
            self.print_Measures(G, fileName_to_print = output_path + "\\G_Measures-(LargestCC).txt")
            print("\n")

            #export files with edges and degrees
            if self.create_nodes_edges_files_flag == 'Y':
                self.nodes_edges_analysis_files(G, output_path)
            
            #LDA Model
            if self.create_topic_model_files_flag == 'Y':
                self.lda_analysis_files(output_path, 
                                        startDate_filter=startDate_filter, 
                                        endDate_filter=endDate_filter, 
                                        arr_edges=arr_edges, 
                                        arr_ht_edges=arr_ht_edges)

            #export ht frequency list 
            if self.create_ht_frequency_files_flag == 'Y':           
                self.ht_analysis_files(output_path, 
                                       startDate_filter=startDate_filter, 
                                       endDate_filter=endDate_filter, 
                                       arr_edges=arr_edges, 
                                       arr_ht_edges=arr_ht_edges)
                
            #export words frequency list 
            if self.create_words_frequency_files_flag == 'Y':
                self.words_analysis_files(output_path, 
                                          startDate_filter=startDate_filter, 
                                          endDate_filter=endDate_filter, 
                                          arr_edges=arr_edges, 
                                          arr_ht_edges=arr_ht_edges)
                                 
            #plot graph
            if self.create_graphs_files_flag == 'Y':
                self.graph_analysis_files(G, output_path)
                
            #time series
            if self.create_timeseries_files_flag == 'Y':
                self.time_series_files(output_path, 
                                       startDate_filter=startDate_filter, 
                                       endDate_filter=endDate_filter, 
                                       arr_edges=arr_edges, 
                                       arr_ht_edges=arr_ht_edges) 

            #hashtag connections
            if self.create_ht_conn_files_flag == 'Y' and self.type_of_graph != 'ht_conn':
                self.ht_connection_files(output_path, 
                                         startDate_filter=startDate_filter, 
                                         endDate_filter=endDate_filter, 
                                         arr_edges=arr_edges)
            
                           
        
        
    #####################################
    # Method: top_nodes_analysis
    # Description: calls methods to create files for each of the top degree nodes
    def top_nodes_analysis(self, G, output_path, startDate_filter=None, endDate_filter=None):                                      

        # Choose which graph you want to run this for
        Graph_to_analyze = G.copy()
        
        top_degree_nodes = self.get_top_degree_nodes(Graph_to_analyze, self.top_degree_start, self.top_degree_end)

        #creates a folder to save the files for this analysis
        path = "Top_" + str(self.top_degree_start) + '-' + str(self.top_degree_end) 
        self.create_path(output_path + '\\' + path)

        i = self.top_degree_end
        # loops through the top degree nodes, creates a subgraph for them and saves the results in a folder
        for x in np.flip(top_degree_nodes, 0):
            node = x[0]

            #creates a subgraph for this node
            G_subgraph = self.create_node_subgraph(Graph_to_analyze, node)    
            G_subgraph_largestComponent = G_subgraph.copy()
            G_subgraph_largestComponent = self.largest_component_no_self_loops(G_subgraph_largestComponent)

            #creates a path to add the files for this node
            path_node = path + "\\" + str(i) + "-" + node
            self.create_path(output_path + '\\' + path_node)
            
            #get array with all edges for this top degree node                          
            if len(G_subgraph) > 1:
                arr_edges = self.concat_edges(G_subgraph)
                self.create_analysis_file(G_subgraph, 
                                          output_path + '\\' + path_node,
                                          startDate_filter=startDate_filter, 
                                          endDate_filter=endDate_filter, 
                                          arr_edges=arr_edges)
    
            i -= 1

            
    #####################################
    # Method: commty_analysis_files
    # Description: calls methods to create files for each of the communities found 
    def commty_analysis_files(self, G, output_path, startDate_filter=None, endDate_filter=None):
        
        print("\n******************************************************")
        print("******** Louvain Communities ********")
                            
        if len(G.edges()) != 0:                                                
            
            # Choose which graph you want to run this for
            Graph_to_analyze = G.copy()            
            
            #creates a folder to save the files for this analysis
            path = output_path + "\\Communities_(Louvain)"
            while os.path.exists(path):
                path = path + "+"                        
            self.create_path(path)                        

            #calculate louvain community for largest connected component
            Graph_to_analyze = self.largest_component_no_self_loops(Graph_to_analyze) 
            Graph_to_analyze, labels, k = self.calculate_louvain_clustering(Graph_to_analyze)            
            
            comm_att = 'community_louvain'

            #find the number of communities in the graph
            no_of_comm = max(nx.get_node_attributes(Graph_to_analyze, comm_att).values())+1    

            print("******************************************************")
            print("Total # of Communities " + str(no_of_comm))

            #loop through the communities print they analysis files
            for commty in range(no_of_comm):

                #find subgraphs of this community
                G_subgraph = Graph_to_analyze.subgraph([n for n,attrdict in Graph_to_analyze.node.items() if attrdict [comm_att] == commty ])                                                
                #only cares about communities with more than 1 node
                if len(G_subgraph.edges()) >= self.commty_edge_size_cutoff:

                    G_subgraph_largestComponent = G_subgraph.copy()
                    G_subgraph_largestComponent = self.largest_component_no_self_loops(G_subgraph_largestComponent)

                    #creates a path to add the files for this node
                    path_community = path + "\\Community-" + str(commty+1)
                    self.create_path(path_community)

                    print("\n")
                    print("******************************************************")
                    print("****** Printing files for community " + str(commty+1) + " ******")
                    #self.print_Measures(G_subgraph, False, False, False, False, fileName_to_print = path_community + '\\G_' + str(commty+1) + '_Measures.txt')    
                    print("\n")
                    
                    if len(G_subgraph) > 1:
                        arr_edges = self.concat_edges(G_subgraph)
                        self.create_analysis_file(G_subgraph, path_community,                                               
                                                  startDate_filter=startDate_filter, 
                                                  endDate_filter=endDate_filter,                                               
                                                  arr_edges=arr_edges)
                
                        
    #####################################
    # Method: get_time_series_df
    # Description: query data in mongoDB for timeseries analysis            
    def get_time_series_df(
            self, 
            ht_arr=None, 
            startDate_filter=None, 
            endDate_filter=None, 
            arr_edges=None, 
            arr_ht_edges=None):
        """  
        Method to query data in mongoDB for timeseries analysis given certain filters.
        It creates all folders, edge files, and any other files based on given settings. 
        The setting of what files are interesting or not, should be set using the setConfigs method.
        
        Parameters
        ----------                                       
        ht_arr :
            array of hashtags to filter the data from
        
        startDate_filter : (Optional)
            filter by a certain start date
            
        endDate_filter : (Optional)
            filter by a certain end date
        
        arr_edges : (Optional)
            and array of concatenated edges that will be used to filter certain connection only.
            the method concat_edges can be used to create that array.
        
        arr_ht_edges : (Optional)
            and array of concatenated hashtag edges that will be used to filter certain ht connection only.
            the method concat_edges can be used to create that array.
    
        Examples
        --------        
            >>> ...
        """   
        
        df = pd.DataFrame()

        if ht_arr is not None:        
            #get timeseries for each of the top hashtags    
            for i, ht in enumerate(ht_arr):
                arrData, file = self.queryData(exportType='tweet_ids_timeseries', 
                                               filepath='', 
                                               inc=0, 
                                               ht_to_filter=ht, 
                                               startDate_filter=startDate_filter, 
                                               endDate_filter=endDate_filter, 
                                               is_bot_Filter=self.is_bot_Filter, 
                                               arr_edges=arr_edges,
                                               arr_ht_edges=arr_ht_edges)
                tweet_df = pd.DataFrame(list(arrData))
                tweet_df.columns = ['tweet_created_at', ht]   
                df = pd.concat([df,tweet_df], axis=0, ignore_index=True)


        else:
            #get timeseries for all tweets
            arrData, file = self.queryData(exportType='tweet_ids_timeseries', 
                                           filepath='', inc=0,                                                     
                                           startDate_filter=startDate_filter, 
                                           endDate_filter=endDate_filter, 
                                           is_bot_Filter=self.is_bot_Filter, 
                                           arr_edges=arr_edges,
                                           arr_ht_edges=arr_ht_edges)    
            tweet_df = pd.DataFrame(list(arrData))
            tweet_df.columns = ['tweet_created_at', 'tweet']   
            df = pd.concat([df,tweet_df], axis=0, ignore_index=True)


        return df


    #####################################
    # Method: plot_top_ht_timeseries
    # Description: get top hashtags and plot their timeseries data
    def plot_top_ht_timeseries(
            self, 
            top_no_start, 
            top_no_end, 
            file, 
            startDate_filter=None, 
            endDate_filter=None, 
            arr_edges=None, 
            arr_ht_edges=None):        
        
        #get the top hashtags to plot
        ht_arr, f = self.queryData(exportType='ht_frequency_list', 
                                   filepath='', inc=0, 
                                   startDate_filter=startDate_filter, 
                                   endDate_filter= endDate_filter, 
                                   is_bot_Filter=self.is_bot_Filter, 
                                   arr_edges=arr_edges, 
                                   arr_ht_edges=arr_ht_edges,
                                   top_no_filter=top_no_end, 
                                   include_hashsymb_FL=False)
                        
        if len(ht_arr) < top_no_end:
            top_no_end = len(ht_arr)
                        
        if len(ht_arr) == 0 or top_no_start >= top_no_end:
            return ""
        
        ht_arr = np.array(ht_arr)
        ht_arr = ht_arr[top_no_start-1:top_no_end,0]
        ht_arr = list(ht_arr)
        
        #get the time series data
        df = self.get_time_series_df(ht_arr=ht_arr, 
                                     startDate_filter=startDate_filter, 
                                     endDate_filter=endDate_filter, 
                                     arr_edges=arr_edges)

        #plot timeseries graph
        arr_columns = ht_arr.copy()
        arr_columns.append('tweet_created_at')        
        self.plot_timeseries(df, arr_columns, file)


        
    #####################################
    # Method: plot_timeseries
    # Description: plot time series data
    def plot_timeseries(self, df, arr_columns, file):                      

        tweet_df = (df[arr_columns]
         .set_index('tweet_created_at')      
         .resample('D') 
         .count()         
        );

        ax = tweet_df.plot(figsize=(25,8))
        ax.set_xlabel("Date")
        ax.set_ylabel("Tweet Count")
        
        
        plt.savefig(file, dpi=200, facecolor='w', edgecolor='w')
        #plt.show()
        plt.cla()   # Clear axis
        plt.clf()   # Clear figure
        plt.close() # Close a figure window
    
    
       
    #####################################
    # Method: eda_analysis
    # Description: Save EDA files
    def eda_analysis(self):
        """  
        Method to print a summary of the initial exploratory data analysis for any dataset.        

        Examples
        --------          
            >>> # Create Exploratory Data Analysis files
            >>> eda_analysis()
            
        It includes the following metrics:
        
        + **Tweet counts**: The number of tweet document in the database, divided by the following categories.
            
                + Total Original Tweets: The number of tweet documents in the database that are original tweets.		
                + Total Replies: The number of tweet documents in the database that are replies to another tweet.		
                + Total Retweets: The number of tweet documents in the database that are retweets.		
                + Total Tweets: The total number of tweet documents in the database.
            
        + **Tweet counts by language**: The number of tweets document for each language used in the tweets.

        + **Tweet counts by month**: The number of tweets document for each month/year.

        + **Tweet counts by file**: The number of tweets document imported from each of the json files.

        + **User counts**: The number of users in the database, divided by the following categories.
            
                + tweet: Users with at least one document in the database.
                + retweet: Users that were retweeted, but are not part of previous group.
                + quote: Users that were quoted, but are not part of previous groups.
                + reply: Users that were replied to, but are not part of previous groups.
                + mention: Users that were mentioned, but are not part of previous groups.
                        
        + **All User Connections Graph**: The metrics for the graph created based on the users connecting by retweets, quotes, mentions, and replies.
            
                + # of Nodes: The total number of nodes in the graph.
                + # of Edges: The total number of edges in the graph.
                + # of Nodes of the largest connected components: The total number of nodes in the largest connected component of the graph.
                + # of Edges of the largest connected components: The total number of edges in the largest connected component of the graph.                
                + # of Disconnected Graphs: The number of sub-graphs within the main graph that are not connected to each other.                
                + # of Louvain Communities found in the largest connected component: The number of communities found in the largest connected component using the Louvain method.                
                + Degree of the top 5 most connected users: List of the top 5 users with the highest degree. Shows the user screen name and respective degrees.                
                + Average Node Degree of largest connected graph: The average degree of all nodes that are part of the largest connected component of the graph.                
                + Plot of the Louvain community distribution: A barchart showing the node count distribution of the communities found with the Louvain method.
                + Disconnected graphs distribution: A plot of a graph showing the distribution of the disconnected graphs. It shows the total number of nodes and edges for each of the disconnected graphs. 
                
        + **Mentions User Connections Graph**: The same metrics as the *All User Connections* graph, but only considering the connections made by mentions.

        + **Retweets User Connections Graph**: The same metrics as the *All User Connections* graph, but only considering the connections made by retweets.

        + **Replies User Connections Graph**: The same metrics as the *All User Connections* graph, but only considering the connections made by replies.

        + **HT Connection Graph**: The same metrics as the *All User Connections* graph, but only considering the connections made by hashtags.           

        """                 
        eda_folder =  self.folder_path  + '\\EDA'
        self.create_path(eda_folder)                    
        eda_file = open(eda_folder + '\\EDA.txt', 'w', encoding="utf-8")
                    
            
        print("**** Tweet counts ******")
        eda_file.write("**** Tweet counts ******\n")
        arr, f = self.queryData(exportType='tweetCount', filepath='', inc=0)
        for x in arr:           
            eda_file.write(str(x))
            eda_file.write("\n")
        df = pd.DataFrame(arr)
        df.columns = ['', '']
        print(df.to_string())
        print("\n")


        print("**** Tweet counts by language ******")           
        eda_file.write("\n**** Tweet counts by language ******\n")
        arr, f = self.queryData(exportType='tweetCountByLanguage', filepath='', inc=0)
        for x in arr:
            eda_file.write(str(x))
            eda_file.write("\n")
        df = pd.DataFrame(arr)
        df.columns = ['', '']
        print(df.to_string())
        print("\n")
        
        
        print("**** Tweet counts by month ******")    
        eda_file.write("\n**** Tweet counts by month ******\n")
        arr, f = self.queryData(exportType='tweetCountByMonth', filepath='', inc=0)
        for x in arr:
            eda_file.write(str(x))
            eda_file.write("\n")
        df = pd.DataFrame(arr)
        df.columns = ['', '', '']
        print(df.to_string())
        print("\n")   
        
        
        print("**** Tweet counts by file ******")    
        eda_file.write("\n**** Tweet counts by file ******\n")
        arr, f = self.queryData(exportType='tweetCountByFile', filepath='', inc=0)
        for x in arr:
            eda_file.write(str(x))
            eda_file.write("\n")
        df = pd.DataFrame(arr)
        df.columns = ['', ''] 
        print(df.to_string())
        print("\n")                  
 

        print("**** User counts ******")    
        eda_file.write("\n**** User counts ******\n")
        arr, f = self.queryData(exportType='userCount', filepath='', inc=0)
        arr.sort()
        for x in arr:
            eda_file.write(str(x))
            eda_file.write("\n")
        df = pd.DataFrame(arr)
        df.columns = ['', '', '', '']
        print(df.to_string())
        print("\n")
                    
        

            
        # Graph EDA
                        
        # Load graph from main edges file if it does not exist 
        edge_file_path = self.folder_path + '\\data_input_files\\UserConnections_AllPeriods_edges.txt'
        if not os.path.exists(edge_file_path):
            self.export_all_edges_for_input(type_of_graph = 'user_conn_all')
                    
        # types of graph
        arr_type_pre = [['UserConnections_', 'edges'], 
                        ['MentionUserConnections_','edges'], 
                        ['RetweetUserConnections_','edges'], 
                        ['ReplyUserConnections_','edges'], 
                        ['QuoteUserConnections_','edges'], 
                        ['HTConnection_', 'ht_edges']] 
        
        # Loop through the type of graphs
        for i in range(len(arr_type_pre)):                        
            
            # find the edge file name
            edge_file_path = self.folder_path + '\\data_input_files\\' + arr_type_pre[i][0] + 'AllPeriods_' + arr_type_pre[i][1] + '.txt'            
            
            # if the edge file already exists
            if os.path.exists(edge_file_path):
                
                print('\n\n*****************************************') 
                print('**** ' + arr_type_pre[i][0] + ' Graph ******') 
                
                # Construct the graph based on the edge file
                G = self.loadGraphFromFile(edge_file_path)   
                
                # if the graph is not empty
                if len(G.nodes()) > 0 and len(G.edges()) > 0:
                    # Plot distribution of the separate connected components
                    print("**** Connected Components - Distribution ******") 
                    no_of_disc_g = self.plot_disconnected_graph_distr(G, file=eda_folder + '\\' + arr_type_pre[i][0] + 'ConnectedComponents-(Graphs).png')
                    no_of_disc_g_gt50 = self.plot_disconnected_graph_distr(G, size_cutoff=50)
                    

                    #calculate louvein community clustering
                    print("**** Calculating Community Distribution of the Largest Connected Component- (Louvain) ******") 
                    G2 = self.largest_component_no_self_loops(G) 
                    G2, labels, k = self.calculate_louvain_clustering(G2)
                    self.plot_graph_att_distr(G2, 
                                              'community_louvain',
                                              title='Louvain Community Distribution for Largest Connected Component',
                                              file_name=eda_folder+'\\' + arr_type_pre[i][0] + 'community_louvain_dist.png')        

                    # Degree arrays
                    arr = np.array(sorted(G2.degree(), key=lambda x: x[1], reverse=True))                
                    #deg_mean = np.asarray(arr[:,1], dtype=np.integer).mean()
                    # get the mean node degree of the nodes
                    deg_mean = self.calculate_average_node_degree(G2)

                    print(" # of Nodes " + str(len(G.nodes())))
                    print(" # of Edges " + str(len(G.edges())))
                    print(" # of Nodes - (Largest Connected Component) " + str(len(G2.nodes())))
                    print(" # of Edges - (Largest Connected Component) " + str(len(G2.edges())))
                    print(" # of Disconnected Graphs " + str(no_of_disc_g))
                    print(" # of Disconnected Graphs with 50 or more nodes " + str(no_of_disc_g_gt50))                    
                    print(" # of Communities found in the largest connected component " + str(k))
                    if len(arr) > 1:
                        print(" Degree of top 1 most connected user " + str(arr[0]))
                    if len(arr) > 2:
                        print(" Degree of top 2 most connected user " + str(arr[1]))
                    if len(arr) > 3:
                        print(" Degree of top 3 most connected user " + str(arr[2]))
                    if len(arr) > 4:
                        print(" Degree of top 4 most connected user " + str(arr[3]))
                    if len(arr) > 5:
                        print(" Degree of top 5 most connected user " + str(arr[4]))
                    print(" Average Node Degree of largest connected graph " + str(deg_mean))
                    eda_file.write("\n")
                    eda_file.write('**** ' + arr_type_pre[i][0] + ' Graph ******') 
                    eda_file.write("\n")
                    eda_file.write("# of Nodes " + str(len(G.nodes())))
                    eda_file.write("\n")
                    eda_file.write("# of Edges " + str(len(G.edges())))
                    eda_file.write("\n")
                    eda_file.write("# of Disconnected Graphs " + str(no_of_disc_g))
                    eda_file.write("\n")
                    eda_file.write("# of Louvain Communities found in the largest connected component " + str(k))
                    eda_file.write("\n")
                    if len(arr) > 1:
                        eda_file.write("Degree of top 1 most connected user " + str(arr[0]))
                        eda_file.write("\n")
                    if len(arr) > 2:
                        eda_file.write("Degree of top 2 most connected user " + str(arr[1]))
                        eda_file.write("\n")
                    if len(arr) > 3:
                        eda_file.write("Degree of top 3 most connected user " + str(arr[2]))
                        eda_file.write("\n")
                    if len(arr) > 4:
                        eda_file.write("Degree of top 4 most connected user " + str(arr[3]))
                        eda_file.write("\n")
                    if len(arr) > 5:
                        eda_file.write("Degree of top 5 most connected user " + str(arr[4]))
                        eda_file.write("\n")
                    eda_file.write("\n")
                    eda_file.write("Average Node Degree of largest connected graph " + str(deg_mean))
                    eda_file.write("\n")
        
        
        #close file
        eda_file.close()
                
        print("*** EDA - END *** - " + self.get_now_dt())
        
        
        
    #####################################
    # Method: print_top_nodes_cluster_metrics
    # Description: calculate clustering metrics for top degree nodes
    def print_top_nodes_cluster_metrics(self, G, top_degree_end, acc_node_size_cutoff=None):                                      
        """
        Calculates clustering metrics for top degree nodes        
                
        Parameters
        ----------               
        G : 
            undirected networkx graph created from the Twitter data                               
        
        top_degree_end :
            the number of top nodes to use for calculation
        
        acc_node_size_cutoff : (Optional)
            The average clustering coefficient metric can take a long time to run, 
            so users can set a cutoff number in this parameter for the graph size 
            that will decide if that metric will be printed or not depending on the graph size. (Default=None)
              
            
        Examples
        --------          
        Create graph visualization files
        
            >>> print_cluster_metrics(
            >>> G_Community, 
            >>> G, 
            >>> top_no=3, 
            >>> acc_node_size_cutoff=None
            >>> )
        """  
        
        exec_tm = 0
        endtime = 0
        starttime = 0
        
        starttime = time.time()
        
        top_degree_nodes = self.get_top_degree_nodes(G, 1, top_degree_end)        

        i = 1
        # loops through the top degree nodes, creates a subgraph for them
        for x in top_degree_nodes:
            
            print("***** Cluster for top " + str(i) + " node")
            
            node = x[0]            
            
            #creates a subgraph for this node
            G_subgraph = self.create_node_subgraph(G, node)    
            
            starttime_met = time.time()
            # print metrics
            self.print_cluster_metrics(G_subgraph, G, top_no=3, acc_node_size_cutoff=acc_node_size_cutoff)
            endtime_met = time.time()
            exec_tm = exec_tm + (endtime_met - starttime_met)
            
            print("\n")

            i += 1
            
        endtime = time.time()
        #exec_tm_total = endtime - starttime        
        print("Execution Time:  %s seconds " % (endtime - starttime - exec_tm))
            

    #####################################
    # Method: print_commty_cluster_metrics
    # Description: calls methods to create files for each of the communities found 
    def print_commty_cluster_metrics(self, G, comm_att='community_louvain', ignore_cmmty_lt=0, acc_node_size_cutoff=None):
        """
        Calculates clustering metrics for top degree nodes        
                
        Parameters
        ----------               
        G : 
            undirected networkx graph created from the Twitter data                               
        
        comm_att : (Optional)
            Possible values: 'community_louvain' or 'spectral_clustering'. (Default='community_louvain')
        
        ignore_cmmty_lt : (Optional)
             Number used to ignore small communitites. 
             The logic will not calculate metrics for communities smaller than this number. (Default=0)

        acc_node_size_cutoff : (Optional)
            The average clustering coefficient metric can take a long time to run, 
            so users can set a cutoff number in this parameter for the graph size 
            that will decide if that metric will be printed or not depending on the graph size. (Default=None)
                         
        Examples
        --------                              
            >>> print_commty_cluster_metrics(G, 'community_louvain', '10')
        """  
        
        if len(G.edges()) != 0:

            # find the number of communities in the graph
            no_of_comm = max(nx.get_node_attributes(G, comm_att).values())+1
            print("Total # of Communities " + str(no_of_comm))            

            print("******************************************************")            
            print("*****" + comm_att + "******")
            print("\n")

            # loop through the communities print they analysis files
            no_of_comm_gt_cutoff = 0
            for commty in range(no_of_comm):
                                
                # find subgraphs of this community
                G_subgraph = G.subgraph([n for n,attrdict in G.node.items() if attrdict [comm_att] == commty ])
                
                # ignore communities that are less than ignore_cmmty_lt
                if len(G_subgraph.nodes()) >= ignore_cmmty_lt:
                    print("****Community #" + str(commty+1))
                    no_of_comm_gt_cutoff += 1
                    self.print_cluster_metrics(G_subgraph, G, top_no=3, acc_node_size_cutoff=acc_node_size_cutoff)
                    print("\n")
             
            
            print("Total # of Communities with more than " + str(ignore_cmmty_lt) + ' nodes: ' + str(no_of_comm_gt_cutoff))
            
            