import sys as _sys
from time import time as _time
from collections import deque as _deque


class ProgressBar(object):
    """ Class for progress bar
        Usage
        -----
        progress = ProgressBar(size, info)
        for n in range(size):
            progress.forward()
            # executions
        progress.end() # finish
    """
    # configuration of ProgressBar
    info = '%(cur)d/%(size)d'
    # the width of progress bar
    width = 28
    # the full mark in progress bar
    full = '#'
    # the empty mark in progress bar
    empty = ' '
    # prefix and suffix to define marks
    prefix = ' |'
    suffix = '| '
    # windos size of moving average for computing the speed
    smooth_window = 100

    def __init__(self, size=1, message="Progress bar", **kwargs):
        # the message before the progress bar
        self._mesg = '\r' + message
        # current step
        self._now_iter = 0
        assert (size > 0), 'None-negative size'
        # max iterations
        self._max_iter = size
        # start time
        self._start_time = _time()
        # time queue for moving average
        self._time_queue = _deque(maxlen=self.smooth_window + 1)
        self._time_queue.append(self._start_time)
        # update configurations fo progress bar
        for key, value in kwargs.iteritems():
            self[key] = value

    @property
    def max(self):
        # read only for max iteration
        return self._max_iter

    @property
    def now(self):
        # read only for current iteration
        return self._now_iter

    def __getitem__(self, key):
        if key.startswith('_'):
            return None
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        if not key.startswith('_'):
            setattr(self, key, value)

    def line(self):
        """ Current line
        """
        full_size = int(1. * self.width * self.cur / self.size)
        empty_size = self.width - full_size
        full = self.full * full_size
        empty = self.empty * empty_size
        mesg = self._mesg % self
        info = self.info % self
        now = _time()
        self._time_queue.append(now)
        elapsed_time = self._time_queue[-1] - self._time_queue[0]
        second_per_iter = 1. * elapsed_time / (len(self._time_queue) - 1)
        speed = '({:.2e}s/iter)'.format(second_per_iter)
        line = ''.join([mesg, self.prefix, full, empty, self.suffix,
                        info, speed])
        # drop the very first time
        if self._now_iter == 1:
            self._time_queue.popleft()
        return line

    def reset(self, size=None, message=None):
        if size is not None:
            self._max_iter = size
        if message is not None:
            self._mesg = '\r' + message
        self._start_time = _time()
        self._now_iter = 0

    def __iter__(self):
        return self

    def next(self):
        if self.cur < self.size:
            self._now_iter += 1
            _sys.stdout.write(self.line())
            _sys.stdout.flush()
            return self.cur - 1
        else:
            raise StopIteration()

    def end(self):
        _sys.stdout.write('\n')

    def forward(self):
        self.next()
