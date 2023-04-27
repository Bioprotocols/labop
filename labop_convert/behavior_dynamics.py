# Core packages
import collections
import copy
import logging
import typing as tp

# 3rd party packages
import networkx as nx
import xarray as xr

import uml

# Project packages
from labop import ActivityNodeExecution, SampleMap
from labop.data import deserialize_sample_format, serialize_sample_format
from labop.primitive_execution import input_parameter_map
from labop.strings import Strings


class _AliquotTransfer:
    @staticmethod
    def apply(op: "_AliquotTransfer", src_idx: int, target_idx: int) -> None:
        for _type, amount in op.contents.items():
            op.graph.nodes[target_idx][Strings.CONTENTS].setdefault(_type, 0)
            op.graph.nodes[target_idx][Strings.CONTENTS][_type] += amount
            op.graph.nodes[src_idx][Strings.CONTENTS][_type] -= amount

    @staticmethod
    def drain(op: "_AliquotTransfer", src_idx: int) -> None:
        for _type, amount in op.contents.items():
            op.graph.nodes[src_idx][Strings.CONTENTS][_type] -= amount

    def __init__(self, contents: tp.Dict[str, float], graph: nx.DiGraph) -> None:
        self.contents = contents
        self.graph = graph

    def __str__(self) -> str:
        items = list(self.contents.items())
        return (
            "{"
            + "".join(f"{k}:{v}\n" for k, v in items[:-1])
            + str(items[-1][0])
            + ":"
            + str(items[-1][1])
            + "}"
        )


class _AliquotContents(collections.UserDict):
    def __str__(self) -> str:
        items = list(self.data.items())
        return (
            "{"
            + "".join(f"{k}:{v}\n" for k, v in items[:-1])
            + str(items[-1][0])
            + ":"
            + str(items[-1][1])
            + "}"
        )


class SampleProvenanceObserver:
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
        self.handlers = {
            "https://bioprotocols.org/labop/primitives/liquid_handling/TransferByMap": TransferByMapUpdater,
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmptyContainer": EmptyContainerUpdater,
        }

    def update(self, record: ActivityNodeExecution):
        call = record.call.lookup()
        behavior = record.node.lookup().behavior.lookup()
        inputs = [
            x
            for x in call.parameter_values
            if x.parameter.lookup().property_value.direction == uml.PARAMETER_IN
        ]
        iparams = input_parameter_map(inputs)

        if behavior.identity in self.handlers:
            updater = self.handlers[behavior.identity](self.graph, self.exec_tick)
            self.exec_tick = updater.update(iparams)
            self.graph = updater.graph
        else:
            self.logger.info(
                f"Behavior {behavior} is not handled by {self.__class__}, skipping ..."
            )

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

        matches = [
            x
            for x, y in self.graph.nodes(data=True)
            if y["tick"] == tick and y[Strings.SAMPLE] in sources["target_aliquot"]
        ]

        content_types = list(self.graph.nodes[matches[0]][Strings.CONTENTS].keys())
        return xr.DataArray(
            [
                [
                    self.graph.nodes[node_idx][Strings.CONTENTS][c]
                    for c in self.graph.nodes[node_idx][Strings.CONTENTS]
                ]
                for node_idx in matches
            ],
            dims=[Strings.SAMPLE, Strings.CONTENTS],
            coords={
                Strings.SAMPLE: sources[Strings.SAMPLE].data,
                Strings.CONTENTS: content_types,
            },
        )

    def draw(self) -> None:
        """
        Draw the provenance graph in its current state.

        Mainly for debugging purposes.
        """
        import matplotlib.pyplot as plt

        pos = nx.multipartite_layout(self.graph, subset_key="layer")
        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            labels={n: self.graph.nodes[n]["label"] for n in self.graph.nodes},
        )

        edge_labels = {
            (u, v): data["label"] for u, v, data in self.graph.edges(data=True)
        }
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels)
        plt.show()


