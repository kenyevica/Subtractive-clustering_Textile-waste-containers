##% Loading existing container's GPS coordinates data
import pandas as pd
# from matplotlib.sphinxext.mathmpl import latex_math
# from packaging.tags import interpreter_name
import matplotlib
matplotlib.use("TkAgg")  # külső ablakos, interaktív backend
import matplotlib.pyplot as plt
plt.ion()

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

# Data of container counts per town
df1 = pd.read_excel('Ruhagyujto-kontenerek-ABC-2024.10.14_ke.xlsx', sheet_name='Table 1',
                   usecols=['County', 'Town', 'pcs_loc']) #GPS itt a konténereké...
# print(df.head())
df1.dropna(axis=0, how='all', inplace=True)
df1=df1.groupby(['Town','County'],as_index=False).sum()

#Data of towns (GPS coordinates, inhabitants)
df2 = pd.read_excel('HKK_nodes (2).xlsx', sheet_name='nodes',
                   usecols=['Town','Inhabitants', 'y_lat','x_lon']) #GPS a településeké...
df2.dropna(axis=0, how='all', inplace=True)

df1["y_lat"]=0.0
df1["x_lon"]=0.0
df1["Inhabitants"]=0
for i in df1['Town']:
    df1.loc[df1['Town']==i,"y_lat"]=df2.loc[df2['Town']==i,"y_lat"].iloc[0]
    df1.loc[df1['Town'] == i,"x_lon"] = df2.loc[df2['Town'] == i,"x_lon"].iloc[0]
    df1.loc[df1['Town'] == i,"Inhabitants"] = df2.loc[df2['Town'] == i,"Inhabitants"].iloc[0]

# df1.columns



##% FIGURE: Distribution of inhabitants in municipalities without containers
import matplotlib.pyplot as plt

df_empty_towns=df2[~df2['Town'].isin(df1['Town'])]

fig, ax = plt.subplots()
# df2['Inhabitants'].hist()
ax.hist(df_empty_towns['Inhabitants'],bins=100)
plt.xlabel('Inhabitants per municipality [-]')
plt.ylabel('Counts [-]')
axin1 = ax.inset_axes([0.6, 0.1, 0.35, 0.25])
axin1.hist(df_empty_towns['Inhabitants'],bins=100,color='red')
axin1.set_ylim([0,8])
plt.show()

# ##% Histogram of empty towns' latitude and longitude
# plt.subplot(1,2,1)
# plt.hist(df_empty_towns['y_lat'],bins=100)
# plt.subplot(1,2,2)
# plt.hist(df_empty_towns['x_lon'],bins=100)
# plt.show()

##% Road network of Hungary (main roads) (runtime=~1 min., cf2 --> 5 min.)

import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox

# #Creating new road_nw from OSMnX
#     ##% OSMnx package:
#     # Help: https://medium.com/@revathyponn/visualise-your-favourite-citys-road-network-using-python-12254d605ed8
#     # Help: https://geoffboeing.com/2016/11/osmnx-python-street-networks/
#     ##% CITE!:https://geoffboeing.com/publications/osmnx-paper/ ( https://geoffboeing.com/2016/11/osmnx-python-street-networks/)
#
# all_types=['motorway','motorway_link','primary','primary_link','secondary',
#  'secondary_link', 'tertiary','tertiary_link','trunk','trunk_link',
#  'unclassified','living_street','residential','rest_area',]
# # cf = ('["highway"~"motorway|motorway_link|primary|primary_link|secondary|secondary_link|'
# #        'tertiary|tertiary_link|trunk|trunk_link|unclassified|living_street|residential"]') #cf2
#
# cf = ('["highway"~"motorway|motorway_link|primary|primary_link|secondary|secondary_link|'
#       'tertiary|tertiary_link|trunk|trunk_link"]') #main roads
# #
# road_nw=ox.graph_from_place('Hungary', network_type ='drive',custom_filter=cf) #load

import pickle
filename="filename3.pickle"

# # SAVE
# with open(filename, 'wb') as f:
#     pickle.dump(road_nw, f)

#Loading road_nw from existing file
# LOAD
# filename3.pickle: filter (cf) without living and residential area; filename4.pickle: whole road network (large!)
road_nw=pickle.load(open(filename, 'rb'))

##% FIGURE
fig, ax = ox.plot_graph(road_nw,node_size=0, edge_linewidth=0.5, edge_color='gainsboro',bgcolor='white',show=True, close=False) #plot here, edge_linewidth=0.05
ax.scatter(df2['x_lon'],df2['y_lat'],c='black',s=1, label='Without containers')
ax.scatter(df1['x_lon'],df1['y_lat'],c='red',s=7, label='With containers')
plt.legend()
ax.legend(loc='upper left')
plt.show()
# plt.savefig('fig3_v1.eps', format='eps')

##% FIGURE: Distribution of containers and inhabitans
import plotly.express as px

