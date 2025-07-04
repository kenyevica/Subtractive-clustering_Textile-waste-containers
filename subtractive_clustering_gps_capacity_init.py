import pandas as pd
import numpy as np


# helper functions
def potential_values(ra, k, sample_data):
    """
    ra = parameter (RADII parameter)
    k = index of row to find potential of in the data

    returns: the potential for that given row given no previous potential known

    """

    val_list = np.array([])

    for l in range(0, len(sample_data)):
        diff = sample_data[k, -1][l]  # distance of the k-th town from the l-th
        value = sample_data[l, 1] * np.exp(-(diff) / (ra / 2) ** 2)  # weighting by inhabitants (sample_data[l,1])
        val_list = np.append(val_list, value)

    return val_list.sum()


def min_dist(array_to_check, list_of_centers):
    '''

    :param array_to_check: array you wish to have compared
    :param list_of_centers: list of accepted centers to measure against
    :return: minimum distance for array_to_check to any of the centers

    Note: Should only be used with the normalised data in this question as it may not scale well
    '''
    dist_old = 10000
    for b in range(0, len(list_of_centers)):
        dist = array_to_check - list_of_centers[b]
        dist = np.sqrt((dist ** 2).sum())
        if dist < dist_old:
            dist_old = dist
        else:
            pass
    return dist_old


def update_array_with_potentials(old_list, accepted_center, accepted_centers_potential, rb, index, original_index,*,container_capacity=float('inf')):
    """

    :param old_list: last array of data points with their centers
    :param accepted_center: the just accepted center
    :param accepted_centers_potential: potential of accepted center
    :param rb: parameter
    :param index: number of accepted centers before this one
    :param original_index: index of the accepted center municipality in the initial dataset (needed in the distance lists)

    :return: updated array of data points with their new potentials
    """

    P_cont = min(container_capacity,accepted_centers_potential)

    for c in range(index + 1,
                   len(old_list)):  # we keep the accepted centers at the beginning of the list with their potential when they were accepted
        diff = old_list[c][2][
            original_index]  # distance of the c-th town in the modified list from the accepted town (original_index)
        Pnew = old_list[c][-1] - P_cont * np.exp(-(diff) / (rb / 2) ** 2) # KE: container capacity
        old_list[c][-1] = Pnew
    old_list = np.append(old_list[:(index + 1), :],
                         old_list[(index + 1):, :][(-old_list[(index + 1):, :][:, -1]).argsort()], axis=0)

    return old_list

def update_array_with_potentials_capacity(old_list, accepted_center, accepted_centers_potential, rb,original_index,*,container_capacity=float('inf')):
    """

    :param old_list: last array of data points with their centers
    :param accepted_center: the just accepted center
    :param accepted_centers_potential: potential of accepted center
    :param rb: parameter
    :param index: number of accepted centers before this one
    :param original_index: index of the accepted center municipality in the initial dataset (needed in the distance lists)

    :return: updated array of data points with their new potentials
    """

    P_cont = min(container_capacity,accepted_centers_potential)

    for c in range(0,
                   len(old_list)):  # we keep the accepted centers at the beginning of the list with their potential when they were accepted
        diff = old_list[c][2][
            original_index]  # distance of the c-th town in the modified list from the accepted town (original_index)
        Pnew = old_list[c][-1] - P_cont * np.exp(-(diff) / (rb / 2) ** 2) # KE: container capacity
        old_list[c][-1] = Pnew
    old_list = old_list[0:, :][(-old_list[0:, :][:, -1]).argsort()]

    return old_list


