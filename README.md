MedicalTagAnnotations2GATE
==========================

Converts several medical tag annotations to GATE compatible files.

bio_portal_tagger.py
--------------------
Annotates text files in a directory with SNOMED-CT ontology using NCBO Annotator (bioportal.bioontology.org) and converts the annotations into GATE 
(General Architecture for Text Engineering) compatible files. Change the input_dir and snomed_ct_output_dir in bio_portal_tagger.py accordingly to use this 
script. Uses the gate_template.xml as seed to file to generate GATE compatible xml files.

metamap_tagger.py
-----------------
Converts the metapmap (http://metamap.nlm.nih.gov/) tagged files to GATE compatible xml files. Change the input_dir in the script accordingly to use. Will 
store the output xml files in the same input_dir. Uses the gate_template.xml as seed to file to generate GATE compatible xml files.
