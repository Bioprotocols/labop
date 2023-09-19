import sbol3
from typing import List
from uml import assign_outer_class_builders
from . import inner


from .utils import *
from .parameter_value import *
from .sample_collection import *
from .activity_edge_flow import *
from .behavior_execution import *
from .call_behavior_execution import *
from .protocol_execution import *
from .activity_node_execution import *

from .primitive import *

from .sample_map import *
from .many_to_one_sample_map import *
from .one_to_many_sample_map import *
from .sample_map import *

from .protocol import *

from .container_spec import *
from .data import *
from .execution_engine import *
from .execution_engine_utils import *
from .lab_interface import *
from .material import *
from .primitive_array import *


from .sample_array import *
from .sample_data import *

from .sample_mask import *
from .sample_metadata import *
from .dataset import *

from .strings import *
from .type_inference import *
from .library import *


#########################################
# Kludge for getting parents and TopLevels - workaround for pySBOL3 issue #234
# TODO: remove after resolution of https://github.com/SynBioDex/pySBOL3/issues/234
def identified_get_parent(self):
    if self.identity:
        return self.document.find(self.identity.rsplit("/", 1)[0])
    else:
        return None


sbol3.Identified.get_parent = identified_get_parent


def identified_get_toplevel(self):
    if isinstance(self, sbol3.TopLevel):
        return self
    else:
        parent = self.get_parent()
        if parent:
            return identified_get_toplevel(parent)
        else:
            return None


sbol3.Identified.get_toplevel = identified_get_toplevel


def where_defined(self) -> List[str]:
    if hasattr(self, "_where_defined"):
        return self._where_defined
    else:
        return ["<location defined unknown>"]


sbol3.Identified.where_defined = where_defined


def __str__(self):
    print(f"{self.type}: self.identity")


for symbol in dir():
    if isinstance(symbol, sbol3.Identified):
        symbol.__str__ = __str__

assign_outer_class_builders(__name__)


def init_logging_config() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        force=True,
    )


def init_logging() -> None:
    # TODO: SBOLFactory permanently disables all DEBUG,INFO logging when it
    # runs. This is a bug tracked in SynbioDex/sbol_factory#77. If that is fixed,
    # this can be removed.
    logging.disable(logging.NOTSET)

    # Set the base logging level. We use force=True to override any other
    # packages/places where a logger was created BEFORE setting this up, and may not
    # have the necessary handlers configured to get stuff to print as a result.
    try:
        import coloredlogs

        coloredlogs.install(
            fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
            level=logging.INFO,
        )
    except ModuleNotFoundError:
        init_logging_config()


# Initialize logging
init_logging()
