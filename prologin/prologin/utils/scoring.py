from collections import namedtuple


class Scoreboard:
    ScoreboardItem = namedtuple('ScoreboardItem', 'rank ex_aequo nonlinear item')

    def __init__(self, iterable):
        self.iterable = list(iterable)
        self.slice = slice(0, None)

    def get_score(self, item):
        return item['score']

    def __getitem__(self, item):
        if isinstance(item, slice):
            self.slice = item
            return self.__iter__()
        raise AttributeError()

    def __iter__(self):
        self.rank = 1
        self.previous_score = None
        self.ex_aequo = True
        self.items = enumerate(self.iterable, 1)
        return self

    def __next__(self):
        while True:
            i, item = next(self.items)
            score = self.get_score(item)
            last_rank = self.rank
            self.ex_aequo = True
            if self.previous_score is None or self.previous_score != score:
                self.rank = i
                self.ex_aequo = False
                self.previous_score = score
            if self.slice.stop is not None and i > self.slice.stop:
                raise StopIteration
            if self.slice.start is None or i >= self.slice.start:
                break
        return Scoreboard.ScoreboardItem(rank=self.rank,
                                         ex_aequo=self.ex_aequo,
                                         nonlinear=i > 1 and last_rank != self.rank - 1,
                                         item=item)


def decorate_with_rank(iterable, score_getter, decorator):
    """
    For each `item` in `iterable`:
        - compute ranking of `item` by its score, retrieved using `score_getter(item)`
        - call `decorator(item, rank, ex_aequo)`

    :param iterable: the iterable to decorate
    :param score_getter: a callable that returns the score of the item passed as first argument
    :param decorator: a callable that modifies the item passed as first argument; rank is second argument; ex-aequo
                      boolean is third argument
    """
    assert callable(score_getter)
    assert callable(decorator)
    rank = 1
    previous_score = None
    for i, item in enumerate(iterable, 1):
        score = score_getter(item)
        ex_aequo = True
        if previous_score is None or previous_score != score:
            rank = i
            ex_aequo = False
            previous_score = score
        decorator(item, rank, ex_aequo)
