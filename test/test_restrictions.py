import unittest
import subprocess
import owl_rdf_utils.restrictions
import os
import pytest


class TestRestrictions(unittest.TestCase):

    def test_bad_restrictions(self):
        ontology_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'paml-bad-restrictions.ttl')
        try:
            owl_rdf_utils.restrictions.main(action='check',
                                            infile=ontology_file_name,
                                            quiet=True)
        except SystemExit as e:
            exit_code = str(e)
            self.assertEqual(exit_code, '1')

    def test_good_restrictions(self):
        ontology_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'paml', 'paml.ttl')
        try:
            owl_rdf_utils.restrictions.main(action='check',
                                            infile=ontology_file_name,
                                            quiet=True,
            )
        except SystemExit as e:
            exit_code = str(e)
            self.assertEqual(exit_code, '0')

    def test_paml_actual(self):
        ontology_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'paml', 'paml.ttl')
        try:
            owl_rdf_utils.restrictions.main(action='check',
                                            infile=ontology_file_name,
                                            quiet=True,
            )
        except SystemExit as e:
            exit_code = str(e)
            self.assertEqual(exit_code, '0')

    def test_uml_actual(self):
        ontology_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'uml-revised.ttl')
        try:
            owl_rdf_utils.restrictions.main(action='check',
                                            infile=ontology_file_name,
                                            quiet=True,
            )
        except SystemExit as e:
            exit_code = str(e)
            self.assertEqual(exit_code, '0')


if __name__ == '__main__':
    unittest.main()
