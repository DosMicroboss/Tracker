from functools import reduce

def compose(*funcs):
    def inner(arg):
        return reduce(lambda acc, f: f(acc), reversed(funcs), arg)
    return inner

def pipe(value, *funcs):
    return reduce(lambda acc, f: f(acc), funcs, value)
