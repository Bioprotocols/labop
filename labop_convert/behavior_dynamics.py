# Core packages
import logging
import os
from abc import abstractmethod
from random import sample

import graphviz
import numpy as np

# 3rd party packages
import xarray as xr
from numpy import nan
from pint import UnitRegistry
from sbol3 import Measure
from tyto import OM

# Project packages
import uml
from labop import ActivityNodeExecution, SampleArray, SampleMap
from labop.data import (
    deserialize_sample_format,
    new_sample_id,
    sample_array_container_type,
    serialize_sample_format,
)
from labop.primitive_execution import input_parameter_map
from labop.strings import Strings


class SampleProvenanceObserver:
    """
    Tracks sample provenance over time, forming a directed graph.

    Samples are implicitly tracked: what aliquots are combined for a given
    operation at t-1 determine the provenance for the aliquots (samples) at t.

    Supported operations are:

    - TransferByMap
    - EmptyContainer
    """

    def __init__(self, outdir, name="sample_graph") -> None:
        self.graph = xr.Dataset()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.exec_tick = 0
        self.outdir = outdir
        self.name = name
        self.handlers = {
            "https://bioprotocols.org/labop/primitives/liquid_handling/TransferByMap": TransferByMapUpdater,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Transfer": TransferUpdater,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Vortex": VortexUpdater,
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmptyContainer": EmptyContainerUpdater,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Provision": ProvisionUpdater,
            "https://bioprotocols.org/labop/primitives/liquid_handling/SerialDilution": SerialDilutionUpdater,
        }
        self.ureg = UnitRegistry()

    def update(self, record: ActivityNodeExecution) -> None:
        """
        Hook to update the provenance graph after each step of execution.
        """
        # call = record.call.lookup()
        behavior = record.node.lookup().behavior.lookup()
        # inputs = [
        #     x
        #     for x in call.parameter_values
        #     if x.parameter.lookup().property_value.direction == uml.PARAMETER_IN
        # ]
        # iparams = input_parameter_map(inputs)

        if behavior.identity in self.handlers:
            updater = self.handlers[behavior.identity](self)
            new_nodes = updater.update(record)
            self.graph = self.update_graph(new_nodes)
            self.to_dot().render(
                os.path.join(self.outdir, f"{self.name}_{self.exec_tick}")
            )
            self.exec_tick += 1
        else:
            self.logger.info(
                "Behavior %s is not handled by %s, skipping ...",
                behavior,
                self.__class__,
            )

    def update_graph(self, graph_addition, graph=None):
        """
        Add new_nodes and associated edges to the graph.

        Parameters
        ----------
        new_nodes : xr.Dataset
            new samples to add to graph
        """
        if graph is None:
            graph = self.graph

        # New Edges
        new_edges = (
            graph_addition.edges if "edges" in graph_addition else xr.DataArray()
        )

        # New Nodes
        new_nodes = (
            graph_addition.drop("edges")
            if "edges" in graph_addition
            else graph_addition
        )

        # Add new nodes to the graph
        if "tick" in graph and "tick" in new_nodes:
            graph_nodes = xr.concat([new_nodes, graph], dim="tick")
        else:
            graph_nodes = xr.merge([new_nodes, graph])

        # Add new edges to the graph
        if "edges" in graph:
            graph_edges = xr.concat(
                xr.concat([new_edges, graph.edges], dim="edge"), dim="edge"
            ).dropna("edge")
        else:
            graph_edges = new_edges
        graph_edges.name = "edges"

        # Combine nodes and edges
        if "edges" in graph_nodes:
            graph_nodes = graph_nodes.drop("edges")
        new_graph = xr.merge([graph_nodes, graph_edges])
        return new_graph

    def sample_provenance(self, sample_id: str, depth: int = None):
        samples = xr.DataArray([sample_id], dims=("edge"))
        all_samples = samples
        updated = True
        count = 0
        while updated:
            prev_samples = self.graph.edges.where(
                self.graph.edges.loc[:, "next_sample_location"].isin(samples)
            ).dropna("edge", how="all")[:, 0:1][:, 0]
            updated = len(prev_samples) > 0
            all_samples = xr.DataArray(
                np.unique(xr.concat([all_samples, prev_samples], dim="edge").data),
                dims=("edge"),
            )
            samples = prev_samples
            count += 1
            if depth is not None and count >= depth:
                break
        return all_samples

    def to_dot(self, dpi=600, for_samples: xr.DataArray = None, draw_transitions=False):
        """
        Plot graph of samples
        """

        def _container_name(container):
            c = str(container).split("/")[-1]
            if c.endswith("]"):
                c = c[:-2]
            return c

        def _contents_str(contents):
            # Assumes contents is 4D: tick, container, location, reagent
            # print(contents)
            if 0 in contents.data.shape:
                return "empty contents"

            content = contents[0][0][0]
            if content.data.shape[0] > 0:
                reagents = list(
                    content.reagent.str.rsplit(sep="/", dim="name", maxsplit=1)[
                        :, 1:2
                    ].data
                )
                return "\n".join(
                    [f"{r[0][0]}: {r[1]}" for r in zip(reagents, content.data)]
                )
            else:
                return "empty contents"

        dot = graphviz.Digraph(
            name=f"sample_graph",
            strict=True,
            graph_attr={
                "dpi": f"{dpi}",
                "label": "SampleGraph",
                "rankdir": "TB",
                # "concentrate": "true",
            },
            node_attr={"ordering": "out"},
        )

        sample_info = self.get_sample_info()
        sample_info = (
            sample_info.where(sample_info.isin(for_samples)).dropna("index")
            if for_samples is not None
            else sample_info
        )
        subgraph = (
            self.graph
            # .where(self.graph.isin(sample_info))
            # .dropna("tick", how="all")
            # .dropna("location", how="all")
            # .dropna("edge", how="all")
        )

        containers = np.unique(sample_info.container.data)
        container_groups = subgraph.sample_location.groupby("container")
        location_subgraphs = {
            _container_name(c): {
                str(location.data): graphviz.Digraph(
                    name=f"cluster_{_container_name(c)}_{location.data}",
                    graph_attr={
                        "label": f"{_container_name(c)}_{location.data}",
                        # "shape": "rectangle",
                        # "color": "black",
                        # "rank": "TB",
                    },
                )
                for location in container_groups[c]
                .dropna("location", how="all")
                .location
            }
            for c in containers
        }

        container_subgraphs = {
            _container_name(c): graphviz.Digraph(
                name=f"cluster_{_container_name(c)}",
                graph_attr={
                    "label": f"{_container_name(c)}",
                    # "shape": "rectangle",
                    # "color": "black",
                    # "rank": "TB",
                },
            )
            for c in containers
        }

        # g_edges = (
        #     self.graph.edges.stack(i=["edge", "tick"])
        #     .transpose("i", ...)
        #     .dropna(dim="i", how="all")
        # )

        for sample in sample_info:
            contents = (
                subgraph.where(subgraph.container.isin(sample.container), drop=True)
                .where(subgraph.location.isin(sample.location), drop=True)
                .where(subgraph.tick.isin(sample.tick), drop=True)
                .contents
            )
            contents_str = _contents_str(contents)
            container_name = _container_name(sample.container.data)
            sample_str = f"{sample.sample.data} @{sample.tick.data}\n{contents_str}"
            g = location_subgraphs[container_name][str(sample.location.data)]
            g.node(str(sample.sample.data), label=sample_str)

            # contents = self.graph.where(self.graph.container.isin(sample.container), drop=True).where(self.graph.location.isin(sample.location), drop=True).where(self.graph.tick.isin(sample.tick), drop=True).contents.squeeze().dropna("tick", how="all").dropna("reagent", how="all")

            # self.graph.contents.groupby("container")['http://igem.org/engineering/cascade_blue_calibrant'].dropna("location", how="all").dropna("reagent", how="all").dropna("tick", how="all")
            # self.graph.where(self.graph.sample=='sample_b85671ee-ecd2-11ed-964a-3e437a74df79', drop=True).dropna("container", how="all").contents.dropna("location", how="all").dropna("tick", how="all")

        if len(subgraph.edges.dims) > 0 and len(subgraph.edges) > 0:
            subgraph_edges = subgraph.edges.where(
                subgraph.edges[:, 0].isin(sample_info)
                & subgraph.edges[:, 1].isin(sample_info)
            ).dropna("edge", how="any")
            for edge in subgraph_edges:
                if draw_transitions:
                    dot.edge(edge.data[0], edge.data[2])
                    dot.edge(edge.data[2], edge.data[1])
                    dot.node(
                        edge.data[2],
                        label=edge.data[2],
                        _attributes={"shape": "box"},
                    )
                else:
                    dot.edge(edge.data[0], edge.data[1])

        for c, ls in location_subgraphs.items():
            csg = container_subgraphs[c]
            for l, sg in ls.items():
                csg.subgraph(sg)
            dot.subgraph(csg)

        return dot

    def get_sample_info(self, graph=None):
        if graph is None:
            graph = self.graph

        sample_info = (
            graph.sample_location.where(graph.sample_location == graph.sample)
            .stack(index=graph.sample_location.dims + (Strings.SAMPLE,))
            .dropna("index", how="all")
        )
        return sample_info

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

    def standardize(self, amount: Measure):
        term = OM.get_term_by_uri(amount.unit)
        u = amount.value * self.ureg(term)

        if self.ureg.liter in u.units.compatible_units():
            base = u.to("microliter")
        else:
            base = u

        return base.magnitude, base.units

    def time_stamp(self, samples: xr.Dataset) -> xr.Dataset:
        return samples.expand_dims("tick").assign_coords({"tick": [self.exec_tick]})

    def drop_graph_edges(self, graph=None):
        if graph is None:
            graph = self.graph
        return graph.drop("edges") if "edges" in graph else graph

    def select_samples_from_graph(
        self, sample_array: xr.DataArray, graph: xr.Dataset = None
    ):
        if graph is None:
            graph = self.graph
        sample_array_subgraph = (
            self.drop_graph_edges(graph=graph)
            .where(  # self.graph.sample.isin(sample_array.sample),
                graph.container.isin(sample_array.container), drop=True
            )
            .where(graph.location.isin(sample_array.location), drop=True)
            .dropna(Strings.LOCATION, how="all")
            .dropna(dim="tick", how="all")
        )
        samples_by_tick = sample_array_subgraph.sample_location.transpose(
            "container", "location", ...
        )
        # latest_sample_index = samples_by_tick.argmax("tick", skipna=True)
        latest_sample_index = samples_by_tick.where(
            samples_by_tick.isnull(), samples_by_tick.tick
        ).max("tick")
        latest_samples = samples_by_tick.where(
            latest_sample_index == samples_by_tick.tick, drop=True
        )
        groups = sample_array_subgraph.where(
            sample_array_subgraph.sample_location.isin(latest_samples),
            drop=True,
        ).groupby("tick")
        # last_relevant_tick = xr.merge(
        #     [g[1].squeeze("tick", drop=True) for g in groups]
        # )
        last_relevant_tick = xr.merge(
            [
                (g[1].squeeze("tick", drop=True) if "tick" in g[1].dims else g[1])
                for g in groups
            ]
        )
        return last_relevant_tick

    def create_persistence_edges(
        self, sample_array: xr.Dataset, next_sample_array: xr.Dataset
    ) -> xr.Dataset:
        # source_map has two variables: Strings.SAMPLE_LOCATION, Strings.NEXT_SAMPLE_LOCATION
        # these correspond to parallel arrays of the sample ids that will have edges
        source_map = xr.merge(
            [
                sample_array.sample_location,
                next_sample_array.rename(
                    {Strings.SAMPLE_LOCATION: Strings.NEXT_SAMPLE_LOCATION}
                ).next_sample_location,
            ]
        )

        # Converting the parallel arrays in the dataset to a dataarray, and creating a node dimension
        # will provide a list of edges
        source_edges = (
            source_map.to_array()
            .rename({Strings.VARIABLE: Strings.NODE})
            .transpose(Strings.CONTAINER, Strings.LOCATION, Strings.NODE)
        )
        source_edges.name = "s"

        # Stacking the container and location will become a new dimension edges
        all_edges = (
            source_edges.transpose(
                Strings.CONTAINER,
                Strings.LOCATION,
                Strings.NODE,
            )
            .stack(
                edge=[
                    Strings.CONTAINER,
                    Strings.LOCATION,
                ]
            )
            .transpose(Strings.EDGE, Strings.NODE)
        )

        # reindex using edge and drop the container and location coords
        edges = all_edges.reset_index(Strings.EDGE).reset_coords(
            names=[
                Strings.CONTAINER,
                Strings.LOCATION,
            ],
            drop=True,
        )
        edges.name = Strings.EDGES

        return edges

    def make_transfer_array(
        self, source_array: xr.Dataset, target_array: xr.Dataset, amount: float
    ) -> xr.DataArray:
        transfer = xr.DataArray(
            [
                [
                    [
                        [
                            amount
                            for target_aliquot in target_array.sel(container=target)[
                                Strings.LOCATION
                            ]
                        ]
                        for target in target_array[Strings.CONTAINER]
                    ]
                    for source_aliquot in source_array.sel(container=source)[
                        Strings.LOCATION
                    ]
                ]
                for source in source_array[Strings.CONTAINER]
            ],
            dims=(
                Strings.SOURCE_CONTAINER,
                Strings.SOURCE_LOCATION,
                Strings.TARGET_CONTAINER,
                Strings.TARGET_LOCATION,
            ),
            coords={
                Strings.SOURCE_CONTAINER: source_array[Strings.CONTAINER].rename(
                    {Strings.CONTAINER: Strings.SOURCE_CONTAINER}
                ),
                Strings.SOURCE_LOCATION: source_array[Strings.LOCATION].rename(
                    {Strings.LOCATION: Strings.SOURCE_LOCATION}
                ),
                Strings.TARGET_CONTAINER: target_array[Strings.CONTAINER].rename(
                    {Strings.CONTAINER: Strings.TARGET_CONTAINER}
                ),
                Strings.TARGET_LOCATION: target_array[Strings.LOCATION].rename(
                    {Strings.LOCATION: Strings.TARGET_LOCATION}
                ),
            },
        )
        return transfer

    def compute_transfer(
        self,
        source_array: xr.Dataset,
        target_array: xr.Dataset,
        transfer: xr.DataArray,
        label: str = None,
    ) -> xr.Dataset:
        # Rename array locations and containers to align with transfer plan
        transfer_source = source_array.fillna(0).rename(
            {
                Strings.CONTAINER: Strings.SOURCE_CONTAINER,
                Strings.LOCATION: Strings.SOURCE_LOCATION,
            }
        )
        transfer_target = target_array.fillna(0).rename(
            {
                Strings.CONTAINER: Strings.TARGET_CONTAINER,
                Strings.LOCATION: Strings.TARGET_LOCATION,
            }
        )

        # 2.
        # Get concentration of the aliquot contents
        transfer_source[
            Strings.CONCENTRATION
        ] = transfer_source.contents / transfer_source.contents.sum(dim=Strings.REAGENT)
        # Get amount of each aliquot's contents that is transferred
        amount_transferred = transfer_source.concentration * transfer

        # Get total amount transferred to all targets
        next_source_contents = transfer_source[
            Strings.CONTENTS
        ] - amount_transferred.sum(
            dim=[Strings.TARGET_LOCATION, Strings.TARGET_CONTAINER]
        )
        next_source_contents = next_source_contents.rename(
            {
                Strings.SOURCE_LOCATION: Strings.LOCATION,
                Strings.SOURCE_CONTAINER: Strings.CONTAINER,
            }
        )
        next_source_contents = next_source_contents.where(
            next_source_contents != 0.0, nan
        )

        next_target_contents = transfer_target[
            Strings.CONTENTS
        ] + amount_transferred.sum(
            dim=[Strings.SOURCE_LOCATION, Strings.SOURCE_CONTAINER]
        )
        next_target_contents = next_target_contents.rename(
            {
                Strings.TARGET_LOCATION: Strings.LOCATION,
                Strings.TARGET_CONTAINER: Strings.CONTAINER,
            }
        )
        next_target_contents = next_target_contents.where(
            next_target_contents != 0.0, nan
        )

        transfer_source = transfer_source.assign_coords(
            {Strings.SAMPLE: [new_sample_id() for _ in transfer_source.sample]}
        )

        next_source_sample_ids = [
            [new_sample_id() for loc in transfer_source.source_location]
            for c in transfer_source.source_container
        ]
        next_source_array = xr.Dataset(
            {
                Strings.SAMPLE_LOCATION: xr.DataArray(
                    next_source_sample_ids,
                    dims=(Strings.CONTAINER, Strings.LOCATION),
                ),
                Strings.CONTENTS: next_source_contents,
            },
            coords={
                Strings.CONTAINER: transfer_source.coords[
                    Strings.SOURCE_CONTAINER
                ].data,
                Strings.LOCATION: transfer_source.coords[Strings.SOURCE_LOCATION].data,
                Strings.SAMPLE: [s for c in next_source_sample_ids for s in c],
            },
        )

        next_target_sample_ids = [
            [new_sample_id() for loc in transfer_target.target_location]
            for c in transfer_target.target_container
        ]
        next_target_array = xr.Dataset(
            {
                Strings.SAMPLE_LOCATION: xr.DataArray(
                    next_target_sample_ids,
                    dims=(Strings.CONTAINER, Strings.LOCATION),
                ),
                Strings.CONTENTS: next_target_contents,
            },
            coords={
                Strings.CONTAINER: transfer_target.coords[
                    Strings.TARGET_CONTAINER
                ].data,
                Strings.LOCATION: transfer_target.coords[Strings.TARGET_LOCATION].data,
                Strings.SAMPLE: [s for c in next_target_sample_ids for s in c],
            },
        )

        source_map = xr.merge(
            [
                source_array.sample_location,
                next_source_array.rename(
                    {Strings.SAMPLE_LOCATION: Strings.NEXT_SAMPLE_LOCATION}
                ).next_sample_location,
            ]
        )
        source_edges = (
            source_map.to_array()
            .rename({Strings.VARIABLE: Strings.NODE})
            .transpose(Strings.CONTAINER, Strings.LOCATION, Strings.NODE)
        ).rename(
            {
                Strings.CONTAINER: Strings.SOURCE_CONTAINER,
                Strings.LOCATION: Strings.SOURCE_LOCATION,
            }
        )
        source_edges.name = "s"
        target_map = xr.merge(
            [
                target_array.sample_location,
                next_target_array.rename(
                    {Strings.SAMPLE_LOCATION: Strings.NEXT_SAMPLE_LOCATION}
                ).next_sample_location,
            ]
        )
        target_edges = (
            target_map.to_array()
            .rename({Strings.VARIABLE: Strings.NODE})
            .transpose(Strings.CONTAINER, Strings.LOCATION, Strings.NODE)
        ).rename(
            {
                Strings.CONTAINER: Strings.TARGET_CONTAINER,
                Strings.LOCATION: Strings.TARGET_LOCATION,
            }
        )
        target_edges.name = "t"
        transfer_map = xr.merge(
            [
                transfer_source.sample_location,
                next_target_array.rename(
                    {
                        Strings.SAMPLE_LOCATION: Strings.NEXT_SAMPLE_LOCATION,
                        Strings.CONTAINER: Strings.TARGET_CONTAINER,
                        Strings.LOCATION: Strings.TARGET_LOCATION,
                    }
                ).next_sample_location,
            ]
        )
        transfer_plan_map = xr.where(transfer > 0, transfer_map, False)
        transfer_edges = (
            transfer_plan_map.to_array().rename({Strings.VARIABLE: Strings.NODE})
            # .stack(
            #     container=[Strings.SOURCE_CONTAINER, Strings.TARGET_CONTAINER],
            #     location=[Strings.SOURCE_LOCATION, Strings.TARGET_LOCATION],
            # )
            # .transpose(Strings.CONTAINER, Strings.LOCATION, Strings.EDGE)
            .transpose(
                Strings.SOURCE_CONTAINER,
                Strings.SOURCE_LOCATION,
                Strings.TARGET_CONTAINER,
                Strings.TARGET_LOCATION,
                Strings.NODE,
            )
        )
        transfer_edges.name = "tr"

        all_edges = (
            xr.merge([source_edges, target_edges, transfer_edges])
            .transpose(
                Strings.SOURCE_CONTAINER,
                Strings.SOURCE_LOCATION,
                Strings.TARGET_CONTAINER,
                Strings.TARGET_LOCATION,
                Strings.NODE,
            )
            .stack(
                edge=[
                    Strings.SOURCE_CONTAINER,
                    Strings.SOURCE_LOCATION,
                    Strings.TARGET_CONTAINER,
                    Strings.TARGET_LOCATION,
                ]
            )
        )

        concat_edges = xr.concat(
            [all_edges.s, all_edges.t, all_edges.tr], dim=Strings.EDGE
        ).transpose(Strings.EDGE, Strings.NODE)

        edges = concat_edges.reset_index(Strings.EDGE).reset_coords(
            names=[
                Strings.SOURCE_CONTAINER,
                Strings.SOURCE_LOCATION,
                Strings.TARGET_CONTAINER,
                Strings.TARGET_LOCATION,
            ],
            drop=True,
        )
        edges.name = Strings.EDGES

        if label is not None:
            edges = self.label_edges(edges, label)

        graph_addition = xr.merge([next_source_array, next_target_array]).expand_dims(
            dim={"tick": [self.exec_tick]}
        )
        graph_addition = xr.merge([graph_addition, edges])

        return graph_addition

    def label_edges(self, edges: xr.DataArray, label: str) -> xr.DataArray:
        return xr.concat(
            [
                edges,
                xr.DataArray(
                    [[label] for e in edges],
                    coords={"node": ["label"]},
                    dims=["edge", "node"],
                ),
            ],
            dim="node",
        )


