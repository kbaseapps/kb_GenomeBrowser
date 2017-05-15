# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
import os
from Bio import SeqIO
from pprint import pprint, pformat
from KBaseReport.KBaseReportClient import KBaseReport
from GenomeFileUtil.GenomeFileUtilClient import GenomeFileUtil
import re
#END_HEADER


class GenomeBrowser:
    '''
    Module Name:
    GenomeBrowser

    Module Description:
    KBase module: GenomeBrowser
This implements the browse_genome function that sets up files needed for JBrowse to run with a
KBase genome object.
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER
    # Class variables and functions can be defined in this block
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR

        # Any configuration parameters that are important should be parsed and
        # saved in the constructor.
        self.callback_url = os.environ.get('SDK_CALLBACK_URL', None)
        self.shared_folder = config['scratch']
        self.workspace_url = config['workspace-url']

        #END_CONSTRUCTOR
        pass


    def browse_genome(self, ctx, genome_ref):
        """
        :param genome_ref: instance of String
        :returns: instance of type "BrowseGenomeResults" -> structure:
           parameter "report_name" of String, parameter "report_ref" of
           String, parameter "genome_ref" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN browse_genome
        print('Initializing browse_genome with params=')
        pprint(params)

        # STEP 1: parameter checking
        # make sure that genome_ref is an object reference, and its a genome, and we have
        # permission to it.
        if not genome_ref:
            raise ValueError('genome_ref parameter is required')
        obj_ref_regex = re.compile('^(?P<wsid>\d+)\/(?P<objid>\d+)(\/(?P<ver>\d+))?$')
        if not obj_ref_regex.match(genome_ref):
            raise ValueError('genome_ref must be an object reference of the format ws/oid or ws/oid/ver')
        # TODO: test if genome ref is a genome type

        # STEP 2: genome_to_gff
        # get the genome as a local gff file
        gfu = GenomeFileUtil(self.callback_url)
        results = gfu.genome_to_gff({ 'genome_ref': genome_ref })

        pprint(results)


        # STEP 3: run jbrowse conversion scripts
        #

        # STEP 4: generate the report
        returnVal = {
            'report_name': 'gb_report',
            'report_ref': '11/22/33',
            'genome_ref': genome_ref
        }

        #END browse_genome

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method browse_genome return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
