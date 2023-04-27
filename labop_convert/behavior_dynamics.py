# Core packages
import logging
import typing as tp
import uuid

# 3rd party packages
import xarray as xr

# Project packages
import uml
from labop import ActivityNodeExecution, SampleMap
from labop.data import deserialize_sample_format, serialize_sample_format
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

    def __init__(self) -> None:
        self.graph = None

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.exec_tick = 0
        self.handlers = {
            "https://bioprotocols.org/labop/primitives/liquid_handling/TransferByMap": TransferByMapUpdater,
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmptyContainer": EmptyContainerUpdater,
            "https://bioprotocols.org/labop/primitives/culturing/CulturePlates": CulturePlatesUpdater
        }

    def update(self, record: ActivityNodeExecution) -> None:
        """
        Hook to update the provenance graph after each step of execution.
        """
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
            new_nodes = updater.update(iparams)
            if self.graph:
                self.graph = xr.concat([new_nodes, self.graph], dim="tick")
            else:
                self.graph = new_nodes
            self.exec_tick = updater.exec_tick
        else:
            self.logger.info(
                "Behavior %s is not handled by %s, skipping ...",
                behavior,
                self.__class__,
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


class BaseUpdater:
    """
    Base class with common functionality for updating the sample provenance graph.
    """

    def __init__(self, graph: tp.Optional[xr.Dataset], exec_tick: int) -> None:
        self.graph = graph
        self.exec_tick = exec_tick
        self.logger = logging.getLogger(__name__)

    def create_sample_nodes(self, sarr: xr.Dataset) -> xr.Dataset:
        """Create or return nodes in the sample provenance graph from ``sarr``.

        Matching is based on sample location.
        """
        nodes = []
        for loc in sarr[Strings.LOCATION]:
            if tracked := self.sample_tracked(loc, self.exec_tick):
                self.logger.debug(
                    "Aliquot=%d already tracked", tracked.location.data.item()
                )
                nodes.append(tracked)
                continue

            # For a hash, use the aliquot ID+parents list. The parents list is
            # an empty set since we are creating a new node.
            idx = hash(f"sample_{loc}" + str(self.exec_tick))
            contents = sarr[Strings.CONTENTS].sel({Strings.LOCATION: loc})
            self.logger.debug("Add aliquot %d=%s", idx, contents)
            uuid = xr.DataArray(
                [[idx]],
                dims=["location", "tick"],
                coords={"location": [loc.data], "tick": [self.exec_tick]},
            )
            nodes.append(xr.merge([{"UUID": uuid}, contents]))

        return xr.concat(nodes, dim="location")

    def sample_tracked(
        self, sample: xr.DataArray, tick: int
    ) -> tp.Optional[xr.Dataset]:
        """
        Determine if a sample is currently tracked in the provenance graph.

        Tracking is determined based on the sample's tick+location.
        """
        if self.graph is None:
            return None

        # Can't do these with compound conditions--raises errors if there is
        # more than 1 tick
        match = self.graph.where(
            self.graph.tick == tick,
            drop=True,
        ).where(self.graph.location == sample.location, drop=True)

        # Check any of the variables in the dataset to see if they are empty,
        # meaning no such sample is tracked.
        if match.UUID.size == 0:
            return None

        return match


class EmptyContainerUpdater(BaseUpdater):
    """
    Update sample states as a result of an EmptyContainer operation.

    This creates new samples that correspond to the initial_contents of the SampleArray.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def update(self, iparams: dict) -> xr.Dataset:
        # Since this is a no-op, nothing to do but create the nodes for each
        # sample in the sample array.
        nodes = self.create_sample_nodes(iparams["sample_array"].to_data_array())
        self.exec_tick += 1

        return nodes


class CulturePlatesUpdater(BaseUpdater):
    """
    Update sample states as a result of a CulturePlates operation.

    This creates new samples that correspond to the initial_contents of the SampleArray.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def update(self, iparams: dict) -> xr.Dataset:
        # Since this is a no-op, nothing to do but create the nodes for each
        # sample in the sample array.
        nodes = self.create_sample_nodes(iparams["sample_array"].to_data_array())
        self.exec_tick += 1

        return nodes


class TransferByMapUpdater(BaseUpdater):
    """
    Updater sample states as a result of a TransferByMap operation.

    Each source aliquot has the specified amount removed and put in ALL
    target aliquots, so the resulting graph is bipartite between one tick and
    the next.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def update(self, iparams: dict) -> xr.Dataset:
        # 1. Rename source and target arrays for applying transfer plan
        # 2. Compute concentrations and apply transfer to source and target
        #    next_source_contents:

        source_array = iparams["source"].to_data_array()
        target_array = iparams["destination"].to_data_array()
        source_name = iparams["source"].name
        target_name = iparams["destination"].name
        current_source_nodes = self.create_sample_nodes(source_array)
        current_target_nodes = self.create_sample_nodes(target_array)

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
        transfer_source = source_array.rename(
            {
                Strings.LOCATION: f"{source_name}_location",
                Strings.CONTAINER: f"{source_name}_container",
            }
        )
        transfer_target = target_array.rename(
            {
                Strings.LOCATION: f"{target_name}_location",
                Strings.CONTAINER: f"{target_name}_container",
            }
        )

        # 2.
        # Get concentration of the aliquot contents
        transfer_source[
            Strings.CONCENTRATION
        ] = transfer_source.contents / transfer_source.contents.sum(dim=Strings.REAGENT)

        # Get amount of each aliquot's contents that is transferred
        amount_transferred = transfer_source.concentration * transfer_plan

        # Get total amount transferred to all targets
        next_source_contents = transfer_source.contents - amount_transferred.sum(
            dim=["target_location", "target_container"]
        )
        next_source_contents = next_source_contents.rename(
            {
                f"{source_name}_location": Strings.LOCATION,
                f"{source_name}_container": Strings.CONTAINER,
            }
        )
        next_target_contents = transfer_target.contents + amount_transferred.sum(
            dim=["source_location", "source_container"]
        )
        next_target_contents = next_target_contents.rename(
            {
                f"{target_name}_location": Strings.LOCATION,
                f"{target_name}_container": Strings.CONTAINER,
            }
        )

        transfer_source = transfer_source.assign_coords(
            {Strings.SAMPLE: [
                f"sample_{uuid.uuid1()}" for _ in transfer_source.sample]}
        )

        next_source_sample_ids = [
            [f"sample_{uuid.uuid1()}" for loc in transfer_source.source_location]
            for c in transfer_source.source_container
        ]
        next_source_array = xr.Dataset(
            {
                "sample_location": xr.DataArray(
                    next_source_sample_ids,
                    dims=(Strings.CONTAINER, Strings.LOCATION),
                ),
                "contents": next_source_contents,
            },
            coords={
                Strings.CONTAINER: transfer_source.coords["source_container"].data,
                Strings.LOCATION: transfer_source.coords["source_location"].data,
                Strings.SAMPLE: [s for c in next_source_sample_ids for s in c],
            },
        )

        next_target_sample_ids = [
            [f"sample_{uuid.uuid1()}" for loc in transfer_target.target_location]
            for c in transfer_target.target_container
        ]
        next_target_array = xr.Dataset(
            {
                "sample_location": xr.DataArray(
                    next_target_sample_ids,
                    dims=(Strings.CONTAINER, Strings.LOCATION),
                ),
                "contents": next_target_contents,
            },
            coords={
                Strings.CONTAINER: transfer_target.coords["target_container"].data,
                Strings.LOCATION: transfer_target.coords["target_location"].data,
                Strings.SAMPLE: [s for c in next_target_sample_ids for s in c],
            },
        )

        source_map = xr.merge(
            [
                source_array.sample_location,
                next_source_array.rename(
                    {"sample_location": "next_sample_location"}
                ).next_sample_location,
            ]
        )
        source_edges = (
            source_map.to_array()
            .rename({"variable": "node"})
            .transpose("container", "location", "node")
        ).rename({"container": "source_container", "location": "source_location"})
        source_edges.name = "s"
        target_map = xr.merge(
            [
                target_array.sample_location,
                next_target_array.rename(
                    {"sample_location": "next_sample_location"}
                ).next_sample_location,
            ]
        )
        target_edges = (
            target_map.to_array()
            .rename({"variable": "node"})
            .transpose("container", "location", "node")
        ).rename({"container": "target_container", "location": "target_location"})
        target_edges.name = "t"
        transfer_map = xr.merge(
            [
                transfer_source.sample_location,
                transfer_target.rename(
                    {"sample_location": "next_sample_location"}
                ).next_sample_location,
            ]
        )
        transfer_plan_map = xr.where(transfer_plan > 0, transfer_map, False)
        transfer_edges = (
            transfer_plan_map.to_array().rename({"variable": "node"})
            # .stack(
            #     container=["source_container", "target_container"],
            #     location=["source_location", "target_location"],
            # )
            # .transpose("container", "location", "edge")
            .transpose(
                "source_container",
                "source_location",
                "target_container",
                "target_location",
                "node",
            )
        )
        transfer_edges.name = "tr"

        all_edges = (
            xr.merge([source_edges, target_edges, transfer_edges])
            .transpose(
                "source_container",
                "source_location",
                "target_container",
                "target_location",
                "node",
            )
            .stack(
                edge=[
                    "source_container",
                    "source_location",
                    "target_container",
                    "target_location",
                ]
            )
        )

        concat_edges = xr.concat(
            [all_edges.s, all_edges.t, all_edges.tr], dim="edge"
        ).transpose("edge", "node")

        edges = concat_edges.reset_index("edge").reset_coords(
            names=[
                "source_container",
                "source_location",
                "target_container",
                "target_location",
            ],
            drop=True,
        )
        edges.name = "edges"

        graph_addition = xr.merge(
            [next_source_array, next_target_array, edges]
        ).expand_dims(dim={"tick": [self.exec_tick]})

        # # FIXME add container dimension to result
        # # TODO need sample_location?
        # next_source_nodes = self.create_sample_nodes(next_source_array)

        # For nicer visual representations of graphs, the space is split into
        # two before/after spaces by using different ticks: one for source
        # aliquots and one for target aliquots.
        self.exec_tick += 1

        # # FIXME add container dimension to result
        # next_target_nodes = self.create_sample_nodes(next_target_array)

        # # One-to-one connectivity between the (now) old source nodes and the new
        # # ones: same contents, minus what was transferred out. Same for old/new
        # # target nodes.
        # connectivity1 = xr.Dataset(
        #     {
        #         "connectivity": xr.DataArray(
        #             [
        #                 [l1 in l2 for l1 in current_source_nodes.location.data]
        #                 for l2 in next_source_nodes.location.data
        #             ],
        #             dims=["source", "target"],
        #             coords={
        #                 "source": current_source_nodes.location.rename(
        #                     {"location": "source"}
        #                 ),
        #                 "target": next_source_nodes.location.rename(
        #                     {"location": "target"}
        #                 ),
        #             },
        #         )
        #     }
        # )
        # current_source_nodes.update(connectivity1)

        # connectivity2 = xr.Dataset(
        #     {
        #         "connectivity": xr.DataArray(
        #             [
        #                 [l1 in l2 for l1 in current_target_nodes.location.data]
        #                 for l2 in next_target_nodes.location.data
        #             ],
        #             dims=["source", "target"],
        #             coords={
        #                 "source": current_target_nodes.location.rename(
        #                     {"location": "source"}
        #                 ),
        #                 "target": next_target_nodes.location.rename(
        #                     {"location": "target"}
        #                 ),
        #             },
        #         )
        #     }
        # )
        # current_target_nodes.update(connectivity2)

        # # One-to-many connectivity from each source node to all target nodes.
        # connectivity3 = xr.Dataset(
        #     {
        #         "connectivity": xr.DataArray(
        #             [
        #                 [True for l2 in next_target_nodes.location.data]
        #                 for l1 in next_source_nodes.location
        #             ],
        #             coords={
        #                 "source": current_source_nodes.location.rename(
        #                     {"location": "source"}
        #                 ),
        #                 "target": next_target_nodes.location.rename(
        #                     {"location": "target"}
        #                 ),
        #             },
        #         )
        #     }
        # )
        # current_source_nodes.update(connectivity3)

        # # FIXME return new stuff; nextsource next target, connectivity
        # all_nodes = xr.concat(
        #     [
        #         next_source_nodes,
        #         next_target_nodes,
        #     ],
        #     dim="tick",
        # )

        # self.exec_tick += 1
        return graph_addition
