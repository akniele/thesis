from GetClusters.differenceMetrics import bucket_diff_top_k
from GetClusters.differenceMetrics import get_entropy_feature
from GetClusters.differenceMetrics import get_top_p_difference
from pipeline import run_transparent_pipeline
from pipeline import run_baseline
from pipeline import make_directories
import sys

"""
Note: If you are using e.g. the bucket transformation function, and therefore don't need the parameter TOP_P,
either leave it the way it is or set it to None
"""

"""
Another note: N_CLUSTERS has to be either an int > 0 or None
"""

# ------- hyperparameters shared between transparent pipeline and baseline ------ #

GENERATE_DATA = False  # if True, generates probability distributions as training data, and features
GENERATE_SORTED_BY_BIG = False  # if True, generate probability distributions sorted by big model, for baseline
N_TEST_SAMPLES = 500  # number of samples used for testing, each sample consists of a sequence of 64 distributions

# ------- end hyperparameters shared between transparent pipeline and baseline -- #

# -------- hyperparameters for transparent pipeline -------- #

FUNCTION = bucket_diff_top_k  # get_top_p_difference   # get_entropy_feature
BUCKET_INDICES = [2, 3]  # if bucket_diff_top_k, choose where buckets should start and end,
# NB: 0 and len(distribution) are added automatically later!
TOP_P = 0.77  # probability for get_top_p_difference transformation function
N_CLUSTERS = None  # number of clusters to use for k-means clustering, if None: no clustering or classifying!
BATCH_SIZE = 16
EPOCHS = 25
LR = 5e-5
TRAIN_CLASSIFIER = False  # if True, trains a new classifier
RANDOM_LABELS = False

# ----- end of hyperparameters for transparent pipeline ----- #


# --------- hyperparameters for baseline model -------#

LR_BASELINE = 0.1      # 1e-5 original learning rate, now using learning rate scheduler
EPOCHS_BASELINE = 60
BATCH_SIZE_BASELINE = 8

# --------- end hyperparameters for baseline model -------#


if __name__ == "__main__":

    make_directories()

    # run_baseline(n_test_samples=N_TEST_SAMPLES, batch_size=BATCH_SIZE_BASELINE, epochs=EPOCHS_BASELINE, lr=LR_BASELINE,
    #              generate_data=GENERATE_DATA, generate_sorted_by_big_data=GENERATE_SORTED_BY_BIG)

    run_transparent_pipeline(function=FUNCTION, n_clusters=N_CLUSTERS, batch_size=BATCH_SIZE, epochs=EPOCHS, lr=LR,
                             generate_data=GENERATE_DATA, generate_sorted_by_big=GENERATE_SORTED_BY_BIG,
                             train_classifier=TRAIN_CLASSIFIER, bucket_indices=BUCKET_INDICES, top_p=TOP_P,
                             n_test_samples=N_TEST_SAMPLES, random_labels=RANDOM_LABELS)