# fig = px.density_map(df1, lat = 'y_lat', lon = 'x_lon',z = (df1['pcs_loc']-df1['pcs_loc'].min())/(df1['pcs_loc'].max()-df1['pcs_loc'].min()),radius=50, zoom=6.5) #normalized
fig = px.density_map(df1, lat = 'y_lat', lon = 'x_lon',z = 'pcs_loc',radius=50, zoom=6.5,range_color=[0,df1['pcs_loc'].max()],color_continuous_scale=px.colors.sequential.Reds[3:],labels={'pcs_loc': 'Containers'}) #count, #piros jobb, [3,:]
fig.show()
fig.write_html("fig_containers.html", auto_open=True)

# fig = px.density_map(df2, lat = 'y_lat', lon = 'x_lon', z = (df2['Inhabitants']-df2['Inhabitants'].min())/(df2['Inhabitants'].max()-df2['Inhabitants'].min()),radius=50,zoom=6.5) #normalized
fig = px.density_map(df2, lat = 'y_lat', lon = 'x_lon', z = 'Inhabitants', radius=50, color_continuous_scale=px.colors.sequential.Reds[3:],zoom=6.5) #count #piros jobb, [2,:]
fig.show()
fig.write_html("fig_inhabitants.html", auto_open=True)

###% Practise: Calculation of distances between towns and containers
##% Match cities and separators with the nearest node_id (runtime=appr. 1.5 min.; with the larger road_nw, very slow)

# G=road_nw
# orig=[]
# dest=[]
# df_cities=df2
#
# for i in range(len(df_cities)):
#     orig.append(ox.distance.nearest_nodes(G, X=df_cities['x_lon'][i], Y=df_cities['y_lat'][i]))
#
# df_cities['node_id']=pd.Series(orig)
#
# #Manual correction (put a node to the nearest two direction node)
# df_cities['node_id'][df_cities['node_id']==11544660596]=9900127605
# df_cities['node_id'][df_cities['node_id']==6800072176]=2826071058
# df_cities['node_id'][df_cities['node_id']==6909949313]=2443858616
# df_cities['node_id'][df_cities['node_id']==6290058001]=1252818474
# df_cities['node_id'][df_cities['node_id']==9900127605]=408936090
# df_cities['node_id'][df_cities['node_id']==9067213422]=9067213458
# df_cities['node_id'][df_cities['node_id']==325238314]=274923610 #274923610 Ráckeve, közelebbi nem volt jó...
# df_cities['node_id'][df_cities['node_id']==325237650]=274923610
# df_cities['node_id'][df_cities['node_id']==448473710]=156576038
# df_cities['node_id'][df_cities['node_id']==317319649]=1765172770
# df_cities['node_id'][df_cities['node_id']==685490906]=5420444892
# df_cities['node_id'][df_cities['node_id']==685490783]=274679388


#
# #Source: Abaliget
# # df_cities['node_id'][df_cities['node_id']==1600073373]=16769876
#
# #
# # df_cities['node_id'][df_cities['node_id']==6909949313]=2443858616
# # df_cities[df_cities['node_id']==9067213422]
#
# #SAVE
# # df_cities.to_csv('df_cities.csv',index=False)

# OR
# LOAD
# df_cities.csv: before manual correction; df_cities1.csv: after manual correction
df_cities = pd.read_csv('df_cities1.csv')

###% Routing: distance of two cities (by coordinates) along the roads
# #Checking runtime while the nearest separator is found for all the cities
# import pickle
# import pandas as pd
# import networkx as nx
#
# road_nw=pickle.load(open('filename3.pickle', 'rb'))
# df_cities = pd.read_csv('df_cities1.csv')
#
# def tic():
#     #Homemade version of matlab tic and toc functions
#     import time
#     global startTime_for_tictoc
#     startTime_for_tictoc = time.time()
#
# def toc():
#     import time
#     if 'startTime_for_tictoc' in globals():
#         print("Elapsed time is " + str(time.time() - startTime_for_tictoc) + " seconds.")
#     else:
#         print("Toc: start time not set")
#
#
# # What is the distance between municipalities (runtime=~90 sec./town)
# tic()
# jj0=3
# jjend=5
# distance_from_towns=pd.Series()
# for jj in list(range(jj0,jjend)): #len(df_cities['node_id']): #range(int(len(df_cities)/3154)): #TIME
#     print(jj)
#     j=df_cities['node_id'][jj] #node ID
#     edge_length=[0]*len(df_cities)
#     for ii in df_cities['node_id'][jj+1:].index.values: #range(len(df_separators)): #TIME
#         i=df_cities['node_id'][jj+1:][ii] #node ID
#         # edge_length.append(nx.shortest_path_length(road_nw, j, i, weight="length")) #TIME: G--> original 'road_nw'
#         edge_length[ii]=nx.shortest_path_length(road_nw, j, i, weight="length")  # TIME: G--> original 'road_nw'
#     distance_from_towns=distance_from_towns._append(pd.Series([edge_length], index=[jj]))
# toc()

