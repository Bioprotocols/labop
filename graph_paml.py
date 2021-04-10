import sbol3
import graphviz
import rdflib
import argparse
import paml


def get_node_label(graph, uri):
    label = None
    for name in graph.objects(rdflib.URIRef(uri), rdflib.URIRef('http://sbols.org/v3#name')):
        return name
    for display_id in graph.objects(rdflib.URIRef(uri), rdflib.URIRef('http://sbols.org/v3#displayId')):
        return display_id
    return uri.split('//')[-1]


def strip_scheme(uri):
    return uri.split('//')[-1]


def visit_children(obj, triples=[]):
    for property_name, sbol_property in obj.__dict__.items():
        if isinstance(sbol_property, sbol3.ownedobject.OwnedObjectSingletonProperty):
            child = sbol_property.get()
            if child is not None:
                visit_children(child, triples)
                triples.append((obj.identity, 
                                property_name,
                                child.identity))
        elif isinstance(sbol_property, sbol3.ownedobject.OwnedObjectListProperty):
            for child in sbol_property:
                visit_children(child, triples)
                triples.append((obj.identity, 
                                property_name, 
                                child.identity))
    return triples


def visit_associations(obj, triples=[]):
    for property_name, sbol_property in obj.__dict__.items():
        if isinstance(sbol_property, sbol3.refobj_property.ReferencedObjectSingleton):
            referenced_object = sbol_property.get()
            if referenced_object is not None:
                triples.append((obj.identity, 
                                property_name, 
                                referenced_object))
        elif isinstance(sbol_property, sbol3.refobj_property.ReferencedObjectList):
            for referenced_object in sbol_property:
                triples.append((obj.identity, 
                                property_name, 
                                referenced_object))
        elif isinstance(sbol_property, sbol3.ownedobject.OwnedObjectSingletonProperty):
            child = sbol_property.get()
            if child is not None:
                visit_associations(child, triples)
        elif isinstance(sbol_property, sbol3.ownedobject.OwnedObjectListProperty):
            for child in sbol_property:
                visit_associations(child, triples)
    return triples


association_relationship = {
        'arrowtail' : 'odiamond',
        'arrowhead' : 'vee',
        'fontname' : 'Bitstream Vera Sans',
        'fontsize' : '8',
        'dir' : 'both'
    } 

composition_relationship = {
        'arrowtail' : 'diamond',
        'arrowhead' : 'vee',
        'fontname' : 'Bitstream Vera Sans',
        'fontsize' : '8',
        'dir' : 'both'
    } 

def graph_sbol(doc, outfile='out'):
    g = doc.graph()
    dot_master = graphviz.Graph()

    for obj in doc.objects:
        dot = graphviz.Graph(name='cluster_%s' %strip_scheme(obj.identity))
        dot.graph_attr['style'] = 'invis'

        # Graph TopLevel
        obj_label = get_node_label(g, obj.identity)
        dot.node('Document')
        dot.node(strip_scheme(obj.identity))
        dot.edge('Document', strip_scheme(obj.identity))

        # Graph owned objects
        t = visit_children(obj, [])
        for start_node, edge, end_node in t:
            start_label = get_node_label(g, start_node)
            end_label = get_node_label(g, end_node)
            dot.node(strip_scheme(start_node), label=start_label)
            dot.node(strip_scheme(end_node), label=end_label)
            dot.edge(strip_scheme(start_node), strip_scheme(end_node), **composition_relationship)

        # Graph associations
        t = visit_associations(obj, [])
        for triple in t:
            start_node, edge, end_node = triple
            start_label = get_node_label(g, start_node)
            end_label = get_node_label(g, end_node)
            dot.node(strip_scheme(start_node), label=start_label)
            dot.node(strip_scheme(end_node), label=end_label)
            dot.edge(strip_scheme(start_node), strip_scheme(end_node), label=edge, **association_relationship)
        
        dot_master.subgraph(dot)
    dot_master.render(outfile, view=True)
 

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        dest="in_file",
        help="Input PAML file",
    )
    args_dict = vars(parser.parse_args())

    doc = sbol3.Document()
    doc.read(args_dict['in_file'])
    graph_sbol(doc, args_dict['in_file'].split('.')[0])