class BaseUpdater:
    def __init__(self, graph: nx.DiGraph, exec_tick: int) -> None:
        self.graph = graph
        self.exec_tick = exec_tick
        self.logger = logging.getLogger(__name__)

    def _create_sample_nodes(self, sarr: xr.Dataset) -> tp.List[int]:
        # Source aliquot data is on dimension 2 (3 total).
        src_indices = []
        for source in sarr[Strings.SAMPLE]:
            source_data = sarr.sel({Strings.SAMPLE: source})
            if idx := self.sample_tracked(source_data, self.exec_tick):
                self.logger.debug("Reference tracked source aliquot=%d", idx)
                src_indices.append(idx)
                continue

            # For a hash, you can't just use the aliquot+tick, because those are
            # the same for both source and target.
            idx = hash("source" + str(source))
            amounts = sarr.sel({Strings.SAMPLE: source})
            # contents = _AliquotContents(
            #     dict(
            #         zip(
            #             sarr[Strings.CONTENTS].data,
            #             amounts / len(sarr[Strings.CONTENTS].data),
            #         )
            #     )
            # )

            # label = f"aliquot={source},tick={self.exec_tick},{contents}"

            # 'layer' attribute is required by the bipartite graph layout we use
            # for drawing. This is a new node which doesn't have any parents, so
            # we use the empty set.
            self.logger.debug("Add source aliquot %d=%s", idx, amounts)
            self.graph.add_node(
                idx,
                sample=amounts,
                # aliquot=source,
                parents=set(),
                tick=self.exec_tick,
                layer=self.exec_tick,
                # label=label,
                # contents=contents,
            )
            src_indices.append(idx)

        return src_indices

    def flow_to_targets(self, target_indices: tp.List[int]) -> None:
        # Flow contents+amounts from source->target nodes
        for target_idx in target_indices:
            target_v = self.graph.nodes[target_idx]
            in_edges = self.graph.in_edges(target_idx, data=True)

            for otheridx, thisidx, data in in_edges:
                _AliquotTransfer.apply(data["transfer"], otheridx, thisidx)

            # If we initialized a target node from an existing source node
            # because they both had the same aliquot, the target node got a copy
            # of the source's contents *before* any transfers out happened. So,
            # we drain out the extra contents to avoid double counting.
            if target_v["init_idx"]:
                self.logger.debug("Draining extra contents from %d", target_idx)
                for u, v, data in self.graph.out_edges(target_v["init_idx"], data=True):
                    _AliquotTransfer.drain(data["transfer"], target_idx)

            # After flowing, update label with new contents
            target_v["label"] = str(target_v[Strings.CONTENTS])

            # The node's parents are the nodes which are at the other edge
            # of edges terminating at the node.
            parents = set()
            for otheridx, thisxidx, _ in in_edges:
                parents |= self.graph.nodes[otheridx]["parents"]
                parents.add(otheridx)

            target_v["parents"] = parents

    def sample_tracked(self, sample: xr.Dataset, tick: int) -> tp.Optional[int]:
        matches = [
            x
            for x, y in self.graph.nodes(data=True)
            if Strings.SAMPLE in y
            and y[Strings.SAMPLE][Strings.SAMPLE] == sample[Strings.SAMPLE]
            # and y["tick"] == tick
        ]

        # There can only be a single aliquot with a given ID tracked per
        # tick. If this isn't true, there's a bug.
        if matches:
            if len(matches) != 1:
                raise RuntimeError(
                    (
                        "Exactly 1 tracked sample expected for "
                        f"aliquot={sample} at tick={tick}, got "
                        f"{len(matches)}"
                    )
                )
            return matches[0]

        return None


