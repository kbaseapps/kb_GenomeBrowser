import os
from pprint import (pprint, pformat)
from KBaseReport.KBaseReportClient import KBaseReport
from GenomeFileUtil.GenomeFileUtilClient import GenomeFileUtil
from AssemblyUtil.AssemblyUtilClient import AssemblyUtil
from Workspace.WorkspaceClient import Workspace
from util import (
    check_reference,
    check_reference_type
)
import subprocess
import shutil


class GenomeBrowserMaker:
    def __init__(self, callback_url, workspace_url, scratch_dir):
        self.callback_url = callback_url
        self.scratch_dir = scratch_dir
        self.workspace_url = workspace_url
        self.ws = Workspace(self.workspace_url)
        self.jbrowse_dir = os.path.abspath(os.path.join(os.sep, 'kb', 'module', 'jbrowse'))
        self.jbrowse_bin = os.path.join(self.jbrowse_dir, 'bin')
        self.out_dir = os.path.join(self.scratch_dir, 'browser_data')

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
        if not check_reference(genome_ref):
            raise ValueError('genome_ref must be a reference of the format ws/oid or ws/oid/ver')
        if not check_reference_type(genome_ref, ['.Genome'], self.workspace_url):
            raise ValueError('genome_ref must reference a KBaseGenomes.Genome object')

        print('Fetching assembly or contig information from genome...')
        assembly_ref = self._get_assembly_ref(genome_ref)
        if len(assembly_ref) > 1:
            raise ValueError('This genome, {}, appears to reference {} Assemblies or ContigSets, with these object references: {}'.format(genome_ref, len(assembly_ref), assembly_ref))
        elif len(assembly_ref) == 0:
            raise ValueError('There was no Assembly or ContigSet found as a reference to this genome. Unable to build browser data.')
        print('Done! Found valid assembly data.')

        # STEP 2: genome_to_gff
        # get the genome as a local gff file
        print('Converting genome annotation data to gff file...')
        gfu = GenomeFileUtil(self.callback_url)
        gff_file = gfu.genome_to_gff({'genome_ref': genome_ref})
        print('Done! GFF file created: {}'.format(gff_file))

        # STEP 3: assembly_to_fasta
        # get a fasta file from the genome's linked assembly or contig set
        print('Converting sequence data to FASTA file...')
        au = AssemblyUtil(self.callback_url)
        fasta_file = au.get_assembly_as_fasta({'ref': assembly_ref[0]})
        print('Done! FASTA file created: {}'.format(fasta_file))

        # STEP 3: run jbrowse conversion scripts
        gff_file_path = gff_file.get('file_path', None)
        fasta_file_path = fasta_file.get('path', None)
        if not gff_file_path:
            raise IOError('GFF file was not apparently generated from the given genome. gff_file object missing key "file_path": {}'.format(gff_file))
        if not fasta_file_path:
            raise IOError('FASTA file was not apparently generated from the given genome fasta_file. fasta_file object missing key "path": {}'.format(fasta_file))

        # STEP 3a: run the refseq creation
        print('Converting FASTA to JBrowse refseq track...')
        refseq_cmd = [os.path.join(self.jbrowse_bin, 'prepare-refseqs.pl'),
                      '--fasta',
                      fasta_file_path,
                      '--out',
                      self.out_dir]
        print('refseq command:')
        print(refseq_cmd)
        p = subprocess.Popen(refseq_cmd, shell=False)
        retcode = p.wait()
        if retcode != 0:
            raise RuntimeError('Failed to build reference sequence track from FASTA file! Return code: {}'.format(retcode))
        print('Done creating refseq track!')

        # STEP 3b: run the feature track creation
        print('Converting GFF to annotation track...')
        track_cmd = [os.path.join(self.jbrowse_bin, 'flatfile-to-json.pl'),
                     '--gff',
                     gff_file_path,
                     '--trackLabel',
                     'FeatureAnnotations',
                     '--trackType',
                     'CanvasFeatures',
                     '--out',
                     self.out_dir]
        print('track command:')
        print(track_cmd)
        p = subprocess.Popen(track_cmd, shell=False)
        retcode = p.wait()
        if retcode != 0:
            raise RuntimeError('Failed to build feature annotation track from GFF file! Return code: {}'.format(retcode))
        print('Done creating annotation track!')

        # Final step: return the directory where the JBrowse data lives.
        return {
            'gff_file': gff_file_path,
            'fasta_file': fasta_file_path,
            'data_dir': self.out_dir
        }

    def package_jbrowse_data(self, data_dir, output_dir):
        """
        Packages the necessary parts of JBrowse (in the standard location:
        /kb/module/jbrowse) along with the data_dir into output_dir.
        output_dir should be an ABSOLUTE path. (e.g. /kb/module/work/tmp/minimal_jbrowse)

        NOTE: this is the big piece necessary for JBrowse compatibility with specific
        versions. It's currently made for JBrowse 1.12.3.
        """
        # mkdir output_dir
        os.makedirs(output_dir)

        # cp pieces of the JBrowse dir into output_dir
        dirs_from_jbrowse = [
            'browser',
            'css',
            'img',
            'plugins',
            'src'
        ]
        files_from_jbrowse = [
            'bower.json',
            'compat_121.html',
            'index.html',
            'jbrowse_conf.json',
            'jbrowse.conf',
            'LICENSE',
            'MYMETA.json',
            'MYMETA.yml',
            'package.json'
        ]
        for d in dirs_from_jbrowse:
            jb_path = os.path.join(self.jbrowse_dir, d)
            shutil.copytree(jb_path, os.path.join(output_dir, d))
        for f in files_from_jbrowse:
            jb_path = os.path.join(self.jbrowse_dir, f)
            shutil.copy2(jb_path, os.path.join(output_dir, f))

        # mv data_dir -> output_dir/data
        shutil.move(data_dir, os.path.join(output_dir, 'data'))


        # upload to shock
        # return report info?
