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
