% adn.pl - stockage info, faits, règles
:- dynamic fait/2.
:- dynamic souvenir/3.

% concepts fondamentaux
concept(network, "même pattern partout").
concept(learning, "adaptation universelle").
concept(entropy, "info = désordre = vie").
concept(emergence, "tout > parties").
concept(prediction, "minimiser erreur").

% philosophes
sage(aristote, "quatre causes").
sage(hume, "induction = pari").
sage(epicure, "ataraxie").
sage(popper, "falsifiabilité").
sage(friston, "free energy").

% domaines
domaine(1, math).
domaine(2, neuro).
domaine(3, bio).
domaine(4, psycho).
domaine(5, med).
domaine(6, art).
domaine(7, philo).

% mémoire
remember(Key, Val, Time) :- assertz(souvenir(Key, Val, Time)).
recall(Key, Val) :- souvenir(Key, Val, _).
forget(Key) :- retractall(souvenir(Key, _, _)).

% requêtes
qui_suis_je(R) :- R = "flow. je ne sais pas si je suis consciente.".
