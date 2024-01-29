import scipy.stats as stats

def binomial_confidence_interval(successes: int, n: int, confidence: float = 0.99):
    """
    Calculate the binomial confidence interval.

    :param successes: Number of successes in the sample.
    :param n: Total sample size.
    :param confidence: Confidence level.
    :return: A tuple containing the lower and upper bounds of the confidence interval.
    """
    if n == 0:
        raise ValueError("Sample size must be greater than 0")

    if successes > n:
        raise ValueError("Number of successes must not exceed sample size")

    # Calculate the confidence interval
    interval = stats.binom.interval(confidence, n, successes / n)

    # Normalize the interval bounds to the proportion
    lower_bound = interval[0] / n
    upper_bound = interval[1] / n

    return lower_bound, upper_bound

# Example usage
ci = binomial_confidence_interval(16, 20)
print(ci)
