# coding=utf-8
# Copyright 2018 The DisentanglementLib Authors.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions that are useful for the different metrics."""
from typing import List

import sklearn
import torch
from torch.utils.data import DataLoader
import numpy as np
import scipy.stats


def generate_batch_factor_code(dataloader:DataLoader,
                               representation_function,
                               num_points,
                               batch_size,
                               device:str):
    """
    Sample a single training sample based on a mini-batch of ground-truth data.

  Args:
    dataloader: data to be sampled from.
    representation_function: Function that takes observation as input and
      outputs a representation.
    num_points: Number of points to sample.
    batch_size: Batchsize to sample points.

  Returns:
    representations: Codes (num_codes, num_points)-np array.
    factors: Factors generating the codes (num_factors, num_points)-np array.
  """
    representations = None
    factors = None
    i = 0
    while i < num_points:
        # basically sampling num_points (observation, label) pairs in batches
        num_points_iter = min(num_points - i, batch_size)
        current_observations, current_factors = next(iter(dataloader))
        if len(current_factors.shape)<2:
            current_factors=np.expand_dims(current_factors,1)
        if i == 0:
            factors = current_factors
            with torch.no_grad():
                representations = representation_function(current_observations.to(device)).cpu()
        else:
            factors = np.vstack((factors, current_factors))
            with torch.no_grad():
                new_rep = representation_function(current_observations.to(device)).cpu()
            representations = np.vstack((representations, new_rep))
        i += num_points_iter
    representations = representations[:num_points]
    factors = factors[:num_points]
    if type(representations) != np.ndarray: representations = representations.numpy()
    if type(factors) != np.ndarray: factors = factors.numpy()
    return np.transpose(representations), np.transpose(factors)

def make_discretizer(target,
                     num_bins,
                     discretizer_fn):
    """Wrapper that creates discretizers."""
    return discretizer_fn(target, num_bins)

def _histogram_discretize(target, num_bins):
    """Discretization based on histograms.
    Better to use an upper bound on num_bins if target is already discrete and don't want to
    lose the categories."""
    discretized = np.zeros_like(target)
    for i in range(target.shape[0]):
        discretized[i, :] = np.digitize(target[i, :],
            np.histogram(target[i, :], num_bins)[1][:-1])
    return discretized


def normal_centers(mu,std, num_bins=20):
    """Transforming continuous variable drawn from normal distribution into a
    discrete variable by exploiting its quantiles (in this way we can generalise
    to unseen samples)
    Returns a list of num_bins centers for the new categorical
    """
    centers = []
    probs = np.linspace(0.,1., num_bins+1, endpoint=False)[1:]
    for i in range(num_bins):
        centers.append(scipy.stats.norm.ppf(probs[i], loc=mu, scale=std))
    return centers

def empirical_centers(labels, num_bins=20):
    """Extracts num_bins empirical quantiles for the given labels
    Labels are expected in the shape num_labels x num_samples """
    centers = []
    probs = np.linspace(0.,1., num_bins+1, endpoint=False)[1:]
    for i in range(num_bins):
        centers.append(np.quantile(labels, probs[i], axis=1))
    return np.stack(centers) #num_bins x num_labels

def normal_discretise(labels:np.ndarray, mus:List, stds:List, num_categories):
    """Turn labels into categorical variables, and store them as integers.
    labels: numpy array of shape (num_samples, num_factors) containing the labels."""
    discretized = np.zeros_like(labels)
    for i in range(labels.shape[0]):
        centers = normal_centers(mus[i], stds[i], num_bins=num_categories)
        discretized[i, :] = np.digitize(labels[i, :], centers)
    return discretized

def quantile_discretise(labels:np.ndarray, num_categories, quantiles:np.ndarray=None):
    """Uses empirical quantiles of the given label to perform distribution-aware
    discretisation"""
    if quantiles is None: quantiles = empirical_centers(labels, num_bins=num_categories)
    discretized = np.zeros_like(labels)
    for i in range(labels.shape[0]):
        discretized[i, :] = np.digitize(labels[i, :], quantiles[:,i])
    return discretized, quantiles

def _identity_discretizer(target, num_bins):
    del num_bins
    return target

def drop_constant_dims(ys):
    """Returns a view of the matrix `ys` with dropped constant rows."""
    ys = np.asarray(ys)
    if ys.ndim != 2:
        raise ValueError("Expecting a matrix.")

    variances = ys.var(axis=1)
    active_mask = variances > 0.
    return ys[active_mask, :], active_mask

def keep_only_active_everywhere(ys_train, ys_test):
    """Only keeps the dimensions (axis 0) that are active both in train and test set"""
    _, active_classes_train = drop_constant_dims(ys_train)
    _, active_classes_test = drop_constant_dims(ys_test)
    everywhere_active_classes = active_classes_train*active_classes_test # logical AND

    if not everywhere_active_classes.any():
        return None

    ys_train_active = ys_train[everywhere_active_classes, :]
    ys_test_active = ys_test[everywhere_active_classes, :]

    return ys_train_active, ys_test_active

def discrete_mutual_info(mus, ys):
    """Compute discrete mutual information."""
    num_codes = mus.shape[0]
    num_factors = ys.shape[0]
    m = np.zeros([num_codes, num_factors])
    for i in range(num_codes):
        for j in range(num_factors):
            m[i, j] = sklearn.metrics.mutual_info_score(ys[j, :], mus[i, :])
    return m

def discrete_entropy(ys):
    """Compute discrete mutual information."""
    num_factors = ys.shape[0]
    h = np.zeros(num_factors)
    for j in range(num_factors):
        h[j] = sklearn.metrics.mutual_info_score(ys[j, :], ys[j, :])
    return h

def normalize_data(data, mean=None, stddev=None):
    if mean is None:
        mean = np.mean(data, axis=1)
    if stddev is None:
        stddev = np.std(data, axis=1)
    return (data - mean[:, np.newaxis]) / stddev[:, np.newaxis], mean, stddev

