import os
from pprint import (pprint, pformat)
from KBaseReport.KBaseReportClient import KBaseReport
from GenomeFileUtil.GenomeFileUtilClient import GenomeFileUtil
from AssemblyUtil.AssemblyUtilClient import AssemblyUtil
from Workspace.WorkspaceClient import Workspace
from util import (
    test_reference,
    test_reference_type
)

class GenomeBrowserMaker:
    def __init__(self, callback_url, workspace_url, shared_folder):
        self.callback_url = callback_url
        self.shared_folder = shared_folder
        self.workspace_url = workspace_url
        self.ws = Workspace(self.workspace_url)

    def _get_assembly_ref(self, genome_ref):
        # test if genome references an assembly type
        # do get_objects2 without data. get list of refs
        genome_obj_info = self.ws.get_objects2({
            'objects': [{'ref': genome_ref}],
            'no_data': 1
        })
        # get the list of genome refs from the returned info.
        # if there are no refs (or something funky with the return), this will be an empty list.
        # this WILL fail if data is an empty list. But it shouldn't be, and we know because
        # we have a real genome reference, or get_objects2 would fail.
        genome_obj_refs = genome_obj_info.get('data', [{}])[0].get('refs', [])

        # see which of those are of an appropriate type (ContigSet or Assembly), if any.
        assembly_ref = list()
        ref_params = [{'ref': x} for x in genome_obj_refs]
        ref_info = self.ws.get_object_info3({'objects': ref_params})
        for idx, info in enumerate(ref_info.get('infos')):
            if "KBaseGenomeAnnotations.Assembly" in info[2] or "KBaseGenomes.ContigSet" in info[2]:
                assembly_ref.append(";".join(ref_info.get('paths')[idx]))

        return assembly_ref

    def create_browser_data(self, ctx, genome_ref):
        # STEP 1: parameter checking
        # make sure that genome_ref is an object reference, and its a genome, and we have
        # permission to it.
        if not genome_ref:
            raise ValueError('genome_ref parameter is required')
        if not test_reference(genome_ref):
            raise ValueError('genome_ref must be a reference of the format ws/oid or ws/oid/ver')
        if not test_reference_type(genome_ref, ['.Genome'], self.workspace_url):
            raise ValueError('genome_ref must reference a KBaseGenomes.Genome object')

        assembly_ref = self._get_assembly_ref(genome_ref)
        if len(assembly_ref) > 1:
            raise ValueError('This genome, {}, appears to reference {} Assemblies or ContigSets, with these object references: {}'.format(genome_ref, len(assembly_ref), assembly_ref))
        elif len(assembly_ref) == 0:
            raise ValueError('There was no Assembly or ContigSet found as a reference to this genome. Unable to build browser data.')

        # STEP 2: genome_to_gff
        # get the genome as a local gff file
        gfu = GenomeFileUtil(self.callback_url)
        gff_file = gfu.genome_to_gff({'genome_ref': genome_ref})

        # STEP 3: assembly_to_fasta
        # get a fasta file from the genome's linked assembly or contig set
        au = AssemblyUtil(self.callback_url)
        fasta_file = au.get_assembly_as_fasta({'ref': assembly_ref[0]})

        # {u'file_path': u'/kb/module/work/tmp/gff_1494890493861/my_test_genome.gff',
        # u'from_cache': 0}

        # STEP 3: run jbrowse conversion scripts
        #
        return {
            'gff_file': gff_file,
            'fasta_file': fasta_file
        }
