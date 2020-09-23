Reference
==============================


TwitterAnalysis
---------------

.. automodule:: ta.TwitterAnalysis
.. autosummary::
   
   :toctree: generated/
   :recursive:
      
   setConfigs
   concat_edges
   build_db_collections
   plot_graph_contracted_nodes
   export_mult_types_edges_for_input
   nodes_edges_analysis_files
   lda_analysis_files
   ht_analysis_files
   words_analysis_files
   time_series_files   
   graph_analysis_files
   edge_files_analysis
   get_time_series_df   
   eda_analysis
   print_top_nodes_cluster_metrics
   print_commty_cluster_metrics
   ht_connection_files
   plot_top_ht_timeseries
   plot_timeseries
   
   
   
TwitterDB
---------

.. automodule:: ta.TwitterDB
.. autosummary::
   
   :toctree: generated/
   :recursive:
      
   setFocusedDataConfigs
   loadDocFromFile   
   search7dayapi
   searchPremiumAPI   
   create_bat_file_apisearch
   loadFocusedData
   loadUsersData
   loadTweetHashTags
   loadTweetConnections
   loadTweetHTConnections
   loadWordsData
   loadAggregations
   set_bot_flag_based_on_arr
   cleanTweetText      
   exportData
   queryData            


TwitterGraphs
-------------

.. automodule:: ta.TwitterGraphs
.. autosummary::
   
   :toctree: generated/
   :recursive:
      
   loadGraphFromFile
   plot_graph_att_distr
   plot_disconnected_graph_distr
   contract_nodes_commty_per
   plotSpringLayoutGraph
   largest_component_no_self_loops
   export_nodes_edges_to_file
   create_node_subgraph
   get_top_degree_nodes
   calculate_spectral_clustering_labels
   calculate_spectral_clustering
   calculate_louvain_clustering
   calculate_separability
   calculate_density
   calculate_average_clustering_coef
   calculate_cliques
   calculate_power_nodes_score
   calculate_average_node_degree
   print_cluster_metrics
   eigenDecomposition
   remove_edges
   remove_edges_eithernode
   print_Measures
   
   
   

TwitterTopics
-------------

.. automodule:: ta.TwitterTopics
.. autosummary::
   
   :toctree: generated/
   :recursive:
      
   get_coh_u_mass
   get_coh_c_v   
   get_docs_from_file
   clean_docs
   train_model
   train_model_from_file
   plot_topics
   read_freq_list_file
   plot_top_freq_list
   plot_word_cloud