package kb_GenomeBrowser::kb_GenomeBrowserClient;

use JSON::RPC::Client;
use POSIX;
use strict;
use Data::Dumper;
use URI;
use Bio::KBase::Exceptions;
my $get_time = sub { time, 0 };
eval {
    require Time::HiRes;
    $get_time = sub { Time::HiRes::gettimeofday() };
};

use Bio::KBase::AuthToken;

# Client version should match Impl version
# This is a Semantic Version number,
# http://semver.org
our $VERSION = "0.1.0";

=head1 NAME

kb_GenomeBrowser::kb_GenomeBrowserClient

=head1 DESCRIPTION


KBase module: kb_GenomeBrowser
This implements the browse_genome function that sets up files needed for JBrowse to run with a
KBase genome object.


=cut

sub new
{
    my($class, $url, @args) = @_;
    

    my $self = {
	client => kb_GenomeBrowser::kb_GenomeBrowserClient::RpcClient->new,
	url => $url,
	headers => [],
    };

    chomp($self->{hostname} = `hostname`);
    $self->{hostname} ||= 'unknown-host';

    #
    # Set up for propagating KBRPC_TAG and KBRPC_METADATA environment variables through
    # to invoked services. If these values are not set, we create a new tag
    # and a metadata field with basic information about the invoking script.
    #
    if ($ENV{KBRPC_TAG})
    {
	$self->{kbrpc_tag} = $ENV{KBRPC_TAG};
    }
    else
    {
	my ($t, $us) = &$get_time();
	$us = sprintf("%06d", $us);
	my $ts = strftime("%Y-%m-%dT%H:%M:%S.${us}Z", gmtime $t);
	$self->{kbrpc_tag} = "C:$0:$self->{hostname}:$$:$ts";
    }
    push(@{$self->{headers}}, 'Kbrpc-Tag', $self->{kbrpc_tag});

    if ($ENV{KBRPC_METADATA})
    {
	$self->{kbrpc_metadata} = $ENV{KBRPC_METADATA};
	push(@{$self->{headers}}, 'Kbrpc-Metadata', $self->{kbrpc_metadata});
    }

    if ($ENV{KBRPC_ERROR_DEST})
    {
	$self->{kbrpc_error_dest} = $ENV{KBRPC_ERROR_DEST};
	push(@{$self->{headers}}, 'Kbrpc-Errordest', $self->{kbrpc_error_dest});
    }

    #
    # This module requires authentication.
    #
    # We create an auth token, passing through the arguments that we were (hopefully) given.

    {
	my %arg_hash2 = @args;
	if (exists $arg_hash2{"token"}) {
	    $self->{token} = $arg_hash2{"token"};
	} elsif (exists $arg_hash2{"user_id"}) {
	    my $token = Bio::KBase::AuthToken->new(@args);
	    if (!$token->error_message) {
	        $self->{token} = $token->token;
	    }
	}
	
	if (exists $self->{token})
	{
	    $self->{client}->{token} = $self->{token};
	}
    }

    my $ua = $self->{client}->ua;	 
    my $timeout = $ENV{CDMI_TIMEOUT} || (30 * 60);	 
    $ua->timeout($timeout);
    bless $self, $class;
    #    $self->_validate_version();
    return $self;
}




=head2 browse_genome_app

  $return = $obj->browse_genome_app($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a kb_GenomeBrowser.BrowseGenomeParams
$return is a kb_GenomeBrowser.BrowseGenomeResults
BrowseGenomeParams is a reference to a hash where the following keys are defined:
	genome_ref has a value which is a string
	result_workspace_name has a value which is a string
	alignment_refs has a value which is a reference to a list where each element is a string
BrowseGenomeResults is a reference to a hash where the following keys are defined:
	report_name has a value which is a string
	report_ref has a value which is a string
	genome_ref has a value which is a string

</pre>

=end html

=begin text

$params is a kb_GenomeBrowser.BrowseGenomeParams
$return is a kb_GenomeBrowser.BrowseGenomeResults
BrowseGenomeParams is a reference to a hash where the following keys are defined:
	genome_ref has a value which is a string
	result_workspace_name has a value which is a string
	alignment_refs has a value which is a reference to a list where each element is a string
BrowseGenomeResults is a reference to a hash where the following keys are defined:
	report_name has a value which is a string
	report_ref has a value which is a string
	genome_ref has a value which is a string


=end text

=item Description

Creates a genome browser from the given genome reference. It extracts the reference sequence from the genome
for one track and uses the genome's feature annotations for the second track. The compiled browser
is stored in the workspace with name result_workspace_name.

TODO:
Add option for BAM alignment file(s).
Add option for other annotation tracks.

=back

=cut

 sub browse_genome_app
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function browse_genome_app (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to browse_genome_app:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'browse_genome_app');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "kb_GenomeBrowser.browse_genome_app",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'browse_genome_app',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method browse_genome_app",
					    status_line => $self->{client}->status_line,
					    method_name => 'browse_genome_app',
				       );
    }
}
 


