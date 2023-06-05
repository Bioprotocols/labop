# DESCRIPTION
The `multicolor-particle-calibration.py` script uses the LabOP Python API to generate a multicolor calibration protocol and subsequently
convert it into any of a number of supported conversion formats. This protocol provides a good ex-
ample for demonstrating how LabOP enables interoperability between different laboratory execution
environments. It was developed for the [iGEM interlaboratory reproducibility studies](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0199432), and, to date,
has been performed using both manual and robotic methods in hundreds of labs.

The multicolor particle calibration protocol is used for evaluating the reproducibility of
absorbance and flurescence measurements across different laboratories. The protocol begins with 
preparation of standard solutions using four different calibrants: fluorescein, sulforhodamine,
cascade blue, and colloidal silica. The calibrants are then serially diluted into a 96-well plate.
Finally, absorbance and fluorescence measurements are performed.

Running with the `-g` switch will generate the LabOP source for the calibration protocol. This
option will execute a sequence of API functions that construct the LabOP representation of the 
protocol. Once the LabOP source is generated, it can be converted to any of the other formats with-
out the need to regenerate it. If, however, the sequence of functions is customized in any way, do
not forget to regenerate the source.

Outputs from the script will be generated in the `artifacts` directory.
 
# USAGE
`multicolor-particle-calibration.py [-h] [-g] [-m] [-a] [-t] [-e]`

# OPTIONAL ARGUMENTS
<pre>
  -h, --help
  -g, --generate-protocol
                        Generate the artifacts/multicolor-particle-calibration-protocol.nt
                        LabOP protocol file.
  -m, --generate-markdown
                        Execute the protocol to generate the artifacts/multicolor-particle-
                        calibration.md Markdown specialization of the LabOP protocol.
  -a, --generate-autoprotocol
                        Execute the protocol to generate the artifacts/multicolor-particle-
                        calibration-autoprotocol.json Autoprotocol specialization of the LabOP
                        protocol.
  -t, --test-autoprotocol
                        Submit the artifacts/multicolor-particle-calibration-autoprotocol.json
                        Autoprotocol file to the Strateos run queue.
  -e, --generate-emeraldcloud
                        Execute the protocol to generate the Emerald Cloud notebook at
                        artifacts/multicolor-particle-calibration-emeraldcloud.nb.
</pre>

# INTERFACING WITH CLOUD LAB INVENTORIES

In order to generate a protocol in either Emerald Cloud or Autoprotocol formats, it is necessary
to map the specific reagents and containers that are used by the calibration protocol to specific
instances of these materials as may already exist in the Strateos and Emerald Cloud inventory. The
`resolutions` dictionary maps a LabOP data object to its instance ID as found in the respective 
cloud laboratory's catalog of materials. This map will need to be updated to reflect the materials
available and accessible to an individual under their cloud laboratory user account.  An example
of this mapping is provided below:

```
   resolutions = {
        ddh2o.identity: "Nuclease-free Water",
        pbs.identity: "1x PBS from 10X stock",
        fluorescein.identity: "1x PBS, 10uM Fluorescein",
        silica_beads.identity: "Silica beads 2g/ml 950nm",
    }
```
