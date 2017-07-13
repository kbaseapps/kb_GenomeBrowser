# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
from __future__ import print_function
import os
import uuid
from pprint import pprint, pformat
from KBaseReport.KBaseReportClient import KBaseReport
from kb_GenomeBrowser.browse_genome import GenomeBrowserMaker
from kb_GenomeBrowser.util import (
    package_directory,
    check_workspace_name,
    check_build_genome_browser_parameters
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
    GIT_COMMIT_HASH = "47f8acdc48c7aba6278ad669bb44cea2500621f5"

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

    def browse_genome_app(self, ctx, params):
        """
        Creates a genome browser from the given genome reference. It extracts the reference sequence from the genome
        for one track and uses the genome's feature annotations for the second track. The compiled browser
        is stored in the workspace with name result_workspace_name.
        TODO:
        Add option for BAM alignment file(s).
        Add option for other annotation tracks.
        :param params: instance of type "BrowseGenomeParams" -> structure:
           parameter "genome_ref" of String, parameter
           "result_workspace_name" of String, parameter "alignment_refs" of
           list of String
        :returns: instance of type "BrowseGenomeResults" -> structure:
           parameter "report_name" of String, parameter "report_ref" of
           String, parameter "genome_ref" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN browse_genome_app
        if params is None:
            raise ValueError("Missing all parameters!")
        genome_ref = params.get("genome_ref", None)
        result_workspace_name = params.get("result_workspace_name", None)
        alignment_refs = params.get("alignment_refs", [])
        print('Initializing browse_genome_app with the following parameters:')
        pprint(params)

        if result_workspace_name is None:
            raise ValueError('result_workspace_name must not be None')
        elif check_workspace_name(result_workspace_name, self.workspace_url) is False:
            raise ValueError('result_workspace_name is not a valid workspace!')

        browser = GenomeBrowserMaker(self.callback_url, self.workspace_url, self.scratch_dir)
        browser_data = browser.create_browser_data(genome_ref, alignment_refs=alignment_refs)
        pprint(browser_data)

        browser.package_jbrowse_data(browser_data['data_dir'],
                                     os.path.join(self.scratch_dir, 'minimal_jbrowse'))
        html_zipped = package_directory(self.callback_url,
                                        os.path.join(self.scratch_dir, 'minimal_jbrowse'),
                                        'index.html',
                                        'Packaged genome browser')
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
        #END browse_genome_app

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method browse_genome_app return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]

    def build_genome_browser(self, ctx, params):
        """
        This saves the genome browser as a report... or maybe it should just return a path to the created directory?
        :param params: instance of type "BuildGenomeBrowserParams" (Note that
           for the list of AlignmentFileInputs, this should be either a list
           of bam files OR a list of alignment references. NOT BOTH. At
           least, not in this version.) -> structure: parameter
           "genome_input" of type "GenomeFileInput" (Should have either a
           genome_ref or BOTH the gff_file and fasta_file paths.) ->
           structure: parameter "gff_file" of String, parameter "fasta_file"
           of String, parameter "genome_ref" of String, parameter
           "alignment_inputs" of list of type "AlignmentFileInput" (Should
           have ONE of bam_file (a local file) or alignment_ref (an object
           reference).) -> structure: parameter "bam_file" of String,
           parameter "alignment_ref" of String, parameter
           "result_workspace_id" of Long, parameter "genome_browser_name" of
           String
        :returns: instance of type "BuildGenomeBrowserResults" -> structure:
           parameter "genome_browser_name" of String, parameter
           "genome_browser_ref" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN build_genome_browser
        output_dir = os.path.join(self.scratch_dir, "min_jbrowse_{}".format(uuid.uuid4()))
        param_errors = check_build_genome_browser_parameters(params)
        if len(param_errors) > 0:
            for err in param_errors:
                print("Error " + err)
            raise ValueError('Errors found in parameters. See previous log statements for details.')

        if "genome_browser_name" not in params or len(params["genome_browser_name"].trim()) == 0:
            params["genome_browser_name"] = "GenomeBrowser-" + str(uuid.uuid4())

        browser = GenomeBrowserMaker(self.callback_url, self.workspace_url, self.scratch_dir)
        # if we have a genome_ref, then build browser data from that.
        # otherwise, assume we have both the gff_file and fasta_file, since we checked.
        if "genome_ref" in params["genome_input"]:
            genome_files = browser.get_genome_data_files(params["genome_input"]["genome_ref"])
        else:
            genome_files = {
                "assembly": params["genome_input"]["fasta_file"],
                "gff": params["genome_input"]["gff_file"]
            }

        # under the alignments, we either have a list of references or a list of bam file paths.
        # the checker ensures we don't have a mix.
        if "alignment_inputs" in params and len(params["alignment_inputs"]) > 0:
            if "alignment_ref" in params["alignment_inputs"][0]:
                alignment_files = browser.get_alignment_data_files(
                    [a["alignment_ref"] for a in params["alignment_inputs"]]
                )
            else:
                alignment_files = dict()
                for idx, align in enumerate(params["alignment_inputs"]):
                    alignment_files["alignment_{}".format(idx)] = align["bam_file"]

        browser_data = browser.create_browser_data_from_files(
            genome_files["assembly"], genome_files["gff"], alignment_files
        )
        browser.package_jbrowse_data(browser_data['data_dir'], output_dir)
        returnVal = {
            "browser_dir": output_dir
        }
        #END build_genome_browser

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method build_genome_browser return value ' +
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
