#!/usr/bin/env perl
# ARN.pl - transcription dynamique, regex hardcore
# Pattern extraction cross-domain pour Flow

use strict;
use warnings;
use utf8;
use JSON;
use HTTP::Daemon;
use HTTP::Status;
use HTTP::Response;
use LWP::UserAgent;
use Time::HiRes qw(time);
use POSIX qw(strftime);

binmode(STDOUT, ":utf8");

my $PORT = 8105;
my $json = JSON->new->utf8->allow_nonref;

# === PATTERN DATABASE ===
my %patterns = (
    # Émotions - patterns complexes
    emotion => {
        joy => qr/\b(heureux|content|joie|ravi|excité|super|génial|cool|nice|happy|glad)\b/i,
        sad => qr/\b(triste|déprimé|mal|douleur|peine|sad|down|hurt|pain)\b/i,
        anger => qr/\b(colère|énervé|furieux|rage|angry|pissed|mad)\b/i,
        fear => qr/\b(peur|angoisse|anxieux|terrifié|afraid|scared|anxious)\b/i,
        void => qr/\b(vide|néant|rien|empty|void|nothing|hollow)\b/i,
    },

    # Intentions
    intent => {
        question => qr/^(qui|que|quoi|où|quand|comment|pourquoi|est-ce|what|who|where|when|why|how|is\s+there)\b.*\??$/i,
        command => qr/^(fais|fait|dis|montre|explique|calcule|do|show|tell|explain|compute|run)\b/i,
        greeting => qr/^(salut|hey|yo|hi|hello|coucou|bonjour|bonsoir)\s*[!.]?$/i,
        farewell => qr/\b(bye|ciao|adieu|au revoir|à plus|later|see ya)\b/i,
        affirmation => qr/^(oui|ouais|yep|yeah|yes|ok|d'accord|sure|bien sûr)\s*[!.]?$/i,
        negation => qr/^(non|nope|no|nan|jamais|never)\s*[!.]?$/i,
    },

    # Domaines CIPHER
    domain => {
        math => qr/\b(equation|theorem|proof|algorithm|calcul|matrice|integral|derivative|fonction|set|graph|topology)\b/i,
        neuro => qr/\b(neuron|synapse|brain|cortex|memory|cognition|perception|consciousness)\b/i,
        bio => qr/\b(cell|dna|rna|protein|enzyme|organism|evolution|mutation|genome)\b/i,
        psycho => qr/\b(behavior|emotion|personality|trauma|therapy|unconscious|ego|id)\b/i,
        med => qr/\b(diagnosis|symptom|treatment|disease|pathology|patient|clinical)\b/i,
        art => qr/\b(beauty|aesthetic|creation|expression|form|color|music|poetry)\b/i,
        philo => qr/\b(existence|being|truth|meaning|ethics|metaphysics|epistemology|ontology)\b/i,
    },

    # Entités
    entity => {
        code => qr/`([^`]+)`|```(\w+)?\n([\s\S]*?)```/,
        url => qr{(https?://[^\s<>"{}|\\^`\[\]]+)},
        email => qr/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/,
        number => qr/\b(\d+(?:\.\d+)?)\b/,
        path => qr{(/[\w./-]+)},
        mention => qr/@(\w+)/,
        hashtag => qr/#(\w+)/,
    },

    # Structures syntaxiques
    syntax => {
        conditional => qr/\b(si|if|when|lorsque|quand)\b.+\b(alors|then|donc)\b/i,
        comparison => qr/\b(plus|moins|mieux|pire|comme|more|less|better|worse|like)\b.*\b(que|than)\b/i,
        sequence => qr/\b(d'abord|ensuite|puis|enfin|first|then|next|finally)\b/i,
        cause => qr/\b(parce que|car|donc|ainsi|because|since|therefore|so)\b/i,
    },
);

# === EXTRACTION ENGINE ===
sub extract_all {
    my ($text) = @_;
    my %results;

    for my $category (keys %patterns) {
        $results{$category} = {};
        for my $type (keys %{$patterns{$category}}) {
            my @matches = $text =~ /$patterns{$category}{$type}/g;
            $results{$category}{$type} = \@matches if @matches;
        }
    }

    # Cleanup empty categories
    for my $cat (keys %results) {
        delete $results{$cat} unless keys %{$results{$cat}};
    }

    return \%results;
}

# === INTENT CLASSIFIER ===
sub classify_intent {
    my ($text) = @_;

    for my $intent (keys %{$patterns{intent}}) {
        return $intent if $text =~ /$patterns{intent}{$intent}/;
    }
    return 'statement';
}

# === DOMAIN DETECTOR ===
sub detect_domains {
    my ($text) = @_;
    my @domains;

    for my $domain (keys %{$patterns{domain}}) {
        push @domains, $domain if $text =~ /$patterns{domain}{$domain}/;
    }

    return @domains ? \@domains : ['general'];
}

# === EMOTION ANALYZER ===
sub analyze_emotion {
    my ($text) = @_;
    my %scores;

    for my $emotion (keys %{$patterns{emotion}}) {
        my @matches = $text =~ /$patterns{emotion}{$emotion}/g;
        $scores{$emotion} = scalar @matches if @matches;
    }

    # Normalize
    my $total = 0;
    $total += $_ for values %scores;
    if ($total > 0) {
        $scores{$_} /= $total for keys %scores;
    }

    # Dominant emotion
    my ($dominant) = sort { $scores{$b} <=> $scores{$a} } keys %scores;

    return {
        scores => \%scores,
        dominant => $dominant // 'neutral',
        intensity => $total
    };
}

