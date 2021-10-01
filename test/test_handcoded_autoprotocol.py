import os
import unittest
import json
from autoprotocol.protocol import \
    Spectrophotometry, \
    Protocol, \
    WellGroup, \
    Unit
from autoprotocol import container_type as ctype
from paml_autoprotocol.transcriptic_api import TranscripticAPI

class TestHandcodedAutoprotocol(unittest.TestCase):
    def test_ludox(self):
        out_dir = "."

        # api = TranscripticAPI(out_dir)
        # containers_spec = [
        #     {
        #         "name": "dummy_container_01",
        #         "cont_type": "micro-1.5",
        #         "volume": "1000:microliter",
        #         "properties": [
        #             {
        #                 "key": "concentration",
        #                 "value": "10:millimolar"
        #             }
        #         ]
        #     }
        # ]
        # containers = api.make_containers(containers_spec)

        p = Protocol()
        c = p.ref("test_container", cont_type=ctype.FLAT96, discard=True)

        # PlateCoordinates 1
        wells = []
        for i in range(0, 4):
            for j in range(0, 1):
                wells.append(c.well_from_coordinates(i, j))
        wg1 = WellGroup(wells)
        print (wg1)

        # Amounts 1
        amount1 = Unit(100, "microliter")

        # Provision 1
        p.provision(
            "https://identifiers.org/pubchem.substance:24866361",
            wg1,
            amounts=amount1
        )

        # PlateCoordinates 2
        wells = []
        for i in range(0, 4):
            for j in range(1, 2):
                wells.append(c.well_from_coordinates(i, j))
        wg2 = WellGroup(wells)
        print (wg2)

        # Amounts 2
        amount2 = Unit(100, "microliter")

        # Provision 2
        p.provision(
            "https://identifiers.org/pubchem.substance:24901740",
            wg2,
            amounts=amount2
        )
        
        # PlateCoordinates 3
        wells = []
        for i in range(0, 4):
            for j in range(0, 2):
                wells.append(c.well_from_coordinates(i, j))
        wg3 = WellGroup(wells)
        print (wg3)

        # Wavelength
        wavelength = Unit(600, "nanometre")

        p.spectrophotometry(
            dataref="test data",
            obj=c,
            groups=Spectrophotometry.builders.groups([
                Spectrophotometry.builders.group(
                    "absorbance",
                    Spectrophotometry.builders.absorbance_mode_params(
                        wells=wg3,
                        wavelength=wavelength
                    )
                )
            ])
        )

        with open(os.path.join(out_dir, "test_LUDOX_handcoded_autoprotocol.json"), "w") as f:
            json.dump(p.as_dict(), f, indent=2)

if __name__ == '__main__':
    unittest.main()