import glob

for file in glob.glob('paml/lib/*.py'):
    exec(open(file).read())
