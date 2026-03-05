##%
import numpy as np
from sklearn.metrics import pairwise_distances

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

#K-medoids method with weights
def weighted_kmedoids(X, D, weights, n_clusters, max_iter=100):
    n = X.shape[0]

    # kezdeti medoidok
    medoids = np.random.choice(n, n_clusters, replace=False)

    for iii in range(max_iter):
        # hozzárendelés
        # 1) minden pont a legközelebbi medoidhoz
        labels = np.argmin(D[:, medoids], axis=1)
        # 2) biztosítjuk, hogy a medoid pontok a saját klaszterükben legyenek
        labels[medoids] = np.arange(len(medoids))

        new_medoids = []
        for k in range(n_clusters):
            cluster_idx = np.where(labels == k)[0]

            if len(cluster_idx) == 0:
                continue

            # súlyozott költség számítása
            costs = []
            for i in cluster_idx:
                cost = np.sum(weights[cluster_idx] * D[i, cluster_idx])
                costs.append(cost)

            new_medoids.append(cluster_idx[np.argmin(costs)])

        new_medoids = np.array(new_medoids)

        if np.all(medoids == new_medoids):
            break

        medoids = new_medoids

    return medoids, labels, iii


##% K-medoid

# LOAD: distances data
import pandas as pd
import pickle
import numpy as np

# distances_all.pickle: all distances between towns [in m], filled both triangular matrices
distances=pickle.load(open("distances_all.pickle", 'rb'))
distances_matrix = np.array(distances.iloc[:, 0].tolist())
# df_cities.csv: before manual correction; df_cities1.csv: after manual correction in node_id-s
df_cities = pd.read_csv('df_cities1.csv')

X = df_cities[['Town']]
D = distances_matrix
N = df_cities['Inhabitants']
n_clusters = 2453

tic()
medoids, labels, iii = weighted_kmedoids(X, D, N, n_clusters)
toc()

# SAVE
# with open("centers_Kmedoid_inhab_2453_raw.pickle", 'wb') as f:
#     pickle.dump(np.array(X.loc[medoids]), f)

##% MILP
import matplotlib
matplotlib.use("TkAgg")  # külső ablakos, interaktív backend
import matplotlib.pyplot as plt
plt.ion()

# To make the computation faster, city is only allowed to be assigned to containers in the max_km km neighborhood
# y_j: how many containers in city j
# x_ij: how many demand (inhabitants) of municipality i is satisfied by municipality j
from ortools.linear_solver import pywraplp
import numpy as np

def solve_container_split_30km(N, D, C, N_cont, max_km=30.0, solver_name="SCIP"):
    """
    Split (flow) MILP:
      - N[i] demand (population)
      - D[i,j] distance in km
      - C capacity per container
      - N_cont total containers
      - Only allow assignments i->j if D[i,j] <= max_km
    Returns: (status, y_sol, x_sol_sparse, objective_value)

    x_sol_sparse is dict {(i,j): value} for allowed arcs only.
    """
    N = np.asarray(N, dtype=float)
    D = np.asarray(D, dtype=float)
    n = N.shape[0]
    assert D.shape == (n, n)

    solver = pywraplp.Solver.CreateSolver(solver_name)
    solver.SetTimeLimit(60000*7) #INFO time limit
    solver.EnableOutput()

    if solver is None:
        raise RuntimeError(f"Could not create solver '{solver_name}'. Try 'SCIP' if available.")

    INF = solver.infinity()

    # --- Build allowed arcs A: for each i list of j where D[i,j] <= max_km ---
    allowed_js = []
    for i in range(n):
        js = np.where(D[i, :] <= max_km)[0].tolist()

        # Safety: ensure at least one allowed j for each i (otherwise infeasible)
        if len(js) == 0:
            j_star = int(np.argmin(D[i, :]))
            js = [j_star]

        allowed_js.append(js)

    # Also useful: incoming lists for capacity constraints
    incoming_is = [[] for _ in range(n)]
    for i in range(n):
        for j in allowed_js[i]:
            incoming_is[j].append(i)

    # --- Variables ---
    # y_j: integer number of containers at town j
    y = [solver.IntVar(0, N_cont, f"y_{j}") for j in range(n)]

    # x_ij: flow (people) from i assigned to j, only for allowed arcs
    x = {}
    for i in range(n):
        for j in allowed_js[i]:
            x[(i, j)] = solver.NumVar(0.0, INF, f"x_{i}_{j}")

    # --- Constraints ---
    # (1) Demand satisfaction: sum_j x_ij = N_i
    for i in range(n):
        solver.Add(sum(x[(i, j)] for j in allowed_js[i]) == float(N[i]))

    # (2) Capacity at each j: sum_i x_ij <= C * y_j (only incoming arcs)
    for j in range(n):
        if incoming_is[j]:
            solver.Add(sum(x[(i, j)] for i in incoming_is[j]) <= float(C) * y[j])
        else:
            # No one can be assigned to j (no incoming arcs) -> force y_j = 0 to avoid wasting containers
            solver.Add(y[j] == 0)

    # (3) Total number of containers
    solver.Add(sum(y[j] for j in range(n)) == int(N_cont))

    # --- Objective ---
    obj = solver.Objective()
    for (i, j), var in x.items():
        obj.SetCoefficient(var, float(D[i, j]))
    obj.SetMinimization()

    status = solver.Solve()

    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return status, None, None, None

    # --- Extract solution ---
    y_sol = np.array([y[j].solution_value() for j in range(n)])
    x_sol = {(i, j): var.solution_value() for (i, j), var in x.items() if var.solution_value() > 1e-9}
    obj_val = solver.Objective().Value()

    return status, y_sol, x_sol, obj_val

