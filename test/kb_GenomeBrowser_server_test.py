# -*- coding: utf-8 -*-
import unittest
import os  # noqa: F401
import json  # noqa: F401
import shutil
import time
import requests

from os import environ
try:
    from ConfigParser import ConfigParser  # py2
except:
    from configparser import ConfigParser  # py3

from pprint import pprint  # noqa: F401

from biokbase.workspace.client import Workspace as workspaceService
from kb_GenomeBrowser.kb_GenomeBrowserImpl import kb_GenomeBrowser
from kb_GenomeBrowser.kb_GenomeBrowserServer import MethodContext
from kb_GenomeBrowser.authclient import KBaseAuth as _KBaseAuth

from AssemblyUtil.AssemblyUtilClient import AssemblyUtil
from GenomeFileUtil.GenomeFileUtilClient import GenomeFileUtil

from kb_GenomeBrowser.util import (
    check_reference,
    check_reference_type,
    check_workspace_name,
    package_directory
)


class GenomeBrowserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_GenomeBrowser'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_GenomeBrowser',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = workspaceService(cls.wsURL)
        cls.serviceImpl = kb_GenomeBrowser(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        if hasattr(self.__class__, 'wsName'):
            return self.__class__.wsName
        suffix = int(time.time() * 1000)
        wsName = "test_GenomeBrowser_" + str(suffix)
        ret = self.getWsClient().create_workspace({'workspace': wsName})  # noqa
        self.__class__.wsName = wsName
        return wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    # # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    # def load_fasta_file(self, filename, obj_name, contents):
    #     f = open(filename, 'w')
    #     f.write(contents)
    #     f.close()
    #     assemblyUtil = AssemblyUtil(self.callback_url)
    #     assembly_ref = assemblyUtil.save_assembly_from_fasta({'file': {'path': filename},
    #                                                           'workspace_name': self.getWsName(),
    #                                                           'assembly_name': obj_name
    #                                                           })
    #     return assembly_ref

    def load_genbank_file(self, local_file, target_name):
        gfu = GenomeFileUtil(self.callback_url)
        genome_ref = gfu.genbank_to_genome({
            "file": {
                "path": local_file
            },
            "genome_name": target_name,
            "workspace_name": self.getWsName(),
            "source": "RefSeq",
            "release": "NC_003098.1",
            "genetic_code": 11,
            "type": "User upload"
        })
        return genome_ref.get('genome_ref') # yeah, i know.


    # /*
    # genome_name - becomes the name of the object
    # workspace_name - the name of the workspace it gets saved to.
    # source - Source of the file typically something like RefSeq or Ensembl
    # taxon_ws_name - where the reference taxons are : ReferenceTaxons
    # taxon_reference - if defined, will try to link the Genome to the specified
    #     taxonomy object insteas of performing the lookup during upload
    # release - Release or version number of the data
    #       per example Ensembl has numbered releases of all their data: Release 31
    # generate_ids_if_needed - If field used for feature id is not there,
    #       generate ids (default behavior is raising an exception)
    # genetic_code - Genetic code of organism. Overwrites determined GC from
    #       taxon object
    # type - Reference, Representative or User upload
    #
    # */
    # typedef structure {
    #     File file;
    #
    #     string genome_name;
    #     string workspace_name;
    #
    #     string source;
    #     string taxon_wsname;
    #     string taxon_reference;
    #
    #     string release;
    #     string generate_ids_if_needed;
    #     int    genetic_code;
    #     string type;
    #     usermeta metadata;
    # } GenbankToGenomeParams;

    def test_browse_genome_ok(self):
        base_gbk_file = "data/streptococcus_pneumoniae_R6_ref.gbff"
        gbk_file = os.path.join(self.scratch, os.path.basename(base_gbk_file))
        shutil.copy(base_gbk_file, gbk_file)
        genome_ref = self.load_genbank_file(gbk_file, 'my_test_genome')

        ret = self.getImpl().browse_genome(self.getContext(), genome_ref, self.getWsName())
        self.assertTrue(ret[0]['report_name'].startswith("GenomeBrowser"))
        self.assertTrue(check_reference(ret[0]['report_ref']))
        self.assertEqual(ret[0]['genome_ref'], genome_ref)

    def test_browse_genome_no_ref(self):
        with self.assertRaises(ValueError) as error:
            self.getImpl().browse_genome(self.getContext(), None, None)

    def test_browse_genome_bad_ref(self):
        with self.assertRaises(ValueError) as error:
            self.getImpl().browse_genome(self.getContext(), 'not_a_genome_ref', self.getWsName())

    def test_browse_genome_not_genome(self):
        pass

    def test_browse_genome_no_assembly(self):
        pass

    def test_browse_genome_too_many_assembly(self):
        pass

    def test_browse_genome_gff_fail(self):
        pass

    def test_browse_genome_fasta_fail(self):
        pass

    def test_browse_genome_bad_ws_name(self):
        with self.assertRaises(ValueError) as error:
            self.getImpl().browse_genome(self.getContext(), 'some_genome', 123)

    def test_browse_genome_no_ws_name(self):
        with self.assertRaises(ValueError) as error:
            self.getImpl().browse_genome(self.getContext(), 'some_genome', None)

    def test_check_ref(self):
        good_refs = [
            '11/22/33', '11/22', '11/22/33;44/55', '11/22;44/55', '11/22;44/55/66'
        ]
        bad_refs = [
            'not_a_ref', '1', '11/', '11/22/', '11/22;'
        ]
        for ref in good_refs:
            self.assertTrue(check_reference(ref))
        for ref in bad_refs:
            self.assertFalse(check_reference(ref))

    def test_check_ref_type(self):
        pass

    def test_package_directory(self):
        pass

    def test_check_workspace_name(self):
        good_names = [
            self.getWsName()
        ]
        bad_names = [
            None, 'foobar', '123', 456
        ]
        for name in good_names:
            self.assertTrue(check_workspace_name(name, self.wsURL))
        for name in bad_names:
            self.assertFalse(check_workspace_name(name, self.wsURL))



    # # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    # def test_filter_contigs_ok(self):
    #
    #     # First load a test FASTA file as an KBase Assembly
    #     fasta_content = '>seq1 something soemthing asdf\n' \
    #                     'agcttttcat\n' \
    #                     '>seq2\n' \
    #                     'agctt\n' \
    #                     '>seq3\n' \
    #                     'agcttttcatgg'
    #
    #     assembly_ref = self.load_fasta_file(os.path.join(self.scratch, 'test1.fasta'),
    #                                         'TestAssembly',
    #                                         fasta_content)
    #
    #     # Second, call your implementation
    #     ret = self.getImpl().filter_contigs(self.getContext(),
    #                                         {'workspace_name': self.getWsName(),
    #                                          'assembly_input_ref': assembly_ref,
    #                                          'min_length': 10
    #                                          })
    #
    #     # Validate the returned data
    #     self.assertEqual(ret[0]['n_initial_contigs'], 3)
    #     self.assertEqual(ret[0]['n_contigs_removed'], 1)
    #     self.assertEqual(ret[0]['n_contigs_remaining'], 2)
    #
    # def test_filter_contigs_err1(self):
    #     with self.assertRaises(ValueError) as errorContext:
    #         self.getImpl().filter_contigs(self.getContext(),
    #                                       {'workspace_name': self.getWsName(),
    #                                        'assembly_input_ref': '1/fake/3',
    #                                        'min_length': '-10'})
    #     self.assertIn('min_length parameter cannot be negative', str(errorContext.exception))
    #
    # def test_filter_contigs_err2(self):
    #     with self.assertRaises(ValueError) as errorContext:
    #         self.getImpl().filter_contigs(self.getContext(),
    #                                       {'workspace_name': self.getWsName(),
    #                                        'assembly_input_ref': '1/fake/3',
    #                                        'min_length': 'ten'})
    #     self.assertIn('Cannot parse integer from min_length parameter', str(errorContext.exception))
