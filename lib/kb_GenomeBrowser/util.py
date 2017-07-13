"""
Some utility functions that deal with object reference validation.
"""
import re
from Workspace.WorkspaceClient import Workspace
from DataFileUtil.DataFileUtilClient import DataFileUtil


def get_object_name(ref, ws_url):
    """
    From an object reference, get the object's name.
    """
    if not check_reference(ref):
        raise ValueError("This must be a valid object reference to find the object's name.")
    ws = Workspace(ws_url)
    info = ws.get_object_info3({"objects": [{"ref": ref}]}).get("infos")[0]
    return info[1]


def check_reference(ref):
    """
    Tests the given ref string to make sure it conforms to the expected
    object reference format. Returns True if it passes, False otherwise.
    """
    obj_ref_regex = re.compile("^(?P<wsid>\d+)\/(?P<objid>\d+)(\/(?P<ver>\d+))?$")
    ref_path = ref.split(";")
    for step in ref_path:
        if not obj_ref_regex.match(step):
            return False
    return True


def check_reference_type(ref, allowed_types, ws_url):
    """
    Tests whether the given object reference is one of the allowed types.
    Specifically, it tests whether the list of allowed_types strings is a substring
    of the ref object's name.
    E.g. if ".Genome" is an allowed type, it'll pass if the object is a "KBaseGenomes.Genome"
    """
    ws = Workspace(ws_url)
    info = ws.get_object_info3({"objects": [{"ref": ref}]}).get("infos")[0]
    passes = False
    for t in allowed_types:
        if t in info[2]:
            passes = True
    return passes


def check_workspace_name(ws_name, ws_url):
    """
    Tests whether the given workspace name actually exists, is accessible by the current user,
    and is an appropriately formatted name.
    Really, it just pokes the Workspace with the name and returns True if it can.
    """
    ws = Workspace(ws_url)
    try:
        # let the Workspace do the work - if this is NOT a real name, it will raise an exception.
        ws.get_workspace_info({"workspace": ws_name})
        return True
    except:
        return False


def package_directory(callback_url, dir_path, zip_file_name, zip_file_description):
    ''' Simple utility for packaging a folder and saving to shock '''
    dfu = DataFileUtil(callback_url)
    output = dfu.file_to_shock({'file_path': dir_path,
                                'make_handle': 0,
                                'pack': 'zip'})
    return {'shock_id': output['shock_id'],
            'name': zip_file_name,
            'description': zip_file_description}


def check_build_genome_browser_parameters(params):
    """
    Checks parameter combinations for correctness. Returns a list of error strings, or an empty
    list if all is well.
    """
    errors = list()
    genome_input = params.get("genome_input", None)
    if genome_input is None:
        errors.append("genome_input must exist and contain ONE of a genome reference or a GFF file.")
    elif "genome_ref" in genome_input:
        # make sure there's no other keys
        if "gff_file" in genome_input or "fasta_file" in genome_input:
            errors.append("genome_input should just have genome_ref or both of gff_file and fasta_file")
        # make sure it's an actual ref
        if not check_reference(genome_input["genome_ref"]):
            errors.append("genome_input.genome_ref must be a valid workspace reference string")
    elif "gff_file" in genome_input or "fasta_file" in genome_input:
        if not ("gff_file" in genome_input and "fasta_file" in genome_input):
            errors.append("When using a gff_file and fasta_file to represent a genome, BOTH files must be present.")

    alignment_inputs = params.get("alignment_inputs", None)
    if alignment_inputs is not None and len(alignment_inputs) > 0:
        for alignment in alignment_inputs:
            if "alignment_ref" not in alignment and "bam_file" not in alignment:
                errors.append("an alignment input must have ONE of alignment_ref or bam_file keys")
            elif "alignment_ref" in alignment and "bam_file" in alignment:
                errors.append("an alignment input must have ONE of alignment_ref or bam_file, not both.")
            elif "alignment_ref" in alignment:
                if not check_reference(alignment["alignment_ref"]):
                    errors.append("alignment.alignment_ref must be a valid workspace reference "
                                  "string, not {}".format(alignment["alignment_ref"]))

    # if "result_workspace_id" not in params or len(params["result_workspace_id"].trim()) == 0:
    #     errors.append("A workspace id must be provided!")
    # else:
    #     try:
    #         int(params["result_workspace_id"])
    #     except:
    #         errors.append("result_workspace_id must be an integer")
    return errors
