# CKY-Parser
Cocke-Kasami-Younger Parser

## Computation
* Parsed and validated PCFG grammar rules
* Implemented vanilla CKY algorithm to check if the grammar can parse the input sentence
* Created a probabilistic parser with backpointers to produce the most probable parse for input sentence
* Retrieved the parse tree from the backpointers

## Evaluation
* Obtained set of spans in each tree including nonterminals
* Computed precision, recall and F-score between predicted tree and target tree
* Reported coverage, average F-score for parsed sentences and all sentences
