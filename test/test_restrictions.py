import unittest
import subprocess
import owl_rdf_utils.restrictions
import os


class TestRestrictions(unittest.TestCase):

    def test_bad_restrictions(self):
        ontology_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'labop-bad-restrictions.ttl')
        try:
            owl_rdf_utils.restrictions.main(action='check',
                                            infile=ontology_file_name,
                                            quiet=True)
        except SystemExit as e:
            exit_code = str(e)
            self.assertEqual(exit_code, '1')

    def test_good_restrictions(self):
        ontology_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'labop', 'labop.ttl')
        try:
            owl_rdf_utils.restrictions.main(action='check',
                                            infile=ontology_file_name,
                                            quiet=True,
            )
        except SystemExit as e:
            exit_code = str(e)
            self.assertEqual(exit_code, '0')

    def test_labop_actual(self):
        ontology_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'labop', 'labop.ttl')
        try:
            owl_rdf_utils.restrictions.main(action='check',
                                            infile=ontology_file_name,
                                            quiet=True,
            )
        except SystemExit as e:
            exit_code = str(e)
            self.assertEqual(exit_code, '0')

    def test_labop_time_actual(self):
        ontology_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'labop_time', 'labop_time.ttl')
        try:
            owl_rdf_utils.restrictions.main(action='check',
                                            infile=ontology_file_name,
                                            quiet=True,
            )
        except SystemExit as e:
            exit_code = str(e)
            self.assertEqual(exit_code, '0')


    def test_uml_actual(self):
        ontology_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'uml', 'uml.ttl')
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
