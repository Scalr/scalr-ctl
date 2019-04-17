"""
Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
2011, 2012, 2013, 2014, 2015, 2016 Python Software Foundation; All Rights
Reserved
"""

import sys

import six
from six.moves.urllib.parse import quote_plus

try:
    unicode
except NameError:
    def _is_unicode(value):
        """Returns False if unicode is disabled"""
        return 0
else:
    def _is_unicode(value):
        """Equal value as unicode"""
        return isinstance(value, unicode)

if six.PY2:
    def urlencode(query, doseq=0, quote_via=quote_plus):
        """Encode a sequence of two-element tuples or dictionary into a URL query string.
        If any values in the query arg are sequences and doseq is true, each
        sequence element is converted to a separate parameter.
        If the query arg is a sequence of two-element tuples, the order of the
        parameters in the output will match the order of parameters in the
        input.
        """

        if hasattr(query, "items"):
            # mapping objects
            query = query.items()
        else:
            # it's a bother at times that strings and string-like objects are
            # sequences...
            try:
                # non-sequence items should not work with len()
                # non-empty strings will fail this
                if query and not isinstance(query[0], tuple):
                    raise TypeError
                # zero-length sequences of all types will get here and succeed,
                # but that's a minor nit - since the original implementation
                # allowed empty dicts that type of behavior probably should be
                # preserved for consistency
            except TypeError:
                _, _, tb = sys.exc_info()
                six.reraise(TypeError, "not a valid non-string sequence"
                                       "or mapping object", tb)
        result = []
        if not doseq:
            # preserve old behavior
            for k, v in query:
                k = quote_via(str(k))
                v = quote_via(str(v))
                result.append(k + '=' + v)
        else:
            for k, v in query:
                k = quote_via(str(k))
                if isinstance(v, str):
                    v = quote_via(v)
                    result.append(k + '=' + v)
                elif _is_unicode(v):
                    # is there a reasonable way to convert to ASCII?
                    # encode generates a string, but "replace" or "ignore"
                    # lose information and "strict" can raise UnicodeError
                    v = quote_via(v.encode("ASCII", "replace"))
                    result.append(k + '=' + v)
                else:
                    try:
                        # is this a sufficient test for sequence-ness?
                        len(v)
                    except TypeError:
                        # not a sequence
                        v = quote_via(str(v))
                        result.append(k + '=' + v)
                    else:
                        # loop over the sequence
                        for elt in v:
                            result.append(k + '=' + quote_via(str(elt)))
        return '&'.join(result)

elif six.PY3:
    def urlencode(query, doseq=False, safe='', encoding=None, errors=None,
              quote_via=quote_plus):
        """Encode a dict or sequence of two-element tuples into a URL query string.

        If any values in the query arg are sequences and doseq is true, each
        sequence element is converted to a separate parameter.

        If the query arg is a sequence of two-element tuples, the order of the
        parameters in the output will match the order of parameters in the
        input.

        The components of a query arg may each be either a string or a bytes type.

        The safe, encoding, and errors parameters are passed down to the function
        specified by quote_via (encoding and errors only if a component is a str).
        """

        if hasattr(query, "items"):
            query = query.items()
        else:
            # It's a bother at times that strings and string-like objects are
            # sequences.
            try:
                # non-sequence items should not work with len()
                # non-empty strings will fail this
                if query and not isinstance(query[0], tuple):
                    raise TypeError
                # Zero-length sequences of all types will get here and succeed,
                # but that's a minor nit.  Since the original implementation
                # allowed empty dicts that type of behavior probably should be
                # preserved for consistency
            except TypeError:
                _, _, tb = sys.exc_info()
                raise TypeError("not a valid non-string sequence "
                                "or mapping object").with_traceback(tb)

        result = []
        if not doseq:
            for k, v in query:
                if isinstance(k, bytes):
                    k = quote_via(k, safe)
                else:
                    k = quote_via(str(k), safe, encoding, errors)

                if isinstance(v, bytes):
                    v = quote_via(v, safe)
                else:
                    v = quote_via(str(v), safe, encoding, errors)
                result.append(k + '=' + v)
        else:
            for k, v in query:
                if isinstance(k, bytes):
                    k = quote_via(k, safe)
                else:
                    k = quote_via(str(k), safe, encoding, errors)

                if isinstance(v, bytes):
                    v = quote_via(v, safe)
                    result.append(k + '=' + v)
                elif isinstance(v, str):
                    v = quote_via(v, safe, encoding, errors)
                    result.append(k + '=' + v)
                else:
                    try:
                        # Is this a sufficient test for sequence-ness?
                        len(v)
                    except TypeError:
                        # not a sequence
                        v = quote_via(str(v), safe, encoding, errors)
                        result.append(k + '=' + v)
                    else:
                        # loop over the sequence
                        for elt in v:
                            if isinstance(elt, bytes):
                                elt = quote_via(elt, safe)
                            else:
                                elt = quote_via(str(elt), safe, encoding, errors)
                            result.append(k + '=' + elt)
        return '&'.join(result)
