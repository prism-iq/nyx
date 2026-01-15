# Chapitre 1: Les Expériences de Levin

*Des preuves que le voltage encode la forme*

---

## Le Laboratoire

Michael Levin dirige le Allen Discovery Center à Tufts University. Son laboratoire étudie comment les organismes "savent" quelle forme construire.

La question fondamentale: Si vous coupez un planaire en morceaux, chaque morceau régénère un ver complet. Comment le fragment "sait-il" où faire la tête et où faire la queue?

## Expérience 1: Planaire à Deux Têtes

### Protocole
1. Couper un planaire (Dugesia japonica) en fragments
2. Exposer le fragment à des agents pharmacologiques qui modifient le potentiel membranaire
3. Observer la régénération

### Résultat Clé (Beane et al., 2011)
En dépolarisant les cellules de la "queue" d'un fragment, on peut induire la formation d'une **tête** à cet endroit.

**Données**:
- 100% des contrôles régénèrent normalement (tête/queue)
- 80%+ des traités dépolarisés forment deux têtes

### Interprétation
L'information "tête vs queue" n'est pas (seulement) génétique. Elle est encodée dans le **pattern bioélectrique** - les gradients de voltage entre cellules.

### Publication
Beane W.S. et al. (2011). "Bioelectric signaling regulates head and organ size during planarian regeneration." Development 138(3):449-58.

## Expérience 2: Yeux Ectopiques sur Têtard

### Protocole
1. Injecter des ARNm codant pour des canaux ioniques dans des cellules de têtard (Xenopus laevis)
2. Cibler des régions non destinées à former des yeux (dos, queue, flanc)
3. Observer le développement

### Résultat Clé (Pai et al., 2012)
Des **yeux fonctionnels** se forment à des positions ectopiques.

**Données**:
- Les yeux sont anatomiquement corrects (cristallin, rétine, nerf optique)
- Les têtards répondent à des stimuli lumineux (tests comportementaux)
- Les yeux fonctionnent même sans connexion directe au cerveau

### Interprétation
Le pattern bioélectrique ne dit pas seulement "où" mais aussi "quoi". Modifier le voltage active le **programme "œil"** même dans des tissus qui ne devaient pas en former.

### Publication
Pai V.P. et al. (2012). "Transmembrane voltage potential controls embryonic eye patterning in Xenopus laevis." Development 139(2):313-23.

## Expérience 3: Cancer et Dépolarisation

### Observation
Les cellules cancéreuses sont typiquement **dépolarisées** - leur potentiel membranaire est moins négatif que les cellules normales.

### Expérience (Blackiston et al., 2011)
Exposer des embryons de Xenopus à des carcinogènes, puis:
- Groupe A: aucun traitement
- Groupe B: hyperpolarisation forcée (canaux potassium)

### Résultat
Le groupe hyperpolarisé développe significativement moins de tumeurs.

### Interprétation
Le cancer n'est pas (seulement) un désordre génétique. C'est aussi un désordre **bioélectrique**. Les cellules "oublient" leur identité tissulaire quand elles perdent leur potentiel normal.

### Implication Thérapeutique
Restaurer le voltage normal pourrait être une stratégie anti-cancer non-génétique.

## Expérience 4: Xenobots

### Contexte
Collaboration Levin + Sam Kriegman (UVM) + Josh Bongard

### Protocole
1. Prendre des cellules de peau de grenouille (Xenopus laevis)
2. Les assembler en configurations prédites par algorithmes évolutifs
3. Observer leur comportement

### Résultats (Kriegman et al., 2020)
Les "xenobots" montrent:
- **Mouvement autonome** (sans neurones ni muscles)
- **Comportement collectif** (s'assemblent en groupes)
- **Auto-réplication cinétique** (assemblent d'autres xenobots à partir de cellules libres)

### Ce Qui N'a Pas Été Fait
Aucune modification génétique. Les mêmes gènes que dans une grenouille normale. Seule la **géométrie** et les **contraintes bioélectriques** changent.

### Implication
Le génome ne détermine pas directement la forme. Il fournit des **composants** que les patterns bioélectriques organisent.

## Le Code Bioélectrique

### Analogie Informatique (Levin)

| Biologie Classique | Vision Levin |
|-------------------|--------------|
| ADN = programme | ADN = liste de pièces |
| Développement = exécution | Développement = émergence |
| Gène → trait | Gène → protéine → pattern → trait |

Le "programme" n'est pas dans l'ADN. Il est dans le **pattern bioélectrique** qui organise les cellules.

### Les Canaux Ioniques Comme "Transistors"

| Électronique | Bioélectricité |
|--------------|----------------|
| Transistor | Canal ionique |
| Circuit | Tissu |
| Voltage | Potentiel membranaire |
| Signal digital | Pattern de polarisation |

Les cellules "calculent" avec des ions ce que les ordinateurs calculent avec des électrons.

## Données Quantitatives

### Potentiels Membranaires Typiques

| Type de cellule | Vm (mV) |
|-----------------|---------|
| Neurone au repos | -70 |
| Cellule musculaire | -90 |
| Cellule épithéliale | -30 à -50 |
| Cellule cancéreuse | -10 à -30 |
| Cellule embryonnaire | Variable |

### Seuils Critiques

- **Dépolarisation → prolifération**: autour de -30 mV
- **Hyperpolarisation → différenciation**: autour de -60 mV
- **Transition tête/queue** (planaire): ~20 mV de différence

## Ce Qui Reste à Découvrir

1. **Le code complet**: Quelle séquence de voltage produit quelle forme?
2. **La lecture**: Comment les cellules "décodent" le signal électrique?
3. **L'universalité**: Les mêmes patterns fonctionnent-ils chez tous les animaux?
4. **Applications**: Peut-on induire la régénération de membres humains?

## Critiques et Réponses

### Critique 1: "C'est corrélationnel"
**Réponse**: Les expériences montrent de la causalité. Changer le voltage CAUSE le changement de forme.

### Critique 2: "C'est spécifique aux planaires/grenouilles"
**Réponse**: Des résultats similaires existent chez d'autres espèces. Le mécanisme semble conservé.

### Critique 3: "Ça contredit la génétique"
**Réponse**: Non. Ça complète. Les gènes codent les protéines (canaux ioniques). Les patterns bioélectriques organisent les cellules.

---

## Sources Clés

- Beane W.S. et al. (2011). Development 138(3):449-58
- Pai V.P. et al. (2012). Development 139(2):313-23
- Blackiston D.J. et al. (2011). Dis Model Mech 4(1):67-85
- Kriegman S. et al. (2020). PNAS 117(4):1853-1859
- Levin M. (2021). BioSystems 209:104514

---

*"Le génome est le hardware. La bioélectricité est le software."* - Michael Levin