# LOAD: distances data
import pandas as pd
import pickle
import numpy as np

# distances_all.pickle: all distances between towns [in m], filled both triangular matrices
distances=pickle.load(open("distances_all.pickle", 'rb'))
distances_matrix = np.array(distances.iloc[:, 0].tolist())
# df_cities.csv: before manual correction; df_cities1.csv: after manual correction in node_id-s
df_cities = pd.read_csv('df_cities1.csv')

D = distances_matrix
N = df_cities['Inhabitants']
N_cont = 2453
C = df_cities['Inhabitants'].sum()/N_cont
max_km = 1000*30 #in meter!

status, y_sol, x_sol, obj_val = solve_container_split_30km(N, D, C, N_cont, max_km=max_km, solver_name="SCIP")

# SAVE
# with open("centersandcounts_MILP_inhab_2453_raw_7min.pickle", 'wb') as f:
#     pickle.dump(pd.concat([df_cities['Town'],pd.Series(y_sol,name='Cont_counts')],axis=1), f)
##% TEST: Wasserstein-distance of two container location lists (without orders, but locations are considered)
from scipy.stats import wasserstein_distance_nd
df_cities = pd.read_csv('df_cities1.csv')

# # METHOD: K-medoid
# # centers = np.array(X.loc[medoids]) #INFO
# centers = pickle.load(open("centers_Kmedoid_inhab_2453_raw.pickle", 'rb'))[:,0] #LOAD [:,0] kell???
# centers_new = np.unique(centers, return_counts=True)
# df_bb = pd.DataFrame({'Town':centers_new[0],'pcs_loc':centers_new[1]})

# METHOD: MILP
df_allcont_withpcs = pickle.load(open("centersandcounts_MILP_inhab_2453_raw_7min.pickle", 'rb')) #"centersandcounts_MILP_inhab_2453_raw_7min.pickle" "centersandcounts_MILP_inhab_2453_raw.pickle"
df_allcont_withpcs = df_allcont_withpcs[df_allcont_withpcs!=0].dropna()
df_bb =  df_allcont_withpcs.rename(columns={"Cont_counts": "pcs_loc"})

from func_container_optimization import give_GPS
df_bb=give_GPS(df_cities,df_bb)
# list_b = pickle.load(open("centers_flexcap_inhab_2453_raw.pickle", 'rb'))[:,0] #INFO
# df_bb=pd.DataFrame({'Town':np.unique(list_b),'pcs_loc':np.unique(list_b, return_counts=True)[1]}) #for faster Wasserstein


WD_pop_contreal = wasserstein_distance_nd(np.array(df2[['y_lat','x_lon']]),np.array(df_bb[['y_lat','x_lon']]),df2['Inhabitants']/df2['Inhabitants'].sum(),df_bb['pcs_loc']/df_bb['pcs_loc'].sum())


##% ##% TEST: How much the 503 current container location [df1] equals to the first 503 predicted [centers]?
import matplotlib
matplotlib.use("TkAgg")  # külső ablakos, interaktív backend
import matplotlib.pyplot as plt
plt.ion()

import pickle
import numpy as np
import pandas as pd
import osmnx as ox
from matplotlib.colors import ListedColormap

# # METHOD: SC OR K-medoid
# centers = pickle.load(open("centers_Kmedoid_inhab_2453_raw.pickle", 'rb'))[:,0] #fig5: "centers_flexcap_inhab_2453_raw.pickle"; fig6: "centers_cap_inhab_2453_raw.pickle", Kmedoid: "centers_Kmedoid_inhab_2453_raw.pickle", MILP: "centersandcounts_MILP_inhab_2453_raw.pickle"
#
# # METHOD: K-medoid
# # centers = np.array(X.loc[medoids]) #INFO
# centers_new = np.unique(centers, return_counts=True)
# df_new = pd.DataFrame({'Town':centers_new[0],'pcs_loc':centers_new[1]})
# # df_allcont_withpcs = pd.concat([df1[['Town','pcs_loc']],df_new]).groupby(['Town'],as_index=False).sum() #with PLUS
# df_allcont_withpcs = pd.concat([df_new]).groupby(['Town'],as_index=False).sum() # with RAW or PLUS (if only the news are wanted)

