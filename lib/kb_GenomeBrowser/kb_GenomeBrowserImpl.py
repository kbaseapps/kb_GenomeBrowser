# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
import os
import uuid
from pprint import pprint, pformat
from KBaseReport.KBaseReportClient import KBaseReport
from kb_GenomeBrowser.browse_genome import GenomeBrowserMaker
from kb_GenomeBrowser.util import (
    package_directory,
    check_workspace_name
)
#END_HEADER


class kb_GenomeBrowser:
    '''
    Module Name:
    kb_GenomeBrowser

    Module Description:
    KBase module: kb_GenomeBrowser
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
    GIT_URL = "https://github.com/briehl/kb_GenomeBrowser"
    GIT_COMMIT_HASH = "d4fb2bca2b4aed45bdcecfcfc94f7c2c87100eb7"

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
        pass


    def browse_genome(self, ctx, genome_ref, result_workspace_name):
        """
        Creates a genome browser from the given genome reference. It extracts the reference sequence from the genome
        for one track and uses the genome's feature annotations for the second track. The compiled browser
        is stored in the workspace with name result_workspace_name.
        TODO:
        Add option for BAM alignment file(s).
        Add option for other annotation tracks.
        :param genome_ref: instance of String
        :param result_workspace_name: instance of String
        :returns: instance of type "BrowseGenomeResults" -> structure:
           parameter "report_name" of String, parameter "report_ref" of
           String, parameter "genome_ref" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN browse_genome
        print('Initializing browse_genome with genome reference = {} to be stored in workspace = {}'.format(genome_ref, result_workspace_name))

        if result_workspace_name is None:
            raise ValueError('result_workspace_name must not be None')
        elif check_workspace_name(result_workspace_name, self.workspace_url) is False:
            raise ValueError('result_workspace_name is not a valid workspace!')

        browser = GenomeBrowserMaker(self.callback_url, self.workspace_url, self.scratch_dir)
        browser_data = browser.create_browser_data(ctx, genome_ref)
        pprint(browser_data)

        browser.package_jbrowse_data(browser_data['data_dir'], os.path.join(self.scratch_dir, 'minimal_jbrowse'))
        html_zipped = package_directory(self.callback_url, os.path.join(self.scratch_dir, 'minimal_jbrowse'), 'index.html', 'Packaged genome browser')
        report_params = {
            "message": "Genome Browser for {}".format(genome_ref),
            "direct_html_link_index": 0,
            "html_links": [html_zipped],
            "report_object_name": "GenomeBrowser-" + str(uuid.uuid4()),
            "workspace_name": result_workspace_name
        }

        pprint(report_params)

        kr = KBaseReport(self.callback_url)
        report_output = kr.create_extended_report(report_params)

        # STEP 4: generate the report
        returnVal = {
            'report_name': report_output['name'],
            'report_ref': report_output['ref'],
            'genome_ref': genome_ref
        }
        pprint('DONE')
        pprint(returnVal)
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