=head2 build_genome_browser

  $return = $obj->build_genome_browser($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a kb_GenomeBrowser.BuildGenomeBrowserParams
$return is a kb_GenomeBrowser.BuildGenomeBrowserResults
BuildGenomeBrowserParams is a reference to a hash where the following keys are defined:
	genome_input has a value which is a kb_GenomeBrowser.GenomeFileInput
	alignment_inputs has a value which is a reference to a list where each element is a kb_GenomeBrowser.AlignmentFileInput
	result_workspace_id has a value which is an int
	genome_browser_name has a value which is a string
GenomeFileInput is a reference to a hash where the following keys are defined:
	gff_file has a value which is a string
	fasta_file has a value which is a string
	genome_ref has a value which is a string
AlignmentFileInput is a reference to a hash where the following keys are defined:
	bam_file has a value which is a string
	alignment_ref has a value which is a string
BuildGenomeBrowserResults is a reference to a hash where the following keys are defined:
	genome_browser_name has a value which is a string
	genome_browser_ref has a value which is a string

</pre>

=end html

=begin text

$params is a kb_GenomeBrowser.BuildGenomeBrowserParams
$return is a kb_GenomeBrowser.BuildGenomeBrowserResults
BuildGenomeBrowserParams is a reference to a hash where the following keys are defined:
	genome_input has a value which is a kb_GenomeBrowser.GenomeFileInput
	alignment_inputs has a value which is a reference to a list where each element is a kb_GenomeBrowser.AlignmentFileInput
	result_workspace_id has a value which is an int
	genome_browser_name has a value which is a string
GenomeFileInput is a reference to a hash where the following keys are defined:
	gff_file has a value which is a string
	fasta_file has a value which is a string
	genome_ref has a value which is a string
AlignmentFileInput is a reference to a hash where the following keys are defined:
	bam_file has a value which is a string
	alignment_ref has a value which is a string
BuildGenomeBrowserResults is a reference to a hash where the following keys are defined:
	genome_browser_name has a value which is a string
	genome_browser_ref has a value which is a string


=end text

=item Description

This saves the genome browser as a report... or maybe it should just return a path to the created directory?

=back

=cut

 sub build_genome_browser
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function build_genome_browser (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to build_genome_browser:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'build_genome_browser');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "kb_GenomeBrowser.build_genome_browser",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'build_genome_browser',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method build_genome_browser",
					    status_line => $self->{client}->status_line,
					    method_name => 'build_genome_browser',
				       );
    }
}
 
  
sub status
{
    my($self, @args) = @_;
    if ((my $n = @args) != 0) {
        Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
                                   "Invalid argument count for function status (received $n, expecting 0)");
    }
    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
        method => "kb_GenomeBrowser.status",
        params => \@args,
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
                           code => $result->content->{error}->{code},
                           method_name => 'status',
                           data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
                          );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method status",
                        status_line => $self->{client}->status_line,
                        method_name => 'status',
                       );
    }
}
   

sub version {
    my ($self) = @_;
    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
        method => "kb_GenomeBrowser.version",
        params => [],
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(
                error => $result->error_message,
                code => $result->content->{code},
                method_name => 'build_genome_browser',
            );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(
            error => "Error invoking method build_genome_browser",
            status_line => $self->{client}->status_line,
            method_name => 'build_genome_browser',
        );
    }
}

sub _validate_version {
    my ($self) = @_;
    my $svr_version = $self->version();
    my $client_version = $VERSION;
    my ($cMajor, $cMinor) = split(/\./, $client_version);
    my ($sMajor, $sMinor) = split(/\./, $svr_version);
    if ($sMajor != $cMajor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Major version numbers differ.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor < $cMinor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Client minor version greater than Server minor version.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor > $cMinor) {
        warn "New client version available for kb_GenomeBrowser::kb_GenomeBrowserClient\n";
    }
    if ($sMajor == 0) {
        warn "kb_GenomeBrowser::kb_GenomeBrowserClient version is $svr_version. API subject to change.\n";
    }
}