class EmptyContainerUpdater(BaseUpdater):
    """
    Updater sample states as a result of an EmptyContainer operation.

    This creates new samples that correspond to the initial_contents of the SampleArray
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def update(self, iparams: dict) -> int:
        src_indices = self._create_sample_nodes(iparams["sample_array"].to_data_array())

        # For nicer visual representations of graphs, the space is split into
        # two before/after spaces by using different ticks: one for source
        # aliquots and one for target aliquots.
        self.exec_tick += 1

        return self.exec_tick


class TransferByMapUpdater(BaseUpdater):
    """
    Updater sample states as a result of a TransferByMap operation.

    Each source aliquot has the specified amount removed and put in ALL
    target aliquots, so the resulting graph is bipartite between one tick and
    the next.

    Assumption: all types of 'contents' appear in all source aliquots.

    Flow:
    - Add source aliquots to graph
    - Add target aliquots to graph
    - Add edges from each source aliquot to all target aliquots
    - Flow contents along edges from sources to targets
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def update(self, iparams: dict) -> int:
        source_array = iparams["source"].to_data_array()
        target_array = iparams["destination"].to_data_array()
        source_name = iparams["source"].name
        target_name = iparams["destination"].name
        current_src_indices = self._create_sample_nodes(source_array)
        current_target_indices = self._create_sample_nodes(target_array)

        transfer_plan = iparams["plan"].get_map()
        # Modify plan to refer to source_array and target_array
        source_containers = list(set(source_array[Strings.CONTAINER].data))
        target_containers = list(set(target_array[Strings.CONTAINER].data))
        assert len(source_containers) == 1
        assert len(target_containers) == 1
        transfer_plan.coords["source_container"] = transfer_plan.coords[
            "source_container"
        ].where(False, source_containers[0])
        transfer_plan.coords["target_container"] = transfer_plan.coords[
            "target_container"
        ].where(False, target_containers[0])

        # Rename array locations and containers to align with transfer plan
        source_array = source_array.rename(
            {
                Strings.LOCATION: f"{source_name}_location",
                Strings.CONTAINER: f"{source_name}_container",
            }
        )
        target_array = target_array.rename(
            {
                Strings.LOCATION: f"{target_name}_location",
                Strings.CONTAINER: f"{target_name}_container",
            }
        )

        # To multiply source_array by transfer_plan, it needs to have an index (source_container, source_location, contents).  It will initially have (sample, contents).  We need to replace the sample index by the multiindex (source_container, source_location)
        # Swap dimensions to match tranfer_plan dimensions
        # source_array = source_array.swap_dims({Strings.SAMPLE: "source_location"}).set_coords(["source_location", "source_container", "contents"]).set_xindex(["source_container"]).reset_coords()
        # target_array = target_array.swap_dims({Strings.SAMPLE: "target_location"}).set_coords(["target_location", "target_container", "contents"]).set_xindex(["target_container"])
        # # target_array = target_array.swap_dims({Strings.SAMPLE: "target_location"}).reset_coords().set_coords(("target_container"))

        source_array["volume"] = xr.DataArray(
            [
                [
                    source_array.contents.sel(
                        sample=source_array.sample_location.sel(
                            source_location=l, source_container=c
                        )
                    )
                    for l in source_array.source_location
                ]
                for c in source_array.source_container
            ],
            dims=["source_container", "source_location", "reagent"],
            coords={
                "source_container": source_array.coords["source_container"],
                "source_location": source_array.coords["source_location"],
                "reagent": source_array.coords["reagent"],
            },
        )

        target_array["volume"] = xr.DataArray(
            [
                [
                    target_array.contents.sel(
                        sample=target_array.sample_location.sel(
                            target_location=l, target_container=c
                        )
                    )
                    for l in target_array.target_location
                ]
                for c in target_array.target_container
            ],
            dims=["target_container", "target_location", "reagent"],
            coords={
                "target_container": target_array.coords["target_container"],
                "target_location": target_array.coords["target_location"],
                "reagent": target_array.coords["reagent"],
            },
        )

        # Get concentration of the aliquot contents
        source_array[
            Strings.CONCENTRATION
        ] = source_array.volume / source_array.volume.sum(dim=Strings.REAGENT)

        # Plan
        #   d d d d
        # s 1   1
        # s 1 1

        #  d
        # s

        # Get amount of each aliquot's contents that is transferred
        amount_transferred = source_array.concentration * transfer_plan

        # Get total amount transferred to all targets
        next_source_contents = source_array.volume - amount_transferred.sum(
            dim=["target_location", "target_container"]
        )
        next_target_contents = target_array.volume + amount_transferred.sum(
            dim=["source_location", "source_container"]
        )

        # For nicer visual representations of graphs, the space is split into
        # two before/after spaces by using different ticks: one for source
        # aliquots and one for target aliquots.
        self.exec_tick += 1

        next_source_indices = self._create_target_nodes(transfer_plan, src_indices)
        next_target_indices = self._create_target_nodes(transfer_plan, src_indices)

        self.flow_to_targets(target_indices)

        return self.exec_tick

    def _create_src_nodes(self, iparams: SampleMap) -> tp.List[int]:
        sarr = iparams["source"].to_data_array()

        # Source aliquot data is on dimension 2 (3 total).
        src_indices = []
        source_samples = sarr[Strings.SAMPLE]
        for source in sarr[Strings.SAMPLE]:
            source_data = sarr.sel({Strings.SAMPLE: source})
            if idx := self.sample_tracked(source_data, self.exec_tick):
                self.logger.debug("Reference tracked source aliquot=%d", idx)
                src_indices.append(idx)
                continue

            # For a hash, you can't just use the aliquot+tick, because those are
            # the same for both source and target.
            idx = hash("source" + str(source))
            amounts = sarr.sel({Strings.SAMPLE: source})
            # contents = _AliquotContents(
            #     dict(
            #         zip(
            #             sarr[Strings.CONTENTS].data,
            #             amounts / len(sarr[Strings.CONTENTS].data),
            #         )
            #     )
            # )

            # label = f"aliquot={source},tick={self.exec_tick},{contents}"

            # 'layer' attribute is required by the bipartite graph layout we use
            # for drawing. This is a new node which doesn't have any parents, so
            # we use the empty set.
            self.logger.debug("Add source aliquot %d=%s", idx, amounts)
            self.graph.add_node(
                idx,
                sample=amounts,
                # aliquot=source,
                parents=set(),
                tick=self.exec_tick,
                layer=self.exec_tick,
                # label=label,
                # contents=contents,
            )
            src_indices.append(idx)

        return src_indices

    def _create_target_nodes(
        self, transfer_plan: xr.DataArray, src_indices: tp.List[int]
    ) -> tp.List[int]:
        # Create target nodes and edges with the transfer amounts from each
        # source aliquot
        target_indices = []
        for src_idx in src_indices:
            src_v = self.graph.nodes[src_idx]

            for target in transfer_plan["target_aliquot"]:
                aliquot = target.data.item()

                # ########################################
                # Target nodes are always "new" in the sense that they are
                # created as the result of an operation, so we don't need to
                # check if they already tracked. We DO
                # need to check if they exist in the graph, because multiple
                # source nodes can transfer to a single target node.

                # For a hash, you can't just use the aliquot+tick, because those
                # are the same for both source and target.
                target_idx = hash("target" + str(aliquot))
                label = f"aliquot={aliquot},tick={self.exec_tick}"

                if init_idx := self.sample_tracked(aliquot, self.exec_tick - 1):
                    contents_init = copy.deepcopy(
                        self.graph.nodes[init_idx][Strings.SAMPLE]
                    )

                else:
                    contents_init = _AliquotContents()

                # 'layer' attribute is required by the bipartite graph layout we
                # use for drawing. This is a new node which doesn't have any
                # parents, so we use the empty set.
                if target_idx not in self.graph.nodes:
                    self.logger.debug(
                        "Add target aliquot %d=%s,contents=%s",
                        target_idx,
                        label,
                        contents_init,
                    )

                    self.graph.add_node(
                        target_idx,
                        # aliquot=aliquot,
                        sample=contents_init,
                        parents=set(),
                        tick=self.exec_tick,
                        layer=self.exec_tick,
                        init_idx=init_idx,
                        # contents=contents_init,
                        # label=label,
                    )
                self.logger.debug("Add edge: %s -> %s", src_idx, target_idx)

                transfer = _AliquotTransfer(
                    {
                        ctype: transfer_plan.data[src_v[Strings.SAMPLE]][target]
                        for ctype in src_v[Strings.CONTENTS].keys()
                    },
                    self.graph,
                )

                self.graph.add_edge(
                    src_idx,
                    target_idx,
                    transfer=transfer,
                    label=f"transfer={transfer}",
                )

                if target_idx not in target_indices:
                    target_indices.append(target_idx)

        return target_indices
