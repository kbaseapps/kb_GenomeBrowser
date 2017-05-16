# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
import os
from pprint import pprint, pformat
from KBaseReport.KBaseReportClient import KBaseReport
from browse_genome import GenomeBrowserMaker
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
        self.scratch_dir = config['scratch']
        self.workspace_url = config['workspace-url']
        #END_CONSTRUCTOR


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
        print('Initializing browse_genome with genome reference = {}'.format(genome_ref))

        browser = GenomeBrowserMaker(self.callback_url, self.workspace_url, self.scratch_dir)
        browser_data = browser.create_browser_data(ctx, genome_ref)

        pprint(browser_data)

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
