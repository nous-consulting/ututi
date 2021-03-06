import translitcodec
import trans
import traceback

def urlify(text, maxlen=None):
    """
    Urlify a string by transliterating it, changing all whitespace to dashes and limitting its length to
    the specified number of chars.

    # XXX unit test me!

    """

    text = text.lower().encode('transliterate')
    text = text.lower().encode('trans/id')

    text = text.encode("ascii", "ignore")

    if maxlen is not None:
        text = text[:maxlen]
    return text