class BaseUpdater:
    """
    Base class with common functionality for updating the sample provenance graph.
    """

    def __init__(self, observer: SampleProvenanceObserver) -> None:
        self.observer = observer
        # self.graph = graph
        # self.exec_tick = exec_tick
        self.logger = logging.getLogger(__name__)
        # self.ureg = ureg

    @abstractmethod
    def update(self, record: ActivityNodeExecution):
        pass


class EmptyContainerUpdater(BaseUpdater):
    """
    Update sample states as a result of an EmptyContainer operation.

    This creates new samples that correspond to the initial_contents of the SampleArray.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def update(self, record: ActivityNodeExecution) -> xr.Dataset:
        # Since this is a no-op, nothing to do but create the nodes for each
        # sample in the sample array.

        parameter_values = record.call.lookup().parameter_value_map()
        samples = parameter_values["samples"]["value"]

        graph_addition = self.observer.time_stamp(samples.to_data_array())

        return graph_addition


class TransferByMapUpdater(BaseUpdater):
    """
    Updater sample states as a result of a TransferByMap operation.

    Each source aliquot has the specified amount removed and put in ALL
    target aliquots, so the resulting graph is bipartite between one tick and
    the next.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def update(self, record: ActivityNodeExecution) -> xr.Dataset:
        # 1. Rename source and target arrays for applying transfer plan
        # 2. Compute concentrations and apply transfer to source and target
        #    next_source_contents:

        parameter_values = record.call.lookup().parameter_value_map()
        # samples = parameter_values["samples"]["value"]

        source_array = parameter_values["source"]["value"].to_data_array()
        target_array = parameter_values["destination"]["value"].to_data_array()
        source_name = parameter_values["source"]["value"].name
        target_name = parameter_values["destination"]["value"].name

        transfer_plan = parameter_values["plan"]["value"].get_map()

        # Modify plan to refer to source_array and target_array
        source_containers = list(set(source_array[Strings.CONTAINER].data))
        target_containers = list(set(target_array[Strings.CONTAINER].data))
        assert len(source_containers) == 1
        assert len(target_containers) == 1
        transfer_plan.coords[Strings.SOURCE_CONTAINER] = transfer_plan.coords[
            Strings.SOURCE_CONTAINER
        ].where(False, source_containers[0])
        transfer_plan.coords[Strings.TARGET_CONTAINER] = transfer_plan.coords[
            Strings.TARGET_CONTAINER
        ].where(False, target_containers[0])

        return self.observer.compute_transfer(source_array, target_array, transfer_plan)


