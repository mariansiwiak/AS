#!/usr/bin/env python
# coding: utf-8

# In[14]:


import scipy.stats as stats

def confidence_interval_for_proportion(successes: int, n: int, confidence=0.99):
    """
    Calculate the confidence interval for a proportion.

    :param successes: Number of successes in the sample.
    :param n: Total sample size.
    :param confidence: Confidence level, default is 0.95.
    :return: A tuple containing the lower and upper bounds of the confidence interval.
    """
    if n == 0:
        raise ValueError("Sample size must be greater than 0")

    elif successes > n:
        raise ValueError("Sample size must be greater than number of sucesses")
    
    p_hat = successes / n
    z = stats.norm.ppf((1 + confidence) / 2)
    margin_of_error = z * (p_hat * (1 - p_hat) / n)**0.5

    print(p_hat - margin_of_error, p_hat + margin_of_error)

