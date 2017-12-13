import os


def check_dirs(folders, action='check', verbose=True):
    if isinstance(folders, list):
        for folder in folders:
            check_dir(folder, action, verbose)
    else:
        check_dir(folders, action, verbose)


def check_dir(folder, action='check', verbose=True):
    """ Check if directory exists and make it when necessary.
        Parameters
        ----------
        folder: folder to be checked
        action: what should be do if the folder does not exists, if action is
                'mkdir', than the Return will also be True
        verbose: For rich info
        Return
        ------
        exists: whether the folder exists
    """
    if action.lower() not in ['check', 'mkdir']:
        raise ValueError('"%s" not in ["check", "mkdir"]' % action.lower())
    exists = os.path.isdir(folder)
    if not exists:
        if action == 'mkdir':
            # make dirs recursively
            os.makedirs(folder)
            exists = True
            if not verbose:
                print ("folder '{}' has been created.".format(folder))
        if action == 'check' and not verbose:
            print ("folder '{}' does not exiets.".format(folder))
    return exists


def check_files(file_list, mode='any', verbose=False):
    """ Check whether files exist, optiaonl modes are ['all','any'] """
    n_file = len(file_list)
    opt_modes = ['all', 'any']
    ops = {'any': lambda x: any(x),
           'all': lambda x: all(x)}
    if mode not in opt_modes:
        print ("Wrong choice of mode, optiaonl modes {}".format(opt_modes))
        return False
    exists = [os.path.isfile(fn) for fn in file_list]
    if verbose:
        print ('filename\t status')
        info = [file_list[i] + '\t' + str(exists[i]) for i in xrange(n_file)]
        print ('\n'.join(info))
    return ops.get(mode)(exists)


def list_files(folder, suffix):
    """ List all files in with given suffix
    """
    return [f for f in os.listdir(folder) if f.endswith(suffix)]
