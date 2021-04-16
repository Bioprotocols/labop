from sbol_utilities.graph_sbol import graph_sbol
import sbol3
import paml

doc = sbol3.Document()
doc.read('test/testfiles/growth_curve.ttl')
graph_sbol(doc)
