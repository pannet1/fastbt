import pandas as pd
import itertools


def multi_args(function, constants, variables, isProduct=None):
    """
    Run a function on different parameters and
    aggregate results
    function
        function to be parametrized
    constants
        arguments that would remain constant
        throughtout all the scenarios
        dictionary with key being argument name
        and value being the argument value
    variables
        arguments that need to be varied
        dictionary with key being argument name
        and value being list of argument values
        to substitute
    isProduct
        list of variables for which all combinations
        are to be tried out. Not implemented

    By default, this function zips through each of the
    variables but if you need to have the Cartesian
    product, specify those variables in isProduct

    returns a dataframe with different variables and
    the results
    """
    from functools import partial
    collect = {}
    func = partial(function, **constants)
    args = [x for x in zip(*variables.values())]
    keys = variables.keys()
    for arg in args:
        kwds = {a:b for a,b in zip(keys, arg)}
        result = func(**kwds)
        collect[arg] = result
    s = pd.Series(collect)
    s.name = 'values'
    s.index.names = keys
    return s