#---
# DO IT WITH calc_dist.py FILE (in multiple consoles) AND LOAD RESULTS HERE:
#---
#
# #Merging result files
# import pandas as pd
# df_cities = pd.read_csv('df_cities1.csv')
#
# console_step=400
# distances=pd.DataFrame()
# for jj0 in list(range(0,len(df_cities),console_step)):
#     distances=distances._append(pd.read_csv(f"test{jj0}_{jj0+400-1}.csv",index_col=0,converters={'0': pd.eval}))
# distances.columns=['Distances']
# #pd.eval (to recreate list from strings) as above OR:
# # from ast import literal_eval
# #literal_eval(distances.iloc[2,0])[1300] #index row number
#
# #Check indexes (if all the towns are gathered; indexes were assigned during the calculation before .csv creation)
# distances.index.values.sum()==sum(range(len(df_cities)))
#
# #Filling the lower triangular matrix symmetrically
# for jj in list(range(len(distances['Distances'][0]))):
#     for ii in range(0,jj):
#         if distances['Distances'][jj][ii]==0:
#             distances['Distances'][jj][ii]=distances['Distances'][ii][jj]
#         else:
#             print('ERROR') #check

#OR
# Loading "distances" from existing file
import pickle
filename="distances_all.pickle"

# # SAVE
# with open(filename, 'wb') as f:
#     pickle.dump(distances, f)


# LOAD
# distances_all.pickle: all distances, filled both triangular matrices
distances=pickle.load(open(filename, 'rb'))


##% Substractive clustering (GPS-based)
# LOAD: distances data
import pandas as pd
import pickle
import numpy as np



# distances_all.pickle: all distances between towns [in m], filled both triangular matrices
distances=pickle.load(open("distances_all.pickle", 'rb'))
# df_waste.csv: textilte waste per inhabitant
df_waste = pd.read_csv('df_waste.csv')
df_waste = pd.read_csv('df_waste.csv')
# df_cities.csv: before manual correction; df_cities1.csv: after manual correction in node_id-s
df_cities = pd.read_csv('df_cities1.csv')

# #-----
# # IF textile waste amount is wanted to be used for weighting instead of population (ON: "WASTE", OFF: "INHAB")
# df2 = pd.read_excel('HKK_nodes (2).xlsx', sheet_name='nodes',
#                    usecols=['County','Town','Inhabitants', 'y_lat','x_lon']) #GPS a településeké...
# df2.dropna(axis=0, how='all', inplace=True)
# # df_cities=df_cities[df_cities['Town']!='LAKCÍM NÉLKÜLI']
# # df_cities=df_cities.reset_index(drop=True)
#
# df_cities['Textile per person']=0
# for i in range(len(df_cities)):
#     if df_cities['Town'][i]!='LAKCÍM NÉLKÜLI':
#         df_cities['Textile per person'][i]=df_waste['Textile per person'][df_waste["County_ID"]==df2['County'][df_cities['Town'].iloc[i]==df2['Town']].iloc[0]]
#         df_cities['Inhabitants'][i] = df_cities['Inhabitants'][i] * df_cities['Textile per person'][i] #Textile per town in real in this case
# #-----

data=pd.concat([df_cities[['Town','Inhabitants']], distances], axis=1)

# applying the algorithm
# from subtractive_clustering_gps import subtractive_clustering_algorithm
# from subtractive_clustering_gps_capacity import subtractive_clustering_algorithm
# from subtractive_clustering_gps_capacity_init import subtractive_clustering_algorithm

import importlib
import subtractive_clustering_gps_capacity_init
importlib.reload(subtractive_clustering_gps_capacity_init)
from subtractive_clustering_gps_capacity_init  import subtractive_clustering_algorithm  # újraimport!

center_init = pd.DataFrame([],columns=['pcs_loc']) #if it is empty, # "RAW"
# center_init = df1[['Town','pcs_loc']] # "PLUS" #SVAE: init_pot
ra=222.71 #mean: 12400 m/person/day
# import math
# ra=math.sqrt(1000000)*2 #KEINNEN  --> IF change, CHANGE init_pot as well... --> tendency is the same, but normalized for 0-1 #KEVISSZA

#For potential sensitivity
# pot_init = pickle.load(open("potential_initial.pickle", 'rb')) #SAVE:init_potential (in RAW case!)
Nc_and_pot_all=[]

# # Original
# centers, newdata, init_potential = subtractive_clustering_algorithm(ra,ra,data, center_init, "center number", N_center=2453) #Eup=0.5, Edown=0.15, TNcenter: there are 2453 cont. at the moment
# centers, newdata, init_potential = subtractive_clustering_algorithm(ra,ra,data,"absolute potential", N_center=503) #Eup=0.5, Edown=0.15

#KEINNEN
# Optimal number of containers (uncovered potential sensitivity)
tic()
for i in [2453]: #range(2500,8000,200): #2453 is included
    print(i)
    centers, newdata, init_potential = subtractive_clustering_algorithm(ra, ra, data, center_init, "center number",
                                                                        N_center=i)  # Eup=0.5, Edown=0.15, TNcenter: there are 2453 cont. at the moment
    # pot_raw_Nc=newdata[:,[0,3]]
    # Nc_and_pot_all.append([i,pot_raw_Nc[:, -1][pot_raw_Nc[:, -1] >= 0].sum() / pot_init[:, -1][pot_init[:, -1] >= 0].sum()])
