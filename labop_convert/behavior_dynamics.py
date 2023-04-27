from labop import ActivityNodeExecution
from labop.primitive_execution import input_parameter_map

class StateTrajectory(object):
    def __init__(self):
        pass

    def advance(self, record: ActivityNodeExecution):
        primitive = record.node.lookup().behavior.lookup()
        call = record.call.lookup()
        inputs = [x for x in call.parameter_values if x.parameter.lookup().property_value.direction == uml.PARAMETER_IN]
        outputs = [x for x in call.parameter_values if x.parameter.lookup().property_value.direction == uml.PARAMETER_OUT]
        input_parameters = input_parameter_map(inputs)
        output_parameters = input_parameter_map(outputs)
        if 'sample_array' in input_parameters:
            sa = input_parameters['sample_array'].to_data_array()
            sample_locs = sa.coords['aliquot'].data

        # m.sel(source_aliquot=0,target_aliquot=0).data

        pass
