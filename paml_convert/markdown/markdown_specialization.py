import logging

import sbol3
import tyto

import paml
import uml
from paml_convert.behavior_specialization import BehaviorSpecialization
from paml_convert.markdown import MarkdownConverter

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


class MarkdownSpecialization(BehaviorSpecialization):
    def __init__(self, out_path) -> None:
        super().__init__()
        self.out_path = out_path
        self.markdown = ""
        self.var_to_entity = {}
        self.markdown_converter = None
        self.markdown_steps = []
        self.doc = None

    def _init_behavior_func_map(self) -> dict:
        return {
            "https://bioprotocols.org/paml/primitives/sample_arrays/EmptyContainer": self.define_container,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Provision": self.provision_container,
            "https://bioprotocols.org/paml/primitives/sample_arrays/PlateCoordinates": self.plate_coordinates,
            "https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance": self.measure_absorbance,
            "https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureFluorescence": self.measure_fluorescence,
            "https://bioprotocols.org/paml/primitives/liquid_handling/SerialDilution": self.serial_dilution,
            "https://bioprotocols.org/paml/primitives/culturing/Culture": self.culture,
            "https://bioprotocols.org/paml/primitives/culturing/Transform": self.transform,
            "https://bioprotocols.org/paml/primitives/culturing/Inoculate": self.inoculate,
            "https://bioprotocols.org/paml/primitives/plate_handling/Incubate": self.incubate
        }

    def on_begin(self):
        if self.execution:
            protocol = self.execution.protocol.lookup()
            self.markdown_converter = MarkdownConverter(protocol.document)
            self.markdown += self.markdown_converter.markdown_header(protocol)
            self.markdown += self._materials_markdown(protocol)
            self.markdown += self._inputs_markdown(self.execution.parameter_values)

    def _inputs_markdown(self, parameter_values):
        markdown = '\n\n## Protocol Inputs:\n'
        for i in parameter_values:
            parameter = i.parameter.lookup()
            if parameter.property_value.direction == uml.PARAMETER_IN:
                markdown += self._parameter_value_markdown(i)
        return markdown

    def _outputs_markdown(self, parameter_values):
        markdown = '\n\n## Protocol Outputs:\n'
        for i in parameter_values:
            parameter = i.parameter.lookup()
            if parameter.property_value.direction == uml.PARAMETER_OUT:
                markdown += self._parameter_value_markdown(i, True)
        return markdown

    def _materials_markdown(self, protocol):
        document_objects = protocol.document.objects
        materials = [x for x in protocol.document.objects if isinstance(x, sbol3.component.Component)]
        markdown = '\n\n## Protocol Materials:\n'
        for item in materials:
            markdown += f"* [{label(item)}]({item.types[0]})\n"
        return markdown

    def _parameter_value_markdown(self, pv : paml.ParameterValue, is_output=False):
        parameter = pv.parameter.lookup().property_value
        value = pv.value.value.lookup() if isinstance(pv.value, uml.LiteralReference) else pv.value.value
        units = tyto.OM.get_term_by_uri(value.unit) if isinstance(value, sbol3.om_unit.Measure) else None
        value = str(f"{value.value} {units}")  if units else str(value)
        if is_output:
            return f"* `{parameter.name}`"
        else:
            return f"* `{parameter.name}` = {value}"

    def _steps_markdown(self):
        markdown = '\n\n## Steps\n'
        for i, step in enumerate(self.markdown_steps):
            markdown += str(i + 1) + '. ' + step + '\n'
        return markdown

    def on_end(self):
        self.markdown += self._outputs_markdown(self.execution.parameter_values)
        self.markdown_steps += [self.reporting_step()]
        self.markdown += self._steps_markdown()
        with open(self.out_path, "w") as f:
            f.write(self.markdown)

    def reporting_step(self):
        output_parameters = []
        for i in self.execution.parameter_values:
            parameter = i.parameter.lookup()
            value = i.value.value
            if parameter.property_value.direction == uml.PARAMETER_OUT:
                output_parameters.append(f"`{parameter.property_value.name}` from `{value}`")
        output_parameters = ", ".join(output_parameters)
        return f"Report values for {output_parameters}."

    def define_container(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        spec = parameter_value_map["specification"]['value']
        samples_var = parameter_value_map["samples"]['value']

        ## Define a container

        l.debug(f"define_container:")
        l.debug(f" specification: {spec}")
        l.debug(f" samples: {samples_var}")

        try:
            possible_container_types = possible_container_types = self.resolve_container_spec(spec)
            containers_str = ",".join([f"\n\t[{c.split('#')[1]}]({c})" for c in possible_container_types])
            self.markdown_steps += [f"Provision a container named `{samples_var.name}` such as: {containers_str}."]
        except Exception as e:
            l.warning(e)
            self.markdown_steps += [f"Provision a container named `{samples_var.name}` meeting specification: {spec.queryString}."]

        return results

    # def provision_container(self, wells: WellGroup, amounts = None, volumes = None, informatics = None) -> Provision:
    def provision_container(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        destination = parameter_value_map["destination"]["value"]
        #dest_wells = self.var_to_entity[destination]
        value = parameter_value_map["amount"]["value"].value
        units = parameter_value_map["amount"]["value"].unit
        units = tyto.OM.get_term_by_uri(units)
        resource = parameter_value_map["resource"]["value"]
        #resource = self.resolutions[resource]
        l.debug(f"provision_container:")
        l.debug(f" destination: {destination}")
        l.debug(f" amount: {value} {units}")
        l.debug(f" resource: {resource}")


        # Get destination coordinates
        coordinates = ''
        if type(destination) is paml.SampleMask:
            coordinates = destination.get_coordinates()
            coordinates = f'({coordinates})'
            destination = destination.source.lookup()

        # Get destination container type
        container_spec = record.document.find(destination.container_type)
        container_class = container_spec.queryString.split(' ')[0]
        container_class = container_class.split(':')[-1]
        #container_str = ContainerOntology.get_term_by_uri(container_class)  # FIXME:  use tyto to get class name
        container_str = container_class
        
        resource_str = f"[{label(resource)}]({resource.types[0]})"
        destination_str = f"{label(destination)}{coordinates}"
        self.markdown_steps += [f"Pipette {value} {units} of {resource_str} into `{destination_str}`."]


        return results

    def plate_coordinates(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]["value"]
        #container = self.var_to_entity[source]
        coords = parameter_value_map["coordinates"]["value"]

        self.var_to_entity[parameter_value_map['samples']["value"]] = coords
        l.debug(f"plate_coordinates:")
        l.debug(f"  source: {source}")
        l.debug(f"  coordinates: {coords}")

        return results

    def measure_absorbance(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        wl = parameter_value_map["wavelength"]["value"]
        wl_units = tyto.OM.get_term_by_uri(wl.unit)
        samples = parameter_value_map["samples"]["value"]
        #wells = self.var_to_entity[samples]
        measurements = parameter_value_map["measurements"]["value"]

        # HACK extract contrainer from well group since we do not have it as input
        container = None #wells[0].container

        l.debug(f"measure_absorbance:")
        l.debug(f"  container: {container}")
        l.debug(f"  samples: {samples}")
        l.debug(f"  wavelength: {wl.value} {wl_units}")

        # Add to markdown

        samples_str = f"`{samples.source.lookup().value.lookup().value.name}({samples.mask})`"
        self.markdown_steps += [f'Make absorbance measurements (named `{measurements}`) of {samples_str} at {wl.value} {wl_units}.']

    def measure_fluorescence(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        excitation = parameter_value_map['excitationWavelength']['value']
        emission = parameter_value_map['emissionWavelength']['value']
        bandpass = parameter_value_map['emissionBandpassWidth']['value'] if 'emissionBandpassWidth' in parameter_value_map else None
        samples = parameter_value_map['samples']['value']
        measurements = parameter_value_map["measurements"]["value"]

        # Lookup sample container to get the container name, and use that
        # as the sample label
        if isinstance(samples, paml.SampleMask):
            # SampleMasks are generated by the PlateCoordinates primitive
            # Their source does not directly reference a SampleArray directly,
            # rather through a LiteralReference and LiteralIdentified
            samples = samples.source.lookup()
        spec = record.document.find(samples.container_type)

        # Provide an informative name for the measurements output
        action = record.node.lookup()
        bandpass_str = ' with {measurement_to_text(bandpass)} bandpass' if bandpass else ''
        if action.name:
            measurements.name = f'{action.name} measurements of {label(samples)}'
            text = f'Measure {action.name} of `{label(samples)}` with excitation wavelength of {measurement_to_text(excitation)} and emission filter of {measurement_to_text(emission)}{bandpass}'
        else:
            measurements.name = f'fluorescence measurements of {label(samples)}'
            text = f'Measure fluorescence of `{label(samples)}` with excitation wavelength of {measurement_to_text(excitation)} and emission filter of {measurement_to_text(emission)}{bandpass}'

        # Add to markdown
        self.markdown_steps += [text]

    def culture(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        inocula = parameter_value_map['inoculum']['value']
        growth_medium = parameter_value_map['growth_medium']['value']
        volume = parameter_value_map['volume']['value']
        volume_scalar = volume.value
        volume_units = tyto.OM.get_term_by_uri(volume.unit)
        duration = parameter_value_map['duration']['value']
        duration_scalar = duration.value
        duration_units = tyto.OM.get_term_by_uri(duration.unit)
        orbital_shake_speed = parameter_value_map['orbital_shake_speed']['value']
        temperature = parameter_value_map['temperature']['value']
        temperature_scalar = temperature.value
        temperature_units = tyto.OM.get_term_by_uri(temperature.unit)
        replicates = parameter_value_map['replicates']['value'] if 'replicates' in parameter_value_map else 1
        container = parameter_value_map['container']['value'] 

        # Generate markdown
        container_str = record.document.find(container.container_type).name 
        text = f'Inoculate `{label(inocula)}` into {volume_scalar} {volume_units} of {growth_medium.name} in {container.name} and grow for {measurement_to_text(duration)} at {measurement_to_text(temperature)} and {orbital_shake_speed.value} rpm.'
        self.markdown_steps += [text]

    def transform(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        host = parameter_value_map['host']['value']
        dna = parameter_value_map['dna']['value']
        medium = parameter_value_map['selection_medium']['value']
        if 'amount' in parameter_value_map:
            amount_measure = parameter_value_map['amount']['value']
            amount_scalar = amount_measure.value
            amount_units = tyto.OM.get_term_by_uri(amount_measure.unit)


        # Instantiate Components to represent transformants and populate
        # these into the output SampleArray
        i_transformant = 1

        # Use a while loop to mint a unique URI for new Components
        UNIQUE_URI = False
        while not UNIQUE_URI:
            try:
                strain = sbol3.Component(f'transformant{i_transformant}',
                                         tyto.NCIT.Organism_Strain,
                                         name=f'{label(host)}+{label(dna)} transformant')
                record.document.add(strain)
                # Populate the output SampleArray with the new strain instances
                #contents[i_dna+1] = strain.identity
                UNIQUE_URI = True
            except:
                i_transformant += 1

        # Populate SampleArray
        transformants = parameter_value_map['transformants']['value']
        transformants.name = strain.name 

        # Add to markdown
        text = f"Transform `{label(dna)}` DNA into `{label(host)}` and plate transformants on {label(medium)}."
        self.markdown_steps += [text]


    def serial_dilution(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        destination = parameter_value_map['destination']['value']
        diluent = parameter_value_map['diluent']['value']
        amount = parameter_value_map['amount']['value']
        dilution_factor = parameter_value_map['dilution_factor']['value']

        # Number of steps in serial dilution is determined by the number of aliquots in the destination SampleArray
        steps = len(destination.get_coordinates())

        # Generate text for destination coordinates
        destination_coordinates = ''
        if isinstance(destination, paml.SampleMask):
            # SampleMasks are generated by the PlateCoordinates primitive
            # Their source does not directly reference a SampleArray directly,
            # rather through a LiteralReference and LiteralIdentified
            destination_coordinates = f'wells ' + ', '.join(destination.get_coordinates()) + ' of '
            destination = destination.source.lookup()

        source_coordinates = ''
        if isinstance(source, paml.SampleMask):
            # SampleMasks are generated by the PlateCoordinates primitive
            # Their source does not directly reference a SampleArray directly,
            # rather through a LiteralReference and LiteralIdentified
            source_coordinates = f'wells ' + ', '.join(source.get_coordinates()) + ' of '
            source = source.source.lookup()

        # Get destination container type
        container_spec = record.document.find(destination.container_type)
        container_class = container_spec.queryString.split(' ')[0]
        container_class = container_class.split(':')[-1]
        #container_str = ContainerOntology.get_term_by_uri(container_class)  # FIXME:  use tyto to get class name
        container_str = container_class

        # Update destination contents

        # Update Markdown
        text = f'Perform a series of {steps} {dilution_factor}-fold dilutions on `{label(source)}` using `{label(diluent)}` as diluent to a final volume of {measurement_to_text(amount)} in {destination_coordinates}{container_str} `{label(container_spec)}`.'

        self.markdown_steps += [text]

    def inoculate(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        destination = parameter_value_map['destination']['value']

        # Generate text for destination coordinates
        destination_coordinates = ''
        if isinstance(destination, paml.SampleMask):
            # SampleMasks are generated by the PlateCoordinates primitive
            # Their source does not directly reference a SampleArray directly,
            # rather through a LiteralReference and LiteralIdentified
            destination_coordinates = f'wells ' + ', '.join(destination.get_coordinates()) + ' of '
            destination = destination.source.lookup()

        # Get destination container type
        container_spec = record.document.find(destination.container_type)
        container_class = container_spec.queryString.split(' ')[0]
        container_class = container_class.split(':')[-1]
        #container_str = ContainerOntology.get_term_by_uri(container_class)  # FIXME:  use tyto to get class name
        container_str = container_class

        text = f'Inoculate {label(source)} in {destination_coordinates}{label(container_spec)} {container_class}'
        self.markdown_steps += [text]

    def incubate(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map['location']['value']
        duration = parameter_value_map['duration']['value']
        temperature = parameter_value_map['temperature']['value']
        shakingFrequency = parameter_value_map['shakingFrequency']['value'] if 'shakingFrequency' in parameter_value_map else None

        shake_str = ' at {shakingFrequency.value}.' if shakingFrequency else ''
        text = f'Incubate `{label(location)}` for {measurement_to_text(duration)} at {measurement_to_text(temperature)} {shake_str}.'

        self.markdown_steps += [text]


def label(obj: sbol3.Identified) -> str:
    return obj.name if obj.name else obj.display_id


def measurement_to_text(measure: sbol3.Measure):
    return f'{measure.value} {tyto.OM.get_term_by_uri(measure.unit)}'