class ProvisionUpdater(BaseUpdater):
    """
    Update sample states as a result of an Provision operation.

    This creates new samples that correspond to the initial_contents of the SampleArray.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def label(self, resource, quantity, units):
        return f"Provision({quantity}, {units}, {resource})@{self.observer.exec_tick}"

    def update(self, record: ActivityNodeExecution) -> xr.Dataset:
        # Since this is a no-op, nothing to do but create the nodes for each
        # sample in the sample array.

        parameter_values = record.call.lookup().parameter_value_map()
        resource = parameter_values["resource"]["value"]
        amount = parameter_values["amount"]["value"]
        destination = parameter_values["destination"]["value"]
        sample_array = self.observer.select_samples_from_graph(
            destination.to_data_array()
        )

        standard_value, standard_units = self.observer.standardize(amount)
        label = self.label(resource, standard_value, standard_units)

        # setup addition to the contents
        new_contents = xr.DataArray(
            [
                [[standard_value] for l in sample_array.location]
                for c in sample_array.container
            ],
            coords={
                Strings.CONTAINER: sample_array.container,
                Strings.LOCATION: sample_array.location,
                Strings.REAGENT: [resource.identity],
            },
            dims=(Strings.CONTAINER, Strings.LOCATION, Strings.REAGENT),
        )

        # update the contents of sample_array with new contents
        if resource.identity in sample_array[Strings.REAGENT]:
            # Need to add the amount to contents
            updated_contents = sample_array.contents + new_contents
        else:
            # Need to concat the reagent to the contents
            updated_contents = xr.concat(
                [sample_array.contents, new_contents],
                dim=Strings.REAGENT,
            )

        # Construct next sample array using updated contents of sample array
        # Create new sample ids for the updated array
        new_samples = [
            [new_sample_id() for l in sample_array.location]
            for c in sample_array.container
        ]

        next_sample_array = xr.Dataset(
            {
                Strings.CONTENTS: updated_contents,
                Strings.SAMPLE_LOCATION: xr.DataArray(
                    new_samples,
                    coords={
                        Strings.CONTAINER: sample_array.container,
                        Strings.LOCATION: sample_array.location,
                    },
                    dims=(Strings.CONTAINER, Strings.LOCATION),
                ),
            },
            coords={
                Strings.SAMPLE: [l for c in new_samples for l in c],
            },
        )

        edges = self.observer.create_persistence_edges(sample_array, next_sample_array)

        labeled_edges = self.observer.label_edges(edges, label)

        # # Set the contents
        # next_sample_array = xr.Dataset(
        #     {
        #         Strings.CONTENTS: updated_contents,
        #         Strings.SAM
        #         **{
        #             k: v
        #             for k, v in sample_array.items()
        #             if k != Strings.CONTENTS
        #         },
        #     }
        # )

        graph_addition = self.observer.time_stamp(
            xr.merge([next_sample_array, labeled_edges])
        )

        return graph_addition


class TransferUpdater(BaseUpdater):
    """
    Update sample states as a result of an Transfer operation.

    This creates new samples that correspond to the initial_contents of the SampleArray.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def label(self, quantity, units):
        return f"Transfer({quantity}, {units})@{self.observer.exec_tick}"

    def update(self, record: ActivityNodeExecution) -> xr.Dataset:
        # Since this is a no-op, nothing to do but create the nodes for each
        # sample in the sample array.

        parameter_values = record.call.lookup().parameter_value_map()
        source = parameter_values["source"]["value"]
        amount = parameter_values["amount"]["value"]
        destination = parameter_values["destination"]["value"]

        standard_value, standard_units = self.observer.standardize(amount)

        label = self.label(standard_value, standard_units)

        source_array = self.observer.select_samples_from_graph(
            source.to_data_array()
        ).reset_coords(drop=True)
        target_array = self.observer.select_samples_from_graph(
            destination.to_data_array()
        ).reset_coords(drop=True)

        assert (
            0 not in source_array.contents.dropna("reagent", how="all").reagent.shape
        ), f"Cannot transfer from source {source.identity} with no contents: {source_array}"

        transfer = self.observer.make_transfer_array(
            source_array, target_array, standard_value
        )

        graph_addition = self.observer.compute_transfer(
            source_array, target_array, transfer, label=label
        )

        return graph_addition


