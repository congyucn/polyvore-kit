import os
import pandas as pd
import numpy as np
try:
    import cPickle as pickle
except ImportError:
    import pickle

from . import config as cfg


def load_pkl(pkl_dir='/data/polyvore/processed/pickles'):
    """ Load fashion_sets and fashion_items
    """
    sets_pkl = os.path.join(pkl_dir, 'fashion_sets.pickle')
    items_pkl = os.path.join(pkl_dir, 'fashion_items.pickle')
    sets, items = {}, {}
    if os.path.isfile(sets_pkl) and os.path.isfile(items_pkl):
        with open(sets_pkl, 'rb') as f:
            sets = pickle.load(f)
        with open(items_pkl, 'rb') as f:
            items = pickle.load(f)
    return sets, items


class DataFile(object):
    """ Class DataFile(data_dir):
        Members
        -------
        tuple_dir: where to read the postive, negative tuples etc
        list_dir: where to read image list
        Arribute
        -------
        image_list: image list for each category
        Methods
        -------
        get_tuples(phase, repeated=True): Return postive and negative tuples
    """
    def __init__(self, tuple_dir, list_dir):
        tuple_dir = os.path.abspath(tuple_dir)
        list_dir = os.path.abspath(list_dir)
        self._tpldir = tuple_dir
        self._listdir = list_dir
        self._image_list = self._load_image_list(list_dir)

    @property
    def image_list(self):
        return self._image_list

    def _load_image_list(self, data_dir):
        """ Read image list for each category
        """
        image_list_fn = ['image_list_{}'.format(cate)
                         for cate in cfg.ClassName]
        image_list = [list() for i in range(cfg.NumCate)]
        for n in range(cfg.NumCate):
            with open(os.path.join(data_dir, image_list_fn[n]), 'r') as f:
                for line in f:
                    image_list[n].append(line.strip('\n'))
        return image_list

    def get_tuples(self, phase, repeated=True):
        """ open tuples file for given phase and return two tuples
            Parameter
            ---------
            phase: tuple for given phase
            Return
            ------
            positive_tuples: shape of (N, 4) or (N * ratio, 4) if repeated
            negative_tuples: shape of (N * ratio, 4)
            ratio: repeated times
        """
        idx = cfg.PhaseIdx[phase]
        posi_tpl_file = ['{}/tuples_{}_posi'.format(self._tpldir, p)
                         for p in cfg.Phase]
        nega_tpl_file = ['{}/tuples_{}_nega'.format(self._tpldir, p)
                         for p in cfg.Phase]
        posi_fn = posi_tpl_file[idx]
        nega_fn = nega_tpl_file[idx]
        posi_tpls = np.array(pd.read_csv(posi_fn))
        nega_tpls = np.array(pd.read_csv(nega_fn))
        # reshape
        num_posi = posi_tpls.shape[0]
        num_nega = nega_tpls.shape[0]
        ratio = num_nega / num_posi
        if repeated:
            posi_tpls = posi_tpls.repeat(ratio, axis=0)
        return posi_tpls, nega_tpls