toc()

# SAVE
# with open("centers_flexcap_inhab_2453_raw_vproba.pickle", 'wb') as f:
#     pickle.dump(centers, f)
# with open("potential_predcont_cap1500_inhab_6000_plus_v1.pickle", 'wb') as f:
#     pickle.dump(newdata[:,[0,3]], f)

# with open("potential_predcont_cap1500_6000_raw.pickle", 'wb') as f:
#     pickle.dump(newdata[:,[0,3]], f)
# with open("potential_realcont_v1.pickle", 'wb') as f: # "PLUS"
#     pickle.dump(init_potential[:,[0,3]], f)
# with open("potential_predcont_inhab_6000_plus.pickle", 'wb') as f:
#     pickle.dump(newdata[:,[0,3]], f)
# with open("potential_flexcap_2453cont_initial.pickle", 'wb') as f:
#     pickle.dump(init_potential[:,[0,3]], f)
#
# with open("sens_cont_number_2500_8000_100_alfa30000.pickle", 'wb') as f:
#     pickle.dump(Nc_and_pot_all, f)

##% FIGURE: Density map of the final containers (CIKK: fig8.png)
import pickle
import numpy as np
import pandas as pd

centers = pickle.load(open("centers_cap_inhab_6500_plus.pickle", 'rb'))[:,0]
centers_new = np.unique(centers, return_counts=True)
df_new = pd.DataFrame({'Town':centers_new[0],'pcs_loc':centers_new[1]})
# df_allcont_withpcs = pd.concat([df1[['Town','pcs_loc']],df_new]).groupby(['Town'],as_index=False).sum() #with PLUS
df_allcont_withpcs = pd.concat([df_new]).groupby(['Town'],as_index=False).sum() # with RAW or PLUS (if only the news are wanted)

df_allcont_withpcs["y_lat"]=0
df_allcont_withpcs["x_lon"]=0
for i in df_allcont_withpcs['Town']:
    df_allcont_withpcs["y_lat"][df_allcont_withpcs['Town']==i]=df2[df2['Town']==i]["y_lat"].iloc[0]
    df_allcont_withpcs["x_lon"][df_allcont_withpcs['Town'] == i] = df2[df2['Town'] == i]["x_lon"].iloc[0]


#% Map (density)
import plotly.express as px
fig = px.density_map(df_allcont_withpcs, lat = 'y_lat', lon = 'x_lon',z = 'pcs_loc',radius=50, zoom=6.5, range_color=[0,df1['pcs_loc'].max()],labels={'pcs_loc': 'Containers'})
fig.show()
fig.write_html("fig_containers_final.html", auto_open=True)

##% FIGURE: Difference density map of the final containers (CIKK:fig5.eps/png,fig6.eps/png; eps: color=gainsboro, 0.05 linewidth)
import pickle
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

centers = pickle.load(open("centers_cap_inhab_2453_raw.pickle", 'rb'))[:,0] #fig5: "centers_flexcap_inhab_2453_raw.pickle"; fig6: "centers_cap_inhab_2453_raw.pickle"
centers_new = np.unique(centers, return_counts=True)
df_new = pd.DataFrame({'Town':centers_new[0],'pcs_loc':centers_new[1]})
# df_allcont_withpcs = pd.concat([df1[['Town','pcs_loc']],df_new]).groupby(['Town'],as_index=False).sum() #with PLUS
df_allcont_withpcs = pd.concat([df_new]).groupby(['Town'],as_index=False).sum() # with RAW or PLUS (if only the news are wanted)

df2_new=df2
df2_new["pcs_loc1"] = 0 #real
df2_new["pcs_loc2"] = 0 #predicted
df2_new["pcs_loc_diff"] = 0
for i in df2_new['Town']:
    if (df1['Town']==i).sum()>0:
        df2_new["pcs_loc1"][df2_new['Town']==i]=df1[df1['Town']==i]["pcs_loc"].iloc[0]
    if (df_allcont_withpcs['Town']==i).sum()>0:
        df2_new["pcs_loc2"][df2_new['Town']==i]=df_allcont_withpcs[df_allcont_withpcs['Town']==i]["pcs_loc"].iloc[0]
df2_new["pcs_loc_diff"] = df2_new["pcs_loc1"] - df2_new["pcs_loc2"]

# #% Map (density)
# import plotly.express as px
# fig = px.density_map(df2_new, lat = 'y_lat', lon = 'x_lon',z = 100*df2_new['pcs_loc_diff'],radius=20, zoom=6.5)
# fig.show()
# fig.write_html("fig_containers_diff.html", auto_open=True)