class VortexUpdater(BaseUpdater):
    """
    Update sample states as a result of an Provision operation.

    This creates new samples that correspond to the initial_contents of the SampleArray.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def label(self, quantity, units):
        return f"Vortex()@{self.observer.exec_tick}"

    def update(self, record: ActivityNodeExecution) -> xr.Dataset:
        # Since this is a no-op, nothing to do but create the nodes for each
        # sample in the sample array.

        parameter_values = record.call.lookup().parameter_value_map()
        samples = parameter_values["samples"]["value"]

        series_array = self.observer.select_samples_from_graph(
            samples.to_data_array(), graph=self.observer.graph
        ).reset_coords(drop=True)

        return xr.Dataset()


class SerialDilutionUpdater(BaseUpdater):
    """
    Update sample states as a result of an SerialDilution operation.

    This creates new samples that correspond to the initial_contents of the SampleArray.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def label(self, quantity, units):
        return f"DiluteTransfer({quantity}, {units})@{self.observer.exec_tick}"

    def update(self, record: ActivityNodeExecution) -> xr.Dataset:
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        # source = parameter_value_map["source"]["value"]
        destination = parameter_value_map["destination"]["value"]
        # diluent = parameter_value_map["diluent"]["value"]
        amount = parameter_value_map["amount"]["value"]
        dilution_factor = parameter_value_map["dilution_factor"]["value"]
        # series = parameter_value_map["series"]["value"]
        # coordinates = destination.get_coordinates()
        standard_value, standard_unit = self.observer.standardize(amount)
        standard_value /= dilution_factor

        # source_array = self.observer.select_samples_from_graph(
        #     source.to_data_array()
        # ).reset_coords(drop=True)
        destination_array = destination.to_data_array()
        series_array = self.observer.select_samples_from_graph(
            destination_array, graph=self.observer.graph
        ).reset_coords(drop=True)
        if "sort_order" in destination_array:
            so = destination_array.sort_order.stack(i=destination_array.sort_order.dims)
            so = so.where(so, drop=True).sortby("order")
        else:
            so = destination_array.sample_location.stack(
                i=destination_array.sample_location.dims
            )

        graph_addition = None
        for i in range(len(coordinates) - 1):
            src_coord = so[i].expand_dims([Strings.CONTAINER, Strings.LOCATION])
            tgt_coord = so[i + 1].expand_dims([Strings.CONTAINER, Strings.LOCATION])
            s_coord = series_array.where(src_coord, drop=True)
            t_coord = series_array.where(tgt_coord, drop=True)
            source_array = (
                s_coord.drop("order").drop("i")
                if not graph_addition
                else self.observer.select_samples_from_graph(
                    s_coord, graph=graph_addition
                ).reset_coords(drop=True)
            )
            target_array = (
                t_coord.drop("order").drop("i")
                if not graph_addition
                or not tgt_coord.isin(graph_addition.sample_location).any()
                else self.observer.select_samples_from_graph(
                    t_coord, graph=graph_addition
                ).reset_coords(drop=True)
            )

            assert (
                0
                not in source_array.contents.dropna("reagent", how="all").reagent.shape
            ), f"Cannot transfer from source {src_coord} with no contents: {source_array}"

            transfer = self.observer.make_transfer_array(
                source_array, target_array, standard_value
            )

            label = self.label(standard_value, standard_unit)
            transfer_diff = self.observer.compute_transfer(
                source_array, target_array, transfer, label=label
            )
            graph_addition = (
                transfer_diff
                if not graph_addition
                else self.observer.update_graph(transfer_diff, graph=graph_addition)
            )
            self.observer.exec_tick += 1

        return graph_addition
