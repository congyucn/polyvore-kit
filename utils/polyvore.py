import os
import json
import shutil
import pandas as pd
import numpy as np
from . import config as cfg
from .check_utils import check_files, list_files, check_dir

try:
    import cPickle as pickle
except ImportError:
    import pickle
from progress import ProgressBar


class polyvore_parser(object):
    """ Polyvore parser for loading items and sets information from raw data.
        Constructor
        -----------
        polyvore_parser(raw_dir):
            Initialize the instance given raw data
        Data Structure
        --------------
        fashion_items: Type of ditc, maintains fasion items with
            pairs of `{image name: item_info}`. item_info is type of dict:
            { 'class': item class in {'top', 'bottom', 'shoe'},
              'name' : the name of item
              'categories' : a list of possible categories,
              'price' : the price of this item,
              'text': the description for this item}
        fashion_sets: Type of list. Maintains fashion sets for each user
            fashion_sets[n]: All fashion sets for n-th user, type of list
            Each set in fashion_sets[n] is a dictionary of
                {'url': set url,
                 'items': Type of list, each one is the
                          list of fashion items of each class.
                 'image': image_path}
        Methods
        -------
        get_all_user_name(): Get all users' name
        parse_items(): Load all fashion items
        parse_sets(): Load all fashion sets
        clean(): Clean items and sets
        Usage
        -----
        >> parser = utils.polyvore.polyvore_parser('~/data/polyvore/raw')
        >> parser.run()
        >> parser.move_images('~/data/polyvore/processed/images')
        >> parser.savez('~/data/polyvore/processed/pickles')

    """
    def __init__(self, raw_dir):
        # save data folders
        raw_dir = os.path.abspath(raw_dir)
        self.image_dir = os.path.join(raw_dir, 'images')
        self.item_dir = os.path.join(raw_dir, 'items')
        self.set_dir = os.path.join(raw_dir, 'sets')
        # load JSON files
        self.set_jsonls = list_files(self.set_dir, 'jsonl')
        self.num_sets_files = len(self.set_jsonls)
        self.item_jsonls = list_files(self.item_dir, 'jsonl')
        self.num_item_files = len(self.item_jsonls)
        self.fashion_items = None
        self.fashion_sets = None
        # see parser_items() and parser_sets() for details
        self.items = None
        self.sets = None
        self.failed_images = None
        self.progress_bar = ProgressBar()

    def run(self):
        self.parse_items()
        self.parse_sets()
        self.clean()

    @staticmethod
    def check_download(item, downloaded_images):
        """ Check whether the image of item has been downloaded
            Parameter
            ---------
            item: One item read from JSON file, type of dict
            downloaded_images: All downloaded images
            Return
            ------
            downloaded: Return True, if the image of item has been downloaded.
                        Otherwise return False
            downloaded_info:
                1. If the image has been recorded as downloaded,
                   and in downloaded_images, return image name
                2. If the image has been recorded as downloaded,
                   but not in deed, return (image_url, 1)
                3. If the image has not been recorded as downloaded,
                   return (image_url, 0)
        """
        downloaded_flag = False
        if len(item['images']) == 0:  # has not been downloaded
            downloaded_info = (item['image_urls'], 0)
        else:  # image has been recorded as downloaded but not in deed
            image_name = item['images'][0]['path'].split('/')[-1]
            if image_name not in downloaded_images:
                downloaded_info = (item['image_urls'], 1)
            else:  # image has been downloaded.
                downloaded_flag = True
                downloaded_info = image_name
        return downloaded_flag, downloaded_info

    @staticmethod
    def find_category(categories, name):
        """ Get the index of category for item.
            Parameters
            ----------
            categories: categories for item
            name: the name of item
            Return
            ------
            i: i-th category
        """
        # category keywords are saved in config.py
        key_word = categories + name.split(' ')
        for key in key_word:
            for i in xrange(cfg.NumCate):
                if key in cfg.ItemKey[i]:
                    return i
        return -1

    @staticmethod
    def check_item_num(set_items):
        """ Check is a fashion set is valid, that is each category must has
            at leat one item
            Parameters
            ----------
            set_items: Type of list. set_items[i] is a list of items in
                       i-th category
            Return
            ------
            True if each category has at leat one item, otherwise False
        """
        assert(len(set_items) == cfg.NumCate)
        for items in set_items:
            if len(items) == 0:
                return False
        return True

    @property
    def user_names(self):
        """ Arribute for user names (both_users, nasty_users)
            1. both_users has both sets and items JOSN
            2. nasty_users has only one of them
        """
        user_by_item = set()
        user_by_set = set()
        for jsonl in self.set_jsonls:
            user_name = jsonl.split('_')[0]
            user_by_set.add(user_name)
        for jsonl in self.item_jsonls:
            user_name = jsonl.split('_')[0]
            user_by_item.add(user_name)
        both_users = (user_by_set & user_by_item)
        nasty_users = (user_by_set | user_by_item) - both_users
        return both_users, nasty_users

    def get_set_items_by_image(self, urls):
        """ Construct a fashion set given urls of item.
        """
        # extract items in one set
        set_items = [[] for n in xrange(cfg.NumCate)]
        for url in urls:
            if url in self.items:
                image_name = self.items[url]['image']['name']
                cate = cfg.ClassIdx[self.items[url]['class']]
                set_items[cate].append(image_name)
        return set_items

    def parse_items(self):
        """ Parse all fashion items.
        Postconditions
        --------------
        self.items: type of dict.
            It saves pairs of {item_url: item_info} for all fashion items.
            The value(image info) of each key(image name) is a dict:
              { 'class': item class in {'top', 'bottom', 'shoe'},
                'categories' : a list of possible categories,
                'image': { 'name': image name, 'path': image path}
                'name' : 'item name, one like 3.1 Phillip Lim tops',
                'price' : "the price like $ 81",
                'text': 'the description'}
        self.failed_images : failed downloaded image urls for each user
        """
        # two types of json files xxx_items.jsonl and xxx_items_append.jsonl
        sub_dirs = {'.jsonl': 'items/full',
                    '_append.jsonl': 'items_append/full'}
        # failed images for each user
        failed_images = {}
        # record {image_url: image info} into all_items
        all_items = {}
        # for each item file
        self.progress_bar.reset(self.num_item_files, 'Dealing with item files')
        for n in xrange(self.num_item_files):
            self.progress_bar.forward()
            # split the name of json file
            user_name, ftype = self.item_jsonls[n].split('_items')
            # if ignore then skip this user_name
            if user_name in cfg.IgnoreUsers:
                continue
            # only parse watch user for debug
            if cfg.WatchUsersFlag and user_name not in cfg.WatchUsers:
                continue
            # image folder for items
            imgdir = os.path.join(self.image_dir, user_name, sub_dirs[ftype])
            # list downloaded images
            downloaded_images = list_files(imgdir, ('jpg', 'png'))
            # open the corresponding JOSN file for this user
            with open(os.path.join(self.item_dir, self.item_jsonls[n])) as f:
                item_jsonl = f.readlines()
            # update the number of items
            for line in item_jsonl:
                # read one item
                item = json.loads(line)
                # skip non-fashion item
                if not item['isfashion']:
                    continue
                downloaded, info = self.check_download(item, downloaded_images)
                if downloaded:  # if downloaded, save the information of item
                    image_name = info
                    image_path = os.path.join(imgdir, image_name)
                    item_url = item['url']
                    checksum = item['images'][0]['checksum']
                    cate = self.find_category(item['categories'], item['name'])
                    if cate == -1 or item_url in all_items:
                        # if not the category we want or has been recorded
                        continue
                    else:
                        # save this item
                        all_items[item_url] = {
                            'class': cfg.ClassName[cate],
                            'image': {'name': image_name, 'path': image_path},
                            'categories': item['categories'],
                            'name': item['name'],
                            'price': item['price'],
                            'text': item['description'],
                            'checksum': checksum}
                else:
                    # if image failed downloaded
                    failed_images.setdefault(user_name, [])
                    failed_images[user_name].append(info)
        self.progress_bar.end()
        self.items = all_items
        self.failed_images = failed_images

    def parse_sets(self):
        """ Parse sets for each user.
            Postconditions
            --------------
            self.sets: Maintains a dictionary for all fashion sets with
                paris of `{user name: all_sets}`. For each user, it stores:
                all_sets['invalid']: an unsuccessful downloaded
                all_sets['valid']: type of list, for each valid set
                    valid_set['url']: set url
                    valid_set['image']: path to fashion set image
                    valid_set['items']: fashion items indicting by item urls
                        items[n]: item urls for n-th category
        """
        if (self.items is None):
            print ("No item has been parsed, "
                   "so automatically run parse_items() first!")
            self.parse_items()
        sets = {}
        self.progress_bar.reset(self.num_sets_files, 'Dealing with user sets')
        for n in xrange(self.num_sets_files):
            self.progress_bar.forward()
            # user name and its set image folder
            user = self.set_jsonls[n].split('_sets')[0]
            # image directory for sets
            image_dir = os.path.join(self.image_dir, user, 'sets/full/')
            if (user in cfg.IgnoreUsers):
                continue
            if cfg.WatchUsersFlag and (user not in cfg.WatchUsers):
                continue
            with open(os.path.join(self.set_dir, self.set_jsonls[n])) as f:
                set_jsonl = f.readlines()
            valid_sets = list([])
            invalid_sets = list([])
            for line in set_jsonl:
                one_set = json.loads(line)
                item_urls = [cfg.BaseUrl + u.lstrip('.')
                             for u in one_set['item_urls']]
                # extract items in one set
                set_items = self.get_set_items_by_image(item_urls)
                if self.check_item_num(set_items):
                    # size = [len(items) for items in set_items]
                    # assert(any(size) > 0)
                    set_image = one_set['images']
                    if len(set_image) is 0:
                        image_path = ''
                    else:
                        image_name = set_image[0]['path'].split('/')[-1]
                        image_path = os.path.join(image_dir, image_name)
                    valid_sets.append({'url': one_set['url'],
                                       'items': set_items,
                                       'image': image_path})
                else:
                    invalid_sets.append(one_set['url'])
            # store all information about sets, organized by user name
            sets[user] = {'valid': valid_sets, 'invalid': invalid_sets}
        self.sets = sets
        self.progress_bar.end()

    def clean(self):
        """ Clean sets and items
            Postconditions
            --------------
            self.fashion_items: for all fashion items
            self.fashion_sets: for all fashion sets
        """
        if (self.sets is None):
            print ("No sets has been parsed, "
                   "so automatically run parse_sets() first!")
            self.parse_sets()
        item_image_set = set()
        fashion_sets = []
        size = len(self.sets)
        self.progress_bar.reset(size, 'Cleaning fashion sets')
        for key, all_sets in self.sets.iteritems():
            self.progress_bar.forward()
            if len(all_sets['valid']) == 0:
                continue
            for one_set in all_sets['valid']:
                for i in xrange(cfg.NumCate):
                    for image_name in one_set['items'][i]:
                        item_image_set.add(image_name)
            fashion_sets.append(all_sets['valid'])
        self.progress_bar.end()
        # check duplicate items url that points to the same image
        duplicate_image_url = {}
        for url, info in self.items.iteritems():
            image_name = info['image']['name']
            if image_name in duplicate_image_url:
                duplicate_image_url[image_name].append(url)
            else:
                duplicate_image_url[image_name] = [url]
        # clean fashion items
        fashion_items = {}
        size = len(duplicate_image_url)
        self.progress_bar.reset(size, 'Cleaning fashion items')
        for image_name, urls in duplicate_image_url.iteritems():
            self.progress_bar.forward()
            # item must in at least one fashion set
            if image_name not in item_image_set:
                continue
            for url in urls:
                # more than one images
                item = self.items[url]
                if image_name not in fashion_items:
                    fashion_items[image_name] = {
                        'class': item['class'],
                        'categories': item['categories'],
                        'name': item['name'],
                        'price': item['price'],
                        'text': item['text']}
                else:
                    # add category
                    category = fashion_items[image_name]['categories']
                    category += item['categories']
                    category = list(set(category))
                    fashion_items[image_name]['categories'] = category
                    # if previous item has no name
                    name = fashion_items[image_name]['name']
                    if len(name) == 0:
                        fashion_items[image_name]['name'] = item['name']
                    # if previous item has no description
                    text = fashion_items[image_name]['text']
                    if len(text) == 0:
                        fashion_items[image_name]['text'] = item['text']
        self.progress_bar.end()
        self.fashion_items = fashion_items
        self.fashion_sets = fashion_sets

    def move_images(self, outdir):
        """ Move items and sets images
        """
        if (self.fashion_items is None):
            self.clean()
        self.progress_bar.reset(len(self.fashion_items), 'Moving item images')
        image_pathes = {}
        for url, info in self.items.iteritems():
            image_name = info['image']['name']
            image_pathes[image_name] = info['image']['path']
        itemdir = os.path.join(outdir, 'items')
        for subdir in cfg.ClassName:
            check_dir(os.path.join(itemdir, subdir), action='mkdir')
        for image_name, info in self.fashion_items.iteritems():
            self.progress_bar.forward()
            image_path = image_pathes[image_name]
            subdir = info['class']
            shutil.copy2(image_path, os.path.join(itemdir, subdir))
        self.progress_bar.end()
        self.progress_bar.reset(len(self.fashion_sets), 'Moving set images')
        setdir = os.path.join(outdir, 'sets')
        check_dir(setdir, action='mkdir')
        for sets in self.fashion_sets:
            self.progress_bar.forward()
            for one_set in sets:
                image_path = one_set['image']
                if len(image_path) == 0:
                    continue
                else:
                    shutil.copy2(image_path, setdir)
        self.progress_bar.end()

    def savez(self, outdir):
        """ Save all_items and all_sets
        """
        if (self.fashion_items is None):
            self.clean()
        check_dir(outdir, action='mkdir')
        pkl_files = ['fashion_sets.pickle', 'fashion_items.pickle']
        file_list = [os.path.join(outdir, fn) for fn in pkl_files]
        if check_files(file_list, 'any', verbose=False):
            print ("Failed to save, in case of overriding previous files.")
            return
        with open(os.path.join(outdir, 'fashion_sets.pickle'), 'wb') as f:
            pickle.dump(self.fashion_sets, f)
        with open(os.path.join(outdir, 'fashion_items.pickle'), 'wb') as f:
            pickle.dump(self.fashion_items, f)