=head1 TYPES



=head2 BrowseGenomeResults

=over 4



=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
report_name has a value which is a string
report_ref has a value which is a string
genome_ref has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
report_name has a value which is a string
report_ref has a value which is a string
genome_ref has a value which is a string


=end text

=back



=head2 BrowseGenomeParams

=over 4



=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
genome_ref has a value which is a string
result_workspace_name has a value which is a string
alignment_refs has a value which is a reference to a list where each element is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
genome_ref has a value which is a string
result_workspace_name has a value which is a string
alignment_refs has a value which is a reference to a list where each element is a string


=end text

=back



=head2 GenomeFileInput

=over 4



=item Description

Should have either a genome_ref or BOTH the gff_file and fasta_file paths.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
gff_file has a value which is a string
fasta_file has a value which is a string
genome_ref has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
gff_file has a value which is a string
fasta_file has a value which is a string
genome_ref has a value which is a string


=end text

=back



=head2 AlignmentFileInput

=over 4



=item Description

Should have ONE of bam_file (a local file) or alignment_ref (an object reference).


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
bam_file has a value which is a string
alignment_ref has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
bam_file has a value which is a string
alignment_ref has a value which is a string


=end text

=back



=head2 BuildGenomeBrowserParams

=over 4



=item Description

Note that for the list of AlignmentFileInputs, this should be either a list of bam files OR a
list of alignment references. NOT BOTH. At least, not in this version.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
genome_input has a value which is a kb_GenomeBrowser.GenomeFileInput
alignment_inputs has a value which is a reference to a list where each element is a kb_GenomeBrowser.AlignmentFileInput
result_workspace_id has a value which is an int
genome_browser_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
genome_input has a value which is a kb_GenomeBrowser.GenomeFileInput
alignment_inputs has a value which is a reference to a list where each element is a kb_GenomeBrowser.AlignmentFileInput
result_workspace_id has a value which is an int
genome_browser_name has a value which is a string


=end text

=back



=head2 BuildGenomeBrowserResults

=over 4



=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
genome_browser_name has a value which is a string
genome_browser_ref has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
genome_browser_name has a value which is a string
genome_browser_ref has a value which is a string


=end text

=back



=cut

package kb_GenomeBrowser::kb_GenomeBrowserClient::RpcClient;
use base 'JSON::RPC::Client';
use POSIX;
use strict;

#
# Override JSON::RPC::Client::call because it doesn't handle error returns properly.
#

sub call {
    my ($self, $uri, $headers, $obj) = @_;
    my $result;


    {
	if ($uri =~ /\?/) {
	    $result = $self->_get($uri);
	}
	else {
	    Carp::croak "not hashref." unless (ref $obj eq 'HASH');
	    $result = $self->_post($uri, $headers, $obj);
	}

    }

    my $service = $obj->{method} =~ /^system\./ if ( $obj );

    $self->status_line($result->status_line);

    if ($result->is_success) {

        return unless($result->content); # notification?

        if ($service) {
            return JSON::RPC::ServiceObject->new($result, $self->json);
        }

        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    elsif ($result->content_type eq 'application/json')
    {
        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    else {
        return;
    }
}


sub _post {
    my ($self, $uri, $headers, $obj) = @_;
    my $json = $self->json;

    $obj->{version} ||= $self->{version} || '1.1';

    if ($obj->{version} eq '1.0') {
        delete $obj->{version};
        if (exists $obj->{id}) {
            $self->id($obj->{id}) if ($obj->{id}); # if undef, it is notification.
        }
        else {
            $obj->{id} = $self->id || ($self->id('JSON::RPC::Client'));
        }
    }
    else {
        # $obj->{id} = $self->id if (defined $self->id);
	# Assign a random number to the id if one hasn't been set
	$obj->{id} = (defined $self->id) ? $self->id : substr(rand(),2);
    }

    my $content = $json->encode($obj);

    $self->ua->post(
        $uri,
        Content_Type   => $self->{content_type},
        Content        => $content,
        Accept         => 'application/json',
	@$headers,
	($self->{token} ? (Authorization => $self->{token}) : ()),
    );
}



1;
