"""simple pattern matching"""


from collections import defaultdict
import collections.abc as abc


class Matcher:
    def __init__(self, num_variables=0):
        self.vars = tuple(Variable() for _ in range(num_variables))
        self.matched = False

    def __iter__(self):
        yield self
        yield self.vars

    def variables(self):
        return self.vars

    def values(self):
        for var in self.vars:
            yield var.value

    def __bool__(self):
        return self.matched

    def __call__(self, pattern, subject):
        self.matched = False  # for starters

        for var in self.vars:
            var.reset()

        if any(count > 1 for var, count in _count_variables(pattern).items()):
            raise Exception('Pattern contains one or more variables that '
                            'appear more than once.  Each variable may appear '
                            'at most once in a pattern.')

        self.matched, bindings = _match(pattern, subject)

        if self.matched:
            for var, value in bindings.items():
                var.value = value

        return self.matched


def _count_variables(pattern):
    counts = defaultdict(int)

    def visit(pattern):
        if isinstance(pattern, Variable):
            counts[pattern] += 1
            visit(pattern.pattern)
        elif isinstance(pattern, abc.Set) or isinstance(pattern, abc.Sequence):
            for subpattern in pattern:
                visit(subpattern)
        elif isinstance(pattern, abc.Mapping):
            for key, value in pattern.items():
                visit(key)
                visit(value)
        
    visit(pattern)
    return counts


def _match(pattern, subject):
    if isinstance(pattern, abc.Set):
        if not isinstance(subject, abc.Set) or len(subject) < len(pattern):
            return False, {}
        else:
            return _match_set(pattern, subject)
    elif isinstance(pattern, abc.Mapping):
        if not isinstance(subject, abc.Mapping) or len(subject) < len(pattern):
            return False, {}
        else:
            return _match_mapping(pattern, subject)
    elif isinstance(pattern, abc.Sequence):
        # of similar types (e.g. distinguish between tuple and list, but not
        # between tuple and NamedTuple).
        if not (isinstance(subject, type(pattern)) or isinstance(pattern, type(subject))):
            return False, {}
        # of the same length
        if len(subject) != len(pattern):
            return False, {}
        else:
            return _match_sequence(pattern, subject)
    elif isinstance(pattern, type):
        if isinstance(subject, pattern):
            return True, {}
        else:
            return False, {}
    elif isinstance(pattern, Variable):
        matched, bindings = _match(pattern.pattern, subject)
        if matched:
            bindings[pattern] = subject
        return matched, bindings
    elif pattern is ANY:
        return True, {}
    else:
        return subject == pattern, {}


def _match_sequence(pattern, subject):
    assert isinstance(pattern, abc.Sequence)
    assert isinstance(subject, abc.Sequence)
    assert len(pattern) == len(subject)

    combined_bindings = {}
    for subpattern, subsubject in zip(pattern, subject):
        matched, bindings = _match(subpattern, subsubject)
        if not matched:
            return False, {}

        combined_bindings.update(bindings)

    return True, combined_bindings


def _match_unordered(pattern, subject):
    # This code is common to matching Sets and Mappings (e.g. sets and dicts)
    # We assume that the input `pattern` and `subject` are iterables of
    # distinct (either by key or by value, depending on the caller) values.

    used = set()  # set of subject indices currently "taken" by a pattern index
    pattern_list = list(pattern)  # in some order
    # `table` is all combinations of matching between subject elements and
    # pattern elements.
    table = [[_match(pat, sub) for sub in subject] for pat in pattern_list]

    # Before trying all possible combinations of pattern/subject match
    # assignments, sort the patterns in order of increasing matchness, so that
    # highly constrained patterns are likely to fail early, avoiding
    # unnecessary work.
    num_matches = [(sum(matched for matched, _ in column), p) for p, column in enumerate(table)]
    num_matches.sort()

    # `num_matches` now contains the new `pattern_list` order.  Now reorder
    # `pattern_list` and `table` accordingly.
    pattern_list = [pattern_list[p] for _, p in num_matches]
    table = [table[p] for _, p in num_matches]

    p = 0  # index into `pattern_list`
    s = [0 for _ in pattern_list]  # index corresponding to a subject in
                                   # `table` for a given `p`

    while True:
        if p == len(pattern_list):
            # All pattern elements have found distinct matching subject
            # elements, so we're done.
            combined_bindings = {}
            for pattern_index in range(len(pattern_list)):
                subject_index = s[pattern_index]
                matched, bindings = table[pattern_index][subject_index]
                assert matched
                combined_bindings.update(bindings)
            
            return True, combined_bindings

        if s[p] == len(subject):
            # We've run out of possible subjects to match the current pattern.
            # Backtrack to the previous pattern and see if it will match a
            # different pattern, this possibly freeing up a subject for this
            # pattern to match.
            if p == 0:
                # ...unless, of course, there's no subject to go back to.  Then
                # there is no match overall.
                return False, {}

            p -= 1
            used.remove(s[p])
            s[p] += 1
            continue

        if s[p] in used:
            # Even if the current pattern element matches the current subject
            # element, the subject element is already "taken" by a previous
            # pattern element, so try another subject element.
            s[p] += 1
            continue

        matched, bindings = table[p][s[p]]
        if not matched:
            # The current pattern element does not match the current subject
            # element, so try another subject element.
            s[p] += 1
            continue

        # We have a partial match consistent with previous partial matches.
        # Mark the matching subject element "used" and carry on to the next
        # pattern element.
        used.add(s[p])
        p += 1

    # Program execution can't reach here.


def _match_set(pattern, subject):
    assert isinstance(pattern, abc.Set)
    assert isinstance(subject, abc.Set)
    assert len(pattern) <= len(subject)

    return _match_unordered(pattern, subject)


def _match_mapping(pattern, subject):
    assert isinstance(pattern, abc.Mapping)
    assert isinstance(subject, abc.Mapping)
    assert len(pattern) <= len(subject)

    return _match_unordered(pattern.items(), subject.items())


class _Symbol:
    """A `_Symbol` is a distinct value that displays with a specified name."""
    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return f'<{self.__module__}.{self._name}>'

            
ANY = _Symbol('ANY')
UNMATCHED = _Symbol('UNMATCHED')


class Variable:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pattern = ANY
        self.value = UNMATCHED

    def __getitem__(self, pattern):
        self.pattern = pattern
        return self

    def __repr__(self):
        if self.value is UNMATCHED:
            # Use the default __repr__
            return object.__repr__(self)
        else:
            return f'<{self.__module__}.{type(self).__name__} value={repr(self.value)}>'
