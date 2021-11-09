################################################################################################
## Approach for assisting developers in deciding about intiating performance testing. 
## Information about how the algorithm works can be found in TODO: Reference to article
##  Returns a json object, TODO: We can use it in our CI analytics tools
################################################################################################
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from bisect import *
from scipy.stats import linregress
## Number of random datapoints to select
SIZE_OF_DATA_POINTS=3

## Acceptable limit for slow-down. Value is a percentage decrease of time. This represents the acceptable limit provided the developer.
# Percentage which is represented as an integer.
PCT_SET_VALUE = 38

## Two analysis used for evaluating our approach:
# 1) perfcitestbug.csv  - This is a performance bug found in the test suite; More information on the bug can be found in our ASE paper https://ieeexplore.ieee.org/document/9286019
# 2) pylintanalysis.csv - We used pylint a static code checker to identify code issues. 
list_commit_analysis = ['perfcitestbug.csv','pylintanalysis.csv' ]



## Clustered data generated from CI analytics system. This file consists of our clustering analysis. 
df = pd.read_csv('dbscan_e9414f04.csv')
#bugcommit_df = pd.read_csv('perfcitestbug.csv')
#pylint_df = pd.read_csv('pylintanalysis.csv')

## Data selected based on random-sampling. In this analysis, we selected three data points.
selected_df = pd.read_csv('selectdatapoints.csv')


""" returns a negative value set by the developer"""
# def get_pct_set_value():
#     return int("-"+str(PCT_SET_VALUE))


"""Identify  number of clusters and get indivial cluster data as a list

    Returns:
        [DataFrame]: Data of each clusters
"""
def get_individual_cluster():
    no_clusters = df['Cluster'].unique()
    return [df.loc[df['Cluster'] == c] for c in no_clusters]


"""Get random data points from each cluster
       [DataFrame] : dataframe consisting of data points representing Conditions upload ID and program behavior
"""
def random_data_points():
    container_df = pd.DataFrame([])
    cluster_data = get_individual_cluster()
    for individual_cluster_data in cluster_data:
        data_points_df = individual_cluster_data.sample(n=SIZE_OF_DATA_POINTS)
        container_df = container_df.append(data_points_df)
    return container_df

""" Sort dataframe based on column value and convert the series from dataframe to list. 
    Arguments:
        Dataframe: dataframe to sort
        String:    column   name of the column to sort
        
        Returns:
                   Sorted dataframe
"""
def sort_dataframe_by_column(dataframe, column):
    sorted_by_column=dataframe.sort_values([column])
    return  sorted_by_column[column].tolist()


""" Makes a decision by first checking whether the updated datapoint is within the threshold or it requires a gradient check to make a final decision.

    Returns:
        Boolean: Returns a decision (T/F)
"""

def decide(current_datapoint,condition, cluster, index):
                
                agreed  = False
                #print (current_datapoint.iloc[0]['time'], condition)                      
                if current_datapoint.iloc[0]['time'] > condition:     
                    
                    agreed = True
                    #print ("Threshold: {}".format(agreed))
                    
                
                if not agreed:
                    prev_point_x_time=cluster.iloc[index]['time']
                    prev_point_y_stmt=cluster.iloc[index]['TExeStmt']
                    
                    prev_x = [0,prev_point_x_time]
                    prev_y = [0,prev_point_y_stmt]
                    
                    
                    prev_slope, _, _, _, _ = linregress(prev_x,prev_y)
                    
                    
                    curr_point_x_time=current_datapoint.iloc[0]['time']
                    curr_point_y_stmt=current_datapoint.iloc[0]['TExeStmt']
                    
                    
                    
                    curr_x = [0,curr_point_x_time]
                    curr_y = [0,curr_point_y_stmt]
                    
                    curr_slope, _, _, _, _ = linregress(curr_x,curr_y)
                    
                    pct_change = ((curr_slope - prev_slope) / prev_slope) * 100
                    
                    # To identify a slow-down, a negative gradient is achieved. We change the sign to make the condition of PCT_SET_VALUE easy to understand.
                    pct_change = -1 * pct_change

                    # If grandient is above the acceptable limit
                    if pct_change > PCT_SET_VALUE:
                        print ("PCT_CHANGE {}".format(pct_change))
                        agreed = True
                        #print ("Gradient: {}".format(agreed))
                return agreed
   


