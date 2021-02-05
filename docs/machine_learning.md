# Machine learning
**Machine learning with tensorflow in 8 easy notebooks.**

## Introduction

The core data set in CAP Checks by Monitoring (CbM) is the annual parcel declaration set compiled from the beneficiaries' registration process. A pre-condition for CbM is that the Member State has a system/systems in place that allow(s) such declarations to be specific for the agricultural parcel (the management unit) and the specific activities that comply with the scheme under which the declaration is made. The obvious benefit of continuous, territory-wide Copernicus Sentinel data use is that we can now cross check the information given in the declarations, by generating relevant markers that confirm compliance.

Given the low overall "material errors" in the annual parcel declaration sets in most Member States, this makes the set an ideal source of information in machine learning. The way we apply machine learning is complementary to classification, and a much better choice indeed. After all, what is the contribution of a classification with an overall accuracy of 90% (at the end of the season), if the parcel declaration set is typically 95-98% correct. What we're interested in is identifying the small percentage of parcels that are not confirmed (i.e. in the 2-5% range), and understand the reasons. Let's leave sorting out classification confusion to the scientists.

A key factor for machine learning is that it needs a regular and consistent sample of observations, both for the learning (or training) stage and the prediction (or testing) stage. This is why Sentinel-1 time series are a prime candidate, because they are regular, consistent (calibrated, no cloud issues) and with a density (at least every 1-3 day for European latitudes) that befits the dynamics of the agricultural growing season. The regularity of Sentinel-1 also applies across several seasons, whereas it would be very difficult to rely on consistent Sentinel-2 time series from one season to the next (esp. at mid to Northern latitudes). We can still use Sentinel-2 after machine learning, e.g. to explain and confirm why certain outliers were detected.

## Data preparation

We choose to apply machine learning to the parcel averages, which were extracted in a previous step. This is not really a pre-requisite for machine learning, which can be applied to pixel time stacks, if needed. However, the shear size of the data volume to process would be prohibitive and, for Sentinel-1, the results would be strongly affected by speckle.


### Determine which classes to include

A typical annual parcel declaration set may include several 100s of different crop types. However, only a small subset of those are cultivated on 90-95% of the overall surface. Machine learning will typically allow the sorting of classes that are distinct in some specific way. A certain robustness is required so that not all minor deviations are assigned to distinct classes. This is achieved by providing a sufficiently large sample of features for "typical" crop types, i.e. those that have at least 1% in the selected area.

We typically try to group crop types that are expected to show similar radiometric behavior over the season. This may include cases like "maize" and "sweet maize", "seed potatoes" and "consumption potatoes", which are expected to have roughly the same crop season and phenological behavior. This is a practical choice, and may not be be applied if it is of interest to keep exactly those classes separate. In fact, machine learning can be easily tailored, for instance, by eliminating confirmed classes and outliers from a first run with group crop types, and then refine in a second run. In our example, we focus on separating the main crop types.

Small parcels are obviously undesired, as they will pollute the training set with mixed feature extractions. In our examples, we eliminate all parcels < 0.3 ha. However, there would be no issue re-inserting small parcels in the testing set, in order to get a first order estimate of their predicted classes.

Machine learning requires many samples to do proper training. Thus, we recommend to select areas in which at least 100,000 parcels are present in the sample. More is better. For very large territories, it may be a good approach to subdivide in large regions that have some agronomic commonality (e.g. similar distribution of the major crop types). An overall precondition is that a sufficient number of samples for the selected classes is present in the sample.


-- insert notebook here --

### Composing the features for machine learning

While Sentinel-1 observations are (very) frequent, they are not regularly sampled. Most EU locations are covered by both ASCending and DESCending orbits and often by more than one overlapping orbit (the more so towards Northern latitudes). We choose to sample these observations over a regular 5 (e.g. North of 50 degrees latitude) or 7 day interval, so that at least 3 observations are averaged. 

-- insert notebook here --

The regularly sampled means much now be organised in a feature vector and be exported for use in follow up routines. At this stage, it should be determined what part of the growing season is most likely to contain the most distinctive features that will help separate the crop types that were identified in the previous step. In our example, we use 5-day means from period 11 (end of February) till period 54 (end of October). 

-- insert notebook here --

The feature set must be matched with unique crop labels (defined as a sequence of integers starting at 0). 

-- insert notebook here --

### Splitting in training and testing sets

The data set for the entire area of interest is now split into training and testing sets. We choose to select random subsets of N% for training with their complementary (100-N)% part for testing. N is typically 20 or 25 percent. In this way, we can execute 100/N separate machine learning runs and combine the results. Each parcel will be labelled with N-1 predictions this way (it is used as training sample in 1 case). This is a practical choice. Scientists prefer to select 80% for training and use 20% for testing, which seems to be somewhat skewed. In fact, training accuracy does not really improve much after a certain percentage of samples is used. We prefer to check the consistency between multiple runs as an indicator for outliers.

-- insert notebook here --

## Running the training and testing

We're now set to run the actual machine learning step. We use tensorflow with the tflearn module. The step consists in reading in the training data and prepare it for the training step. The machine learning model is chosen to be a deep neural network with 2 layers of 32 fully connected nodes. The training step is then run for 50 epochs using the softmax criterion for convergence and interactive review of the accuracy assessment. In most cases, convergence happens well before the end of the 50 epochs. 

The trained model is than used to predict the class probabilities for each of the testing sample. These are then stored to disk.

-- insert notebook here --

The tensorflow model is run for each of the 100/N runs to produce 100/N distinct predictions. 

## Checking the results

### Confusion matrix for testing sets

### Combining different tensorflow runs

### Identifying outliers


## Next steps