# FIGURE
import osmnx as ox
import pickle
import matplotlib.pyplot as plt
import matplotlib.lines
# filename3.pickle: filter (cf) without living and residential area; filename4.pickle: whole road network (large!)
road_nw=pickle.load(open('filename3.pickle', 'rb'))
#eps (linewidht, color)
# fig, ax = ox.plot_graph(road_nw,node_size=0, edge_linewidth=0.05,edge_color='gainsboro', bgcolor='white',show=True, close=False) #plot here
#png
fig, ax = ox.plot_graph(road_nw,node_size=0, edge_linewidth=0.05,edge_color='black', bgcolor='white',show=True, close=False) #plot here
#OR: size scale
ax.scatter(df2_new['x_lon'][df2_new['pcs_loc_diff']>0],df2_new['y_lat'][df2_new['pcs_loc_diff']>0],c='red',s=2*3*df2_new['pcs_loc_diff'][df2_new['pcs_loc_diff']>0],label='Surplus') #real-predicted
ax.scatter(df2_new['x_lon'][df2_new['pcs_loc_diff']<0],df2_new['y_lat'][df2_new['pcs_loc_diff']<0],c='blue',s=2*3*abs(df2_new['pcs_loc_diff'][df2_new['pcs_loc_diff']<0]),label='Deficit') #predicted
# # ax.scatter(df2_new['x_lon'][df2_new['pcs_loc_diff']==0],df2_new['y_lat'][df2_new['pcs_loc_diff']==0],facecolors='None', edgecolors='k',s=0.5,label='Optimal') #predicted
#OR: colorscale
# ax.scatter(df2_new['x_lon'][df2_new['pcs_loc_diff']>0],df2_new['y_lat'][df2_new['pcs_loc_diff']>0],c=df2_new['pcs_loc_diff'][df2_new['pcs_loc_diff']>0],cmap=ListedColormap(plt.cm.Reds(np.linspace(0.2, 0.9, 256))),s=2*3*2,label='Surplus') #real-predicted
# ax.scatter(df2_new['x_lon'][df2_new['pcs_loc_diff']<0],df2_new['y_lat'][df2_new['pcs_loc_diff']<0],c=abs(df2_new['pcs_loc_diff'][df2_new['pcs_loc_diff']<0]),cmap=ListedColormap(plt.cm.Blues(np.linspace(0.2, 0.9, 256))),s=2*3*2,label='Deficit') #predicted


xxx = 10
xxxx = 30
custom_legend = [
    matplotlib.lines.Line2D([], [], marker='o', color='r', label=f'Surplus (+{xxxx}) ',
                            markerfacecolor='red', markersize=np.sqrt(6 * xxxx), linestyle='None'),  # Larger marker
    matplotlib.lines.Line2D([], [], marker='o', color='r', label=f'Surplus (+{xxx}) ',
           markerfacecolor='red', markersize=np.sqrt(6*xxx),linestyle='None'),  # Larger marker
    matplotlib.lines.Line2D([], [], marker='o', color='r', label='Surplus (+1)',
                            markerfacecolor='red', markersize=np.sqrt(6),linestyle='None'),  # Smaller marker
    matplotlib.lines.Line2D([], [], marker='o', color='b', label=f'Deficit (-{xxxx})',
                            markerfacecolor='blue', markersize=np.sqrt(6 * xxxx), linestyle='None'),  # Larger marker
    matplotlib.lines.Line2D([], [], marker='o', color='b', label=f'Deficit (-{xxx})',
           markerfacecolor='blue', markersize=np.sqrt(6*xxx),linestyle='None'),  # Larger marker
    matplotlib.lines.Line2D([], [], marker='o', color='b', label='Deficit (-1)',
                            markerfacecolor='blue', markersize=np.sqrt(6),linestyle='None')  # Smaller marker
]
plt.legend(handles=custom_legend,loc='upper left').set_draggable(True)
fig.set_size_inches(11.5, 8.7)
plt.show()

## FIGURE: Sensitivity analysis on container number (remaining potential vs. settled containers) (CIKK: fig7)
import pickle
Nc_and_pot_all = pickle.load(open('sens_cont_number_2500_8000_100.pickle', 'rb'))

import matplotlib.pyplot as plt
plt.figure()
plt.plot([Nc_and_pot_all[i][0] for i in range(len(Nc_and_pot_all))],[Nc_and_pot_all[i][1] for i in range(len(Nc_and_pot_all))])
plt.xlabel('Number of containers [-]')
plt.ylabel(r'$\Delta \, P$' + '  [-]')
plt.show()
# [Nc_and_pot_all[i][0] for i in range(len(Nc_and_pot_all))]
##% TEST: Jaccard-similarity of two container location lists (without orders)
from simphile import jaccard_list_similarity
import pickle

list_init=[]
for i in range(len(df1)):
    list_init = list_init + int(df1['pcs_loc'][i])*[df1['Town'][i]]


# list_a = pickle.load(open("centers_cap_waste_2453_raw.pickle", 'rb'))[:,0]
list_b = pickle.load(open("centers_flexcap_inhab_2453_raw.pickle", 'rb'))[:,0]

print(f"Jaccard Similarity: {jaccard_list_similarity(list_b, list_init)}")

##% TEST: Wasserstein-distance of two container location lists (without orders, but locations are considered)
from scipy.stats import wasserstein_distance_nd
import pickle
import numpy as np

