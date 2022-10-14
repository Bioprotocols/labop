# import paml
# from paml.lib.library_type_inference import primitive_type_inference_functions
#
# ##############################
# # Class for carrying a typing process
#
#
# class ProtocolTyping:
#     def __init__(self):
#         self.flow_values = {}  # dictionary of paml.Flow : type value, includes subprotocols too
#         self.typed_protocols = set()  # protocol and subprotocols already evaluated or in process of evaluation
#         self.cache = {} # kludge for accelerating inflow satisfaction computation
#
#     def infer_typing(self, protocol : paml.Protocol):
#         self.typed_protocols.add(protocol)
#         pending_activities = set(protocol.activities)
#         print('Building activity cache non-blocked')
#         self.cache.update({a:a.input_flows() for a in pending_activities}) # speed kludge
#         while pending_activities:
#             print('Collecting non-blocked activities out of pending '+str(len(pending_activities)))
#             non_blocked = {a for a in pending_activities if self.inflows_satisfied(a)}
#             if not non_blocked:
#                 raise ValueError("Could not infer all flow types in "+protocol.identity+": circular dependency?")
#             for activity in non_blocked:
#                 print('Inferring typing for '+activity.identity)
#                 activity.infer_typing(self)
#             pending_activities -= non_blocked
#
#     def inflows_satisfied(self, activity):
#         #unsatisfied = {flow for flow in activity.input_flows() if flow not in self.flow_values.keys()}
#         unsatisfied = {flow for flow in self.cache[activity] if flow not in self.flow_values.keys()}
#         return len(unsatisfied) == 0
#
#
# #############################
# # Inference utilities
#
# def pin_input_type(self, typing: ProtocolTyping):
#     try:
#         return self.value
#     except AttributeError:
#         in_flows = self.input_flows()
#         assert len(in_flows) == 1, \
#             ValueError("Expected one input flow for '" + self.get_parent().identity + "' but found " + len(in_flows))
#         return typing.flow_values[in_flows.pop()]
# paml.Pin.input_type = pin_input_type
#
#
# def pin_assert_output_type(self, typing: ProtocolTyping, value):
#     out_flows = self.output_flows()
#     # TODO: need to decide if this type of implicit fork is acceptable
#     for f in out_flows:
#         typing.flow_values[f] = value
#     # assert len(out_flows) == 1, \
#     #     ValueError("Expected one output flow for '" + self.get_parent().identity + "' but found " + str(len(out_flows)))
#     # typing.flow_values[out_flows.pop()] = value
# paml.Pin.assert_output_type = pin_assert_output_type
#
#
# #############################
# # Inference over Activities
# def initial_infer_typing(self, typing: ProtocolTyping):
#     typing.flow_values.update({f: None for f in self.direct_output_flows()})
# paml.Initial.infer_typing = initial_infer_typing
#
#
# def final_infer_typing(self, _: ProtocolTyping):
#     assert len(self.direct_output_flows()) == 0  # should be no outputs
# paml.Final.infer_typing = final_infer_typing
#
#
# def fork_decision_infer_typing(self, typing: ProtocolTyping):
#     assert len(self.direct_input_flows()) == 1  # should be precisely one input
#     in_type = typing.flow_values[self.direct_input_flows().pop()]
#     typing.flow_values.update({f: in_type for f in self.direct_output_flows()})
# paml.Fork.infer_typing = fork_decision_infer_typing
# paml.Decision.infer_typing = fork_decision_infer_typing
#
#
# def join_infer_typing(self, typing: ProtocolTyping):
#     #assert len(self.direct_output_flows()) == 1  # should be precisely one output
#     value = join_values({typing.flow_values[f] for f in self.direct_input_flows()})
#     typing.flow_values.update({f: value for f in self.direct_output_flows()})
# paml.Join.infer_typing = join_infer_typing
#
# # TODO: add type inference for Merge
#
#
# def primitiveexecutable_infer_typing(self, typing: ProtocolTyping):
#     typing.flow_values.update({f: None for f in self.direct_output_flows()})
#     inference_function = primitive_type_inference_functions[self.instance_of.lookup().identity]
#     inference_function(self, typing)
# paml.PrimitiveExecutable.infer_typing = primitiveexecutable_infer_typing
#
# # TODO: add type inference for SubProtocol
# def subprotocol_infer_typing(self: paml.SubProtocol, typing: ProtocolTyping):
#     typing.flow_values.update({f: None for f in self.direct_output_flows()})
#     subprotocol = self.instance_of.lookup()
#     if subprotocol not in typing.typed_protocols:
#         # add types for inputs
#         input_pin_flows = self.input_flows() - self.direct_input_flows()
#         for f in input_pin_flows:
#             typing.flow_values.update({subflow: typing.flow_values[f] for subflow in subprotocol.get_input(f.sink.lookup().name).activity.lookup().direct_output_flows()})
#         # run the actual inference
#         typing.infer_typing(subprotocol)
#     # pull values from outputs' inferred values
#     output_pin_flows = self.output_flows() - self.direct_output_flows()
#     for f in output_pin_flows:
#         typing.flow_values.update({subflow: typing.flow_values[f] for subflow in subprotocol.get_output(f.source.lookup().name).activity.lookup().direct_input_flows()})
# paml.SubProtocol.infer_typing = subprotocol_infer_typing
#
#
# def type_to_value(type_name: str, **kwargs):
#     if type_name == 'http://bioprotocols.org/paml#LocatedSamples':
#         return paml.LocatedSamples(**kwargs)
#     elif type_name == 'http://bioprotocols.org/paml#LocatedData':
#         return paml.LocatedData(**kwargs)
#     else:
#         ValueError("Don't know how to make dummy object for type "+type_name)
#
#
# def value_infer_typing(self: paml.Value, typing: ProtocolTyping):
#     # assert len(self.direct_output_flows()) == 1  # should be precisely one output --- or maybe not. TODO: decide
#     output_instance = (type_to_value(self.type, name=self.name) if self.type else None)
#     # Don't overwrite values that are already written
#     unset_values = {f for f in self.direct_output_flows() if f not in typing.flow_values.keys()}
#     typing.flow_values.update({f: output_instance for f in unset_values})
# paml.Value.infer_typing = value_infer_typing
#
#
#
# #################
# # Join is a kludge for now
# # TODO: Make a more principled approach to inference of Join, which will also provide an architcture for Merge
# def join_locations(value_set):
#     if not value_set:
#         return paml.HeterogeneousSamples()
#     next_value = value_set.pop()
#     rest = join_locations(value_set)
#     if isinstance(next_value, paml.ReplicateSamples):
#         rest.replicate_samples.append(next_value)
#     elif isinstance(next_value, paml.HeterogeneousSamples):
#         for x in next_value.replicate_samples:
#             rest.replicate_samples.append(x)
#     else:
#         raise ValueError("Don't know how to join locations for "+str(value_set))
#     return rest
#
# def join_values(value_set):
#     if all(isinstance(x,paml.LocatedSamples) for x in value_set):
#         return join_locations(value_set)
#     elif all(x is None for x in value_set):
#         return None
#     # if we fall through to the end, then we didn't know how to infer
#     raise ValueError("Don't know how to join values types for "+str(value_set))
#
#
#
#
