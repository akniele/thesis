"""Create feature vector for clustering"""

import sys
sys.path.insert(1, '../Transformation')
from Transformation.fill_up_distributions import fill_distribution
from Transformation.fill_up_distributions import fill_multiple_distributions
import numpy as np
from sklearn.preprocessing import StandardScaler
import pickle
from tqdm import tqdm
import config
from scipy.stats import entropy
import time

from GetClusters.differenceMetrics import entropy_difference
from GetClusters.differenceMetrics import bucket_diff_top_k
from GetClusters.differenceMetrics import sort_probs


# def create_bucket_feature_vector(functions, bucket_list, num_sheets):
#     feature_vector = []
#     for i, sheet in enumerate(probs0[:num_sheets]):  # for sheet in sheets
#         for j in range(len(sheet)):  # for sample in sheet
#             vector = []
#             for function in functions: # right now there is only one function
#                 for k, bucket in enumerate(bucket_list):  # loop over list with the different indices and numbers of buckets
#                     number_of_buckets, indices = bucket_list[k]
#                     difference_metric = function(probs0[i][j], probs1[i][j], number_of_buckets, indices)
#                     vector.extend(difference_metric)
#             feature_vector.append(vector)
#     return np.array(feature_vector, dtype=float)


def create_feature_vector(functions, probs0, probs1, num_sheets):
    feature_vector = []
    for i, sheet in enumerate(tqdm(probs0[:num_sheets], desc="creating feature vector")):  # for sheet in sheets
        for j in range(len(sheet)):  # for sample in sheet
            vector = []
            for function in functions:
                difference_metric = function(probs0[i][j], probs1[i][j])
                vector.extend(difference_metric)
            feature_vector.append(vector)
    return np.array(feature_vector, dtype=float)


def get_entropy_feature(probs0, probs1):
    small_entropies = entropy(probs0, axis=-1)
    big_entropies = entropy(probs1, axis=-1)
    entropy_diff = big_entropies - small_entropies

    return entropy_diff


def create_individual_feature_vector(functions, distr0, distr1):
    feature_vector = []
    for function in functions:
        difference_metric = function(distr0, distr1)
        feature_vector.extend(difference_metric)
    return np.array(feature_vector, dtype=float)


def scale_feature_vector(feature_vector):
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(feature_vector)
    return scaled_features


def create_and_save_feature_vector(functions, num_sheets, filled=True): # (not needed if we scale the feature vector first when loading, only save unscaled)
    scaled_name = "unscaled"
    filled_name = "unfilled"
    if filled:
        filled_name = "filled"

    function_names = "_".join([function.__name__ for function in functions])
    num_features = 1 # sum([config.function_feature_dict[f"{function.__name__}"] for function in functions])

    for i in tqdm(range(9), desc="creating feature vector"):
        probs0 = pickle.load(open(f"train_data/train_small_100000_{i}.pkl", "rb"))
        probs1 = pickle.load(open(f"train_data/train_big_100000_{i}.pkl", "rb"))
        probs0 = probs0.numpy()
        probs1 = probs1.numpy()
        if filled:
            indices0 = pickle.load(open(f"train_data/indices_small_100000_{i}.pkl", "rb"))
            indices1 = pickle.load(open(f"train_data/indices_big_100000_{i}.pkl", "rb"))
            feature_vector = np.zeros((probs0.shape[0], probs0.shape[1], num_features))
            for j in range(10):
                feature_vector_tmp = fill_all_distributions_and_create_features(
                    probs0[j*1000:(j+1)*1000, :, :], probs1[j*1000: (j+1)*1000, :, :],
                    indices0[j*1000:(j+1)*1000, :, :], indices1[j*1000: (j+1)*1000, :, :],
                    functions, num_features=num_features, topk=256)
                feature_vector[j*1000:(j+1)*1000, :, :] = feature_vector_tmp

        else:
            feature_vector = create_feature_vector(functions, probs0, probs1, num_sheets)

        with open(f"train_data/{scaled_name}_{filled_name}_features_{i}_{function_names}.pkl", "wb") as h:
            pickle.dump(feature_vector, h)
        del feature_vector


def load_feature_vector(functions, num_features, num_sheets=10000, scaled=True):  # num features depends on the number of feature functions
    # used, and on how many features they each have
    features = np.zeros((64*num_sheets*9, num_features))

    scaled_name = "unscaled"
    # if scaled:
    #     scaled_name = "scaled"

    function_names = "_".join([function.__name__ for function in functions])

    for i in range(9):
        with open(f"train_data/{scaled_name}_features_{i}_{function_names}.pkl", "rb") as f:
            feature = pickle.load(f)
        features[i*(64*num_sheets):(i+1)*(64*num_sheets)] = feature

    if scaled:
        features = scale_feature_vector(features)
    return features


def fill_all_distributions_and_create_features(probs0, probs1, indices0, indices1, functions, num_features, topk=256):
    assert probs0.shape == probs1.shape
    assert len(probs0.shape) == 3

    array_shape = probs0.shape
    array_shape_new = (array_shape[0], array_shape[1], num_features)

    tmp_array = np.zeros(array_shape_new)

    # start = time.time()

    print("  => FILL DISTRIBUTIONS")
    filled_distr_small = fill_multiple_distributions(probs0, indices0, topk=256)
    filled_distr_big = fill_multiple_distributions(probs1, indices1, topk=256)

    print("  => DONE FILLING DISTRIBUTIONS")
    # end = time.time()
    # diff = end - start
    # print(f'time: {diff:.2f} s')

    #return filled_distr_small, filled_distr_big

    # for i, rows in enumerate(tqdm(probs0, desc="filling up distributions")):
    #     for j, distribution in enumerate(rows):
    #         filled_distribution_small = fill_distribution(distribution, indices0[i][j], topk=256)
    #         filled_distribution_big = fill_distribution(probs1[i][j], indices1[i][j], topk=256)
    #         tmp_features = create_individual_feature_vector(functions, filled_distribution_small, filled_distribution_big)
    #         tmp_array[i][j] = tmp_features

    print("  => CREATING FEATURE VECTORS")
    big_sorted, small_sorted = sort_probs(filled_distr_big, filled_distr_small)
    #feature_vector = get_entropy_feature(filled_distr_small, filled_distr_big)   #create_feature_vector()

    return big_sorted, small_sorted


if __name__ == "__main__":
    functions = [entropy_difference, bucket_diff_top_k]
    num_features = sum([config.function_feature_dict[f"{function.__name__}"] for function in functions])
    print(num_features)