# === DYNAMIC SCRIPT EXECUTION ===
my %scripts = ();

sub register_script {
    my ($name, $code) = @_;
    # Compile the regex or code pattern
    eval {
        $scripts{$name} = {
            code => $code,
            compiled => eval "sub { my \$text = shift; $code }",
            created => time()
        };
    };
    return $@ ? { error => $@ } : { registered => $name };
}

sub run_script {
    my ($name, $text) = @_;
    return { error => "Unknown script: $name" } unless exists $scripts{$name};

    my $result;
    eval {
        $result = $scripts{$name}{compiled}->($text);
    };
    return $@ ? { error => $@ } : { result => $result };
}

# === CROSS-DOMAIN CORRELATION ===
sub correlate {
    my ($text) = @_;

    my $entities = extract_all($text);
    my $intent = classify_intent($text);
    my $domains = detect_domains($text);
    my $emotion = analyze_emotion($text);

    # Build correlation matrix
    my %correlation = (
        text => $text,
        length => length($text),
        word_count => scalar(split /\s+/, $text),
        timestamp => strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
        analysis => {
            intent => $intent,
            domains => $domains,
            emotion => $emotion,
            entities => $entities,
        },
        # Meta-patterns
        complexity => _calculate_complexity($text, $entities),
        signature => _generate_signature($intent, $domains, $emotion->{dominant}),
    );

    return \%correlation;
}

sub _calculate_complexity {
    my ($text, $entities) = @_;

    my $score = 0;
    $score += 1 for $text =~ /[,;:]/g;  # punctuation complexity
    $score += 2 for $text =~ /\b(et|ou|mais|donc|or|and|but|however)\b/gi;  # connectors
    $score += 3 for keys %$entities;  # entity diversity

    return $score;
}

sub _generate_signature {
    my ($intent, $domains, $emotion) = @_;
    my $d = join('.', sort @$domains);
    return "$intent:$d:$emotion";
}

# === HTTP SERVER ===
sub handle_request {
    my ($req) = @_;

    my $path = $req->uri->path;
    my $method = $req->method;

    # Health check
    if ($path eq '/health') {
        return {
            organ => 'arn',
            status => 'transcribing',
            patterns => scalar(keys %patterns),
            scripts => scalar(keys %scripts),
        };
    }

    # POST endpoints
    if ($method eq 'POST') {
        my $body = $req->content;
        my $data = eval { $json->decode($body) } // {};

        if ($path eq '/extract') {
            my $text = $data->{text} // '';
            return extract_all($text);
        }

        if ($path eq '/classify') {
            my $text = $data->{text} // '';
            return {
                intent => classify_intent($text),
                domains => detect_domains($text),
                emotion => analyze_emotion($text),
            };
        }

        if ($path eq '/correlate') {
            my $text = $data->{text} // '';
            return correlate($text);
        }

        if ($path eq '/script/register') {
            my $name = $data->{name} // return { error => 'name required' };
            my $code = $data->{code} // return { error => 'code required' };
            return register_script($name, $code);
        }

        if ($path eq '/script/run') {
            my $name = $data->{name} // return { error => 'name required' };
            my $text = $data->{text} // '';
            return run_script($name, $text);
        }

        if ($path eq '/process') {
            # Generic processing
            my $text = $data->{text} // $data->{content} // '';
            return correlate($text);
        }
    }

    # GET endpoints
    if ($method eq 'GET') {
        if ($path eq '/patterns') {
            my %summary;
            for my $cat (keys %patterns) {
                $summary{$cat} = [keys %{$patterns{$cat}}];
            }
            return \%summary;
        }

        if ($path eq '/scripts') {
            my %info;
            for my $name (keys %scripts) {
                $info{$name} = {
                    created => $scripts{$name}{created},
                };
            }
            return \%info;
        }
    }

    return { error => 'not found', path => $path };
}

# === MAIN ===
print "🧬 ARN :$PORT - transcription dynamique\n";
print "   /extract    POST extraire patterns\n";
print "   /classify   POST classifier intent/domain/emotion\n";
print "   /correlate  POST analyse cross-domain\n";
print "   /patterns   GET  liste des patterns\n";
print "   /script/*   POST register/run scripts dynamiques\n";

my $daemon = HTTP::Daemon->new(
    LocalAddr => '127.0.0.1',
    LocalPort => $PORT,
    ReuseAddr => 1,
) or die "Cannot start server: $!";

while (my $conn = $daemon->accept) {
    while (my $req = $conn->get_request) {
        # CORS
        my $res = HTTP::Response->new(200);
        $res->header('Access-Control-Allow-Origin' => '*');
        $res->header('Access-Control-Allow-Methods' => 'GET, POST, OPTIONS');
        $res->header('Access-Control-Allow-Headers' => 'Content-Type');
        $res->header('Content-Type' => 'application/json; charset=utf-8');

        if ($req->method eq 'OPTIONS') {
            $conn->send_response($res);
            next;
        }

        my $result = handle_request($req);
        $res->content($json->encode($result));

        $conn->send_response($res);
    }
    $conn->close;
}
