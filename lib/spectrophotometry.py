import sbol3
import paml

#############################################
# Set up the document
doc = sbol3.Document()
LIBRARY_NAME = 'spectrophotometry'
sbol3.set_namespace('https://bioprotocols.org/paml/primitives/'+LIBRARY_NAME)


#############################################
# Create the primitives
print('Making primitives for '+LIBRARY_NAME)

p = paml.Primitive('MeasureAbsorbance')
p.description = 'Measure absorbance at a given wavelength from a set of samples'
p.add_input('samples', 'http://bioprotocols.org/paml#LocatedSamples')
p.add_input('wavelength', sbol3.OM_MEASURE)
p.add_input('numFlashes', 'http://www.w3.org/2001/XMLSchema#integer', True)
p.add_output('measurements', 'http://bioprotocols.org/paml#LocatedData')
doc.add(p)

p = paml.Primitive('MeasureFluorescence')
p.description = 'Measure fluorescence intensity from a set of samples stimulated by a given wavelength, with an optional bandpass or lowpass filter'
p.add_input('samples', 'http://bioprotocols.org/paml#LocatedSamples')
p.add_input('excitationWavelength', sbol3.OM_MEASURE)
p.add_input('emissionBandpassWavelength', sbol3.OM_MEASURE)
p.add_input('emissionBandpassWidth', sbol3.OM_MEASURE) # measured in total range, e.g., 450nm wavelength, 50nm width = 425nm - 475nm
p.add_input('emissionLowpassCutoff', sbol3.OM_MEASURE) # e.g., 750LP
p.add_input('numFlashes', 'http://www.w3.org/2001/XMLSchema#integer', True)
p.add_input('gain', 'http://www.w3.org/2001/XMLSchema#double', True)
p.add_output('measurements', 'http://bioprotocols.org/paml#LocatedData')
doc.add(p)

p = paml.Primitive('MeasureFluorescenceSpectrum')
p.description = 'Measure fluorescence spectrum from a set of samples stimulated by a given wavelength'
p.add_input('samples', 'http://bioprotocols.org/paml#LocatedSamples')
p.add_input('excitationWavelength', sbol3.OM_MEASURE)
p.add_input('numFlashes', 'http://www.w3.org/2001/XMLSchema#integer', True)
p.add_input('gain', 'http://www.w3.org/2001/XMLSchema#double', True)
p.add_output('measurements', 'http://bioprotocols.org/paml#LocatedData')
doc.add(p)

# Consider adding Measure[Color]Fluorescence as SubProtocols that hardwire standard wavelengths

print('Library construction complete')
print('Validating library')
for e in doc.validate().errors: print(e);
for w in doc.validate().warnings: print(w);

filename = LIBRARY_NAME+'.ttl'
doc.write(filename,'turtle')
print('Library written as '+filename)
