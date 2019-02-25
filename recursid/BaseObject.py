from textwrap import indent

ANCESTOR_INDENT = 2

class BaseObject:
    """
    ancestors: str - A string representation of the ancestors
    """
    def str_content(self):
        """
        Override this function to specify the a representation of the object
        that will automatically be used to generate ancestors and __str__

        Do not override __str__, the output from this will be used to build it
        """
        raise RuntimeError("Ran str_content on BaseObject")

    def __str__(self):
        return """Object Type: {}\nTTL: {}\nContent:\n{}\nAncestors:\n{}""".format(
                  self.__class__.__name__,
                  self.ttl,
                  self.str_content(),
                  indent(self.ancestors, " " * ANCESTOR_INDENT),
                  )
