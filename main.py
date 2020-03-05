''' authors
Team name: cizos
Ashwani Kumar Kashyap, axk190033@utdallas.edu
Anshul Pardhi, anshul.pardhi@utdallas.edu
'''

# import required libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# import dataset
driver_ids = pd.read_csv('driver_ids.csv')
ride_timestamps = pd.read_csv('ride_timestamps.csv')
ride_ids = pd.read_csv('ride_ids.csv')

# constant vairables
BASEFARE = 2.00
COSTPERMILE = 1.15
COSTPERMIN = 0.22
SERVICEFEE = 1.75
MINFARE = 5.00
MAXFARE = 400.00

# calculate the totol ride cost
ride_ids['ride_total_cost'] = (1 + ride_ids['ride_prime_time']/100)*(BASEFARE+(COSTPERMILE*(ride_ids['ride_distance']*0.000621))+(COSTPERMIN*(ride_ids['ride_duration']/60)))+SERVICEFEE

# apply lower and upper bound to ride cost
ride_ids['ride_total_cost'] = np.where(ride_ids['ride_total_cost'] < 5, 5, ride_ids['ride_total_cost'])
ride_ids['ride_total_cost'] = np.where(ride_ids['ride_total_cost'] > 400, 400, ride_ids['ride_total_cost'])

# pivot the ride events and merge with ride_ids
ride_events = ride_timestamps.pivot(index = 'ride_id', columns = 'event', values = 'timestamp')



cumulative_ride_events = pd.merge(ride_ids, ride_events, on='ride_id')

# feature Scaling
cumulative_ride_events["ride_distance"] = cumulative_ride_events["ride_distance"]/1000;
cumulative_ride_events["ride_duration"] = cumulative_ride_events["ride_duration"]/60;

# calculate required basic features for ride
cumulative_ride_events['ride_accept_response_time'] = (pd.to_datetime(cumulative_ride_events['accepted_at']) - pd.to_datetime(cumulative_ride_events['requested_at'])).astype('timedelta64[s]')
cumulative_ride_events['ride_arrival_time'] = (pd.to_datetime(cumulative_ride_events['arrived_at']) - pd.to_datetime(cumulative_ride_events['accepted_at'])).astype('timedelta64[s]')
cumulative_ride_events['ride_wait_time'] = (pd.to_datetime(cumulative_ride_events['picked_up_at']) - pd.to_datetime(cumulative_ride_events['arrived_at'])).astype('timedelta64[s]')
cumulative_ride_events['ride_avg_speed'] = (cumulative_ride_events['ride_distance'])/(cumulative_ride_events['ride_duration']/60)
cumulative_ride_events["ride_length"] = np.where(cumulative_ride_events["ride_distance"] > 8, (np.where(cumulative_ride_events["ride_distance"] < 20, "med_ride", "long_ride")), "short_ride")
cumulative_ride_events["ride_time"] = np.where(pd.to_datetime(cumulative_ride_events['accepted_at']).dt.hour > 6, (np.where(pd.to_datetime(cumulative_ride_events['accepted_at']).dt.hour <= 15, "morning_ride", (np.where(pd.to_datetime(cumulative_ride_events['accepted_at']).dt.hour <= 21, "evening_ride", "night_ride")))), "night_ride")
cumulative_ride_events['ride_date'] = pd.to_datetime(cumulative_ride_events['accepted_at']).dt.date

# calculate driver_perday_ridecount
driver_perday_ridecount = cumulative_ride_events.pivot_table(index = 'driver_id', columns = 'ride_date', aggfunc='size').fillna(0)

driver_perday_ridecount = cumulative_ride_events.pivot_table(index = 'driver_id', columns = 'ride_date', aggfunc='size').fillna(0)

driver_info = pd.DataFrame()

# calculatre driver total ride count, distance, duration
driver_info['total_ride_count'] = cumulative_ride_events.pivot_table(index=['driver_id'], aggfunc='size')
driver_info['total_distance']  = ride_ids.groupby('driver_id')['ride_distance'].sum()
driver_info['total_duration']  = ride_ids.groupby('driver_id')['ride_duration'].sum()
driver_info['total_earnings'] = ride_ids.groupby('driver_id')['ride_total_cost'].sum()

# map variance, mean, median of rides per day for a driver
driver_info['perday_ridecount_var'] = driver_perday_ridecount.var(axis=1);
driver_info['perday_ridecount_mean'] = driver_perday_ridecount.mean(axis=1);

# map mean, var of other features with driver info
aggregation_functions = {'ride_accept_response_time': 'mean'}
driver_info['accept_response_time_mean'] = (cumulative_ride_events.groupby(cumulative_ride_events['driver_id']).aggregate(aggregation_functions)).iloc[:,0]
aggregation_functions = {'ride_accept_response_time': 'var'}
driver_info['accept_response_time_var'] = (cumulative_ride_events.groupby(cumulative_ride_events['driver_id']).aggregate(aggregation_functions)).iloc[:,0]

