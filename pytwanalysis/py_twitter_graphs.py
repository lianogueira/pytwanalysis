import os
import csv
import datetime
import networkx as nx
import numpy as np
import numpy.linalg as la
import community as community_louvain
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from networkx import algorithms
from networkx.algorithms import distance_measures
from networkx.algorithms.components import is_connected
from networkx.algorithms.dominance  import immediate_dominators
import numpy as np
from sklearn.cluster import SpectralClustering
from sklearn import metrics
import math

import scipy as sp
from scipy.sparse import csgraph
import scipy.cluster.vq as vq
import scipy.sparse.linalg as SLA
    
import pandas as pd
import seaborn as sns
    
    
class TwitterGraphs:   

    def __init__(self, folder_path):
        
        #creates path if does not exists
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    
        self.folder_path = folder_path        
        self.graph_details_file = folder_path + "\\log_graph_plots.txt"
        
        f = open(self.graph_details_file, "a")
        f.write('graph_name\t scale\t k\t iteration\t kmeans_k\t starttime\t endtime\t'  + '\n')
        f.close()
            

    #####################################
    # Method: loadGraphFromFile
    # Description: method receives nodes and edges files and returns an nwtworkx 
    # Parameters: 
    #   -nodes_file = file path and file name for netwrok nodes
    #   -edge_file = file path and file name for netwrok edges with weight
    def loadGraphFromFile(self, edge_file):
        
        G = nx.Graph()
        G = nx.read_edgelist(edge_file, data=(('weight',float),))

        return G

        
    # function to plot network graph
    # Parameters: G - NetworkX graph
    #             v_graph_name - The name of your graph
    #             v_scale - Scale factor for positions. The nodes are positioned in a box of size [0,scale] x [0,scale].
    #             v_k - Optimal distance between nodes - Increase this value to move nodes farther apart.
    #             v_iterations - Number of iterations of spring-force relaxation
    #             cluster_fl - determines if you are sending labels for clusters or not
    #             v_labels - cluster labels
    #             kmeans_k - k_means k used for clustering
    #             node_color - node color, default '#A0CBE2'
    #             edge_color - edge color, default '#A79894'
    #             width - with, default 0.05
    #             node_size - node size, default 0.6
    #             font_size - font size, default 1
    #             dpi - size of the image in dpi, default 800
    # More details at: https://networkx.github.io/documentation/networkx-1.9/reference/generated/networkx.drawing.layout.spring_layout.html
    '''
    def plotSpringLayoutGraph(self, G, v_graph_name, v_scale, v_k, v_iterations, 
                              cluster_fl='N', v_labels=None, kmeans_k='', v_node_color='#A0CBE2', v_edge_color='#A79894', 
                              v_width=0.05, v_node_size=0.6, v_font_size=1, v_dpi=900):
    '''
    
        

    #####################################
    # Method: plot_graph_att_distr
    # Description: Plot distribution of nodes based on graph attribute (e.g. communitiy)
    def plot_graph_att_distr(self, G, att, title='Community Counts', xlabel='Community ID', ylabel='Count', file_name=None, replace_existing_file=True):
        #create dataframe based on the given attribute
        df = pd.DataFrame.from_dict(nx.get_node_attributes(G, att),  orient='index')
        df.columns = [att] 
        df.index.rename('node' , inplace=True)
        sns.distplot(df[att], kde=False, bins=100)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        #if file name was give, save file in default folder
        if file_name != None:
            if replace_existing_file==True or not os.path.exists(file_name):
                plt.savefig(file_name)
            
        plt.show()
        plt.cla()   # Clear axis
        plt.clf()   # Clear figure
        plt.close() # Close a figure window
        

        
    #####################################
    # Method: plot_disconnected_graph_distr
    # Description: plot the distribution of disconnected graphs
    def plot_disconnected_graph_distr(self, G, file=None, replace_existing_file=True, size_cutoff=None):
    
        sub_conn_graphs = sorted(list(nx.connected_component_subgraphs(G)), key = len, reverse=True)
    
        if size_cutoff is not None:
            sub_conn_graphs2 = sub_conn_graphs.copy()
            sub_conn_graphs = []

            for x in sub_conn_graphs2:
                if len(x.nodes()) > size_cutoff:
                    sub_conn_graphs.append(x)
                
                
        x = []
        y = []
        for i, a in enumerate(sub_conn_graphs):
            x.append(len(a.nodes()))
            y.append(len(a.edges()))

        fig, axs = plt.subplots(2, 3,figsize=(16,10))
        
        try:
            axs[0, 0].plot(x, y, 'ro'); axs[0, 0].set_title('All subgraphs')
            x.pop(0); y.pop(0); axs[0, 1].plot(x, y, 'ro'); axs[0, 1].set_title('Excluding top1')
            x.pop(0); y.pop(0); axs[0, 2].plot(x, y, 'ro'); axs[0, 2].set_title('Excluding top2')
            x.pop(0); y.pop(0); axs[1, 0].plot(x, y, 'ro'); axs[1, 0].set_title('Excluding top3')
            x.pop(0); y.pop(0); axs[1, 1].plot(x, y, 'ro'); axs[1, 1].set_title('Excluding top4')
            x.pop(0); y.pop(0); axs[1, 2].plot(x, y, 'ro'); axs[1, 2].set_title('Excluding top5')
        except Exception as e:            
                print("Warning: could not plot all 6  - " +str(e))
                pass 
        
        for ax in axs.flat:
            ax.set(xlabel='Nodes', ylabel='Edges')
            
        #if file name was give, save file in default folder
        if file != None:
            if replace_existing_file==True or not os.path.exists(file):
                plt.savefig(file)
            
        plt.show()
        plt.cla()   # Clear axis
        plt.clf()   # Clear figure
        plt.close() # Close a figure window
        
        return len(sub_conn_graphs)

    
    #####################################
    # Method: contract_nodes_commty_per
    # Description: reduce graph based on a percentage given for each community found
    def contract_nodes_commty_per(
            self,
            G, 
            perc, 
            comm_att='community_louvain', 
            enforce_ext_nodes_conn_fl ='N', 
            commty_already_calculated='N'):

        G_to_contract = G.copy()        
        all_nodes = []

        #if we need to calculate the communities because the original report doesn't have the community labels
        if commty_already_calculated == 'N':
            G_to_contract, labels, k = self.calculate_louvain_clustering(G_to_contract)


        #find the number of communities in the graph
        no_of_comm = max(nx.get_node_attributes(G_to_contract, comm_att).values())+1    

        #loop through the communities and get the top nodes for each communities based on the given percentage
        for commty in range(no_of_comm):

            #find subgraphs of this community
            com_sub_graph = G_to_contract.subgraph([n for n,attrdict in G_to_contract.node.items() if attrdict [comm_att] == commty ])
            arr_nodes = np.array(sorted(com_sub_graph.degree(), key=lambda x: x[1], reverse=True))

            #get the comunity size and calculate how many top nodes we want to use based on the given percentage
            comm_size = len(com_sub_graph)        
            top_nodes = math.ceil(comm_size*(1-(perc/100)))
            if top_nodes == 1: top_nodes=top_nodes+1
            arr_top_nodes = arr_nodes[:top_nodes,0]

            if enforce_ext_nodes_conn_fl == 'Y':
                #create subgraph including external edges
                G_W_Ext_Edges = G_to_analyze.edge_subgraph(G_to_analyze.edges(com_sub_graph.nodes()))    
                #find the nodes in this community with external edges
                G_edges_Rem = G_W_Ext_Edges.copy()
                G_edges_Rem.remove_edges_from(com_sub_graph.edges())
                nodes_w_ext_edges = G_edges_Rem.edge_subgraph(G_edges_Rem.edges()).nodes()                            
                arr_top_nodes = np.concatenate((arr_top_nodes, nodes_w_ext_edges))

            all_nodes = np.concatenate((all_nodes, arr_top_nodes))

        #Create graph with only the contracted nodes
        G_Contracted = G_to_contract.subgraph(all_nodes)
        G_Contracted = self.largest_component_no_self_loops(G_Contracted)

        return G_Contracted


    #####################################
    # Method: draw_scaled_labels
    # Description: draw labels in the graphs
    def draw_labels_for_node(self, G, nodes, size, pos):  
        labels = {}        
        for node in G.nodes():
            if node in nodes:
                #set the node name as the key and the label as its value 
                labels[node] = node

        nx.draw_networkx_labels(G, pos, labels, font_size=size)


    #####################################
    # Method: draw_scaled_labels
    # Description: draw labels in the graph scaled by node degree
    def draw_scaled_labels(self, G, pos, default_font_size, font_size_multiplier):
        #get array of nodes in sorted order
        arr = np.array(sorted(G.degree(), key=lambda x: x[1], reverse=True))    
        #get the value of the highest degree. We will use this as reference to calculate the fonte sizes
        top_value = int(arr[:1,1])

        nodes_with_same_font_size = []
        for node, degree in arr:    

            #calculate the font size for this node
            size_scale = (int(degree) * 1) / top_value
            new_font_size = size_scale*font_size_multiplier

            #if the calculate font size is greater than the parameter give, print that label. If not add to the array of nodes with the default size.
            if new_font_size > default_font_size:
                self.draw_labels_for_node(G, node, new_font_size, pos)
            else:
                nodes_with_same_font_size.append(node)

        #Print labels for all nodes with the default size.
        self.draw_labels_for_node(G, nodes_with_same_font_size, default_font_size, pos)


    #####################################
    # Method: plotSpringLayoutGraph
    # Description: plot graph
    def plotSpringLayoutGraph(
            self, 
            G,  
            v_graph_name,  
            v_scale,  
            v_k,  
            v_iterations, 
            cluster_fl='N',  
            v_labels=None,  
            kmeans_k='',  
            v_node_color='#A0CBE2',  
            v_edge_color='#A79894', 
            v_width=0.05,  
            v_node_size=0.6,  
            v_font_size=0.4,  
            v_dpi=900,  
            v_alpha=0.6,  
            v_linewidths=0.6,
            scale_node_size_fl='Y',  
            draw_in_mult_steps_fl='N',  
            node_size_multiplier=6,  
            font_size_multiplier=7, 
            replace_existing_file=True):


        if replace_existing_file==True or not os.path.exists(v_graph_name):
            
            v_with_labels = True
            if scale_node_size_fl == 'Y':
                d = dict(G.degree)
                v_node_size = [(v * node_size_multiplier)/10 for v in d.values()]
                v_with_labels = False

            #node_color=v_labels,
            #node_color=v_node_color,
            #draw graph
            pos=nx.spring_layout(G, scale=v_scale, k=v_k, iterations=v_iterations)   #G is my graph
            if cluster_fl == 'N':                    
                nx.draw(G, pos,                 
                        width=v_width,                          
                        edge_color=v_edge_color,
                        node_color=v_node_color,
                        edge_cmap=plt.cm.Blues, 
                        with_labels=v_with_labels, 
                        node_size=v_node_size, 
                        font_size=v_font_size,                  
                        linewidths=v_linewidths,
                        alpha=v_alpha)
            else:         
                nx.draw(G, pos,
                        node_color=v_labels,
                        edge_color=v_edge_color,
                        width=v_width,
                        cmap=plt.cm.viridis,
                        edge_cmap=plt.cm.Purples,
                        with_labels=v_with_labels,
                        node_size=v_node_size,
                        font_size=v_font_size,
                        linewidths=v_linewidths,
                        alpha=v_alpha)


            # draw labels - logic to print labels in nodes in case we 
            # want to change the font size to match the scale of the node size
            if scale_node_size_fl == 'Y':
                self.draw_scaled_labels(G, pos, v_font_size, font_size_multiplier)           


            plt.savefig(v_graph_name, dpi=v_dpi, facecolor='w', edgecolor='w')

            plt.show()
            plt.cla()   # Clear axis
            plt.clf()   # Clear figure
            plt.close() # Close a figure window
   


        
    #####################################
    # Method: largest_component_no_self_loops
    # Description: remove self loops nodes, isolate nodes and exclude smaller components
    def largest_component_no_self_loops(self, G):           
                
        G2 = G.copy()
        
        G2.remove_edges_from(nx.selfloop_edges(G2))    
        for node in list(nx.isolates(G2)):
            G2.remove_node(node)
         
        graphs = sorted(list(nx.connected_component_subgraphs(G2)), key = len, reverse=True)
        
        #G = max(nx.connected_components(G), key=len)
        if len(graphs) > 0:
            return graphs[0]
        else:
            return G2
        
    
    #####################################
    # Method: export_nodes_edges_to_file
    # Description: export nodes and edges of a graph into a file
    def export_nodes_edges_to_file(self, G, node_f_name, edge_f_name):
                        
        nx.write_edgelist(G,  edge_f_name)               
        np.savetxt(node_f_name, np.array(sorted(G.degree(), key=lambda x: x[1], reverse=True)), fmt="%s", encoding="utf-8")
        
        
    #####################################
    # Method: create_node_subgraph
    # Description: creates a subgraph for one node. 
    # subgraph contains all nodes connected to that node and their edges to each other
    def create_node_subgraph(self, G, node):
        G_subgraph_edges = nx.Graph()
        G_subgraph_edges = G.edge_subgraph(G.edges(node))
        G_subgraph = G.subgraph(G_subgraph_edges.nodes())
        
        return G_subgraph
        
    #####################################
    # Method: get_top_degree_nodes
    # Description: returns a array of the top degree nodes based on parameter passed by user    
    def get_top_degree_nodes(self, G, top_degree_start, top_degree_end):
        
        return np.array(sorted(G.degree(), key=lambda x: x[1], reverse=True))[top_degree_start-1:top_degree_end]
    
    
    #####################################
    # Method: calculate_spectral_clustering_labels
    # Description: calculate cluster labels for a graph
    def calculate_spectral_clustering_labels(self, G, k, affinity = 'precomputed', n_init=100):
        #adj_mat = nx.to_numpy_matrix(G)
        adj_mat = nx.to_scipy_sparse_matrix(G)        
        sc = SpectralClustering(k, affinity=affinity, n_init=n_init)
        sc.fit(adj_mat)
               
        return  sc.labels_
    
    
    #####################################
    # Method: calculate_spectral_clustering
    # Description: calculate cluster labels for a graph
    def calculate_spectral_clustering(self, G, k=None, affinity = 'precomputed', n_init=100):
        
        #calculate adjacent matrix
        adj_mat = nx.to_scipy_sparse_matrix(G)  
        
        #get number of clusters if None was given
        if k == None:
            nb_clusters, eigenvalues, eigenvectors = self.eigenDecomposition(adj_mat)            
            k = nb_clusters[0]
              
        #calculate spectral clustering labels
        sc = SpectralClustering(k, affinity=affinity, n_init=n_init)
        sc.fit(adj_mat)
        
        #update graph with the communitites
        dic = dict(zip(G.nodes(), sc.labels_))
        nx.set_node_attributes(G, dic, 'community_spectral')        
               
        return G, list(sc.labels_), k
    
    
    #####################################
    # Method: calculate_louvain_clustering
    # Description: calculate cluster labels for a graph using community_louvain
    def calculate_louvain_clustering(self, G):
        
        # compute the best partition
        partition = community_louvain.best_partition(G)

        #get number of clusters
        partition_arr = list(partition.values())
        partition_arr_no_dups = list(dict.fromkeys(partition_arr)) 
        k = len(partition_arr_no_dups) #number of clusters

        #update graph with the communitites
        dic = dict(zip(G.nodes(), partition.values()))
        nx.set_node_attributes(G, dic, 'community_louvain')
               
        return G, partition.values(), k
    
    
    #####################################
    # Method: calculate_separability
    # Description: calculates the separability score for a community
    # Parameters:
    #   -G_Community: the subgraph with of nodes that belong to the same commty
    #   -G_All: The entire graph
    #   -dens: separability score
    def calculate_separability(self, G_Community, G_All):            
        
        # #of edges for that community - (internal nodes)
        ms = len(G_Community.edges(G_Community.nodes()))
        
        # #of edges edges pointing outside of the community - (external nodes)        
        cs = len(G_All.edges(G_Community.nodes())) - ms
        
        # ratio between internal and external nodes
        sep = ms/cs
        
        return sep
    
    
    #####################################
    # Method: calculate_density
    # Description: calculates the density score for a community
    # Parameters:
    #   -G_Community: the subgraph with of nodes that belong to the same commty    
    # Returns:
    #   -dens: density score
    def calculate_density(self, G_Community):            
        
        # #of edges for that community 
        ms = len(G_Community.edges())
        
        # #of nodes for that community 
        ns = ms = len(G_Community.nodes())
        
        # fraction of the edges that appear between the nodes in G_Community
        dens = ms / (ns * (ns-1) / 2)
        
        return dens
    
    
    #####################################
    # Method: calculate_average_clustering_coef
    # Description: calculates the average clustering coefficient of a graph
    # Parameters:
    #   -G_Community: the subgraph with of nodes that belong to the same commty    
    # Returns:
    #   -acc: the average clustering coefficient
    def calculate_average_clustering_coef(self, G_Community):
        
        # calculates the average clustering coefficient number
        acc = nx.average_clustering(G_Community)

        return acc
    
    
    #####################################
    # Method: calculate_cliques
    # Description: calculates the clique number of the graph and 
    # the number of maximal cliques in the graph.
    # Parameters:
    #   -G_Community: the subgraph with of nodes that belong to the same commty    
    # Returns:
    #   -gcn: the clique number of the graph
    #   -nofc: the number of maximal cliques in the graph
    def calculate_cliques(self, G):
        
        gcn = nx.graph_clique_number(G)
        nofc = nx.graph_number_of_cliques(G)

        return gcn, nofc
    
    
    #####################################
    # Method: calculate_power_nodes_score
    # Description: calculates power nodes score    
    # This is to calculate how many of the total nodes 
    # in graph are connected to a few top degree nodes
    # Parameters:
    #   -G: the graph to analyze
    #   -top_no: top number of nodes you want to analyze
    # Returns:
    #   -pns: power nodes score    
    #         1 means that all other nodes in the graph 
    #         are connected to the top nodes
    def calculate_power_nodes_score(self, G, top_no=3):

        # number of nodes of the original graph
        no_of_nodes = len(G.nodes())                

        # get the top 3 high degree nodes
        arr_nodes = []
        for x in list(self.get_top_degree_nodes(G, 1, top_no)):
            arr_nodes.append(x[0])
    
        # creates a subgrpah of all nodes conencted to the top nodes
        sub_graph = self.create_node_subgraph(G, arr_nodes)
        
        # number of nodes of the sub-graph of top nodes
        no_of_nodes_sub_graph = len(sub_graph.nodes()) 
        
        # calculates the ratio between the two.        
        pns = no_of_nodes_sub_graph / no_of_nodes

        return pns
    
    #####################################
    # Method: calculate_average_node_degree
    # Description: calculates the average of the degree of all nodes        
    # Parameters:
    #   -G: the graph to analyze    
    # Returns:
    #   -deg_mean: the mean 
    def calculate_average_node_degree(self, G):
        
        arr = np.array(sorted(G.degree(), key=lambda x: x[1], reverse=True))                
        deg_mean = np.asarray(arr[:,1], dtype=np.integer).mean()
        
        return deg_mean

    
    #####################################
    # Method: print_cluster_metrics
    # Description: print cluster graphs metrics
    def print_cluster_metrics(self, G_Community, G_All, top_no=3, acc_node_size_cutoff=None):
    
        if acc_node_size_cutoff is None:
            acc_node_size_cutoff = len(G_Community.nodes())
            
        print("# of Nodes: " + str(len(G_Community.nodes())))
        print("# of Edges: " + str(len(G_Community.edges())))
        
        deg_mean = self.calculate_average_node_degree(G_Community)
        print("Average Node Degree: " + str(deg_mean)  + " - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        sep = self.calculate_separability(G_Community, G_All)
        print("Separability: " + str(sep)+ " - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        den = self.calculate_density(G_Community)
        print("Density: " + str(den)+ " - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            
        if acc_node_size_cutoff > len(G_Community.nodes()):
            acc = self.calculate_average_clustering_coef(G_Community)
            print("Average Clustering Coefficient: " + str(acc) + " - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        else:
            print("Average Clustering Coefficient: " + " (**more nodes than the cutoff number)")
                
        gcn, nofc = self.calculate_cliques(G_Community)
        print("Clique number: " + str(gcn))
        print("Number of maximal cliques: " + str(nofc) + " - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
        pns = self.calculate_power_nodes_score(G_Community, top_no)
        print("Power Nodes Score: " + str(pns) + " - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        


    #####################################
    # Method: eigenDecomposition
    # Description: This method performs the eigen decomposition on a given affinity matrix
    # Re-used code from https://github.com/ciortanmadalina/high_noise_clustering
    # Parameters: 
    #   -af_matrix = Affinity matrix
    #    -bln_plot = flag to determine if we should plot the sorted eigen values for visual inspection or not
    #    -topK = number of suggestions as the optimal number of of clusters
    # Returns: 
    #   -nb_clusters = the optimal number of clusters by eigengap heuristic
    #   -eigenvalues = all eigen values
    #   -eigenvectors = all eigen vectors
    def eigenDecomposition(self, af_matrix, bln_plot = False, topK = 5):       
        
        #construct the laplacian of the matrix
        L = csgraph.laplacian(af_matrix, normed=True)
        n_components = af_matrix.shape[0]

        # LM parameter : Eigenvalues with largest magnitude (eigs, eigsh), that is, largest eigenvalues in 
        # the euclidean norm of complex numbers.
        #eigenvalues, eigenvectors = sp.sparse.linalg.eigs(L)
        eigenvalues, eigenvectors = SLA.eigsh(L, which = 'LM')

        if bln_plot:
            plt.title('Largest eigen values of input matrix')
            plt.scatter(np.arange(len(eigenvalues)), eigenvalues)
            plt.grid()

        # Identify the optimal number of clusters as the index corresponding
        # to the larger gap between eigen values
        index_largest_gap = np.argsort(np.diff(eigenvalues))[::-1][:topK]
        nb_clusters = index_largest_gap + 1

        return nb_clusters, eigenvalues, eigenvectors

    


    
        
    #####################################
    # Method: remove_edges
    # Description: removes edges of nodes with less than the given degree. 
    # (both nodes in the edge must be less than the given degree for us to remove the edge)
    def remove_edges(self, G, min_degree_no):
        
        G2 = G.copy()        
        count = 0
        for edge in list(G2.edges()):
            degree_node_from = G2.degree(edge[0])
            degree_node_to = G2.degree(edge[1])

            if degree_node_from < min_degree_no and degree_node_to < min_degree_no:
                count = count +1
                G2.remove_edge(edge[0], edge[1])

        print(str(count) + ' edges removed')        
        return G2    
    
    

    #####################################
    # Method: remove_edges_eithernode
    # Description: removes edges of nodes with less than the given degree. 
    # (both nodes in the edge must be less than the given degree for us to remove the edge)
    def remove_edges_eithernode(self, G, min_degree_no):
        
        G2 = G.copy()
        count = 0
        for edge in list(G2.edges()):
            degree_node_from = G2.degree(edge[0])
            degree_node_to = G2.degree(edge[1])

            if degree_node_from < min_degree_no or degree_node_to < min_degree_no:
                count = count +1
                G2.remove_edge(edge[0], edge[1])

        print(str(count) + ' edges removed')
        return G2       
    
    
    
    #####################################
    # Method: contract_nodes_degree1
    # Description: Contract nodes degree 1 in groups of the given number
    def contract_nodes_degree1(self, G, n_to_group):    
        
        G2 = G.copy()    
        degree_to_contract = 1                 
        
        for node_degree in list(sorted(G2.degree, key=lambda x: x[1], reverse=True)):    
            
            try:
                D = nx.descendants(G2, node_degree[0])
                D.add(node_degree[0])
                this_node_subgraph = G2.subgraph(D)


                ##################### degree1
                nodes_degree1 = [node for node, degree in list(this_node_subgraph.degree()) if degree == degree_to_contract]
                subgraph_degree1 = this_node_subgraph.subgraph(nodes_degree1)

                j = 0
                n = int(n_to_group/(degree_to_contract))

                for node in list(subgraph_degree1):                           
                    if j==0 or j%n==0:
                        first_node = node
                    else:        
                        G2 = nx.contracted_nodes(G2, first_node, node, self_loops=True)

                    j=j+1                                                                             

            except Exception as e:        
                continue
          

        return G2    
    
        
    #####################################
    # Method: print_Measures
    # Description: print Graph measures to the screen and to a file 
    def print_Measures(
            self, 
            G, 
            blnCalculateDimater=False, 
            blnCalculateRadius = False, 
            blnCalculateExtremaBounding=False, 
            blnCalculateCenterNodes=False, 
            fileName_to_print = None):
        
        
        #verify if graph is connected or not
        try:
            blnGraphConnected =  is_connected(G)
        except:
            blnGraphConnected = False
            
        
        no_nodes =  str(len(G.nodes()))
        no_edges = str(len(G.edges()))
        print("# Nodes: " + no_nodes)
        print("# Edges: " + no_edges)
        
        
        #Calculate and print Diameter 
        if blnCalculateDimater == True:
            if blnGraphConnected == True:
                diameter_value = str(distance_measures.diameter(G))
                print("Diameter: " + diameter_value)
            else:
                diameter_value = "Not possible to calculate diameter. Graph must be connected"
                print(diameter_value)
                
        #Calculate and print Radius 
        if blnCalculateRadius == True:
            if blnGraphConnected == True:
                radius_value = str(distance_measures.radius(G))
                print("Radius: " + radius_value)
            else:
                radius_value = "Not possible to calculate radius. Graph must be connected"
                print(radius_value)        
        
        #Calculate and print Extrema bounding 
        if blnCalculateExtremaBounding == True:
            if blnGraphConnected == True:
                extrema_bounding_value = str(distance_measures.extrema_bounding(G))
                print("Extrema bounding: " + extrema_bounding_value) 
            else:
                extrema_bounding_value = "Not possible to calculate Extrema bounding. Graph must be connected"
                print(extrema_bounding_value)
        
        #Calculate and print Centers
        if blnCalculateCenterNodes == True:
            str_centers_nodes=""
            if blnGraphConnected == True:
                centers_nodes = distance_measures.center(G)    
                str_centers_nodes = str(sorted(G.degree(centers_nodes), key=lambda x: x[1], reverse=True))
                print("Centers with their degree: " + str_centers_nodes) 
            else:
                centers_nodes = "Not possible to calculate Centers. Graph must be connected"
                print(centers_nodes)


        # if file name is passed in the parameters, we save the measures into a file
        if fileName_to_print != None:
            #creates path if does not exists
            
            if not os.path.exists(os.path.dirname(fileName_to_print)):
                os.makedirs(os.path.dirname(fileName_to_print))
                        
            f = open(fileName_to_print, "w")
            f.write("# Nodes: " + no_nodes + "\n")
            f.write("# Edges: " + no_edges + "\n")
            
            if blnCalculateDimater == True:
                f.write("Diameter: " + diameter_value + "\n")
            if blnCalculateRadius == True:
                f.write("Radius: " + radius_value + "\n")
            #if blnCalculateBaryCenter == True:
            #    f.write("Bary Center: " + barycenter_node + "\n")        
            if blnCalculateExtremaBounding == True:
                f.write("Extrema bounding: " + extrema_bounding_value + "\n")
            if blnCalculateCenterNodes == True:
                f.write("Centers with their degree: " + str_centers_nodes + "\n")
                
            f.close()
