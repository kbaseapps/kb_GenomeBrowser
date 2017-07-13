"""
A little class for munging about files when testing the Genome Browser.
"""
from AssemblyUtil.AssemblyUtilClient import AssemblyUtil
from GenomeFileUtil.GenomeFileUtilClient import GenomeFileUtil
from ReadsAlignmentUtils.ReadsAlignmentUtilsClient import ReadsAlignmentUtils
from ReadsUtils.ReadsUtilsClient import ReadsUtils
from Workspace.WorkspaceClient import Workspace


class FileUtil(object):
    def __init__(self, ws_name, ws_url, callback_url):
        self.ws_name = ws_name
        self.ws_url = ws_url
        self.callback_url = callback_url

    def load_reads_file(self, tech, file_fwd, file_rev, target_name):
        """
        Loads FASTQ files as either SingleEndLibrary or PairedEndLibrary. If file_rev is None,
        then we get a single end, otherwise, paired.
        """
        reads_util = ReadsUtils(self.callback_url)
        upload_params = {
            "wsname": self.ws_name,
            "fwd_file": file_fwd,
            "name": target_name,
            "sequencing_tech": tech
        }
        if file_rev is not None:
            upload_params["rev_file"] = file_rev
        reads_ref = reads_util.upload_reads(upload_params)
        return reads_ref["obj_ref"]

    def load_bam_file(self, file_path, genome_ref, reads_ref, obj_name):
        rau = ReadsAlignmentUtils(self.callback_url, service_ver='dev')
        return rau.upload_alignment({
            "destination_ref": "{}/{}".format(self.ws_name, obj_name),
            "file_path": file_path,
            "read_library_ref": reads_ref,
            "assembly_or_genome_ref": genome_ref,
            "condition": "none"
        })["obj_ref"]

    def load_fasta_file(self, filename, obj_name, contents):
        f = open(filename, 'w')
        f.write(contents)
        f.close()
        assembly_util = AssemblyUtil(self.callback_url)
        assembly_ref = assembly_util.save_assembly_from_fasta({
            'file': {'path': filename},
            'workspace_name': self.ws_name,
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
            "workspace_name": self.ws_name,
            "source": "RefSeq",
            "release": "NC_003098.1",
            "genetic_code": 11,
            "generate_ids_if_needed": 1,
            "type": "User upload"
        })
        return genome_ref.get('genome_ref')  # yeah, i know.

    def get_gff_file(self, genome_ref):
        gfu = GenomeFileUtil(self.callback_url)
        gff_file = gfu.genome_to_gff({'genome_ref': genome_ref})
        return gff_file["file_path"]

    def get_fasta_file(self, genome_ref):
        ws = Workspace(self.ws_url)
        # test if genome references an assembly type
        # do get_objects2 without data. get list of refs
        genome_obj_info = ws.get_objects2({
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
        ref_info = ws.get_object_info3({'objects': ref_params})
        for idx, info in enumerate(ref_info.get('infos')):
            if "KBaseGenomeAnnotations.Assembly" in info[2] or "KBaseGenomes.ContigSet" in info[2]:
                assembly_ref.append(";".join(ref_info.get('paths')[idx]))
        # now just get the file.
        au = AssemblyUtil(self.callback_url)
        fasta_file = au.get_assembly_as_fasta({'ref': assembly_ref[0]})
        return fasta_file["path"]
