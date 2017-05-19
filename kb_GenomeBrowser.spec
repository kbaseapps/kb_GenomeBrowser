/*
KBase module: kb_GenomeBrowser
This implements the browse_genome function that sets up files needed for JBrowse to run with a
KBase genome object.
*/

module kb_GenomeBrowser {
    typedef structure {
        string report_name;
        string report_ref;
        string genome_ref;
    } BrowseGenomeResults;



    /*
    Creates a genome browser from the given genome reference. It extracts the reference sequence from the genome
    for one track and uses the genome's feature annotations for the second track. The compiled browser
    is stored in the workspace with name result_workspace_name.

    TODO:
    Add option for BAM alignment file(s).
    Add option for other annotation tracks.
    */
    funcdef browse_genome(string genome_ref, string result_workspace_name) returns (BrowseGenomeResults) authentication required;
};
