import collections


def is_iterable(obj):
    return isinstance(obj, collections.Iterable) and not isinstance(obj, str)


def flatten(*values):
    for value in values:
        if isinstance(value, str):
            yield value
            continue
        if isinstance(value, collections.Iterable):
            yield from flatten(*value)
        elif value is not None:
            yield value


def generator(func):
    """This decorator builds the generator, nothing else."""
    return func()


def to_camel_case(name):
    words = name.split('_')
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])


def last(iterator, *args):
    """Return the last item from the iterator."""
    value = next(iterator, *args)
    for value in iterator:
        pass
    return value
