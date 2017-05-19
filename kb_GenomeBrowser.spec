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

    funcdef browse_genome(string genome_ref) returns (BrowseGenomeResults) authentication required;
};
