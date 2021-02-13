import sys
import os
import posixpath
import argparse

sys.path.insert(0, posixpath.join(os.path.dirname(os.path.abspath(__file__)), 'opil'))


if not '-i' in sys.argv:
    sys.argv.append('-i')
    sys.argv.append(posixpath.join(os.path.dirname(os.path.abspath(__file__)), 'paml.ttl'))
    sys.argv.append('-n')
    sys.argv.append('http://bioprotocols.org/paml#')

from opil.opil_factory import *