def load_pkl(pkl_dir):
    """ Load pickle files
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


def take_users(idxs, data_set):
    """ Take users with indices specificed in idxs
        Parameter
        ---------
        idxs: The index for which user to take
        data_set: Type of list, fashhion sets for each user
        Return
        ------
        taked data sets
    """
    return [data_set[u] for u in idxs]


def clip_data(data_set, clip):
    """ Clip fasion sets for each user
        Parameter
        ---------
        data_set: Type of list, fashhion sets for each user
                  data_set[i]: Type of set
        clip: Maximum number of fashion sets
        Return
        ------
        clipped data sets
    """
    return [set(list(sets)[0:clip]) for sets in data_set]


class concise_sets(object):
    """ Convert fashion_sets to concise_sets
        Override method convert_set() to define how to convert one fashion set
    """
    def __init__(self, fashion_sets, clip=0):
        self.fashion_sets = fashion_sets

    def convert_set(self, set_items):
        """ Read one fashion set
            Parameters
            ----------
            set_items: Type of list
                       set_items[i] : A list of item in i-th category
            Return
            ------
            sets: A list of tuples extracted from set_items
        """
        sets = []
        # only the set with one bottom and one shoe is considered
        if (len(set_items[0]) >= 1) and \
           (len(set_items[1]) == 1) and \
           (len(set_items[2]) == 1):
            # split tops to make fashion tuples
            num_sets = len(set_items[0])
            for n in xrange(num_sets):
                one_set = [set_items[c][0] for c in xrange(cfg.NumCate)]
                one_set[0] = set_items[0][n]
                sets.append(tuple(one_set))
        return sets

    def run(self, clip=0):
        """ Read the origin data to a concise data structure and remove users
            that have insufficient fashion sets.
        """
        concise_sets = []
        for all_sets in self.fashion_sets:
            # parse one user's fashion sets
            set_tuples = []
            for one_set in all_sets:
                # parse each valid set
                set_tuples += self.convert_set(one_set['items'])
            concise_sets.append(set_tuples)
        clipped_sets = []
        for sets in concise_sets:
            if len(sets) < clip:
                continue
            clipped_sets.append(set(sets))
        return clipped_sets


class polyvore_spliter(object):
    """ Class for generating polyvore training, validation and test data
        Constructor
        -----------
        polyvore_data(sets, min_size)
            sets: Type of list
                  sets[i]: Type of set, save a set of (top, bottom, shoe)
                           for i-th user
            min_size: minimal size for train / val / test
        Attribute
        ---------
        datasets: Separated data sets for each pahse
        image_dict: Pairs of {image name: id}
        image_list: Type of list, list of image name
            image_dict[image_list[i]] == i
        Methods
        -------
        run(usize): Run spliter:
                    1. split the data set
                    2. leave some users out randomly, say 'S0' and
                       the other is 'S1', then datasets = S0 U S1
        get_datasets(is_leaved, dtype):
            dtype = {'id', 'raw'}
                if dtype == 'id' the fashion set is:
                    (top id, bottom id, shoe id)
                if dtype == 'raw' the fashion sets is
                    (top image, bottom image, top image)
            is_leaved: If True, return data set that leaved out (S0) else S1
    """
    def __init__(self, sets, min_size=[250, 20, 20]):
        self.min_size = min_size
        self.num_items, self.num_sets = None, None
        self.image_dict, self.image_list = None, None
        self.num_users = len(sets)
        self.raw_sets = sets
        self.datasets = [set(), set(), set()]
        # splited data sets for training / val / test
        self.progress_bar = ProgressBar()
        self._splited_ = False
        self.update()

    def get_datesets(self, is_leaved, dtype='id'):
        if not self._splited_:
            self.run()
        if is_leaved:
            datasets = self._S0_
        else:
            datasets = self._S1_
        if dtype == 'id':
            return self._convert(datasets)
        else:
            return datasets

    def run(self, usize=80):
        """ Run spliter, split the data set and leave some users out randomly
            Postconditions
            --------------
            self.datasets: data set that splited
            use self.get_datasets() to get datasets
            Parameter
            --------
            usize: leave some user for use
        """
        self.split()
        self.leave(usize)
        self.update()

    def leave(self, usize):
        """ Leave some users out randomly
        """
        if not self._splited_:
            self.split()
        idxs = np.random.permutation(self.num_users)
        small_idx = idxs[0:usize]
        large_idx = idxs[usize:]
        S0, S1 = [], []
        for n in xrange(cfg.NumPhase):
            S0.append(take_users(small_idx, self.datasets[n]))
            S1.append(take_users(large_idx, self.datasets[n]))
        self._S0_ = S0
        self._S1_ = S1

    def update(self):
        assert (len(self.datasets[0]) == len(self.datasets[1]))
        assert (len(self.datasets[0]) == len(self.datasets[2]))
        num_users = len(self.datasets[0])
        num_sets = [0] * num_users
        image_set = [set() for n in xrange(cfg.NumCate)]
        for datasets in self.datasets:
            for uid, sets in enumerate(datasets):
                num_sets[uid] += len(sets)
                for one_set in sets:
                    for n in xrange(cfg.NumCate):
                        image_set[n].add(one_set[n])
        image_list = [list(image_set[n]) for n in xrange(cfg.NumCate)]
        nitems = [len(image_list[n]) for n in xrange(cfg.NumCate)]
        image_dict = [{} for n in xrange(cfg.NumCate)]
        for n in xrange(cfg.NumCate):
            for idx in xrange(nitems[n]):
                image_name = image_list[n][idx]
                image_dict[n][image_name] = idx
        self.num_users = num_users
        self.num_sets = num_sets
        self.num_items = nitems
        self.image_list = image_list
        self.image_dict = image_dict

    def count_sets(self):
        """ Count number of users and number of sets for each user
        """
        self.num_users = len(self.sets)
        self.num_sets = [len(user_outfits) for user_outfits in self.sets]

    def count_items(self):
        """ Count number of items in each category, save a list for item urls
            and a map for image name to its index.
        """
        item_set = [set() for n in xrange(cfg.NumCate)]
        image_dict = [{} for n in xrange(cfg.NumCate)]
        for sets in self.sets:
            for one_set in sets:
                for n in xrange(cfg.NumCate):
                    item_set[n].add(one_set[n])
        image_list = [list(item_set[n]) for n in xrange(cfg.NumCate)]
        num_items = [len(image_list[n]) for n in xrange(cfg.NumCate)]
        for n in xrange(cfg.NumCate):
            for idx in xrange(num_items[n]):
                image_name = image_list[n][idx]
                image_dict[n][image_name] = idx
        self.num_items = num_items
        self.image_list = image_list
        self.image_dict = image_dict

    def _convert(self, datasets):
        if not self._splited_:
            self.run()
        assert (len(datasets[0]) == len(datasets[1]) == len(datasets[2]))
        num_users = len(datasets[0])
        id_datasets = []
        for n in xrange(cfg.NumPhase):
            id_sets = [set() for u in xrange(num_users)]
            for uid, sets in enumerate(datasets[n]):
                for one_set in sets:
                    id_tpl = tuple(self.image_dict[c][one_set[c]]
                                   for c in xrange(cfg.NumCate))
                    id_sets[uid].add(id_tpl)
            id_datasets.append(id_sets)
        return id_datasets

    def save_list(self, outdir):
        if not self._splited_:
            self.run()
        check_dir(outdir, action='mkdir')
        for n, key in enumerate(cfg.ClassName):
            fn = os.path.join(outdir, "image_list_{}.txt".format(key))
            with open(fn, 'w') as f:
                for image_name in self.image_list[n]:
                    f.write(image_name + '\n')

    def split(self):
        """ Divide fashion sets into trainning, validation and test set.
            Override self._split_() to split the data set.
            Postconditions
            --------------
            self.datasets: Fashion sets for each phase
        """
        self.datasets = self._split_()
        self.update()
        self._splited_ = True

    def _split_(self):
        # split data set into three sets
        print ("Spliting data coarsely...")
        log = "Spliting data for training..."
        train, left = self._split_once(self.raw_sets, self.min_size[0], log)
        # split the left set into two sets
        log = "Spliting data for test ..."
        test, val = self._split_once(left, self.min_size[2], log)
        print("Done! Hold left data for validation")
        datasets = [train, val, test]
        # Check the partition for fashion sets
        assert (len(datasets[0]) == len(datasets[1]) == len(datasets[2]))
        num_users = len(datasets[0])
        # check whcih user satisfies the minimal constrains
        idxs = [u for u in xrange(num_users) if (
            len(datasets[0][u]) >= self.min_size[0] and
            len(datasets[1][u]) >= self.min_size[1] and
            len(datasets[2][u]) >= self.min_size[2])]
        # clean data set
        for n in xrange(cfg.NumPhase):
            datasets[n] = take_users(idxs, datasets[n])
            datasets[n] = clip_data(datasets[n], self.min_size[n] + 10)
        return datasets

    def _split_once(self, sets, min_size, log='Spliting'):
        """ To split at least min_size positive outfits for each user.
            Separated outfits has no overlap with left outfits for each user.
            Parameter
            ---------
            sets: Fashion sets (type of tuple) for each user, type of list
            min_size: Minimum number of sets for each user
            Return
            ------
            sept_sets: Separated fashion sets, each user has at least min_size
            rest_sets: Fashion sets have been left
        """
        sept_sets = [set() for u in xrange(len(sets))]
        rest_sets = [set() for u in xrange(len(sets))]
        self.progress_bar.reset(len(sets), log)
        for u in xrange(len(sets)):
            self.progress_bar.forward()
            # parted and left outfits for this users
            num = len(sets[u])
            part_set = set()
            left_set = sets[u]
            while (min_size >= len(part_set) != num):
                # do split once
                pset, left_set = self._atom_split(left_set)
                # append posi_tuples
                part_set |= pset
            rest_sets[u] = left_set
            sept_sets[u] = part_set
        self.progress_bar.end()
        return sept_sets, rest_sets

    def _atom_split(self, tuple_set):
        """ Split one user's fashion sets that two separated sets have no
            overlapping items.
            Parameter
            ---------
            tuple_set: A set of fashion tuples
            Return
            ------
            part_set: minimal separated set
            left_set: left set
        """
        # convert set of (top_id,bot_id,sho_id) to np.ndarray
        items = [set() for n in xrange(cfg.NumCate)]
        part_set = set()
        left_set = tuple_set.copy()
        # pop one fashion set to start partition
        if len(tuple_set) == 0:
            return items, part_set, left_set
        # pop one tuple
        tpl = left_set.pop()
        part_set.add(tpl)
        items = [set(tpl[n]) for n in xrange(cfg.NumCate)]
        # loop until the size of part_set not increase
        pre_size = -1
        while(len(part_set) != pre_size):
            pre_size = len(part_set)
            for tpl in tuple_set:
                if tpl in part_set:
                    continue
                check = [tpl[n] in items[n] for n in xrange(cfg.NumCate)]
                if (any(check)):
                    for n in xrange(cfg.NumCate):
                        items[n].add(tpl[n])
                    part_set.add(tpl)
                    left_set.discard(tpl)
        return part_set, left_set


class Dataset(object):
    """ A class for data set for each phase
        Constructor
        -----------
        Dateset(datasets): Initialize a set of data for given phase
    """

    def __init__(self, datasets):
        """ Initialize all members, some members are for feature use
            Parameter
            ---------
            outfis: Type of list, maintains fashion set for users.
                    Each one is a list of id tuples
            phase: in which phase the data_set is used
        """
        train, val, test = datasets
        assert (len(train) == len(val) == len(test))
        self.num_users = len(train)
        self.generators = [NegativeGenerator(train, 'train'),
                           NegativeGenerator(val, 'val'),
                           NegativeGenerator(test, 'test')]

    def run(self, ratio=5, factor=2):
        for generators in self.generators:
            generators.run(ratio, factor)

    def save(self, outdir):
        for generators in self.generators:
            generators.save(outdir)


class NegativeGenerator(object):
    def __init__(self, dataset, phase):
        self.num_users = len(dataset)
        self._dataset = dataset
        self.col = cfg.NumCate + 1
        # number of items of each category
        self.num_items = [0] * cfg.NumCate
        # number of sets for each user
        self.num_sets = [len(sets) for sets in dataset]
        self.phase = phase
        self.positive_array = None
        self.negative_array = None
        self.progress_bar = ProgressBar()
        self.load_positive()

    @property
    def positive(self):
        return self._convert(self.positive_array)

    @property
    def negative(self):
        return self._convert(self.negative_array)

    def load_positive(self):
        # convert positive sets to np.array
        positive_array = []
        for uid, posi_sets in enumerate(self._dataset):
            positive_array += [[uid] + list(tpl) for tpl in posi_sets]
        positive_array = np.array(positive_array, dtype=np.int)
        # compress the item id
        self.id_mapping = []
        for n in xrange(cfg.NumCate):
            item_idxs = positive_array[:, n + 1]
            mapping, indices = np.unique(item_idxs, return_inverse=True)
            positive_array[:, n + 1] = indices
            self.id_mapping.append(mapping)
        self.positive_array = positive_array
        # number of items in each category
        self.num_items = [len(m) for m in self.id_mapping]
        # position for each user
        self.upos = np.array([0] + self.num_sets).cumsum()
        # save positive set
        positive_set = set()
        for sets in self._dataset:
            positive_set |= sets
        self.positive_set = positive_set

    def negative_tuples_type1(self, uid, nposi, positive):
        """ For each positive outfit, fix one item randomly,
            then pick two other random items
            implementation: num_cate copies of positive tuples
            the n-th copy are all fixed with n-th item
            a random number of "rand(0,num_cate) * num_posi + u"
            means that randomly fix the rand(0,num_cate)-th category
        """
        num = nposi * cfg.NumCate
        negative = np.zeros((num, self.col), dtype=np.int)
        negative[:, 0] = uid
        # randomly tuples
        for n in xrange(cfg.NumCate):
            negative[:, n + 1] = np.random.choice(self.num_items[n], num)
        # fix one category
        for n in xrange(cfg.NumCate):
            rows = xrange(n * nposi, (n + 1) * nposi)
            negative[rows, n + 1] = positive[:, n + 1]
        # to fix which category
        idxs = np.random.choice(cfg.NumCate, nposi) * nposi + np.arange(nposi)
        negative = negative.take(idxs, axis=0)
        return negative

    def negative_tuples_type2(self, uid, num):
        negative = np.zeros((num, self.col), dtype=np.int)
        negative[:, 0] = uid
        for n in xrange(cfg.NumCate):
            nitem = self.num_items[n]
            # random choose a item
            negative[:, n + 1] = np.random.choice(nitem, num)
        return negative

    def run(self, ratio, factor=2):
        # create negative tuples for each user
        self.negative_array = np.ndarray((0, self.col), dtype=np.int)
        self.progress_bar.reset(self.num_users, 'Creating negative tuples')
        for u in xrange(self.num_users):
            # positive positive for u-th user
            self.progress_bar.forward()
            nposi = self.num_sets[u]
            uposi = self.positive_array[self.upos[u]:self.upos[u + 1], :]
            # total number of negetive tuples need to created
            nrequired = nposi * ratio
            negative1 = self.negative_tuples_type1(u, nposi, uposi)
            negative2 = self.negative_tuples_type2(u, nrequired)
            negative = np.vstack((negative1, negative2))
            idxs = []
            for idx, tpl in enumerate(negative):
                if len(idxs) == nrequired:
                    break
                if tuple(tpl[1:]) in self.positive_set:
                    continue
                idxs.append(idx)
            # take out qualified neg tuples, according to row idx
            negative = negative.take(idxs, axis=0)
            np.random.shuffle(negative)
            self.negative_array = np.vstack((self.negative_array, negative))
            # nega tuples number of this user should be at least the ratio
            if len(negative) < nrequired:
                print ("Need to increase factor, now it is {}".format(factor))
        self.progress_bar.end()

    def save(self, outdir):
        """ Save tuples.
        """
        check_dir(outdir, action='mkdir')
        cols = ['user'] + cfg.ClassName
        posi = pd.DataFrame(self.positive, columns=cols)
        posi_fn = os.path.join(outdir, "tuples_{}_posi".format(self.phase))
        posi.to_csv(posi_fn, index=False)
        nega = pd.DataFrame(self.negative, columns=cols)
        nega_fn = os.path.join(outdir, "tuples_{}_nega".format(self.phase))
        nega.to_csv(nega_fn, index=False)

    def _convert(self, array):
        res_array = np.empty_like(array)
        res_array[:, 0] = array[:, 0]
        for n in range(cfg.NumCate):
            real_id = self.id_mapping[n][array[:, n + 1]]
            res_array[:, n + 1] = real_id
        return res_array
