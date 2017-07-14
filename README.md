
# GenomeBrowser
---
## Introduction
This module implements apps and utilities to enable browsing genomes with [JBrowse](http://jbrowse.org/).

The general flow of the main path (in this version) is like this:
1. Use GenomeFileUtils to convert from a KBase Genome object to a GFF file and FASTA sequence file.
2. Retrieve BAM files from ReadsAlignmentUtils (if requested).
3. Use the JBrowse scripts to convert the downloaded files into JBrowse tracks.
4. Package everything using KBaseReports, and make them accessible through the HTML file server.
5. Opening the HTML report directory will run JBrowse with your Genome and tracks.

## Usage
There are two ways to employ the genome browser. There's a Browse Genome app that directly makes use of this (make sure your RNASeqAlignments are aligned against your genome of interest, or you'll just see blank tracks).

The other way is to run the `build_genome_browser` function in your app. This builds the JBrowse directory in your app's scratch space. You can then use it to create your own HTML report.

### Using `build_genome_browser`
To build your own genome browser, the following steps will work.

Install this into your module:
```
> kb-sdk install kb_GenomeBrowser
```

Then integrate this code into your module (Python version, others are an exercise for the user):  
(initialization)
```Python
from kb_GenomeBrowser.kb_GenomeBrowserClient import kb_GenomeBrowser
gb = kb_GenomeBrowser(self.callback_url)
```

(build genome browser from object references)
```Python
gb_info = gb.build_genome_browser({
    "genome_input": {
        "genome_ref": "my/genome/ref"
    },
    "alignment_inputs": [{
        "alignment_ref": "my/align_ref/1",
    }, {
        "alignment_ref": "my/align_ref/2"
    }]
})
browser_directory = gb_info["browser_dir"]
```

(build genome browser from files)
```Python
gb_info = gb.build_genome_browser({
    "genome_input": {
        "gff_file": "/path/to/gff/file",
        "fasta_file": "/path/to/fasta/file"
    },
    "alignment_inputs": [{
        "bam_file": "/path/to/bam/file/1"
    }, {
        "bam_file": "/path/to/bam/file/2"
    }]
})
browser_directory = gb_info["browser_dir"]
```

Note that the genome and alignment inputs can be mixed up with what's ref or what's file. E.g., you can give a reference to a genome object but a list of alignment files, or vice-versa. HOWEVER, in this version, all alignment inputs must be either references or files, not mixed (see Next Steps below). Also note, that for the genome input, you must give a reference or BOTH the GFF file and FASTA file.

## Next Steps
(in no particular order)
* Add ability to mix up alignment inputs to accept a list of files and references in each. E.g., make this valid:
```Python
"alignment_inputs": [{
    "alignment_ref": "xx/yy/zz"
}, {
    "bam_file": "/path/to/file"
}]
```
* Remove need to package up all the JBrowse files with each genome.
* Build some dynamic service to provide REST-like access to alignment files, then just put that URL in the JBrowse trackList.json. Right now, it bundles those files all together which can be both large and redundant.
* Build a separate web service to serve up JBrowse all together, not just bundled into a KBaseReport object.
* Add support for other types of tracks. Maybe a converter from expression data -> BigWig format?
* Add support for aligned genomes, tree viewer, etc.
