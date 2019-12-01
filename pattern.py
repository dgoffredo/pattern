"""simple pattern matching"""


class Matcher:
    def __init__(self, num_variables=0):
        "TODO: create variables"
        self.vars = ['TODO']
        self.matched = False

    def __iter__(self):
        return (self, self.vars)

    def variables(self):
        return list(self.vars)

    def values(self):
        return [var.value for var in self.vars]

    def __bool__(self):
        return self.matched

    def __call__(self, pattern, subject):
        "TODO: and don't forget to set self.matched accordingly"
        return self


any = object()
unmatched = object()


class Variable:
    def __init__(self):
        self.pattern = any
        self.value = unmatched

    def __getitem__(self, pattern):
        "TODO: consistency check, assign self.pattern"
        return self