# Mapping from PAML libraries to Autoprotocol instructions

## liquid_handling

| autoprotocol | PAML |
| :--- | :--- |
| `provision` | `Provision` |
| `liquid_handle`, `mode=dispense` | `Dispense` |
| `liquid_handle` up one place, down another | `Transfer` |
| `liquid_handle` up & down in one source | `PipetteMix` |

Note: this assumes the internal Strateos operation `DISPENSE` is equivalent to `liquid_handle`, `mode=dispense`

## spectrophotometry
This library handles plate readers and other spectrophotometers

| autoprotocol | PAML |
| :--- | :--- |
| `spectrophotometry`, `mode=absorbance` | `MeasureAbsorbance` |
| `spectrophotometry`, `mode=fluorescence` | `MeasureFluorescence` |

## plate_handling
| autoprotocol | PAML |
| :--- | :--- |
| `cover` | `Cover` |
| `incubate` | `Incubate` |
| `seal` | `Seal` |
| `uncover` | `Uncover` |
| `unseal` | `Unseal` |

## Currently unmapped:

- `acoustic_transfer`
- `flow_cytometry`
- `measure_mass`
- `measure_volume`
- `spectrophotometry`, `mode=luminescence`
- `spectrophotometry`, `mode=shake`
- `spin`

# Operators at strateos not listed in autoprotocol
- `SUPPLY NEW CONTAINER`
- `DISPOSE CONTAINER`

These can likely be handled implicitly based on container use and garbage collection.