def step_6(E_up, E_down, ra, list_of_centers, sorted_data_with_potential2, sample_data, index, P1, rb, stopping_method,
           N_center, P_threshold, container_capacity):
    """
    :param Eup: Parameter (in case of "relative potential")
    :param Edown: Parameter (in case of "relative potential")
    :param ra: Parameter
    :param list_of_centers: List of all accepted centers in array form
    :param sorted_data_with_potential2: all the points with their current potential
    :param index: number of accepted centers before this one
    :param P1: Potential of very first center that was accepted
    :param rb: Parameter
    :param stopping_method: Switch
    :param P_threshold: Parameter
    :param N_center: Parameter
    :return: updated list of centers, the data with it's updated potential, the new index value
    """


    match stopping_method:
        case "relative potential":
            Pk = sorted_data_with_potential2[index][-1]
            # print(sorted_data_with_potential2[index][0])  # KE:CHECK
            X = sorted_data_with_potential2[index][0:-1]  # point we are considering
            original_id = np.where(sample_data[:, 0] == sorted_data_with_potential2[index, 0])[0][0]

            if Pk / P1 > E_up:
                # accept it and look for more
                list_of_centers.append(X)  # add it to list of centers
                sorted_data_with_potential2 = update_array_with_potentials(sorted_data_with_potential2, X, Pk, rb,
                                                                           index, original_id)
                index = index + 1  # update sorted data with potential
                original_id = np.where(sample_data[:, 0] == sorted_data_with_potential2[index, 0])[0][0]
                return list_of_centers, sorted_data_with_potential2, index

            elif Pk / P1 < E_down:
                # reject it and stop
                index = "stop"  # will use this index to stop the algorithm
                return list_of_centers, sorted_data_with_potential2, index

            else:
                # more ambiguous case
                dmin = min_dist(X, list_of_centers)
                value = dmin / ra + Pk / P1
                if value >= 1:
                    list_of_centers.append(X)
                    sorted_data_with_potential2 = update_array_with_potentials(sorted_data_with_potential2, X, Pk, rb,
                                                                               index, original_id,stopping_method)
                    index = index + 1
                    original_id = np.where(sample_data[:, 0] == sorted_data_with_potential2[index, 0])[0][0]
                    return list_of_centers, sorted_data_with_potential2, index
                    # accept X and move to next point for next center
                else:
                    index = index + 1
                    return list_of_centers, sorted_data_with_potential2, index
                    # reject X, set its potential to zero, and look for next center
        case "absolute potential":
            Pk = sorted_data_with_potential2[index][-1]
            # print(sorted_data_with_potential2[index][0])  # KE:CHECK
            X = sorted_data_with_potential2[index][0:-1]  # point we are considering
            original_id = np.where(sample_data[:, 0] == sorted_data_with_potential2[index, 0])[0][0]

            if Pk > P_threshold:
                # accept it and look for more
                list_of_centers.append(X)  # add it to list of centers
                sorted_data_with_potential2 = update_array_with_potentials(sorted_data_with_potential2, X, Pk, rb,
                                                                           index,
                                                                           original_id)
                index = index + 1  # update sorted data with potential
                original_id = np.where(sample_data[:, 0] == sorted_data_with_potential2[index, 0])[0][0]
                return list_of_centers, sorted_data_with_potential2, index
            else:
                index = "stop"
                return list_of_centers, sorted_data_with_potential2, index
        case "center number":
            Pk = sorted_data_with_potential2[0][-1]
            # print(sorted_data_with_potential2[0][0])  # KE:CHECK
            X = sorted_data_with_potential2[0][0:-1]  # point we are considering
            original_id = np.where(sample_data[:, 0] == sorted_data_with_potential2[0, 0])[0][0]

            if index <= N_center - 1:
                # accept it and look for more
                list_of_centers.append(X)  # add it to list of centers
                sorted_data_with_potential2 = update_array_with_potentials_capacity(sorted_data_with_potential2, X, Pk, rb,
                                                                           original_id,container_capacity=container_capacity)
                index = index + 1  # update sorted data with potential
                # original_id = np.where(sample_data[:, 0] == sorted_data_with_potential2[0, 0])[0][0]
                return list_of_centers, sorted_data_with_potential2, index
            else:
                index = "stop"
                return list_of_centers, sorted_data_with_potential2, index

def reduce_initial_containers(data_with_potential,center_init,rb,container_capacity="inf"):
    # data_with_potential: before sorted! --> original index can be determined from it

    data_with_potential_init=data_with_potential #store original data
    for i in range(len(center_init)):
        accepted_centers_potential = data_with_potential_init[data_with_potential_init[:, 0] == center_init['Town'][i],-1]
        P_cont = min(container_capacity * center_init['pcs_loc'][i], accepted_centers_potential[0])
        original_index = np.where(data_with_potential[:,0]==center_init['Town'][i]) #in the index list the original (before sorted) index should be used

        for c in range(0,len(data_with_potential)):
            diff = data_with_potential[c][2][original_index[0][0]]  # distance of the c-th town in the modified list from the accepted town (original_index)
            Pnew = data_with_potential[c][-1] - P_cont * np.exp(-(diff) / (rb / 2) ** 2)  # KE: container capacity
            data_with_potential[c][-1] = Pnew

    return data_with_potential #not sorted!