aggregation_functions = {'ride_arrival_time': 'mean'}
driver_info['arrival_time_mean'] = (cumulative_ride_events.groupby(cumulative_ride_events['driver_id']).aggregate(aggregation_functions)).iloc[:,0]
aggregation_functions = {'ride_arrival_time': 'var'}
driver_info['arrival_time_var'] = (cumulative_ride_events.groupby(cumulative_ride_events['driver_id']).aggregate(aggregation_functions)).iloc[:,0]

aggregation_functions = {'ride_wait_time': 'mean'}
driver_info['wait_time_mean'] = (cumulative_ride_events.groupby(cumulative_ride_events['driver_id']).aggregate(aggregation_functions)).iloc[:,0]
aggregation_functions = {'ride_arrival_time': 'var'}
driver_info['wait_time_var'] = (cumulative_ride_events.groupby(cumulative_ride_events['driver_id']).aggregate(aggregation_functions)).iloc[:,0]

aggregation_functions = {'ride_avg_speed': 'mean'}
driver_info['speed_mean'] = (cumulative_ride_events.groupby(cumulative_ride_events['driver_id']).aggregate(aggregation_functions)).iloc[:,0]
aggregation_functions = {'ride_arrival_time': 'var'}
driver_info['speed_var'] = (cumulative_ride_events.groupby(cumulative_ride_events['driver_id']).aggregate(aggregation_functions)).iloc[:,0]

# count total no. of short/medium/long evening rides
driver_info = pd.merge(driver_info, cumulative_ride_events.pivot_table(index = 'driver_id', columns = 'ride_length', aggfunc='size') ,on='driver_id')
# count total no. of day/night/night evening rides
driver_info = pd.merge(driver_info, cumulative_ride_events.pivot_table(index = 'driver_id', columns = 'ride_time', aggfunc='size') ,on='driver_id')

# fill nan value with 0
driver_info = driver_info.fillna(0)

# check for heat map for correlated features
sns.heatmap(driver_info.corr())

#driver_info = driver_info.drop(columns=['speed_mean', 'speed_var'])

# create required feature set
X = driver_info.iloc[:,:].values

# Using the elbow method to find the optimal number of clusters
from sklearn.cluster import KMeans
wcss = []
for i in range(1, 11):
    kmeans = KMeans(n_clusters = i, init = 'k-means++', random_state = 42)
    kmeans.fit(X)
    wcss.append(kmeans.inertia_)
plt.plot(range(1, 11), wcss)
plt.xlabel('Number of clusters')
plt.ylabel('WCSS')
plt.show()

# Fitting K-Means to the dataset
kmeans = KMeans(n_clusters = 3, init = 'k-means++', random_state = 42)
y_kmeans = kmeans.fit_predict(X)

# Visualising the clusters
for i in range(19):
    for j in range(i+1,19):
        if i!=j:
            plt.scatter(X[y_kmeans == 0, i], X[y_kmeans == 0, j], s = 100, c = 'red', label = 'Cluster 0')
            plt.scatter(X[y_kmeans == 1, i], X[y_kmeans == 1, j], s = 100, c = 'green', label = 'Cluster 1')
            plt.scatter(X[y_kmeans == 2, i], X[y_kmeans == 2, j], s = 100, c = 'blue', label = 'Cluster 2')
            plt.scatter(kmeans.cluster_centers_[:, i], kmeans.cluster_centers_[:, j], s = 300, c = 'yellow', label = 'Centroids')
            plt.title('Driver Details')
            plt.xlabel(str(driver_info.columns.values[i]))
            plt.ylabel(str(driver_info.columns.values[j]))
            plt.legend()
            plt.show()
            
# seperating clusters
driver_info['cluster'] = y_kmeans
cluster0 = driver_info[driver_info.cluster == 0]
cluster1 = driver_info[driver_info.cluster == 1]
cluster2 = driver_info[driver_info.cluster == 2]


cluster0['total_lifetime_value'] = cluster0['total_earnings']*4*1 # bad drivers
cluster1['total_lifetime_value'] = cluster1['total_earnings']*4*5 # good drivers
cluster2['total_lifetime_value'] = cluster2['total_earnings']*4*3 # mediocre drivers


# writing clusters
cluster0.to_csv (r'output/cluster0_bad_drivers.csv', header=True)
cluster1.to_csv (r'output/cluster1_good_drivers.csv', header=True)
cluster2.to_csv (r'output/cluster2_mediocre_drivers.csv', header=True)