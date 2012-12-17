from pprint import pformat
from pygments import highlight
from pygments.lexers import PythonLexer
#from pygments.lexers.web import JSONLexer
from pygments.formatters.terminal256 import Terminal256Formatter


def pp(arg):
    print highlight(pformat(arg), PythonLexer(), Terminal256Formatter())
    #print highlight(pformat(arg), JSONLexer(), Terminal256Formatter())
