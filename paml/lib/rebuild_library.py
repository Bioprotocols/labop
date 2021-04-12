import glob
import os

#############
# Run this file in order to rebuild the library when you change something in it

os.chdir('paml/lib/')
for file in glob.glob('*.py'):
    if os.path.realpath(file) == os.path.realpath(__file__):
        continue  # don't rerun this file and start an infinite loop
    exec(open(file).read())