list_init=[]
for i in range(len(df1)):
    list_init = list_init + int(df1['pcs_loc'][i])*[df1['Town'][i]]

list_a = pickle.load(open("centers_cap_waste_2453_raw.pickle", 'rb'))[:,0] #INFO
list_b = pickle.load(open("centers_flexcap_inhab_2453_raw_vproba.pickle", 'rb'))[:,0] #INFO "centers_flexcap_inhab_2453_raw.pickle"

df_b=pd.DataFrame(list_b,columns=['Town'])
df_bb=pd.DataFrame({'Town':np.unique(list_b),'pcs_loc':np.unique(list_b, return_counts=True)[1]}) #for faster Wasserstein
df_aa=pd.DataFrame({'Town':np.unique(list_a),'pcs_loc':np.unique(list_a, return_counts=True)[1]}) #for faster Wasserstein
df_a=pd.DataFrame(list_a,columns=['Town'])
df_init=pd.DataFrame(list_init,columns=['Town'])

from func_container_optimization import give_GPS
df_b=give_GPS(df2,df_b)
df_a=give_GPS(df2,df_a)
df_bb=give_GPS(df2,df_bb)
df_aa=give_GPS(df2,df_aa)

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

# # #Real vs. predicted (1 minute)
# tic()
# WD_real_pred = wasserstein_distance_nd(np.array(df1[['y_lat','x_lon']]),np.array(df_bb[['y_lat','x_lon']]),df1['pcs_loc']/df1['pcs_loc'].sum(),df_bb['pcs_loc']/df_bb['pcs_loc'].sum())
# toc()
# #Predicted: waste vs. inhab
# tic()
# WD_waste_inhab = wasserstein_distance_nd(np.array(df_aa[['y_lat','x_lon']]),np.array(df_bb[['y_lat','x_lon']]),df_aa['pcs_loc']/df_aa['pcs_loc'].sum(),df_bb['pcs_loc']/df_bb['pcs_loc'].sum())
# toc()
# #Population vs. (real) container distribution (6 min.)
# tic()
# WD_pop_contreal = wasserstein_distance_nd(np.array(df2[['y_lat','x_lon']]),np.array(df1[['y_lat','x_lon']]),df2['Inhabitants']/df2['Inhabitants'].sum(),df1['pcs_loc']/df1['pcs_loc'].sum())
# toc()
# #Population vs. (predicted) container distribution (20 min.)
tic()
WD_pop_contpredict = wasserstein_distance_nd(np.array(df2[['y_lat','x_lon']]),np.array(df_bb[['y_lat','x_lon']]),df2['Inhabitants']/df2['Inhabitants'].sum(),df_bb['pcs_loc']/df_bb['pcs_loc'].sum())
toc()
print(f"Wasserstein Distance (real vs. optimal): {WD_real_pred}")
##% TEST: Initial potentials (100%) vs. final potentials (remaining potentials)
import pickle

pot_init = pickle.load(open("potential_initial.pickle", 'rb')) #SAVE:init_potential
# pot_raw_2453 = pickle.load(open("potential_predcont_inhab_2453_raw.pickle", 'rb')) #SAVE:newdata
pot_raw_2453 = pickle.load(open("potential_predcont_cap1500_inhab_2453_raw.pickle", 'rb')) #SAVE:newdata
pot_raw_6000 = pickle.load(open("potential_predcont_cap1500_inhab_6000_raw.pickle", 'rb')) #SAVE:newdata, potential_predcont_inhab_6000_raw.pickle
pot_real_2453 = pickle.load(open("potential_realcont_cap1500.pickle", 'rb')) #SAVE:init_potential
pot_plus_6000 = pickle.load(open("potential_predcont_cap1500_inhab_6000_plus.pickle", 'rb'))  #SAVE:newdata #these are the final potentials (the real containers are considered at the beginning), potential_predcont_cap1500_inhab_6000_plus_v1.pickle


pot_init[:,-1][pot_init[:,-1]>=0].sum()
CC=pot_raw_2453[:,-1][pot_raw_2453[:,-1]>=0].sum()/pot_init[:,-1][pot_init[:,-1]>=0].sum()
DD=pot_raw_6000[:,-1][pot_raw_6000[:,-1]>=0].sum()/pot_init[:,-1][pot_init[:,-1]>=0].sum()
AA=pot_real_2453[:,-1][pot_real_2453[:,-1]>=0].sum()/pot_init[:,-1][pot_init[:,-1]>=0].sum()
BB=pot_plus_6000[:,-1][pot_plus_6000[:,-1]>=0].sum()/pot_init[:,-1][pot_init[:,-1]>=0].sum()


# eee = pickle.load(open('centers_cap1500_inhab_6000_plus_v1.pickle','rb'))
# fff = pickle.load(open('centers_cap_inhab_6000_plus.pickle','rb'))





##% FIGURE: Initial potentials
# Histogram
import matplotlib.pyplot as plt
plt.hist(init_potential[:,3],bins=100)
plt.xlabel('Initial potential')
plt.ylabel('Counts')
plt.show()

