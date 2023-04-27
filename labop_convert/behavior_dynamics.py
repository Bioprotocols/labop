# Core packages
import logging

# 3rd party packages
import networkx as nx
import xarray as xr

# Project packages
from labop import ActivityNodeExecution, primitive_execution
import uml


class SampleProvenanceObserver():
    """
    Tracks sample provenance over time, forming a directed graph.

    Samples are implicitly tracked: what aliquots are combined for a given
    operation at t-1 determine the provenance for the aliquots (samples) at t.

    Supported operations are:

    - TransferByMap
    """

    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.exec_tick = 0

    def update(self, record: ActivityNodeExecution):
        call = record.call.lookup()
        inputs = [x for x in call.parameter_values if x.parameter.lookup(
        ).property_value.direction == uml.PARAMETER_IN]
        iparams = primitive_execution.inout_parameter_map(inputs)

        # We are only interested in the actual TransferByMap command, which
        # contains source, destination, and plan keys.
        if 'plan' in iparams:
            self._update_on_transfer_by_map(iparams)

    def metadata(self, sources: xr.DataArray, tick: int) -> xr.Dataset:
        """Return metadata about aliquots at the specified tick.

        Really just a graph indexing operation.

        Assumption: sources contains an 'aliquot' dimension which has the
                    aliquots of interest.

        Assumption: All aliquots of interest have the same types of contents. If
                    an aliquot doesn't have a given content type, then the
                    corresponding amount is 0.

        """
        if tick < 0 or tick > self.exec_tick:
            raise RuntimeError(f"Bad tick: Must be [0, {self.exec_tick}]")

        matches = [x for x, y in self.graph.nodes(data=True) if
                   y['tick'] == tick and y['aliquot'] in sources['target_aliquot']]

        content_types = list(self.graph.nodes[matches[0]]['contents'].keys())
        return xr.DataArray([[self.graph.nodes[node_idx]['contents'][c]
                             for c in self.graph.nodes[node_idx]['contents']]
                            for node_idx in matches],
                            dims=["aliquot", "contents"],
                            coords={"aliquot": sources['aliquot'].data,
                                    "contents": content_types}
                            )

    def draw(self) -> None:
        """
        Draw the provenance graph in its current state.

        Mainly for debugging purposes.
        """
        import matplotlib.pyplot as plt
        pos = nx.multipartite_layout(self.graph, subset_key='layer')
        nx.draw(self.graph,
                pos,
                with_labels=True,
                labels={n: self.graph.nodes[n]['label'] for n in self.graph.nodes})

        nx.draw_networkx_edge_labels(self.graph, pos,
                                     edge_labels={(u, v):
                                                  self.graph.edges[u, v]['amount']
                                                  for u, v in self.graph.edges})
        plt.show()

    def _update_on_transfer_by_map(self,
                                   iparams: dict
                                   ) -> None:
        """
        Track sample states as a result of a TransferByMap operation.

        Each source aliquot has the specified amount removed and put in ALL
        target aliquots, so the resulting graph is bipartite.

        Assumption: all types of 'contents' appear in all source aliquots.

        Flow:
        - Add source aliquots to graph
        - Add target aliquots to graph
        - Add edges from each source aliquot to all target aliquots
        - Flow metadata along edges
        """

        sarr = iparams['source'].to_data_array()

        # Source aliquot data is on dimension 2 (3 total).
        src_indices = []
        for source in range(0, sarr.shape[1]):
            # For a hash, you can't just use the aliquot+tick, because those are
            # the same for both source and target.
            idx = hash('source' + str(source) + str(self.exec_tick))
            amounts = sarr.data[0][source]
            contents = dict(zip(sarr['contents'].data,
                                amounts / len(sarr['contents'].data)))

            label = f"aliquot={source},tick={self.exec_tick},contents=" + \
                "{" + ''.join(f'{k}:{v}\n' for k, v in contents.items()) + "}"

            self.logger.debug("Add %d=%s", idx, label)

            # layer attribute is required by the bipartite graph layout we use
            # for drawing.
            self.graph.add_node(idx,
                                aliquot=source,
                                tick=self.exec_tick,
                                layer=self.exec_tick,
                                label=label,
                                contents=contents)
            src_indices.append(idx)

        transfer_plan = iparams['plan'].get_map().sel(source_array='source',
                                                      target_array='target')
        self.exec_tick += 1

        # Create target nodes and edges with the transfer amounts from each
        # source aliquot
        for src_idx in src_indices:
            for target in transfer_plan['target_aliquot']:
                target = target.data.item()
                # For a hash, you can't just use the aliquot+tick, because those
                # are the same for both source and target.
                target_idx = hash('target' + str(target) + str(self.exec_tick))
                label = f"aliquot={target},tick={self.exec_tick}"

                if target_idx not in self.graph.nodes:
                    self.logger.debug("Add %d=%s", target_idx, label)

                    # layer attribute is required by the bipartite graph layout
                    # we use for drawing.
                    self.graph.add_node(target_idx,
                                        aliquot=target,
                                        tick=self.exec_tick,
                                        layer=self.exec_tick,
                                        label=label)

                self.logger.debug("Add edge: %s -> %s",
                                  self.graph.nodes[src_idx],
                                  target)
                self.graph.add_edge(src_idx,
                                    target_idx,
                                    amount=transfer_plan.data[source][target])

        # Flow contents+amounts from source->target nodes
        target_nodes = [x for x, y in self.graph.nodes(data=True) if
                        y['tick'] == self.exec_tick]

        for idx in target_nodes:
            contents = {}
            for u, v, data in self.graph.in_edges(idx, data=True):
                for thing in self.graph.nodes[u]['contents']:
                    contents.setdefault(thing, 0)
                    contents[thing] += data['amount']

                self.graph.edges[u, v]['label'] = data['amount']

            # Update target node with precise description of how much of what is
            # in it.
            self.graph.nodes[idx]['contents'] = contents
            self.graph.nodes[idx]['label'] += ',contents={' + \
                ''.join(f'{k}:{v}\n' for k, v in contents.items()) + "}"
