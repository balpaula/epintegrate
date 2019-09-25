import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from sklearn.cluster import KMeans
from scipy.stats.stats import pearsonr
import itertools


#This script uses the first eigenvector of hic matrices as data, only for the first chromosome and with a resolution of 100kb per bin
#20 samples per cell type are present

df = pd.read_csv('complete_genome_data_onlyvalues_corrected.csv', sep=' ', header=None)
x = df.values

num_classes = 7
genome_length = 30344

def calinski_harabasz_score(X, labels):
	n_samples, _ = X.shape
	n_labels = len(set(labels))

	extra_disp, intra_disp = 0., 0.
	mean = np.mean(X, axis=0)
	for k in range(n_labels):
		cluster_k = X[labels == k]
		mean_k = np.mean(cluster_k, axis=0)
		extra_disp += len(cluster_k) * np.sum((mean_k - mean) ** 2)
		intra_disp += np.sum((cluster_k - mean_k) ** 2)
	
	return (1. if intra_disp == 0. else extra_disp * (n_samples - n_labels) / (intra_disp * (n_labels - 1.)))

def get_importance_vector(i,j):
	xlist = list(x)
	data = xlist[20*i:20*(i+1)] + xlist[20*j:20*(j+1)]
	data = np.array(data)
	importance_vector = np.zeros(genome_length)
	occurrence_vector = np.zeros(genome_length)
	num_samples = 100000
	remaining_percentage = 0.01 #We only take 1% of the data. And the clusters still form!
	remaining_number = int(genome_length*remaining_percentage)

	
	for i in range(num_samples):
		#if (i % 1000 == 0): print(i)
		remaining_positions = []
		xx = []
	
		for i in range(remaining_number):
			index = random.randint(0, len(data[0])-1)
			remaining_positions.append(index)

		for i in range(len(remaining_positions)):
			occurrence_vector[remaining_positions[i]] += 1

		for i in range(len(data)):
			v = [data[i][j] for j in remaining_positions]
			xx.append(v)

		xx = np.asarray(xx)

		kmeans = KMeans(n_clusters=2)
		kmeans.fit(xx)
		
		cluster_performance = calinski_harabasz_score(xx, kmeans.labels_)

		for index in remaining_positions:
			importance_vector[index] += cluster_performance

	for i in range(len(importance_vector)):
		if (occurrence_vector[i] != 0):
			importance_vector[i] = importance_vector[i] / occurrence_vector[i]
		else:
			importance_vector[i] = 0
	return importance_vector

imp_matrix = np.zeros((num_classes, num_classes, genome_length))
for i in range(num_classes):
	for j in range(i+1, num_classes):
		imp_matrix[i][j] = get_importance_vector(i, j)
		filename = 'imp_matrix_'+i+'_'+j+'.txt'
		np.savetxt(filename, imp_matrix)


def get_common_regions():
	#Common most important regions between two transitions
	correlations = {}

	for i in range(num_classes):
		for j in range(i+1, num_classes):
			for k in range(num_classes):
				for l in range(k+1, num_classes):
					if (set([i,j]) != set([k,l])):
						a = set(imp_matrix[i][j].argsort()[-20:]) #We take the 20 most "important" positions
						b = set(imp_matrix[k][l].argsort()[-20:])
						correlations[str(i) + '->' + str(j) + ':' + str(k) + '->' + str(l)] = len(a.intersection(b)) / len(a.union(b))
	
	return correlations
						
def get_correlations():
	#Correlations between importance vectors associated to two transitions
	df = pd.DataFrame()
	for i in range(6):
		for j in range(6):
			df[str(i) + '_' + str(j)] = imp_matrix[i][j]

	correlations = {}

	columns = df.columns.tolist()
	for col_a, col_b in itertools.combinations(columns, 2):
		correlations[col_a + '__' + col_b] = pearsonr(df.loc[:,col_a], df.loc[:,col_b])

	return correlations


#print(get_correlations())
print(get_common_regions())
