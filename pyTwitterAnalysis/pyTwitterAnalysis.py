from pyTwitterGraphAnalysis import pyTwitterGraphAnalysis
from pyTwitterDB import pyTwitterDB_class
from pyTwitterTopics import pyTwitterTopics

from pymongo import MongoClient
import networkx as nx
import numpy as np
import os
import datetime
import csv
import pandas as pd
import matplotlib.pyplot as plt



class pyTwitterAnalysis(pyTwitterGraphAnalysis, pyTwitterDB_class, pyTwitterTopics):

    def __init__(self, base_folder_path, mongoDB_database, strFocusedTweetFields, strFocusedTweetUserFields):        
        pyTwitterGraphAnalysis.__init__(self,base_folder_path)
        pyTwitterDB_class.__init__(self, mongoDB_database, strFocusedTweetFields, strFocusedTweetUserFields)
        pyTwitterTopics.__init__(self, base_folder_path, mongoDB_database)
        
        
    #creates a path to add the files for this node    
    def create_path(self, path):       
        if not os.path.exists(path):
            os.makedirs(path)      


    #aux function to concatenate edges to help filter in mongoDB
    def concat_edges(self, G):
        arr_edges = []
        for u,v,a in G.edges(data=True):
            arr_edges.append(u.lower() + '-' +v.lower())
            arr_edges.append(v.lower() + '-' +u.lower())

        return arr_edges

    
    def build_db_collections(self, inc=100000):
        
        
        ### Loading Focused Data into MongoDB
        self.loadFocusedData(inc)
        
        ### Loading user information to collection
        # Loading user information for the actual tweet document
        self.loadUsersData(inc, 'tweet')
        # Loading user information for the original tweet in case of retweets
        self.loadUsersData(inc, 'retweet')
        # Loading user information for the quoted tweet
        self.loadUsersData(inc, 'quote')
        # Loading user information for replies - (in this case we we don't have full information about the user. Only screen_name and user_id)
        self.loadUsersData(inc, 'reply')
        # Loading user information for mention - (in this case we we don't have full information about the user. Only screen_name and sometimes user_id)
        self.loadUsersData(inc, 'mention')

        #####    
        ### Breaking tweets into Words        
        self.loadWordsData(inc)

        #####    
        ### Loading tweet connections - These are the edges formed between users by replies, retweets, quotes and mentions
        self.loadTweetConnections(inc) # You can set the number of tweets to analyze at a time. (Large number may cause out of memory errors, low number may take a long time to run)

        
                
    
    #aux function to plot graph. This steps repets in different parts of this code, so creating a function to avoid repetition
    def plot_graph_contracted_nodes(self, G, file, graph_plot_cutoff_no_edges=1000, comty_contract_per=90, remove_edges='Y'):
                                
        
        graph_to_plot = G.copy()                
        
        print("Graph to plot before changes: nodes=" + str(len(graph_to_plot.nodes)) + " edges=" + str(len(graph_to_plot.edges)))
        
        att = 'community_louvain'
        G2 = self.contract_nodes_commty_per(graph_to_plot, comty_contract_per, att)
        G2 = self.largest_component_no_self_loops(G2)        

        #another level of contraction
        if remove_edges == 'Y':
        
            if len(G2.edges()) > 100000:       
                cutoff_no = 3
                G2 = self.remove_edges_eithernode(G2, cutoff_no)
                contraction_name = contraction_name + '[RmEitherNodeCutoff=' + str(cutoff_no) +  ']'
            
            cutoff_no = 5
            if len(G2.edges()) > graph_plot_cutoff_no_edges:
                while len(G2.edges()) > graph_plot_cutoff_no_edges:
                    G2 = self.remove_edges(G2, cutoff_no)
                    if len(G2.edges()) > 0:
                        G2 = self.largest_component_no_self_loops(G2)                    
                        
                    if cutoff_no < 150:
                        cutoff_no += 10
                    elif cutoff_no < 1000:
                        cutoff_no += 100
                    elif cutoff_no < 10000:
                        cutoff_no += 500
                    else:
                        cutoff_no += 1000                    
                        
                contraction_name = contraction_name + '[RmEdgeCutOff=' + str(cutoff_no) +  ']'
                        
            file = file.replace('.', contraction_name + '.') 
            
            
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

        if len(G2.edges()) < graph_plot_cutoff_no_edges and len(G2.edges()) != 0:
            if not os.path.exists(file):
                G_to_plot, labels2, k = self.calculate_louvain_clustering(G2)
                #labels = nx.get_node_attributes(G2, 'community_louvain').values()
                self.plotSpringLayoutGraph(G_to_plot, file, v_scale, v_k, v_iterations, cluster_fl='Y', v_labels=list(list(labels2)))                


        
    def export_all_edges_for_input(self, period_arr=None, bot_filter_fl='N'):
                                
        #creates path to add the edge files to be used as input
        input_files_path = self.folder_path + '\\data_input_files'
        self.create_path(input_files_path)

        #export ALL edges for ALL periods
        print("** exporting edges for AllPeriods - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.exportData('edges', input_files_path + '\\AllPeriods_', 0)

        if bot_filter_fl == 'Y':
            #export edges for ALL periods, excluding edges associated with bots
            print("** exporting edges for AllPeriods_ExcludingBots - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.exportData('edges', input_files_path + '\\AllPeriods_ExcludingBots_', 0, is_bot_Filter = '0')

            #export edges for ALL periods, only edges associated with bots
            print("** exporting edges for AllPeriods_BotsOnly - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.exportData('edges', input_files_path + '\\AllPeriods_BotsOnly_', 0, is_bot_Filter = '1')


        #export edges by period using the dates set on array period_arr
        if period_arr is not None:

            for idx, period in enumerate(period_arr):

                #export ALL edges for this period    
                print("** exporting edges for " + period[0] + " - "  + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                edges = self.exportData('edges', input_files_path + '\\' + period[0] + '_', 0, startDate_filter=period[1], endDate_filter=period[2], is_bot_Filter=None)

                if bot_filter_fl == 'Y':
                    #export edges for this period, excluding edges associated with bots
                    print("** exporting edges for " + period[0] + "_ExcludingBots - "  + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    edges = self.exportData('edges', input_files_path + '\\' + period[0] + '_ExcludingBots_', 0, startDate_filter=period[1], endDate_filter=period[2], is_bot_Filter='0')

                    #export edges for this period, only edges associated with bots        
                    print("** exporting edges for " + period[0] + "_BotsOnly - "  + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    edges = self.exportData('edges', input_files_path + '\\' + period[0] + '_BotsOnly_', 0, startDate_filter=period[1], endDate_filter=period[2], is_bot_Filter='1')

            
            
    def nodes_edges_analysis_files(self, G, path):                        
        
        print("****** Exporting nodes and edges to file - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.export_nodes_edges_to_file(G, path + "\\G_NodesWithDegree.txt", path + "\\G_Edges.txt")
        print("\n")

        print("****** Ploting Nodes Wordcloud *********** - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))        
        node_file_name = path + '\\G_NodesWithDegree.txt'
        df = self.read_freq_list_file(node_file_name,' ')    
        self.plot_word_cloud(df, file=path +'\\G_Nodes_WordCloud.png')
        print("\n")
        

    def lda_analysis_files(self, path, num_of_topics, startDate_filter=None, endDate_filter=None, is_bot_Filter=None, arr_edges=None):
    
        #export text for topic analysis
        print("****** Exporting text for topic analysis - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))    
        self.exportData('text_for_topics', path + "\\" , 0, startDate_filter, endDate_filter, is_bot_Filter, arr_edges)
        print("\n")

        # Train LDA models and print topics
        print("****** Topic discovery analysis (lda model) ****** - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))        
        topics_file_name = path + '\\T_tweetTextsForTopics.txt'        
        model_name = "Topics"
        self.train_model_from_file(topics_file_name, num_of_topics, model_name)
        self.plot_topics(path + '\\Topics-(LDA model).png', num_of_topics, 'lda')           
        


    def ht_analysis_files(self, path, startDate_filter=None, endDate_filter=None, is_bot_Filter=None, arr_edges=None):        
        
        #export ht frequency list         
        print("****** Exporting ht frequency list - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.exportData('ht_frequency_list', path + "\\" , 0, startDate_filter, endDate_filter, is_bot_Filter, arr_edges)
        print("\n")
                

        print("******************************************************")
        print("****** Ploting HashTags Barchart and Wordcloud *********** - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))                   
        ht_file_name = path + '\\T_HT_FrequencyList.txt'
        
        if os.stat(ht_file_name).st_size != 0:            
            df = self.read_freq_list_file(ht_file_name)
            self.plot_top_freq_list(df, 30, 'HashTag', exclude_top_no=0, file=path + '\\T_HT_Top30_BarChart.png')
            self.plot_top_freq_list(df, 30, 'HashTag', exclude_top_no=1, file=path + '\\T_HT_Top30_BarChart-(Excluding Top1).png')
            self.plot_top_freq_list(df, 30, 'HashTag', exclude_top_no=2, file=path + '\\T_HT_Top30_BarChart-(Excluding Top2).png')
            self.plot_word_cloud(df, file=path + '\\T_HT_WordCloud.png')
        

    def words_analysis_files(self, path, startDate_filter=None, endDate_filter=None, is_bot_Filter=None, arr_edges=None, top_no_word_filter=None):        
        
        #export words frequency list 
        print("****** Exporting words frequency list - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))        
        self.exportData('word_frequency_list', path + "\\" , 0, startDate_filter, endDate_filter, is_bot_Filter, arr_edges, top_no_word_filter)
        print("\n")    

        print("******************************************************")
        print("****** Ploting Word Barchart and Wordcloud *********** - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))                   
        word_file_name = path + '\\T_Words_FrequencyList.txt'
        if os.stat(word_file_name).st_size != 0:
            df = self.read_freq_list_file(word_file_name)
            self.plot_top_freq_list(df, 30, 'Word', exclude_top_no=0, file=path+'\\T_Words_Top30_BarChart.png')    
            self.plot_word_cloud(df, file=path+'\\T_Words_WordCloud.png')
        
        
    def time_series_files(self, path, startDate_filter=None, endDate_filter=None, is_bot_Filter=None, arr_edges=None):        
                          
        print("****** Exporting time series files - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))   
        #plot time series for all tweets
        tweet_df = self.get_time_series_df(startDate_filter=startDate_filter, endDate_filter=endDate_filter, is_bot_Filter=is_bot_Filter, arr_edges=arr_edges)
        self.plot_timeseries(tweet_df, ['tweet', 'tweet_created_at'], path + '\\TS_TweetCount.png')   
        
        #plot time series for top hashtags
        self.plot_top_ht_timeseries(top_no_start=1, top_no_end=5, file = path + '\\TS_TweetCountByHT[1-5].png', startDate_filter=startDate_filter, endDate_filter=endDate_filter, is_bot_Filter=is_bot_Filter, arr_edges=arr_edges)
        self.plot_top_ht_timeseries(top_no_start=3, top_no_end=10, file = path + '\\TS_TweetCountByHT[3-10].png', startDate_filter=startDate_filter, endDate_filter=endDate_filter, is_bot_Filter=is_bot_Filter, arr_edges=arr_edges)

            
        
    def graph_analysis_files(self, G, path, graph_plot_cutoff_no_edges=1000, comty_contract_per=90):                    
    
        #plot graph        
        print("******************************************************")
        print("****** Ploting graph... *********** - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))                
        
        
        if not os.path.exists(path + '\\Graph-(cutoff[' + str(graph_plot_cutoff_no_edges) + '].png') and not os.path.exists(path + '\\GraphOld-(cutoff[' + str(graph_plot_cutoff_no_edges) + '].png'):
            if len(G.edges()) < 450:
                v_scale = 0.01; v_k =0.7; v_iterations=50; v_node_size=2
            elif len(G.edges()) < 5000:
                v_scale = 2; v_k = 0.6; v_iterations=200; v_node_size=0.8
            elif len(G.edges()) < 10000:
                v_scale = 1; v_k = 0.1; v_iterations=200; v_node_size=0.6
            elif len(G.edges()) >= 10000:
                v_scale = 1; v_k = 0.05; v_iterations=500; v_node_size=0.6        

            if len(G.edges()) <= graph_plot_cutoff_no_edges and len(G.edges()) != 0:   
                G_to_plot, labels2, k = self.calculate_louvain_clustering(G)
                self.plotSpringLayoutGraph(G_to_plot, path + '\\Graph-(cutoff[' + str(graph_plot_cutoff_no_edges) + '].png', v_scale, v_k, v_iterations, cluster_fl='Y', v_labels=list(list(labels2))
                )
                   
                self.plotSpringLayoutGraph(G, path + '\\GraphOld-(cutoff[' + str(graph_plot_cutoff_no_edges) + '].png',
                                           v_scale, v_k, v_iterations, cluster_fl='N', v_alpha=1, scale_node_size_fl='N' )
                    
                

        #contracted        
        self.plot_graph_contracted_nodes(G, path + '\\Graph-(ContractedNodes).png', 
                                         graph_plot_cutoff_no_edges=graph_plot_cutoff_no_edges, 
                                         comty_contract_per=comty_contract_per)
        print("\n")
                        

    
    def edge_files_analysis(self, output_path, is_bot_Filter=None, period_arr=None, 
                      create_nodes_edges_files_flag='Y', create_graphs_files_flag='Y', create_topic_model_files_flag='Y', 
                      create_ht_frequency_files_flag='Y', create_words_frequency_files_flag='Y', create_timeseries_files_flag='Y',   
                      num_of_topics=4, top_no_word_filter=None, graph_plot_cutoff_no_edges=1000, comty_contract_per=90,
                      top_degree_start=1, top_degree_end=10, period_top_degree_start=1, period_top_degree_end=5
                     ):        
                
        
        #Get the right edges file to inport
        if is_bot_Filter is None:
            edge_file_path = self.folder_path + '\\data_input_files\\AllPeriods_edges.txt'
            parent_path = output_path + '\\All'
        elif is_bot_Filter == '0':
            edge_file_path = self.folder_path + '\\data_input_files\\AllPeriods_ExcludingBots_edges.txt'
            parent_path = output_path + '\\ExcludingBots'
        elif is_bot_Filter == '1':
            edge_file_path = self.folder_path + '\\data_input_files\\AllPeriods_BotsOnly_edges.txt'
            parent_path = output_path + '\\Bots_Edges_Only'
            
        self.create_path(output_path)
            
        G = self.loadGraphFromFile(edge_file_path)        
        self.all_analysis_file(G, parent_path, 
                               num_of_topics=num_of_topics,
                               is_bot_Filter=is_bot_Filter,
                               create_nodes_edges_files_flag=create_nodes_edges_files_flag, 
                               create_graphs_files_flag=create_graphs_files_flag, 
                               create_topic_model_files_flag=create_topic_model_files_flag, 
                               create_ht_frequency_files_flag=create_ht_frequency_files_flag, 
                               create_words_frequency_files_flag=create_words_frequency_files_flag,  
                               create_timeseries_files_flag=create_timeseries_files_flag,
                               startDate_filter=None, 
                               endDate_filter=None, 
                               graph_plot_cutoff_no_edges=graph_plot_cutoff_no_edges, 
                               comty_contract_per=comty_contract_per,
                               top_no_word_filter=top_no_word_filter,                                       
                               top_degree_start=top_degree_start, 
                               top_degree_end=top_degree_end
                               )
                                        
        #run analysis by period using the dates set on array period_arr
        if period_arr is not None:                                    
            
            #Creates a text file with the period information. This is just so that whoever is looking at these folder can know what dates we used for each period
            myFile = open(output_path + '\\PeriodsInfo.txt', 'w', encoding="utf-8")
            with myFile:
                writer = csv.writer(myFile, delimiter='\t', lineterminator='\n')
                writer.writerows(period_arr)
                    
            for idx, period in enumerate(period_arr):                    

                #Set the period information variables
                period_name = period[0]
                period_start_date = period[1]
                period_end_date = period[2]

                print("**********************************************************")
                print("************************** " + period_name + " ****************************\n" ) 

                #edge file path 
                if is_bot_Filter is None:
                    parent_path = output_path + "\\All_By_Period\\" + period_name
                    edge_file_path = output_path + "\\data_input_files\\" + period_name +"_edges.txt"    
                elif is_bot_Filter  == '0':
                    parent_path = output_path + "\\Excluding_Bots_By_Period\\" + period_name
                    edge_file_path = output_path + "\\data_input_files\\" + period_name +"_ExcludingBots_edges.txt"                
                elif is_bot_Filter  == '1':
                    parent_path = output_path + "\\Bots_Edges_Only_By_Period\\" + period_name
                    edge_file_path = output_path + "\\data_input_files\\" + period_name +"_BotsOnly_edges.txt"                

                self.create_path(parent_path)        

                #load graph from edge file
                G = self.loadGraphFromFile(edge_file_path)                
                #call function to genrate all files for this graph
                self.all_analysis_file(G, parent_path, 
                                       num_of_topics=num_of_topics,
                                       is_bot_Filter=is_bot_Filter,
                                       create_nodes_edges_files_flag=create_nodes_edges_files_flag, 
                                       create_graphs_files_flag=create_graphs_files_flag, 
                                       create_topic_model_files_flag=create_topic_model_files_flag, 
                                       create_ht_frequency_files_flag=create_ht_frequency_files_flag, 
                                       create_words_frequency_files_flag=create_words_frequency_files_flag,   
                                       create_timeseries_files_flag=create_timeseries_files_flag,
                                       startDate_filter=period_start_date, 
                                       endDate_filter=period_end_date, 
                                       graph_plot_cutoff_no_edges=graph_plot_cutoff_no_edges, 
                                       comty_contract_per=comty_contract_per,
                                       top_no_word_filter=top_no_word_filter,                                       
                                       top_degree_start=period_top_degree_start, top_degree_end=period_top_degree_end
                                       )
        
            
                    
    def all_analysis_file(self, G, output_path, num_of_topics=4, is_bot_Filter=None,
                          create_nodes_edges_files_flag='Y', create_graphs_files_flag='Y', create_topic_model_files_flag='Y', 
                          create_ht_frequency_files_flag='Y', create_words_frequency_files_flag='Y', create_timeseries_files_flag='Y',                         
                          startDate_filter=None, endDate_filter=None, graph_plot_cutoff_no_edges=1000, comty_contract_per=90,
                          top_no_word_filter=None, top_degree_start = 1, top_degree_end = 10
                         ):
        
        print("all_analysis_file" + output_path)
        
        
        #files for the main graph
        self.create_analysis_file(G, output_path, 
                                  num_of_topics, 
                                  create_nodes_edges_files_flag, 
                                  create_graphs_files_flag, 
                                  create_topic_model_files_flag, 
                                  create_ht_frequency_files_flag, 
                                  create_words_frequency_files_flag,   
                                  create_timeseries_files_flag,
                                  startDate_filter=startDate_filter, 
                                  endDate_filter=endDate_filter, 
                                  is_bot_Filter=is_bot_Filter,                                   
                                  graph_plot_cutoff_no_edges=graph_plot_cutoff_no_edges, 
                                  comty_contract_per=comty_contract_per,
                                  top_no_word_filter=top_no_word_filter
                         )
        
        #files for the top nodes        
        self.top_nodes_analysis( G, output_path, num_of_topics, 
                                create_nodes_edges_files_flag=create_nodes_edges_files_flag, 
                                create_graphs_files_flag=create_graphs_files_flag, 
                                create_topic_model_files_flag=create_topic_model_files_flag, 
                                create_ht_frequency_files_flag=create_ht_frequency_files_flag, 
                                create_words_frequency_files_flag=create_words_frequency_files_flag, 
                                create_timeseries_files_flag=create_timeseries_files_flag,
                                startDate_filter=startDate_filter, 
                                endDate_filter=endDate_filter, 
                                is_bot_Filter=is_bot_Filter, 
                                graph_plot_cutoff_no_edges=graph_plot_cutoff_no_edges, 
                                comty_contract_per=comty_contract_per, 
                                top_no_word_filter=top_no_word_filter,
                                top_degree_start=top_degree_start, 
                                top_degree_end=top_degree_end
                         )
        
        
    
    
    
    def create_analysis_file(self, G, output_path, num_of_topics, 
                          create_nodes_edges_files_flag, create_graphs_files_flag, create_topic_model_files_flag, 
                          create_ht_frequency_files_flag, create_words_frequency_files_flag, create_timeseries_files_flag,                         
                          startDate_filter=None, endDate_filter=None, is_bot_Filter=None, arr_edges=None, 
                          graph_plot_cutoff_no_edges=1000, comty_contract_per=90, top_no_word_filter=None
                         ):
                        
        
        #create graph from edge file
        #G = self.loadGraphFromFile(edge_file_path)
        
        #export file with measures
        self.print_Measures(G, fileName_to_print = output_path + "\\G_Measures-(All).txt")
        print("\n")

        #get largest connected component and export file with measures
        G = self.largest_component_no_self_loops(G)
        self.print_Measures(G, fileName_to_print = output_path + "\\G_Measures-(LargestCC).txt")
        print("\n")

        #export files with edges and degrees
        if create_nodes_edges_files_flag == 'Y':
            self.nodes_edges_analysis_files(G, output_path)
        
        #LDA Model
        if create_topic_model_files_flag == 'Y':
            self.lda_analysis_files(output_path, num_of_topics, startDate_filter=startDate_filter, endDate_filter=endDate_filter, is_bot_Filter=is_bot_Filter, arr_edges=arr_edges)

        #export ht frequency list 
        if create_ht_frequency_files_flag == 'Y':           
            self.ht_analysis_files(output_path, startDate_filter=startDate_filter, endDate_filter=endDate_filter, is_bot_Filter=is_bot_Filter, arr_edges=arr_edges)
            
        #export words frequency list 
        if create_words_frequency_files_flag == 'Y':
            self.words_analysis_files(output_path, startDate_filter=startDate_filter, endDate_filter=endDate_filter, is_bot_Filter=is_bot_Filter, arr_edges=arr_edges, top_no_word_filter=top_no_word_filter)
                             
        #plot graph
        if create_graphs_files_flag == 'Y':
            self.graph_analysis_files(G, output_path, graph_plot_cutoff_no_edges=graph_plot_cutoff_no_edges, comty_contract_per=comty_contract_per)
            
        if create_timeseries_files_flag == 'Y':
            self.time_series_files(output_path, startDate_filter=startDate_filter, endDate_filter=endDate_filter, is_bot_Filter=is_bot_Filter, arr_edges=arr_edges) 
        
        
    
    def top_nodes_analysis(self, G, output_path, num_of_topics, 
                          create_nodes_edges_files_flag, create_graphs_files_flag, create_topic_model_files_flag, 
                          create_ht_frequency_files_flag, create_words_frequency_files_flag, create_timeseries_files_flag,                        
                          startDate_filter=None, endDate_filter=None, is_bot_Filter=None, 
                          graph_plot_cutoff_no_edges=1000, comty_contract_per=90, top_no_word_filter=None,
                          top_degree_start = 1, top_degree_end = 10
                         ):                
        
        # Choose which graph you want to run this for
        Graph_to_analyze = G.copy()      
        
        top_degree_nodes = self.get_top_degree_nodes(Graph_to_analyze, top_degree_start, top_degree_end)

        #creates a folder to save the files for this analysis
        path = "Top_" + str(top_degree_start) + '-' + str(top_degree_end) 
        self.create_path(output_path + '\\' + path)

        i = top_degree_end
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

            
            print(path_node + '\\G_subgraph_' + node + '_Measures.txt')
            
            print("******************************************************")
            print("****** Printing measures for G_subgraph_" + node)
            self.print_Measures(G_subgraph, False, False, False, False, fileName_to_print = path_node + '\\G_subgraph_' + node + '_Measures.txt')    
            print("\n")
            
            
            arr_edges = self.concat_edges(G_subgraph)
            
            self.create_analysis_file(G_subgraph, output_path + '\\' + path_node, 
                                      num_of_topics=num_of_topics, 
                                      create_nodes_edges_files_flag=create_nodes_edges_files_flag, 
                                      create_graphs_files_flag=create_graphs_files_flag, 
                                      create_topic_model_files_flag=create_topic_model_files_flag, 
                                      create_ht_frequency_files_flag=create_ht_frequency_files_flag, 
                                      create_words_frequency_files_flag=create_words_frequency_files_flag, 
                                      create_timeseries_files_flag=create_timeseries_files_flag,
                                      startDate_filter=startDate_filter, 
                                      endDate_filter=endDate_filter, 
                                      is_bot_Filter=is_bot_Filter, 
                                      arr_edges=arr_edges, 
                                      graph_plot_cutoff_no_edges=graph_plot_cutoff_no_edges, 
                                      comty_contract_per=comty_contract_per,
                                      top_no_word_filter=top_no_word_filter)
            i -= 1
            

                        
                
                        
                    
    def get_time_series_df(self, ht_arr=None, is_bot_Filter=None, startDate_filter=None, endDate_filter=None, arr_edges=None):

        
        df = pd.DataFrame()

        if ht_arr is not None:        
            #get timeseries for each of the top hashtags    
            for i, ht in enumerate(ht_arr):
                arrData, file = self.queryData(exportType='tweet_ids_timeseries', filepath='', inc=0, 
                                                         ht_to_filter=ht, 
                                                         startDate_filter=startDate_filter, 
                                                         endDate_filter=endDate_filter, 
                                                         is_bot_Filter=is_bot_Filter, 
                                                         arr_edges=arr_edges)    
                tweet_df = pd.DataFrame(list(arrData))
                tweet_df.columns = ['tweet_created_at', ht]   
                df = pd.concat([df,tweet_df], axis=0, ignore_index=True)


        else:
            #get timeseries for all tweets
            arrData, file = self.queryData(exportType='tweet_ids_timeseries', filepath='', inc=0,                                                     
                                                         startDate_filter=startDate_filter, 
                                                         endDate_filter=endDate_filter, 
                                                         is_bot_Filter=is_bot_Filter, 
                                                         arr_edges=arr_edges)    
            tweet_df = pd.DataFrame(list(arrData))
            tweet_df.columns = ['tweet_created_at', 'tweet']   
            df = pd.concat([df,tweet_df], axis=0, ignore_index=True)


        return df


    
    def plot_top_ht_timeseries(self, top_no_start, top_no_end, file, is_bot_Filter=None, startDate_filter=None, endDate_filter=None, arr_edges=None):
        
        
        #get the top hashtags to plot
        ht_arr, f = self.queryData(exportType='ht_frequency_list', filepath='', inc=0, 
                                   startDate_filter=startDate_filter, endDate_filter= endDate_filter, is_bot_Filter=is_bot_Filter, arr_edges=arr_edges, 
                                   top_no_filter=top_no_end, include_hashsymb_FL=False)
        
                
        if len(ht_arr) < top_no_end:
            top_no_end = len(ht_arr)
            
            
        if len(ht_arr) == 0 or top_no_start >= top_no_end:
            return ""
        
        ht_arr = np.array(ht_arr)
        ht_arr = ht_arr[top_no_start-1:top_no_end,0]
        ht_arr = list(ht_arr)
        
        #get the time series data
        df = self.get_time_series_df(ht_arr=ht_arr, is_bot_Filter=is_bot_Filter, startDate_filter=startDate_filter, endDate_filter=endDate_filter, arr_edges=arr_edges)

        #plot timeseries graph
        arr_columns = ht_arr.copy()
        arr_columns.append('tweet_created_at')        
        self.plot_timeseries(df, arr_columns, file)


        

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
    
       

    def eda_analysis(self):
                
        edge_file_path = self.folder_path + '\\data_input_files\\AllPeriods_edges.txt'
        G = self.loadGraphFromFile(edge_file_path)
        
        self.plot_disconnected_graph_distr(G, file=self.folder_path + '\\EDA.png')
        
        
            