# main logic
# def subtractive_clustering_algorithm(ra, rb, E_up, E_down, data):
def subtractive_clustering_algorithm(ra, rb, data, center_init, stopping_method, *, E_up=0.01, E_down=0.01, N_center=10,
                                     P_threshold=11500):
    """
    An implementation of the subtractive clustering algorithm.

    Further detail on the algorithm and how it works can be found in the following paper:
    "Support vector machines based on subtractive clustering"
    http://ieeexplore.ieee.org/abstract/document/1527702/


    :param ra: 0 < r ≤ 1 is the clustering RADII parameter, which defines the neighborhood radius of each point. The
    data outside the radius of xi have little influence on its potential. So the point having more data within the
    radius will get higher potential.

    :param rb: rb > 0 defines the neighborhood of a cluster center with which the existence of other cluster centers
    are discouraged. The points close to the selected cluster center will have significant reduction in their potential
    after computation. When Pi ≤ 0 , the point xi is rejected for the cluster center forever. In this way, some closer
    samples are replaced by their center. To avoid closely space centers, usually, rb = 1.5ra.

    :param E_up: ε_up is the accept ratio above which another data point will be accepted as a cluster center with no doubts (in case of "relative potential").

    :param E_down: ε_down is the reject ratio below which another data point will be definitely rejected (in case of "relative potential").

    :param data: data points input as a pandas DataFrame.

    :param center_init: initially existing centers (town and pcs/loc)

    :param stopping_method: either "relative potential", "absolute potential" or "center number".
            "center number": defines the desired number of clusters as a stopping criterion.
            "absolute potential": has one threshold defining the maximal acceptable remaining potential value.
            "relative potential": two threshold, above Eup center is accepted, below Edown run terminates, between the two
                                there is another condition related to potential value AND distance from other centers belonging
                                to the new center.

    :param P_threshold: the maximal acceptable remaining potential value (in case of "absolute potential")

    :param N_center: desired number of ALL clusters (in case of "center number")

    :return: list_of_centers: List containing the coordinates of all centers that were found

    :return: data: The data with a label indicating which center it belongs to

    NOTE: container capacity is only considered for "center number" method.
    """

    sample_data = pd.DataFrame(data)

    all_inhabitant = data['Inhabitants'].sum()  # for container capacity
    # cont_capacity = all_inhabitant / N_center, "FLEXCAP"
    cont_capacity = 1500 #if #INHAB; 1500 person/container, "CAP"

    # step 2: compute the potential value for each xi
    sample_data = np.array(sample_data)

    potential = np.array([])
    for k in range(0, len(sample_data)):
        potential = np.append(potential, potential_values(ra, k, sample_data))

    data_with_potential = np.c_[sample_data, np.array([potential]).transpose()]
    if stopping_method=="center number":
        data_with_potential = reduce_initial_containers(data_with_potential,center_init,rb, container_capacity=cont_capacity) #KE:NEW init. containers
    else:
        data_with_potential = reduce_initial_containers(data_with_potential,rb, center_init)
    data_with_potential_initial = data_with_potential

    #KEINNEN: correcting the potentials with the initial centers (fentről?); pcs_loc-kal meg kell szorozni!
    # üresen is működjön!

    # KEINNEN: argsort most reálisnak tűnik..
    # step 3: select point with highest potential as first center
    list_of_centers = [] #KEINNEN: kiszedni a listát (ua. legyen mint a későbbi data-alapú)
    sorted_data_with_potential = data_with_potential[(-data_with_potential[:, -1]).argsort()]
    list_of_centers.append(sorted_data_with_potential[0][0:data.shape[1]])


    if stopping_method == "center number": #for container capacity
        P1_cont = min(cont_capacity,sorted_data_with_potential[0][-1])
    else:
        P1_cont = sorted_data_with_potential[0][-1]  # and its associated potential; original, without contianer capacity
    # print(P1_cont)

    # step 4: reduce the potential values of remaining data points
    x1_star = sorted_data_with_potential[0][0:data.shape[1]]
    x1_star_id = np.where(sample_data[:, 0] == sorted_data_with_potential[0, 0])[0][0]

    for m in range(1, len(sorted_data_with_potential)):
        vector = sorted_data_with_potential[m, 2][x1_star_id]  # distance between m-th and x1_star ([0])
        # Remark: in the distance lists they will be at the original (alphabetical) order like in sample_data
        vector1 = np.exp(-(vector) / (rb / 2) ** 2)
        sorted_data_with_potential[m][-1] = sorted_data_with_potential[m][
                                                -1] - P1_cont * vector1  # reduce the m-th potential by x1_star's considering distance
        # KE: container capacity
    #

    # step 5: select the highest potential from the reduced potential
    sorted_data_with_potential2 = sorted_data_with_potential[(-sorted_data_with_potential[:, -1]).argsort()]

    # Pk = sorted_data_with_potential2[1][-1]  # and its potential
    # step 6: determine next cluster center
    # step 7: Compute the potential for the remaining points
    if stopping_method == "center number":
        P1_cont = min(cont_capacity,sorted_data_with_potential2[0][-1])
    else:
        P1_cont = sorted_data_with_potential2[0][-1]  # and its associated potential; original, without container capacity
    # print(P1_cont)

    id = 1 #its only a counter of extra containers
    updated_centers, new_data, index = step_6(E_up, E_down, ra, list_of_centers, sorted_data_with_potential2,
                                              sample_data, id, P1_cont, rb, stopping_method, N_center - center_init['pcs_loc'].sum(),
                                              P_threshold, cont_capacity)

    while index != 'stop':
        if stopping_method == "center number":
            P1_cont = min(cont_capacity, new_data[0][-1])
        else:
            P1_cont = new_data[0][-1]  # and its associated potential; original, without contianer capacity
        # print(P1_cont)

        updated_centers, new_data, index = step_6(E_up, E_down, ra, updated_centers, new_data, sample_data, index, P1_cont,
                                                  rb, stopping_method, N_center - center_init['pcs_loc'].sum(), P_threshold, cont_capacity)

    updated_centers = np.array(updated_centers)

    return updated_centers, new_data, data_with_potential_initial
    # Output:
    # -updated_centers: only with municipality name, inhabitants, distances from others
    # -new_data: municipality name, inhabitants, distances from others, END POTENTIAL  (when they were accepted in case of accepted ones)
    # -data_with_potential_initial: ALPHABETICAL municipality name, inhabitants, distances from others, INITIAL POTENTIALS, reduced by the initial containers in this case
