"""
Some utility functions that deal with object reference validation.
"""
import re
from Workspace.WorkspaceClient import Workspace
from DataFileUtil.DataFileUtilClient import DataFileUtil
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
