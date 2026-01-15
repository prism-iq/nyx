#!/usr/bin/perl
# NYXX QUANTUM - Post-Quantique (Core Perl)
use strict;
use warnings;
use Digest::SHA qw(sha256_hex);
use MIME::Base64;
use Time::HiRes qw(gettimeofday);

use constant { DIM => 128, MOD => 3329 };

sub qseed {
    my ($s,$u) = gettimeofday();
    sha256_hex("$s:$u:$$:" . rand());
}

sub prng {
    my ($seed, $n) = @_;
    my @o; my $st = $seed;
    for (1..$n) { $st = sha256_hex($st); push @o, hex(substr($st,0,4)) % MOD; }
    return @o;
}

sub keygen {
    my $seed = qseed();
    my @sk = prng($seed, DIM);
    my @pk = map { ($sk[$_] * (($_+1) % DIM + 1)) % MOD } (0..DIM-1);
    return { pk => encode_base64(pack("S*",@pk),''), seed => substr($seed,0,32) };
}

sub trigger {
    my $a = shift || 'ping';
    my $k = keygen();
    my $sig = sha256_hex($k->{seed} . $a . time());
    print "TOKEN=" . substr($sig,0,32) . "\n";
    print "QSIG=" . substr($k->{pk},0,32) . "\n";
}

@ARGV ? trigger(join(' ',@ARGV)) : do {
    my $k = keygen();
    print "=== NYXX QUANTUM ===\nSeed: $k->{seed}\nStatus: READY\n";
};
