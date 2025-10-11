#!/usr/bin/perl
use strict;
use warnings;
use File::Find;
use File::Copy;

my $total_files = 0;
my $modified_files = 0;
my @emojis_found = ();

print "=== PROFESSIONAL EMOJI REMOVAL ===\n";
print "Cleaning repository for professional presentation\n\n";

# Define emoji patterns to remove
my $emoji_pattern = qr/
    [\x{1F300}-\x{1F9FF}]  | # Emoticons, misc symbols, etc
    [\x{2600}-\x{26FF}]    | # Miscellaneous symbols
    [\x{2700}-\x{27BF}]    | # Dingbats
    [\x{1F600}-\x{1F64F}]  | # Emoticons
    [\x{1F680}-\x{1F6FF}]  | # Transport and map symbols
    [\x{1F900}-\x{1F9FF}]  | # Supplemental symbols
    [\x{2B50}]             | # Star
    [\x{1F4A1}]            | # Light bulb
    [\x{1F50D}]            | # Magnifying glass
    [\x{1F916}]            | # Robot
    [\x{2699}]             | # Gear
    [\x{1F4DD}]            | # Memo
    [\x{2705}]             | # Check mark
    [\x{1F3AF}]            | # Target
    [\x{1F680}]            | # Rocket
    [\x{2728}]             | # Sparkles
    [\x{1F389}]            | # Party
    [\x{1F31F}]            | # Star2
    [\x{1F4BB}]            | # Computer
    [\x{1F6E1}]            | # Shield
    [\x{1F31E}]            | # Sun
    [\x{26A1}]             | # Lightning
    [\x{1F527}]            | # Wrench
    [\x{1F319}]            | # Moon
    [\x{1F310}]            | # Globe
    [\x{1F512}]            | # Lock
    [\x{1F6E0}]            | # Tools
    [\x{1F4CA}]            | # Chart
    [\x{1F9E9}]            | # Puzzle
    [\x{1F517}]            | # Link
    [\x{1F4A5}]            | # Boom
    [\x{1F525}]            | # Fire
    [\x{1F4AF}]            | # 100
    [\x{1F44D}]            | # Thumbs up
    [\x{1F44E}]            | # Thumbs down
    [\x{1F44F}]            | # Clap
    [\x{1F4AA}]            | # Muscle
    [\x{1F47E}]            | # Alien
    [\x{1F3C6}]            | # Trophy
    [\x{1F947}]            | # 1st place medal
    [\x{1F948}]            | # 2nd place medal
    [\x{1F949}]              # 3rd place medal
/x;

# Process file
sub process_file {
    my $file = shift;
    return unless -f $file;
    return if $file =~ /\.git/;
    return if $file =~ /node_modules/;
    return if $file =~ /\.bak$/;

    # Only process text files
    return unless $file =~ /\.(md|astro|tsx?|jsx?|html|css|json|yml|yaml|txt)$/i;

    open(my $fh, '<:utf8', $file) or die "Can't open $file: $!";
    my @lines = <$fh>;
    close($fh);

    my $content = join('', @lines);
    my $original = $content;

    # Remove emojis
    $content =~ s/$emoji_pattern//g;

    # If content changed, write it back
    if ($content ne $original) {
        # Backup original
        copy($file, "$file.bak") or die "Copy failed: $!";

        open(my $out, '>:utf8', $file) or die "Can't write to $file: $!";
        print $out $content;
        close($out);

        unlink("$file.bak");

        print "  [CLEANED] $file\n";
        $modified_files++;
    }

    $total_files++;
}

# Find all files to process
my $base_dir = '/home/jeremy/projects/claude-code-plugins';
find(\&process_file, $base_dir);

print "\n=== EMOJI REMOVAL COMPLETE ===\n";
print "Total files processed: $total_files\n";
print "Files modified: $modified_files\n";
print "\nRepository is now professional and emoji-free.\n";