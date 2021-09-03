package owlet;

import java.lang.Throwable;
import java.io.File;
import java.io.IOException;
import java.io.FileNotFoundException;
import java.net.UnknownHostException;
import java.util.HashSet;
import java.util.Set;
import java.util.Map;
import java.util.logging.Logger;
import java.util.logging.Level;

import org.semanticweb.HermiT.ReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.IRI;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.io.OWLParser;
import org.semanticweb.owlapi.model.OWLDataFactory;
import org.semanticweb.owlapi.model.OWLDataProperty;
import org.semanticweb.owlapi.model.OWLEntity;
import org.semanticweb.owlapi.model.OWLIndividual;
import org.semanticweb.owlapi.model.OWLNamedIndividual;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyLoaderConfiguration;
import org.semanticweb.owlapi.io.FileDocumentSource;
import org.semanticweb.owlapi.io.OWLParserException;
import org.semanticweb.owlapi.model.OWLOntologyCreationException;
import org.semanticweb.owlapi.io.OWLOntologyCreationIOException;
import org.semanticweb.owlapi.model.UnloadableImportException;
import org.semanticweb.owlapi.io.UnparsableOntologyException;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.reasoner.ConsoleProgressMonitor;
import org.semanticweb.owlapi.reasoner.InferenceType;
import org.semanticweb.owlapi.reasoner.NodeSet;
import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.semanticweb.owlapi.reasoner.OWLReasonerConfiguration;
import org.semanticweb.owlapi.reasoner.OWLReasonerFactory;
import org.semanticweb.owlapi.reasoner.SimpleConfiguration;
import org.semanticweb.owlapi.search.EntitySearcher;
import org.semanticweb.owlapi.util.DefaultPrefixManager;
import uk.ac.manchester.cs.owl.owlapi.OWLDataPropertyImpl;
import uk.ac.manchester.cs.owl.owlapi.OWLObjectPropertyImpl;

/**
 * Example of use of OWL-API 4.x and the HermiT reasoner.
 * Realized with Gradle and Java 8.
 * 
 * Semantic Web course, Politecnico di Torino, Italy
 * 
 * @author Luigi De Russis, Politecnico di Torino,
 *         <a href="https://elite.polito.it">e-Lite</a> group
 * @version 1.0 (2017-02-22)
 *
 */
public class App
{
    public boolean validateOntology(String ontologyPath, OWLOntologyLoaderConfiguration config) throws Exception {
        Logger logger = Logger.getLogger(App.class.getName());
        logger.setLevel(Level.INFO);
        logger.log(Level.INFO, "[OntologyValidator::validateOntology] BEGIN");
        boolean result = false;
        try {

            OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
            File file = new File(ontologyPath);
            FileDocumentSource source = new FileDocumentSource(file);
            OWLOntology localont = manager.loadOntologyFromOntologyDocument(source, config);
            String ontologyUri = localont.getOntologyID().getOntologyIRI().toString();
            logger.log(Level.INFO, "[OntologyValidator::validateOntology] Loaded ontology with URI: " + ontologyUri);
            IRI documentIRI = manager.getOntologyDocumentIRI(localont);
            logger.log(Level.INFO, "[OntologyValidator::validateOntology] Artefact: " + documentIRI);
            result = true;
            
            // get and configure a reasoner (HermiT)
            OWLReasonerFactory reasonerFactory = new ReasonerFactory();
            ConsoleProgressMonitor progressMonitor = new ConsoleProgressMonitor();
            OWLReasonerConfiguration reasoner_config = new SimpleConfiguration(progressMonitor);
    
            // create the reasoner instance, classify and compute inferences
            OWLReasoner reasoner = reasonerFactory.createReasoner(localont, reasoner_config);
            if (!reasoner.isConsistent())
                 return false;
        } catch (OWLOntologyCreationIOException e) {
            Throwable ioException = e.getCause();
            if (ioException instanceof FileNotFoundException) {
                logger.log(Level.SEVERE, "[OntologyValidator::validateOntology] Could not load ontology. File not found: " + ioException.getMessage());
            } else if (ioException instanceof UnknownHostException) {
                logger.log(Level.SEVERE, "[OntologyValidator::validateOntology] Could not load ontology. Unknown host: " + ioException.getMessage());
            } else {
                logger.log(Level.SEVERE, "[OntologyValidator::validateOntology] Could not load ontology: " + ioException.getClass().getSimpleName() + " " + ioException.getMessage());
            }
            throw e;
        } catch (UnparsableOntologyException e) {
            logger.log(Level.SEVERE, "[OntologyValidator::validateOntology] Could not parse the ontology: " + e.getMessage());
            Map<OWLParser, OWLParserException> exceptions = e.getExceptions();
            for (OWLParser parser : exceptions.keySet()) {
                logger.log(Level.SEVERE, "Tried to parse the ontology with the " + parser.getClass().getSimpleName() + " parser");
                logger.log(Level.SEVERE, "Failed because: " + exceptions.get(parser).getMessage());
            }
            throw e;
        } catch (UnloadableImportException e) {
            logger.log(Level.SEVERE, "[OntologyValidator::validateOntology] Could not load import: " + e.getImportsDeclaration());
            OWLOntologyCreationException cause = e.getOntologyCreationException();
            logger.log(Level.SEVERE, "Reason: " + cause.getMessage());
            throw e;
        } catch (OWLOntologyCreationException e) {
            logger.log(Level.SEVERE, "[OntologyValidator::validateOntology] Could not load ontology: " + e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.log(Level.SEVERE, "[OntologyValidator::validateOntology] Ontology validation unsuccessful. Check ontology and parameters in input.", e);
            throw e;
        }
        logger.log(Level.INFO, "[OntologyValidator::validateOntology] END");
        return result;
    }
	
}
