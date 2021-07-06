import os
import posixpath
from sbol_factory import SBOLFactory, UMLFactory
import sbol3
import uml # Note: looks unused, but is used in SBOLFactory
import paml_time as pamlt
import tyto

# Import ontology
__factory__ = SBOLFactory(locals(),
                          posixpath.join(os.path.dirname(os.path.realpath(__file__)), 'paml_time.ttl'),
                          'http://bioprotocols.org/paml-time#')
__umlfactory__ = UMLFactory(__factory__)

# Helper functions
class MalformedInterval(Exception):
    pass

## Start and end time constraints

def startTime(element, interval, units=tyto.OM.second):
    return constrainTimePoint(element, interval, units=units, first=True)

def endTime(element, interval, units=tyto.OM.second):
    return constrainTimePoint(element, interval, units=units, first=False)

def _getUMLInterval(interval, intervalType, units=tyto.OM.second):
    if isinstance(interval, list) and len(interval) == 2:
        min = interval[0]
        max = interval[1]
    elif isinstance(interval, int) or isinstance(interval, float):
        min = interval
        max = interval
    else:
        raise MalformedInterval(f"Cannot constrain time point with interval: {interval}")

    uml_interval = intervalType(
        min=uml.TimeExpression(expr=pamlt.TimeMeasure(expr=sbol3.Measure(min, units))),
        max=uml.TimeExpression(expr=pamlt.TimeMeasure(expr=sbol3.Measure(min, units)))
    )
    return uml_interval

def constrainTimePoint(element : uml.Behavior, interval, units=tyto.OM.second, first=True):
    return timePointExpression(element, _getUMLInterval(interval, uml.TimeInterval, units=units), first=first)

def timePointExpression(element : uml.Behavior, interval : uml.TimeInterval, first=True):
    name = f"{element.identity}_start" if first else  f"{element.identity}_end"
    return uml.TimeConstraint(name, constrained_elements=[element], specification=interval, firstEvent=first)

## Duration Constraints

def duration(element : uml.Behavior, interval, units=tyto.OM.second):
    return constrainDuation(element, interval, units=units)

def constrainDuation(element : uml.Behavior, interval, units=tyto.OM.second):
    return durationExpression(element, _getUMLInterval(interval, uml.DurationInterval, units=units))

def durationExpression(element : uml.Behavior, interval : uml.DurationInterval):
    name = f"{element.identity}_duration"
    return uml.DurationConstraint(name, constrained_elements=[element], specification=interval)

## Allen relations

def binaryDuration(element1 : uml.Behavior, first1 : bool,
                   interval : uml.DurationInterval,
                   element2 : uml.Behavior, first2 : bool):
    name1 = f"{element1.identity}_start" if first1 else  f"{element1.identity}_end"
    name2 = f"{element2.identity}_start" if first2 else  f"{element2.identity}_end"

    return uml.DurationConstraint(
            constrained_elements=[element1, element2],
            specification=interval,
            firstEvent=[first1, first2],
            identity=f"{name1}_{name2}"
        )

def precedes(element1 : uml.Behavior, interval, element2 : uml.Behavior, units=tyto.OM.second):
    return binaryDuration(element1, False,
                          _getUMLInterval(interval, uml.DurationInterval, units=units),
                          element2, True)

## Logical constraints

def And(elements):
    name = "and" #TODO use a more descriptive name
    return AndConstraint(name, constrained_elements=elements)