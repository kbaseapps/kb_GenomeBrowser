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

    typedef structure {
        string genome_ref;
        string result_workspace_name;
        list<string> alignment_refs;
    } BrowseGenomeParams;

    /*
    Creates a genome browser from the given genome reference. It extracts the reference sequence from the genome
    for one track and uses the genome's feature annotations for the second track. The compiled browser
    is stored in the workspace with name result_workspace_name.

    TODO:
    Add option for BAM alignment file(s).
    Add option for other annotation tracks.
    */
    funcdef browse_genome_app(BrowseGenomeParams params) returns (BrowseGenomeResults) authentication required;


    /*
    Should have either a genome_ref or BOTH the gff_file and fasta_file paths.
    */
    typedef structure {
        string gff_file;
        string fasta_file;
        string genome_ref;
    } GenomeFileInput;

    /*
    Should have ONE of bam_file (a local file) or alignment_ref (an object reference).
    */
    typedef structure {
        string bam_file;
        string alignment_ref;
    } AlignmentFileInput;

    /*
    Note that for the list of AlignmentFileInputs, this should be either a list of bam files OR a
    list of alignment references. NOT BOTH. At least, not in this version.
     */
    typedef structure {
        GenomeFileInput genome_input;
        list<AlignmentFileInput> alignment_inputs;
        int result_workspace_id;
        string genome_browser_name;
    } BuildGenomeBrowserParams;

    typedef structure {
        string browser_dir;
    } BuildGenomeBrowserResults;

    /*
    This returns a path to the newly created browser directory.
    */
    funcdef build_genome_browser(BuildGenomeBrowserParams params) returns (BuildGenomeBrowserResults) authentication required;
};
