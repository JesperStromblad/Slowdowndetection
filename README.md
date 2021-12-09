# Slowdowndetection

Implementation of cluster data point evaluation and slow-down detection algorithm proposed for a recommendation system for performance testing decision making evaluated on CERN CMS uploader service. This requires an understanding of our entire approach which is present in the [article] (link to be updated). This approach is useful during performance regression testing of web service that deals with many test inputs.

# Files information

- `install.sh` sets up python virtual environment and install all packages.
- `dbscan_e9414f04.csv` consists of clustered data based on DBSCAN clustering technique.
- `selectdatapoints.csv` data points selected randomly. This is done with `random_data_points()` method in slowdown_detection file.
- `perfcibug.csv` and `pylintanalysis.csv` files consists of two cases for evaluating our algorithm. These files are a result of `sample profiling` which we mention in our [article] ().

# Instructions for running the slow-down detection algorithm.

- Run install.sh file
- Run slowdown_detection.py
- The output will be a json object which consists of decisions on different inputs about an update.
