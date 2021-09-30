import os
import tempfile
import unittest
import filecmp
import sbol3
import paml
import tyto
import paml_md


class TestMarkdown(unittest.TestCase):
    def test_markdown(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')

        protocol_execution_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testfiles", "igem_ludox_test_exec.nt")
        doc.read(protocol_execution_file, 'nt')

        execution_id = 'https://bbn.com/scratch/test_execution'
        markdown_file = f"{doc.find(execution_id).protocol.lookup().name}.md"

        markdown = paml_md.MarkdownConverter(doc).convert(execution_id, out=markdown_file)

        ########################################
        # Validate and write the document

        # Checking if files are identical
        # assert filecmp.cmp(markdown_file,'test/testfiles/iGEM_LUDOX_OD_calibration_2018.md')


if __name__ == '__main__':
    unittest.main()
