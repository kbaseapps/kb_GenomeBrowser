import os
from GenomeFileUtil.GenomeFileUtilClient import GenomeFileUtil
from AssemblyUtil.AssemblyUtilClient import AssemblyUtil
from ReadsAlignmentUtils.ReadsAlignmentUtilsClient import ReadsAlignmentUtils
from Workspace.WorkspaceClient import Workspace
from util import (
    check_reference,
    check_reference_type,
    get_object_name
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

    def create_browser_data_from_files(self, fasta_file, gff_file, alignment_files):
        """
        fasta_file = string, path to file
        gff_file = string, path to file
        alignment_files = dict,
            keys = alignment "name" (not necessarily file name),
            values = path to file
        """
        print('Starting create_browser_data_from_files')
        # STEP 1: run the refseq creation
        print('Converting FASTA to JBrowse refseq track...')
        refseq_cmd = [os.path.join(self.jbrowse_bin, 'prepare-refseqs.pl'),
                      '--fasta',
                      fasta_file,
                      '--out',
                      self.out_dir]
        print('refseq command:')
        print(refseq_cmd)
        p = subprocess.Popen(refseq_cmd, shell=False)
        retcode = p.wait()
        if retcode != 0:
            raise RuntimeError('Failed to build reference sequence track from FASTA file! Return code: {}'.format(retcode))
        print('Done creating refseq track!')

        # STEP 2: run the feature track creation
        print('Converting GFF to annotation track...')
        track_cmd = [os.path.join(self.jbrowse_bin, 'flatfile-to-json.pl'),
                     '--gff',
                     gff_file,
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

        # STEP 3: run the BAM track creation
        print('Converting BAM files to alignment tracks...')
        for alignment_name in alignment_files:
            print('Converting BAM file {}'.format(alignment_name))
            # 1. get the actual file name for the bam file
            align_file_fullpath = alignment_files[alignment_name]
            align_filename = os.path.basename(align_file_fullpath)
            # 2. move it (copy?) to the right location
            shutil.copy2(align_file_fullpath, os.path.join(self.out_dir, align_filename))

            # 2.a. TODO: check the header inside the file that it's the correct chromosome...
            # 3. make a BAI file with samtools
            align_file_fullpath = os.path.join(self.out_dir, align_filename)
            sam_bai_cmd = ['samtools',
                           'index',
                           align_file_fullpath,
                           "{}.bai".format(align_file_fullpath)]
            print("Building BAM index with command: {}".format(" ".join(sam_bai_cmd)))
            p = subprocess.Popen(sam_bai_cmd, shell=False)
            retcode = p.wait()
            if retcode != 0:
                raise RuntimeError('Failed to make index file from BAM file! Return code: {}'.format(retcode))
            # 4. add the filename to the trackList with add-bam-track.pl
            track_cmd = [os.path.join(self.jbrowse_bin, 'add-bam-track.pl'),
                         '--label',
                         alignment_name,
                         '--bam_url',
                         align_filename,
                         '--in',
                         os.path.join(self.out_dir, 'trackList.json')]
            p = subprocess.Popen(track_cmd, shell=False)
            retcode = p.wait()
            if retcode != 0:
                raise RuntimeError('Failed to build alignment track from BAM file! Return code: {}'.format(retcode))
            print('Done creating alignment track {}'.format(alignment_name))
        print('Done creating all alignment tracks!')
        print('Done running create_browser_data_from_files')
        # Final step: return the directory where the JBrowse data lives.
        return {
            'gff_file': gff_file,
            'fasta_file': fasta_file,
            'data_dir': self.out_dir
        }

    def get_genome_data_files(self, genome_ref):
        genome_files = {
            "assembly": None,
            "gff": None
        }
        print('Fetching assembly or contig information from genome...')
        assembly_ref = self._get_assembly_ref(genome_ref)
        if len(assembly_ref) > 1:
            raise ValueError('This genome, {}, appears to reference {} Assemblies or ContigSets, with these object references: {}'.format(genome_ref, len(assembly_ref), assembly_ref))
        elif len(assembly_ref) == 0:
            raise ValueError('There was no Assembly or ContigSet found as a reference to this genome. Unable to build browser data.')
        print('Done! Found valid assembly data.')

        print('Converting sequence data to FASTA file...')
        au = AssemblyUtil(self.callback_url)
        fasta_file = au.get_assembly_as_fasta({'ref': assembly_ref[0]})
        print('Done! FASTA file created: {}'.format(fasta_file))

        if "path" not in fasta_file:
            raise IOError('FASTA file was not apparently generated from the given genome fasta_file. fasta_file object missing key "path": {}'.format(fasta_file))
        genome_files["assembly"] = fasta_file.get('path', None)

        print('Converting genome annotation data to gff file...')
        gfu = GenomeFileUtil(self.callback_url)
        gff_file = gfu.genome_to_gff({'genome_ref': genome_ref})
        print('Done! GFF file created: {}'.format(gff_file))
        if "file_path" not in gff_file:
            raise IOError('GFF file was not apparently generated from the given genome. gff_file object missing key "file_path": {}'.format(gff_file))
        genome_files["gff"] = gff_file.get('file_path', None)

        return genome_files

    def get_alignment_data_files(self, alignment_refs):
        """
        Returns a dictionary of data files. Key = object name, value = path to the file.
        """
        alignment_files = dict()
        ru = ReadsAlignmentUtils(self.callback_url, service_ver='dev')
        for ref in alignment_refs:
            ref_name = get_object_name(ref, self.workspace_url)
            align_file = ru.download_alignment({
                "source_ref": ref,
                "downloadBAI": 0
            })
            for f in os.listdir(align_file["destination_dir"]):
                if f.endswith("bam"):
                    alignment_files[ref_name] = os.path.join(align_file["destination_dir"], f)
        return alignment_files

    def get_browser_data_files(self, genome_ref=None, alignment_refs=None):
        """
        if genome_ref is not None, this figures out the assembly ref, then returns paths to
        both the GFF file and FASTA for the assembly.

        if the alignment_refs list is not None, it fetches the BAM files from each alignment in
        the list.

        Returns a dictionary of the following:
        {
            assembly: string (file path) or None,
            gff: string (file path) or None,
            alignments: {
                name1 (from alignment obj ref): path1,
                name2: path2,
                ...etc
            }
        }

        if genome_ref and alignment_refs are both none, this doesn't do much, and returns a boring
        empty dict.
        """
        files = dict()
        if genome_ref is not None:
            files.update(self.get_genome_data_files(genome_ref))

        files["alignment_refs"] = dict()
        if alignment_refs is not None:
            files["alignment_refs"] = self.get_alignment_data_files(alignment_refs)
        return files

    def create_browser_data(self, genome_ref, alignment_refs=None):
        # parameter checking
        # make sure that genome_ref is an object reference, and its a genome, and we have
        # permission to it.
        if not genome_ref:
            raise ValueError('genome_ref parameter is required')
        if not check_reference(genome_ref):
            raise ValueError('genome_ref must be a reference of the format ws/oid or ws/oid/ver')
        if not check_reference_type(genome_ref, ['.Genome'], self.workspace_url):
            raise ValueError('genome_ref must reference a KBaseGenomes.Genome object')
        if alignment_refs is not None:
            for ref in alignment_refs:
                if not check_reference(ref):
                    raise ValueError('all alignment_refs must be a reference of the format ws/oid or ws/oid/ver')

        files = self.get_browser_data_files(genome_ref=genome_ref, alignment_refs=alignment_refs)
        return self.create_browser_data_from_files(
            files.get("assembly", None), files.get("gff", None), files.get("alignment_refs", dict())
        )

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

        # get rid of the src/util tree
        shutil.rmtree(os.path.join(output_dir, 'src', 'util'))

        # mv data_dir -> output_dir/data
        shutil.move(data_dir, os.path.join(output_dir, 'data'))
