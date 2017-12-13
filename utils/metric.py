import numpy as np


def ndcg_score(y_score, y_label, wtype='max'):
    """ Normalize Discounted cumulative gain (NDCG).
        Parameters
        ----------
        y_score : array, shape = [n_samples]
            Predicted scores.
        y_label : array, shape = [n_samples]
            Ground truth lambel (binary).
        wtype : 'log' or 'max'
            type for discounts
        Returns
        -------
        score : ndcg@m
    """
    order = np.argsort(y_score)[::-1]
    p_label = np.take(y_label, order)
    i_label = np.sort(y_label)[::-1]
    p_gain = 2 ** p_label - 1
    i_gain = 2 ** i_label - 1
    if wtype.lower() == 'max':
        discounts = np.log2(np.maximum(np.arange(len(y_label)) + 1, 2.))
    else:
        discounts = np.log2(np.arange(len(y_label)) + 2)
    dcg_score = (p_gain / discounts).cumsum()
    idcg_score = (i_gain / discounts).cumsum()
    return (dcg_score / idcg_score)


def mean_ndcg_score(u_scores, u_labels, wtype='max'):
    """ mean Normalize Discounted cumulative gain (NDCG) for all users
        Parameters
        ----------
        u_score : array of arrays, shape = [num_users]
            Each array is the predicted scores, shape = [n_samples[u]]
        u_label : array of arrays, shape = [num_users]
            Each array is the ground truth label, shape = [n_samples[u]]
        wtype : 'log' or 'max'
            type for discounts
        Returns
        -------
        mean_ndcg : array, shape = [num_users]
            mean ndcg for each user (averaged among all rank)
        avg_ndcg : array, shape = [max(n_samples)], averaged ndcg at each
            position (averaged among all users for given rank)
    """
    num_users = len(u_scores)
    n_samples = [len(scores) for scores in u_scores]
    max_sample = max(n_samples)
    count = np.zeros(max_sample)
    mean_ndcg = np.zeros(num_users)
    avg_ndcg = np.zeros(max_sample)
    for u in range(num_users):
        y_score = u_scores[u]
        y_label = u_labels[u]
        ndcg = ndcg_score(y_score, y_label, wtype)
        avg_ndcg[:n_samples[u]] += ndcg
        count[:n_samples[u]] += 1
        mean_ndcg[u] = ndcg.mean()
    return mean_ndcg, avg_ndcg / count
