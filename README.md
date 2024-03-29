![](pattern.png)

pattern
=======
simple pattern matching in Python

Why
---
Pattern matching can hide object destructuring boilerplate.  For example,
suppose you're writing an HTTP server library that dispatches requests to an
application-supplied callback.  The callback can return any of a variety of
values:

1. `None`: status code 200 with no body,
2. an `int`: a status code with no body,
3. a `bytes`: status code 200 with a body,
4. a `(int, bytes)`: a status code with a body,
5. a `{str: bytes}`: status code 200 with a `Content-Type` header and a body.
6. a `(int, {str: bytes})`: a status code with a `Content-Type` and a body.

This is simple to write using Python:  check the type of the return value, and
then unpack it as necessary to get the inner values, all the while checking
that inner values are also of the correct type.

Imagine how complicated the code would be to `if`/`elif` on each of the six
cases above.

With pattern matching, things are less complicated (though still not ideal):

```python
import pattern


def parse_response(response):
    """Return `(status, content_type, body)` parsed from `response`."""

    # create a pattern matcher with three variables
    match, (status, content_type, body) = pattern.Matcher(3)

    if match(None, response):
        return 200, None, None
    elif match(status[int], response):
        return status.value, None, None
    elif match(body[bytes], response):
        return 200, 'text/html', body.value
    elif match((status[int], body[bytes]), response):
        return status.value, 'text/html', body.value
    elif match({content_type[str]: body[bytes]}, response):
        return 200, content_type.value, body.value
    else:
        match((status[int], {content_type[str]: body[bytes]}), response)
        assert match  # a Matcher remembers the result of the last invocation
        return match.values()
```

How
---
```python
import pattern


# A Matcher instance is an object that can be invoked as a function to match
# a "pattern" against a "subject".  A Matcher can be associated with zero or
# more variables, which can be bound to values during the match.

match = pattern.Matcher()  # Matcher without any variables

match, (foo,) = pattern.Matcher(1)  # Matcher with exactly one variable.  Note
                                    # how the second element of the returned
                                    # tuple is also a tuple, even though it
                                    # contains only one element.

match, (foo, bar) = pattern.Matcher(2)  # Matcher with exactly two variables

# A pattern is an object, typically constructed using literal
# list/dict/set/tuple syntax, that contains class objects (types) that
# constrain the types of objects that can be matched.  A variable returned by
# `pattern.Matcher` can be bound to the pattern by including it in the pattern
# together with its expected sub-pattern, using the [] syntax.

# For example, here we attempt to match (using the Matcher defined above) a
# pattern having no variables.  The pattern is the first argument, while the
# subject (the thing we're checking) is the second argument:
assert match(['foo', int, {int: str}], ['foo', -4, {12: 'hi'}])

# In order for a list or a tuple to match, it must have the same length as the
# corresponding list or tuple in the pattern, and the elements must match
# respectively.
assert match([int, 4, str], [1, 4, 'five'])
assert not match([int, 4, str], ['one', 4, 'five'])
assert not match([int, 4, str], [1, 4, 'five', 'extra'])

# dict and set are more lenient.  In order for a dict or set to match, the
# subject must contain a matching subset of the corresponding dict or list in
# the pattern (i.e. extra elements are ok).
assert match({int: str}, {4: 'yep'})
assert match({int: str}, {4: 'yep', 'extra': 'no problem'})
assert match({1, 2, int}, {1, 2, 3, 4, 5})   # 1, 2, and any int are present
assert not match({1, 2, int}, {1, 3, 5, 7})  # 2 is missing

# Note that patterns within a set or dict exclude other patterns within the
# same set or dict when matching part of the subject.  For example,
assert not match({int, 2, 3}, {2, 3, 'nope'})
# 2 and 3 are already "taken," so int doesn't have anything to match.

# If a variable appears in a pattern without a `[<pattern>]` after it, then it
# imposes no constraint on the matched value.  To impose a constraint on the
# matched value (such as a type), the constraining pattern must appear in
# square brackets after the variable.  For example:
assert match([23, foo], [23, 'any value would work here'])
assert not match([23, foo[int], [23, 'has to be an int here'])

match({23: foo[{int: int}]}, {23: {1: 2}})
assert match
foo, = match.values()
assert foo == {1: 2}

# A variable may not appear more than once in a pattern.  It's just too hard.
raised = False
try:
    match([foo, foo], [2, 2])
except:
    raised = True
assert raised

# The most annoying this about using this library is the number of times you
# need to name the variables.  Initially, you must declare the variables
# themselves using the matcher:
match, (foo, bar) = pattern.Matcher(2)

# Then the variables can appear in patterns passed to the Matcher instance:
match((int, foo[str], bar[list]), (1, 'two', [3, 4, 5]))

# But, annoyingly, the variables then have to be mentioned again in order to
# have those names refer to the bound values, rather than to the variable
# sentinels returned by Matcher:
foo, bar = match.values()

# In particular, if you are using only a subset of the variables, `.values()`
# will still return all of them, and so you have to leave gaps for the values
# you didn't bind to:
if match(['head', foo[list]], subject):
    foo, _ = match.values()
    # ...

# Alternatively, you could _not_ rebind the names of the variables and instead
# use the `.value` attribute of each variable.  That's annoying in its own way,
# though:
if match([foo[int], bar[list]], [1, [2, 3, 4]]):
    assert foo.value == 1
    assert bar.value == [2, 3, 4]

# Finally, keep in mind that this library does not support repetition wildcards
# or other powerful features of most pattern matchers.  This library was
# written after I found a minimal motivating use case (see the "Why" section,
# above), and omitting wildcards was an easy way to simplify the
# implementation.  It also wasn't obvious to me how cleanly to represent those
# features in the literal-syntax mini-language of this library.
```