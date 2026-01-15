"""
CIPHER NLP Extraction Module

Advanced claim extraction using spaCy for:
- Named Entity Recognition (scientific terms)
- Dependency parsing (causal relationships)
- Linguistic feature analysis
- Confidence scoring based on hedging/certainty markers

Improves on regex-based extraction with linguistic understanding.
"""

import logging
import re
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Lazy load spaCy to avoid import overhead
_nlp = None
_nlp_model = "en_core_web_sm"


def get_nlp():
    """Lazy load spaCy model."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            logger.info(f"Loading spaCy model: {_nlp_model}")
            _nlp = spacy.load(_nlp_model)
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.warning(f"spaCy model {_nlp_model} not found. Run: python -m spacy download {_nlp_model}")
            raise ImportError(f"spaCy model {_nlp_model} not installed")
    return _nlp


class ClaimType(Enum):
    """Types of scientific claims"""
    HYPOTHESIS = "hypothesis"
    FINDING = "finding"
    METHOD = "method"
    DEFINITION = "definition"
    OBSERVATION = "observation"
    CONCLUSION = "conclusion"


class EvidenceStrength(Enum):
    """Strength of evidence for a claim"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    DEFINITIVE = "definitive"


@dataclass
class CausalRelation:
    """A causal relationship extracted from text"""
    cause: str
    effect: str
    relation_type: str  # causes, leads_to, results_in, correlates_with
    confidence: float
    negated: bool = False
    hedged: bool = False


@dataclass
class ScientificEntity:
    """An extracted scientific entity"""
    text: str
    label: str  # CHEMICAL, DISEASE, GENE, ORGANISM, etc.
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class ExtractedClaim:
    """A claim extracted with NLP analysis"""
    text: str
    claim_type: ClaimType
    confidence: float
    evidence_strength: EvidenceStrength
    entities: List[ScientificEntity]
    causal_relations: List[CausalRelation]
    hedging_markers: List[str]
    certainty_markers: List[str]
    negation: bool
    statistical_info: Dict[str, Any]
    source_sentence: str


