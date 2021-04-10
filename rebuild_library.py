import glob

for file in glob.glob('lib/*.py'):
    exec(open(file).read())