#METHOD: MILP
df_allcont_withpcs = pickle.load(open("centersandcounts_MILP_inhab_2453_raw.pickle", 'rb'))
df_allcont_withpcs = df_allcont_withpcs[df_allcont_withpcs!=0].dropna()
df_allcont_withpcs = df_allcont_withpcs.rename(columns={"Cont_counts": "pcs_loc"})
centers = df_allcont_withpcs['Town'].to_numpy().reshape(-1, 1)

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
    df1.loc[df1['Town']==i,"y_lat"]=df2[df2['Town']==i]["y_lat"].iloc[0]
    df1.loc[df1['Town'] == i,"x_lon"] = df2[df2['Town'] == i]["x_lon"].iloc[0]
    df1.loc[df1['Town'] == i,"Inhabitants"] = df2[df2['Town'] == i]["Inhabitants"].iloc[0]



#N_center=503 if only the places are considered without capacity; N_centers=2453 with capacity
agrees=(df1['Town'].isin(centers[:,0]))
print(agrees.sum())
print(str(agrees.sum()) + ' municipalities appears in both lists.')
agreed_cities=df1['Town'][df1['Town'].isin(centers[:,0])]


#if capacity is considered:
np.unique(centers[:,0]).shape #number of container municipalities
print(str(int(np.unique(centers[:,0]).shape[0])) + ' municipalities appears in the optimal container system.')

S_point=10

##% FIGURE
road_nw=pickle.load(open('filename3.pickle', 'rb'))
fig, ax = ox.plot_graph(road_nw,node_size=0, edge_linewidth=0.2, bgcolor='white',show=True, close=False) #plot here
ax.scatter(df2['x_lon'][df2['Town'].isin(centers[:,0])],df2['y_lat'][df2['Town'].isin(centers[:,0])],c='blue',s=S_point,label='Predicted containers') #predicted
ax.scatter(df1['x_lon'],df1['y_lat'],c='green',s=S_point,label='Real containers') #real
ax.scatter(df2['x_lon'][df2['Town'].isin(agreed_cities)],df2['y_lat'][df2['Town'].isin(agreed_cities)],c='red',s=S_point,label='Both') #both
plt.legend()
plt.show(block=True)




##%FIGURE:  Difference density map of the final containers (CIKK:fig5.eps/png,fig6.eps/png; eps: color=gainsboro, 0.05 linewidth)
df2_new=df2
df2_new["pcs_loc1"] = 0 #real
df2_new["pcs_loc2"] = 0 #predicted
df2_new["pcs_loc_diff"] = 0
for i in df2_new['Town']:
    if (df1['Town']==i).sum()>0:
        df2_new.loc[df2_new['Town']==i,"pcs_loc1"]=df1[df1['Town']==i]["pcs_loc"].iloc[0]
    if (df_allcont_withpcs['Town']==i).sum()>0:
        df2_new.loc[df2_new['Town']==i,"pcs_loc2"]=df_allcont_withpcs[df_allcont_withpcs['Town']==i]["pcs_loc"].iloc[0] #df_allcont_withpcs contains the df_new...
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
plt.show(block=True)

####%  MILP

from ortools.linear_solver import pywraplp
import numpy as np

def solve_container_problem(N_i, d_ij, C, N_cont):
    n = len(N_i)

    solver = pywraplp.Solver.CreateSolver("CBC")  # vagy "SCIP"

    # ----- Változók -----

    # x_ij >= 0 (flow)
    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = solver.NumVar(0, solver.infinity(), f"x_{i}_{j}")

    # y_j integer >= 0
    y = {}
    for j in range(n):
        y[j] = solver.IntVar(0, N_cont, f"y_{j}")

    # ----- Korlátok -----

    # 1) Demand kielégítése
    for i in range(n):
        solver.Add(
            sum(x[i, j] for j in range(n)) == N_i[i]
        )

    # 2) Kapacitás
    for j in range(n):
        solver.Add(
            sum(x[i, j] for i in range(n)) <= C * y[j]
        )

    # 3) Összes konténer száma
    solver.Add(
        sum(y[j] for j in range(n)) == N_cont
    )

    # ----- Célfüggvény -----

    objective = solver.Objective()
    for i in range(n):
        for j in range(n):
            objective.SetCoefficient(x[i, j], d_ij[i, j])

    objective.SetMinimization()

    # ----- Megoldás -----

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("Optimális megoldás.")
    else:
        print("Nem optimális vagy nem megoldható.")

    return solver, x, y

# 1️⃣ Csak közeli települések között engedj kapcsolatot
#
# Pl. max 30 km:

if d_ij[i, j] <= 30:
    x[i,j] = solver.NumVar(...)