#% Map (density)
import plotly.express as px
fig = px.density_map(df_cities, lat = 'y_lat', lon = 'x_lon',z = init_potential[:,3],radius=20, zoom=6.5)
fig.show()
fig.write_html("fig_init_potentials.html", auto_open=True)

##% TEST: Spearman rank correlation between the population-based order and the container placement order (only without capacity! because cannot be repeated...)
from scipy import stats

step=1
n_from=0
to=len(centers)
rank_corr2_list=[]
for n_first in range(n_from,to,step): #n_first: how many first towns in the list are considered
    centers2=centers[:n_first,:]

    order_container=centers2[:,0]
    order_inhab=centers2[:,0][(-centers2[:,1]).argsort()]

    df_cities2=df_cities[df_cities['Town'].isin(order_container)]['Town']
    order_container2=[0]*len(order_container)
    order_inhab2=[0]*len(order_inhab)
    for i in range(len(df_cities2)):
        order_container2[i]=list(order_container).index(df_cities2.iloc[i]) #rank in case of the container order
        order_inhab2[i] = list(order_inhab).index(df_cities2.iloc[i]) #rank in case of the inhabitant order
    rank_corr2=stats.spearmanr(order_inhab2,order_container2) #equal to the pearson (as we created the ranks just like spearman do, and then pearson)
    rank_corr2_list.append(rank_corr2.statistic)

print(f"The Spearman correlation coefficient between the rank of municipalities by inhabitants and container settlements: {rank_corr2.statistic}.")

plt.figure()
plt.plot(range(n_from,to,step),rank_corr2_list)
plt.xlabel('$N_{towns}$ [-]')
plt.ylabel('Rank correlation coefficient [-]')
plt.ylim([-1,1])
plt.show()


##% TEST: How much the 503 current container location [df1] equals to the first 503 predicted [centers]?
# method="center number", N_center=503
import osmnx as ox
import numpy as np

#centers_(flex)cap_inhab_2453_raw.pickle: first 2453 by inhabitants; centers_cap_waste_2453_raw.pickle: first 2453 by textile
centers=pickle.load(open("centers_cap_inhab_2453_raw_wrong.pickle", 'rb'))

#N_center=503 if only the places are considered without capacity; N_centers=2453 with capacity
agrees=(df1['Town'].isin(centers[:,0]))
print(agrees.sum())
print(str(agrees.sum()) + ' municipalities appears in both lists.')
agreed_cities=df1['Town'][df1['Town'].isin(centers[:,0])]


#if capacity is considered:
np.unique(centers[:,0]).shape #number of container municipalities
print(str(int(np.unique(centers[:,0]).shape[0])) + ' municipalities appears in the optimal container system.')

S_point=10

# FIGURE
fig, ax = ox.plot_graph(road_nw,node_size=0, edge_linewidth=0.2, bgcolor='white',show=True, close=False) #plot here
ax.scatter(df2['x_lon'][df2['Town'].isin(centers[:,0])],df2['y_lat'][df2['Town'].isin(centers[:,0])],c='blue',s=S_point,label='Predicted containers') #predicted
ax.scatter(df1['x_lon'],df1['y_lat'],c='green',s=S_point,label='Real containers') #real
ax.scatter(df2['x_lon'][df2['Town'].isin(agreed_cities)],df2['y_lat'][df2['Town'].isin(agreed_cities)],c='red',s=S_point,label='Both') #both
plt.legend()
plt.show()

##% Bifurcation analysis (alpha): Substractive clustering (GPS-based)
# LOAD: distances data
import math
import numpy as np
import pandas as pd
import pickle
# distances_all.pickle: all distances between towns [in m], filled both triangular matrices
distances=pickle.load(open("distances_all.pickle", 'rb'))
# df_waste.csv: textilte waste per inhabitant
df_waste = pd.read_csv('df_waste.csv')
# df_cities.csv: before manual correction; df_cities1.csv: after manual correction in node_id-s
df_cities = pd.read_csv('df_cities1.csv')


data=pd.concat([df_cities[['Town','Inhabitants']], distances], axis=1)

# applying the algorithm6
from subtractive_clustering_gps_capacity_init import subtractive_clustering_algorithm

center_init = pd.DataFrame([],columns=['pcs_loc']) #if it is empty, # "RAW"
# center_init = df1[['Town','pcs_loc']] # "PLUS"
# ra=222.71 #mean: 12400 m/person/day; ORIGINAL
df_bifurcation=pd.DataFrame()
for alpha_mean in np.arange(5000,15000,100):
    print(alpha_mean)
    # alpha_mean=12400
    ra=math.sqrt(alpha_mean)*2
    centers, newdata, init_potential = subtractive_clustering_algorithm(ra,ra,data, center_init, "center number", N_center=1000) #Eup=0.5, Edown=0.15, TNcenter: there are 2453 cont. at the moment
    # centers, newdata, init_potential = subtractive_clustering_algorithm(ra,ra,data,"absolute potential", N_center=503) #Eup=0.5, Edown=0.15
    df_bifurcation[str(alpha_mean)]=centers[:,0]