class NLPExtractor:
    """
    Advanced NLP-based claim extraction.

    Uses spaCy for linguistic analysis and custom rules
    for scientific text understanding.
    """

    # Hedging markers (indicate uncertainty)
    HEDGING_MARKERS = {
        'may', 'might', 'could', 'possibly', 'perhaps', 'probably',
        'likely', 'unlikely', 'suggests', 'appears', 'seems',
        'potentially', 'presumably', 'arguably', 'tentatively',
        'preliminary', 'initial', 'exploratory', 'speculative'
    }

    # Certainty markers (indicate confidence)
    CERTAINTY_MARKERS = {
        'clearly', 'definitely', 'certainly', 'undoubtedly',
        'demonstrates', 'proves', 'establishes', 'confirms',
        'conclusively', 'significantly', 'strongly', 'robustly'
    }

    # Causal verbs and phrases
    CAUSAL_PATTERNS = {
        'causes': 'causes',
        'leads to': 'leads_to',
        'results in': 'results_in',
        'produces': 'causes',
        'induces': 'causes',
        'triggers': 'causes',
        'promotes': 'promotes',
        'inhibits': 'inhibits',
        'prevents': 'prevents',
        'reduces': 'reduces',
        'increases': 'increases',
        'enhances': 'enhances',
        'modulates': 'modulates',
        'regulates': 'regulates',
        'affects': 'affects',
        'influences': 'influences',
        'is associated with': 'correlates_with',
        'correlates with': 'correlates_with',
        'is linked to': 'correlates_with',
        'is related to': 'correlates_with',
    }

    # Claim type indicators
    FINDING_VERBS = {
        'found', 'discovered', 'observed', 'showed', 'demonstrated',
        'revealed', 'identified', 'detected', 'measured', 'recorded',
        'confirmed', 'established', 'determined', 'documented'
    }

    HYPOTHESIS_VERBS = {
        'hypothesize', 'propose', 'suggest', 'predict', 'postulate',
        'theorize', 'speculate', 'conjecture', 'assume', 'expect'
    }

    METHOD_VERBS = {
        'developed', 'designed', 'created', 'implemented', 'introduced',
        'applied', 'used', 'employed', 'utilized', 'constructed'
    }

    DEFINITION_MARKERS = {
        'defined as', 'refers to', 'known as', 'termed', 'called',
        'is a', 'are a', 'represents', 'constitutes', 'means'
    }

    # Scientific entity patterns (for custom NER)
    SCIENTIFIC_PATTERNS = [
        # Chemical compounds
        (r'\b[A-Z][a-z]?(?:\d+[A-Z][a-z]?\d*)+\b', 'CHEMICAL'),
        # Gene names (often italicized or uppercase)
        (r'\b[A-Z]{2,}[0-9]*\b', 'GENE'),
        # Protein names
        (r'\b[A-Z][a-z]+(?:ase|in|or|er)\b', 'PROTEIN'),
        # Measurements
        (r'\b\d+(?:\.\d+)?\s*(?:mg|kg|ml|µl|nm|µm|mm|cm|m|Hz|kHz|MHz|mV|µV)\b', 'MEASUREMENT'),
        # P-values
        (r'p\s*[<>=]\s*0?\.\d+', 'P_VALUE'),
        # Effect sizes
        (r'\b(?:d|r|η²?|ω²?)\s*=\s*-?\d+\.?\d*\b', 'EFFECT_SIZE'),
        # Sample sizes
        (r'\b[Nn]\s*=\s*\d+\b', 'SAMPLE_SIZE'),
        # Confidence intervals
        (r'\b(?:CI|confidence interval)\s*[:=]?\s*\[?\d+\.?\d*\s*[-–,]\s*\d+\.?\d*\]?', 'CI'),
    ]

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize the NLP extractor.

        Args:
            model_name: spaCy model to use
        """
        global _nlp_model
        _nlp_model = model_name
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), label)
            for pattern, label in self.SCIENTIFIC_PATTERNS
        ]

    def extract_claims(
        self,
        text: str,
        title: str = "",
        min_confidence: float = 0.3
    ) -> List[ExtractedClaim]:
        """
        Extract claims from scientific text.

        Args:
            text: Abstract or full text
            title: Paper title (provides context)
            min_confidence: Minimum confidence threshold

        Returns:
            List of ExtractedClaim objects
        """
        if not text or len(text.strip()) < 20:
            return []

        nlp = get_nlp()
        doc = nlp(text)

        claims = []

        for sent in doc.sents:
            sent_text = sent.text.strip()

            # Skip very short sentences
            if len(sent_text) < 30:
                continue

            # Analyze the sentence
            claim_type = self._classify_claim_type(sent)
            if claim_type is None:
                continue

            # Extract linguistic features
            hedging = self._find_hedging_markers(sent)
            certainty = self._find_certainty_markers(sent)
            negation = self._detect_negation(sent)

            # Calculate confidence
            confidence = self._calculate_confidence(
                sent, claim_type, hedging, certainty, negation
            )

            if confidence < min_confidence:
                continue

            # Extract entities
            entities = self._extract_entities(sent)

            # Extract causal relations
            causal_relations = self._extract_causal_relations(sent)

            # Extract statistical info
            stats = self._extract_statistical_info(sent_text)

            # Determine evidence strength
            evidence_strength = self._determine_evidence_strength(
                claim_type, stats, certainty, hedging
            )

            claims.append(ExtractedClaim(
                text=sent_text,
                claim_type=claim_type,
                confidence=confidence,
                evidence_strength=evidence_strength,
                entities=entities,
                causal_relations=causal_relations,
                hedging_markers=hedging,
                certainty_markers=certainty,
                negation=negation,
                statistical_info=stats,
                source_sentence=sent_text
            ))

        return claims

    def _classify_claim_type(self, sent) -> Optional[ClaimType]:
        """Classify the type of claim in a sentence."""
        text_lower = sent.text.lower()

        # Check for definition markers first
        for marker in self.DEFINITION_MARKERS:
            if marker in text_lower:
                return ClaimType.DEFINITION

        # Analyze verb lemmas
        verbs = [token.lemma_.lower() for token in sent if token.pos_ == "VERB"]

        # Check for finding verbs
        if any(v in self.FINDING_VERBS for v in verbs):
            return ClaimType.FINDING

        # Check for hypothesis verbs
        if any(v in self.HYPOTHESIS_VERBS for v in verbs):
            return ClaimType.HYPOTHESIS

        # Check for method verbs
        if any(v in self.METHOD_VERBS for v in verbs):
            return ClaimType.METHOD

        # Check for causal language (indicates finding or hypothesis)
        for pattern in self.CAUSAL_PATTERNS:
            if pattern in text_lower:
                # If hedged, it's a hypothesis; otherwise finding
                if any(h in text_lower for h in self.HEDGING_MARKERS):
                    return ClaimType.HYPOTHESIS
                return ClaimType.FINDING

        # Check for statistical markers (usually findings)
        if re.search(r'p\s*[<>=]|significant|correlated?|effect size', text_lower):
            return ClaimType.FINDING

        # Check for conclusion markers
        conclusion_markers = ['conclude', 'conclusion', 'therefore', 'thus', 'hence']
        if any(m in text_lower for m in conclusion_markers):
            return ClaimType.CONCLUSION

        # Check for observation markers
        observation_markers = ['observed', 'noted', 'noticed', 'seen', 'appeared']
        if any(m in text_lower for m in observation_markers):
            return ClaimType.OBSERVATION

        return None  # Not a classifiable claim

    def _find_hedging_markers(self, sent) -> List[str]:
        """Find hedging markers in sentence."""
        found = []
        text_lower = sent.text.lower()

        for marker in self.HEDGING_MARKERS:
            if marker in text_lower:
                found.append(marker)

        return found

    def _find_certainty_markers(self, sent) -> List[str]:
        """Find certainty markers in sentence."""
        found = []
        text_lower = sent.text.lower()

        for marker in self.CERTAINTY_MARKERS:
            if marker in text_lower:
                found.append(marker)

        return found

    def _detect_negation(self, sent) -> bool:
        """Detect if the main claim is negated."""
        for token in sent:
            if token.dep_ == "neg":
                # Check if negation is attached to main verb
                if token.head.pos_ == "VERB":
                    return True

        # Check for negative words
        negative_words = {'no', 'not', 'never', 'neither', 'nor', 'none', 'cannot', "n't"}
        for token in sent:
            if token.text.lower() in negative_words:
                return True

        return False

    def _calculate_confidence(
        self,
        sent,
        claim_type: ClaimType,
        hedging: List[str],
        certainty: List[str],
        negation: bool
    ) -> float:
        """Calculate confidence score for a claim."""
        # Base confidence by claim type
        base_confidence = {
            ClaimType.FINDING: 0.7,
            ClaimType.HYPOTHESIS: 0.5,
            ClaimType.METHOD: 0.8,
            ClaimType.DEFINITION: 0.9,
            ClaimType.OBSERVATION: 0.6,
            ClaimType.CONCLUSION: 0.65,
        }

        confidence = base_confidence.get(claim_type, 0.5)

        # Adjust for hedging (reduces confidence)
        confidence -= len(hedging) * 0.08

        # Adjust for certainty markers (increases confidence)
        confidence += len(certainty) * 0.05

        # Negation slightly reduces confidence (harder to interpret)
        if negation:
            confidence -= 0.05

        # Sentence length penalty (very long sentences are often complex/uncertain)
        word_count = len([t for t in sent if not t.is_punct])
        if word_count > 50:
            confidence -= 0.1
        elif word_count < 10:
            confidence -= 0.15  # Too short, may lack context

        return max(0.1, min(0.95, confidence))

    def _extract_entities(self, sent) -> List[ScientificEntity]:
        """Extract scientific entities from sentence."""
        entities = []

        # Use spaCy NER
        for ent in sent.ents:
            # Map spaCy labels to our scientific labels
            label_map = {
                'ORG': 'ORGANIZATION',
                'PERSON': 'RESEARCHER',
                'GPE': 'LOCATION',
                'DATE': 'DATE',
                'CARDINAL': 'NUMBER',
                'PERCENT': 'PERCENTAGE',
            }

            label = label_map.get(ent.label_, ent.label_)

            entities.append(ScientificEntity(
                text=ent.text,
                label=label,
                start=ent.start_char,
                end=ent.end_char,
                confidence=0.8
            ))

        # Apply custom scientific patterns
        sent_text = sent.text
        for pattern, label in self._compiled_patterns:
            for match in pattern.finditer(sent_text):
                # Avoid duplicates
                is_duplicate = any(
                    e.start <= match.start() < e.end or
                    e.start < match.end() <= e.end
                    for e in entities
                )

                if not is_duplicate:
                    entities.append(ScientificEntity(
                        text=match.group(),
                        label=label,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.9
                    ))

        # Extract noun chunks as potential scientific concepts
        for chunk in sent.noun_chunks:
            # Filter for likely scientific terms
            if self._is_scientific_term(chunk):
                is_duplicate = any(
                    e.text.lower() == chunk.text.lower()
                    for e in entities
                )

                if not is_duplicate:
                    entities.append(ScientificEntity(
                        text=chunk.text,
                        label='CONCEPT',
                        start=chunk.start_char,
                        end=chunk.end_char,
                        confidence=0.7
                    ))

        return entities

    def _is_scientific_term(self, chunk) -> bool:
        """Determine if a noun chunk is likely a scientific term."""
        text = chunk.text.lower()

        # Skip common non-scientific phrases
        skip_phrases = {
            'this', 'that', 'these', 'those', 'it', 'they',
            'we', 'our', 'the study', 'the results', 'the data',
            'the findings', 'the analysis', 'the present study'
        }

        if text in skip_phrases:
            return False

        # Scientific suffixes
        scientific_suffixes = [
            'tion', 'sion', 'ment', 'ity', 'ness', 'ism', 'ase',
            'ine', 'ide', 'ate', 'oid', 'gen', 'logy', 'pathy'
        ]

        for suffix in scientific_suffixes:
            if text.endswith(suffix):
                return True

        # Multi-word technical terms
        if len(chunk) >= 2 and any(t.pos_ == "ADJ" for t in chunk):
            return True

        return False

    def _extract_causal_relations(self, sent) -> List[CausalRelation]:
        """Extract causal relations from sentence using dependency parsing."""
        relations = []
        text_lower = sent.text.lower()

        # Find causal patterns
        for pattern, rel_type in self.CAUSAL_PATTERNS.items():
            if pattern in text_lower:
                # Try to extract cause and effect using dependency parsing
                relation = self._parse_causal_structure(sent, pattern, rel_type)
                if relation:
                    relations.append(relation)

        return relations

    def _parse_causal_structure(
        self,
        sent,
        pattern: str,
        rel_type: str
    ) -> Optional[CausalRelation]:
        """Parse the causal structure of a sentence."""
        # Find the causal verb/phrase
        text_lower = sent.text.lower()
        pattern_start = text_lower.find(pattern)

        if pattern_start == -1:
            return None

        # Find subjects and objects
        subjects = []
        objects = []

        for token in sent:
            if token.dep_ in ("nsubj", "nsubjpass"):
                # Get the full noun phrase
                subtree = list(token.subtree)
                subjects.append(" ".join(t.text for t in subtree))
            elif token.dep_ in ("dobj", "pobj", "attr"):
                subtree = list(token.subtree)
                objects.append(" ".join(t.text for t in subtree))

        if not subjects or not objects:
            return None

        # Check for negation
        negated = self._detect_negation(sent)

        # Check for hedging
        hedging = self._find_hedging_markers(sent)

        return CausalRelation(
            cause=subjects[0] if subjects else "",
            effect=objects[0] if objects else "",
            relation_type=rel_type,
            confidence=0.6 if hedging else 0.8,
            negated=negated,
            hedged=bool(hedging)
        )

    def _extract_statistical_info(self, text: str) -> Dict[str, Any]:
        """Extract statistical information from text."""
        stats = {}

        # P-value
        p_match = re.search(r'p\s*([<>=])\s*(0?\.\d+)', text, re.IGNORECASE)
        if p_match:
            stats['p_value'] = {
                'operator': p_match.group(1),
                'value': float(p_match.group(2))
            }

        # Sample size
        n_match = re.search(r'\b[Nn]\s*=\s*(\d+)', text)
        if n_match:
            stats['sample_size'] = int(n_match.group(1))

        # Effect size
        effect_match = re.search(
            r'\b(d|r|η²?|Cohen\'?s?\s*d)\s*=\s*(-?\d+\.?\d*)',
            text, re.IGNORECASE
        )
        if effect_match:
            stats['effect_size'] = {
                'type': effect_match.group(1),
                'value': float(effect_match.group(2))
            }

        # Confidence interval
        ci_match = re.search(
            r'(?:CI|confidence interval)[:\s]*\[?(\d+\.?\d*)\s*[-–,]\s*(\d+\.?\d*)\]?',
            text, re.IGNORECASE
        )
        if ci_match:
            stats['confidence_interval'] = {
                'lower': float(ci_match.group(1)),
                'upper': float(ci_match.group(2))
            }

        # Percentage
        pct_match = re.search(r'(\d+\.?\d*)\s*%', text)
        if pct_match:
            stats['percentage'] = float(pct_match.group(1))

        return stats

    def _determine_evidence_strength(
        self,
        claim_type: ClaimType,
        stats: Dict[str, Any],
        certainty: List[str],
        hedging: List[str]
    ) -> EvidenceStrength:
        """Determine the strength of evidence for a claim."""
        # Definitions are always strong
        if claim_type == ClaimType.DEFINITION:
            return EvidenceStrength.DEFINITIVE

        # Methods are typically strong
        if claim_type == ClaimType.METHOD:
            return EvidenceStrength.STRONG

        # Statistical evidence
        if 'p_value' in stats:
            p_val = stats['p_value']['value']
            if p_val < 0.001:
                return EvidenceStrength.STRONG
            elif p_val < 0.05:
                return EvidenceStrength.MODERATE

        # Effect size
        if 'effect_size' in stats:
            effect = abs(stats['effect_size']['value'])
            if effect > 0.8:
                return EvidenceStrength.STRONG
            elif effect > 0.5:
                return EvidenceStrength.MODERATE

        # Sample size
        if 'sample_size' in stats:
            n = stats['sample_size']
            if n > 1000:
                return EvidenceStrength.STRONG
            elif n > 100:
                return EvidenceStrength.MODERATE

        # Certainty vs hedging
        if certainty and not hedging:
            return EvidenceStrength.MODERATE

        if hedging and not certainty:
            return EvidenceStrength.WEAK

        # Default based on claim type
        if claim_type == ClaimType.FINDING:
            return EvidenceStrength.MODERATE

        return EvidenceStrength.WEAK

    def extract_entities_only(self, text: str) -> List[ScientificEntity]:
        """Extract only entities from text (faster than full claim extraction)."""
        nlp = get_nlp()
        doc = nlp(text)

        all_entities = []
        for sent in doc.sents:
            entities = self._extract_entities(sent)
            all_entities.extend(entities)

        # Deduplicate by text
        seen = set()
        unique_entities = []
        for ent in all_entities:
            key = ent.text.lower()
            if key not in seen:
                seen.add(key)
                unique_entities.append(ent)

        return unique_entities

    def extract_causal_relations_only(self, text: str) -> List[CausalRelation]:
        """Extract only causal relations from text."""
        nlp = get_nlp()
        doc = nlp(text)

        all_relations = []
        for sent in doc.sents:
            relations = self._extract_causal_relations(sent)
            all_relations.extend(relations)

        return all_relations


# Singleton instance
_extractor: Optional[NLPExtractor] = None


def get_nlp_extractor() -> NLPExtractor:
    """Get or create the global NLP extractor."""
    global _extractor
    if _extractor is None:
        _extractor = NLPExtractor()
    return _extractor


# Convenience functions
def extract_claims(text: str, title: str = "") -> List[ExtractedClaim]:
    """Extract claims from text using default extractor."""
    extractor = get_nlp_extractor()
    return extractor.extract_claims(text, title)


def extract_entities(text: str) -> List[ScientificEntity]:
    """Extract scientific entities from text."""
    extractor = get_nlp_extractor()
    return extractor.extract_entities_only(text)


def extract_causal_relations(text: str) -> List[CausalRelation]:
    """Extract causal relations from text."""
    extractor = get_nlp_extractor()
    return extractor.extract_causal_relations_only(text)
