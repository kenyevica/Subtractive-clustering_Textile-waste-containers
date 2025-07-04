###% Routing: distance of two cities (by coordinates) along the roads --> (runtime for 3200 municipalities = ~10 hours (400 municipalities/console))
#Checking runtime while the nearest separator is found for all the cities
import pickle
import pandas as pd
import networkx as nx

road_nw=pickle.load(open('filename3.pickle', 'rb'))
df_cities = pd.read_csv('df_cities1.csv')

def tic():
    #Homemade version of matlab tic and toc functions
    import time
    global startTime_for_tictoc
    startTime_for_tictoc = time.time()

def toc():
    import time
    if 'startTime_for_tictoc' in globals():
        print("Elapsed time is " + str(time.time() - startTime_for_tictoc) + " seconds.")
    else:
        print("Toc: start time not set")


# What is the distance between municipalities (runtime=~90 sec./town)
# tic()
nn=5
jj0=400*nn
jjend=400*(nn+1)
distance_from_towns=pd.Series()
for jj in list(range(jj0,jjend)):
    print(jj)
    j=df_cities['node_id'][jj] #node ID
    edge_length=[0]*len(df_cities)
    for ii in df_cities['node_id'][jj+1:].index.values:
        i = df_cities['node_id'][jj + 1:][ii]  # node ID

        solved = False
        while not solved:
            try:
                # edge_length.append(nx.shortest_path_length(road_nw, j, i, weight="length"))
                edge_length[ii] = nx.shortest_path_length(road_nw, j, i, weight="length")
                solved = True
            except nx.exception.NetworkXNoPath:
                try:
                    edge_length[ii] = nx.shortest_path_length(road_nw, i,j, weight="length")
                except nx.exception.NetworkXNoPath:
                    print((i,j))
                solved = True

    distance_from_towns=distance_from_towns._append(pd.Series([edge_length], index=[jj]))
distance_from_towns.to_csv(f"test{jj0}_{jjend-1}.csv") #SAVE
# toc()

