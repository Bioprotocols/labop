# Mapping from PAML libraries to Autoprotocol instructions

## liquid_handling

| autoprotocol | PAML |
| :--- | :--- |
| `provision` | `Provision` |
| `liquid_handle`, `mode=dispense` | `Dispense` |
| `liquid_handle` up one place, down another | `Transfer` |
| `liquid_handle` with a non-empty destination | `TransferInto` |
| `liquid_handle` up & down in one source | `PipetteMix` |

Note: this assumes the internal Strateos operation `DISPENSE` is equivalent to `liquid_handle`, `mode=dispense`

## spectrophotometry
This library handles plate readers and other spectrophotometers

| autoprotocol | PAML |
| :--- | :--- |
| `spectrophotometry`, `mode=absorbance` | `MeasureAbsorbance` |
| `spectrophotometry`, `mode=fluorescence` | `MeasureFluorescence` |
| `spectrophotometry`, new mode |`MeasureFluorescenceSpectrum` |

## plate_handling
| autoprotocol | PAML |
| :--- | :--- |
| `cover` | `Cover` |
| `incubate` | `Incubate` |
| `seal`,flexible mode | `Seal` |
| `seal`,`mode=thermal` | `AdhesiveSeal` |
| `seal`,`mode=adhesive` | `ThermalSeal` |
| `spin` | `Spin` |
| `uncover` | `Uncover` |
| `unseal` | `Unseal` |

## Currently unmapped:

- `acoustic_transfer`
- `flow_cytometry`
- `measure_mass`
- `measure_volume`
- `spectrophotometry`, `mode=luminescence`
- `spectrophotometry`, `mode=shake`

# Operators at strateos not listed in autoprotocol
- `SUPPLY NEW CONTAINER`
- `DISPOSE CONTAINER`

These can likely be handled implicitly based on container use and garbage collection.