""" Makes a decision based on approximation about whether the change in executed statements gives a worst execution time
    Arguments:
        Dataframe:  cluster_data containing cluster data
        Dataframe:  datapoint_to_check_df consists of datapoints with the effect of code change 
    Returns:  
        Boolean:  True / False whether to run performance tests or not    
"""
def decision_to_perform_tests(cluster_data, datapoint_to_check_df):
    
    ## Considering all the decisions made by each input from the sample
    main_decision = []
    
    # Split dataframes based on data selected from each cluster
    start_index = 0
    end_index = SIZE_OF_DATA_POINTS
        
    for current_cluster in cluster_data:
        
        # Check whether we are on the same cluster or a new cluster
        is_new_cluster = True
        
        # Select updated data points for the current cluster
        datapoints_in_current_cluster = datapoint_to_check_df.iloc[start_index:end_index,:]
                
        for index,executed_statement in enumerate(datapoints_in_current_cluster['TExeStmt']):
            # Check if new executed statement matches executed statement in current cluster. We take the maximum time for that particular executed statement as a threshold and also calculate the gradient of time
            
            if executed_statement in current_cluster['TExeStmt']:
                # TODO: Find scenarios where this path will be executed. 
                previous_datapoint_current_cluster=current_cluster[current_cluster['TExeStmt'] == executed_statement]
                prev_time_datapoint = previous_datapoint_current_cluster.iloc[0]['time'].max()
                
                current_datapoint = datapoints_in_current_cluster[datapoints_in_current_cluster['TExeStmt'] == executed_statement]
                
                decision = decide(current_datapoint, prev_time_datapoint, current_cluster, index)
                
                
            # Executed statments are  not in the current cluster
            else:

                # Case: Executed statements does not match; we need to find the data points (i.e., executed statements) above and below the new executed statement. 
                # We try to find their respective execution time
                
                # Dont need to unneccessarily  create datastructure and run sorting operations. 
                if is_new_cluster:
                    
                    # Identify all previous executed statements in a given cluster
                    list_statements = sort_dataframe_by_column(current_cluster, 'TExeStmt')
                 
                    is_new_cluster = False
                
                # Get lower and point above based on the given point in the cluster  
                lower_data_point_stmt = list_statements[bisect_left(list_statements, executed_statement) - 1]
                above_data_point_stmt = list_statements[bisect_right(list_statements, executed_statement)]
                
                # Outlier case above the cluster: If above point does not exits, it means that the new executed statement is an outlier.
                if not above_data_point_stmt:
                    # Executed statement which will be at the top of the cluster
                    top_data_point_stmt=list_statements[len(list_statements)-1]
                    
                    top_data_point_in_cluster=current_cluster[current_cluster['TExeStmt'] == top_data_point_stmt]
                    
                    # Get the max time for the top most data point in the cluster
                    max_time_cluster=top_data_point_in_cluster['time'].max()
                    
                    current_datapoint = datapoints_in_current_cluster[datapoints_in_current_cluster['TExeStmt'] == executed_statement]
                    
                    # Make a decision
                    decision=decide(current_datapoint, max_time_cluster, current_cluster, index)
                    
                    # Add it to the list of decision
                    main_decision.append(decision)  
                    
                    # No need to further process
                    break
                    
                    
                lower_data_point = current_cluster[current_cluster['TExeStmt'] == lower_data_point_stmt]
                above_data_point = current_cluster[current_cluster['TExeStmt'] == above_data_point_stmt]
                
                #There is a change we can get many same executed statements above or below. We select the last one which will have the highest time.
                # We calculate the midpoint of the line between two data points where time is on x-axis and executed statments is on y-axis
                x1_axis_datapoint = lower_data_point['time'].max()
                x2_axis_datapoint = above_data_point['time'].max()
                                
                mid_time_point = (x1_axis_datapoint + x2_axis_datapoint)/2

                ## Get time information from datapoint  
                current_datapoint = datapoints_in_current_cluster[datapoints_in_current_cluster['TExeStmt'] == executed_statement]
                
                decision = decide(current_datapoint, mid_time_point, current_cluster, index)
                
            main_decision.append(decision)   
            
        start_index=end_index
        end_index = end_index+SIZE_OF_DATA_POINTS    
        
    # Returns the list of decisions representing decision based on each input
    return main_decision



#decision_to_perform_tests(bugcommit_df)


if __name__ == '__main__':
    

    
    for commit_info in list_commit_analysis:
        
        # This consists of our two analysis 1) perfcitestbug and 2) pylintanalysis
        analysis_df = pd.read_csv(commit_info)
        
        # Analysis name
        analysis =  commit_info.split(".")[0].capitalize()
        
        
        # Getting list of cluster dataframes
        cluster_data = get_individual_cluster()
        
        # This is the list of decision (T/F) based on each input selected by random sampling
        decision_on_inputs = decision_to_perform_tests(cluster_data, analysis_df)
        
        decision_data = {analysis: decision_on_inputs}
        
        final_decision = json.dumps(decision_data)
        print (final_decision)
        
        