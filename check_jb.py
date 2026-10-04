import sys

try:
    import jupyter_book
    print("jupyter_book is installed version:", jupyter_book.__version__)
except ImportError:
    print("jupyter_book NOT installed")

try:
    import nbconvert
    print("nbconvert is installed version:", nbconvert.__version__)
except ImportError:
    print("nbconvert NOT installed")

try:
    import sphinx
    print("sphinx is installed version:", sphinx.__version__)
except ImportError:
    print("sphinx NOT installed")