# SAVE
# with open("bifurcation_town1000_alfa5000_15000.pickle", 'wb') as f:
#     pickle.dump(df_bifurcation, f)

# df_bifurcation.stack().unique()

##% FIGURE: Pixel plot (CIKK: fig9.eps)

#Loading data
import pickle
df_bifurcation = pickle.load(open('bifurcation_town1000_alfa5000_20000.pickle', 'rb'))

#Data transformation (counting each cities and collecting in a matrix)
df_pixel = pd.DataFrame(df_bifurcation.stack().unique(),columns=['Municipality'])
for j in df_bifurcation.columns:
    df_pixel[str(j)] = 0
    for i in range(len(df_pixel)):
        df_pixel[str(j)].iloc[i] = (df_bifurcation[str(j)]==df_pixel['Municipality'].iloc[i]).sum()

# Creating a plot
import numpy as np
import matplotlib.pyplot as plt
data = df_pixel.drop('Municipality', axis=1).to_numpy() #np.random.random((50, 10))

fig,ax = plt.subplots(1,1)
pixel_plot = ax.imshow(data, cmap='Reds',vmin=0, interpolation='nearest') #vmax=100

fig.colorbar(pixel_plot,label='Containers')
ax.set_xticks(range(df_pixel.shape[1]-1))
ax.tick_params(axis='x', labelrotation=90, labelsize=8)
ax.set_xticklabels(df_pixel.columns[1:].astype(int)/1000) #to km
ax.set_yticks(range(df_pixel.shape[0]))
ax.set_yticklabels(df_pixel['Municipality'])
ax.tick_params(axis='y', labelsize=8)
plt.xlabel('Average mobility [km/person/day]')
plt.ylabel('Municipalities')
plt.show()
##% Creating textile tons/inhabitants by regions
import pandas as pd

percent_textile = 3.5 # INFO %
df_inhab = pd.read_excel('HKK_nodes (2).xlsx', sheet_name='nodes',
                   usecols=['County','Town','Inhabitants']) #inhabitants
df_inhab.dropna(axis=0, how='all', inplace=True)
df_inhab=df_inhab[df_inhab['County']!='AAA']

df_waste=pd.read_excel('KSHról.xlsx', sheet_name='Munka2',
                   usecols=['County_ID','y_2019']) #in tones

df_waste["Inhabitants"] = 0
df_waste["MSW per person"] = 0
df_waste["Textile per person"] = 0
for i in df_waste['County_ID']:
    df_waste["Inhabitants"][df_waste['County_ID']==i]=df_inhab[df_inhab['County'] == i]['Inhabitants'].sum()

df_waste["MSW per person"] = df_waste["y_2019"]/df_waste["Inhabitants"] # in tones
df_waste["Textile per person"] = df_waste["MSW per person"] * percent_textile/100 # in tones

df_waste.to_csv('df_waste.csv',index=False)

##% Utility code: Cutting and edge for two parts (for correcting edge assignment) --> that would be OK only if the point would be exactly at the edge, but it is not there
nodes_for_change=[6800072176]
g=road_nw

for i in nodes_for_change:
    c=i
    nearest_edge_id=ox.distance.nearest_edges(road_nw, df_cities['x_lon'][df_cities['node_id']==6800072176], df_cities['y_lat'][df_cities['node_id']==6800072176], return_dist=False)[0]
    f, t = ox.distance.nearest_edges(road_nw, df_cities['x_lon'][df_cities['node_id'] == 6800072176],
                                       df_cities['y_lat'][df_cities['node_id'] == 6800072176], return_dist=False)[0][0:2]

    edge_attrs = g[f][t]  # Copy edge attributes
    g.remove_edge(f, t)  # Remove edge from graph
    g.add_node(c, y=df_cities['y_lat'][df_cities['node_id'] == 6800072176], x=df_cities['x_lon'][df_cities['node_id']== 6800072176], street_count=2)

    # Add new edges, recalculating atttributes as required
    g.add_edge(f, c, **{**edge_attrs, 'length': d(f, c)})
    g.add_edge(c, t, **{**edge_attrs, 'length': d(c, t)})

##% Utility code: Map for checking node assignment (for identifying nodes should be manually corrected): cities and roads
import webbrowser
import osmnx as ox

filename="map_8"
G=road_nw #road_nw
nodes, edges=ox.graph_to_gdfs(road_nw)

m=ox.graph_to_gdfs(G, nodes=False).explore(tiles='OpenStreetMap',zoom=12,name="Roads") #center, zoom, edge_color, edge_width,node_size,bgcolor
m=nodes.explore(m=m,color="green",name="Nodes of road network") #all nodes

#Nodes for change?
m=nodes.loc[[410474803]].explore(m=m,color="orange",name="NOT connected",size=10000)
m=nodes.loc[[5323689251]].explore(m=m,color="orange",name="NOT connected",size=10000)

m.save(filename+".html")
webbrowser.open(filename+".html")