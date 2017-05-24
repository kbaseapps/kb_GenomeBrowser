
# GenomeBrowser
---

This module implements apps and utilities to enable browsing genomes with [JBrowse](http://jbrowse.org/).

The general flow of the main path is like this:
1. Use GenomeFileUtils to convert from a KBase Genome object to a GFF file.
2. Use the JBrowse scripts to convert that file to both a reference sequence file and annotation track file.
3. Package all of those using KBaseReports, and make them accessible through the HTML file server.
4. Run JBrowse pointed at those files as output.

So Far...
* Demonstrated that we can export KBase Genomes to the appropriate files.
* Manually converted those files to JBrowse data.
* Started JBrowse with those data files.
* Bundled everything up (including a minimal install of JBrowse) as a Report object that can be viewed through the Narrative.

TODO List:
* **(done)** Convert from a Genome to a GFF file.
* **(done)** Convert from a Genome's referenced Assembly or ContigSet to a FASTA file.
* **(done)** Fail if there's 0 or more than one assembly available.
* **(done)** Use JBrowse scripts to convert those to track files.
* **(done)** Automate JBrowse scripts as part of the job.
* **(done)** Package all JBrowse files into a Report (or something else)
* Make those files accessible to a JBrowse instance.
* Create an HTML report that can link out to JBrowse.
* Wherever those files get stored, add a way to signal that they've been created for a given genome, so we only make them once per genome object (MD5? SHA-256?)
