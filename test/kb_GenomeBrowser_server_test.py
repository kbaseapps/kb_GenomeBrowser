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

        # Upload genomes
        base_gbk_file = "data/streptococcus_pneumoniae_R6_ref.gbff"
        gbk_file = os.path.join(self.scratch, os.path.basename(base_gbk_file))
        shutil.copy(base_gbk_file, gbk_file)
        cls.genome_ref = self.load_genbank_file(gbk_file, 'my_test_genome')
        # get gff file

        # Upload alignments
        base_align_file = "data/at_chr1_wt_rep1_hisat2.bam"
        cls.align_file = os.path.join(self.scratch, os.path.basename(base_align_file))
        shutil.copy(base_align_file, align_file)
        cls.align_ref = self.load_bam_file(cls.align_file, cls.genome_ref, 'my_hisat2_alignment')

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

    def load_bam_file(self, filename, genome_ref, obj_name):
        """
        TODO: this.
        """
        return "1/2/3"

    def load_fasta_file(self, filename, obj_name, contents):
        f = open(filename, 'w')
        f.write(contents)
        f.close()
        assembly_util = AssemblyUtil(self.callback_url)
        assembly_ref = assembly_util.save_assembly_from_fasta({
            'file': {'path': filename},
            'workspace_name': self.getWsName(),
            'assembly_name': obj_name
        })
        return assembly_ref

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
        return genome_ref.get('genome_ref')  # yeah, i know.

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

    def test_browse_genome_app_ok_no_alignments(self):
        ret = self.getImpl().browse_genome_app(self.getContext(), {
            "genome_ref": self.genome_ref,
            "result_workspace_name": self.getWsName()
        })
        self.assertTrue(ret[0]['report_name'].startswith("GenomeBrowser"))
        self.assertTrue(check_reference(ret[0]['report_ref']))
        self.assertEqual(ret[0]['genome_ref'], genome_ref)

    @unittest.skip
    def test_browse_genome_app_ok_with_alignments(self):
        pass

    def test_browse_genome_app_no_ref(self):
        with self.assertRaises(ValueError) as error:
            self.getImpl().browse_genome_app(self.getContext(), None)

    def test_browse_genome_app_bad_ref(self):
        with self.assertRaises(ValueError) as error:
            self.getImpl().browse_genome_app(self.getContext(), {
                "genome_ref": "not_a_genome_ref",
                "result_workspace_name": self.getWsName()
            })

    def test_browse_genome_app_not_genome(self):
        with self.assertRaises(ValueError) as error:
            self.getImpl().browse_genome_app(self.getContext(), {
                "genome_ref": self.getWsName() + "/12345",
                "result_workspace_name": self.getWsName()
            })

    def test_browse_genome_app_no_assembly(self):
        # NEED A GENOME AS WS JSON FILE TO UPLOAD, or unlink (can I do that?) from an assembly
        pass

    @unittest.skip
    def test_browse_genome_app_too_many_assembly(self):
        # NEED A GENONE AND AN EXTRA ASSEMBLY FILE TO LINK.
        fasta_content = """>seq1 something soemthing asdf
agcttttcat
>seq2
agctt
>seq3
agcttttcatgg"""
        assembly_ref = self.load_fasta_file(os.path.join(self.scratch, 'test1.fasta'),
                                            'TestAssembly',
                                            fasta_content)
        pass

    def test_browse_genome_app_gff_fail(self):
        # NEED TO TRIGGER flatfile-to-json.pl FAILURE
        pass

    def test_browse_genome_app_fasta_fail(self):
        # NEED TO TRIGGER prepare-refseqs.pl FAILURE
        pass

    def test_browse_genome_app_bad_ws_name(self):
        with self.assertRaises(ValueError) as error:
            self.getImpl().browse_genome_app(self.getContext(), {
                "genome_ref": "some_genome",
                "result_workspace_name": 123
            })

    def test_browse_genome_app_no_ws_name(self):
        with self.assertRaises(ValueError) as error:
            self.getImpl().browse_genome_app(self.getContext(), {
                "genome_ref": "some_genome",
                "result_workspace_name": None
            })

    @unittest.skip
    def test_build_genome_browser_ok_no_bam(self):
        """
        Test the good cases:
        1. valid genome ref, no alignments
        2. valid gff and fasta files, no alignments
        3. valid gff/fasta, valid bam file(s)
        4. valid gff/fasta, valid alignment refs
        """
        genome_ref = self.
        inputs = [{
            "genome_input": {},
            "alignment_inputs": []
        }, {
            "genome_input": {},
            "alignment_inputs": []
        }]

    @unittest.skip
    def test_build_genome_browser_no_genome(self):
        pass

    @unittest.skip
    def test_build_genome_browser_bad_genome_ref(self):
        pass

    @unittest.skip
    def test_build_genome_browser_bad_genome_files(self):
        pass

    @unittest.skip
    def test_build_genome_browser_bad_bam_file(self):
        pass

    @unittest.skip
    def test_build_genome_browser_bad_alignment_refs(self):
        pass

    @unittest.skip
    def test_build_genome_browser_mix_align_refs_bam_file(self):
        pass

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
