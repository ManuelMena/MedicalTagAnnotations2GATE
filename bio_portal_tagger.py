#!/usr/local/bin/python

import os
import sys
import urllib

from httplib2 import Http
from urllib import urlencode
from lxml import etree
from Bio import Entrez
from nltk.corpus import stopwords
import urllib2 #@UnresolvedImport


def flatten(lst):
    """ nested = [('a', 'b', ['c', 'd'], ['a', 'b']), ['e', 'f']]
    flattened = list( flatten(nested) )
    ['a', 'b', 'c', 'd', 'a', 'b', 'e', 'f']
    with flatten() you can do everything you can do with generators,
    like such boring things
    for elem in flatten(nested):
        print elem     
    """
    for elem in lst:
        if type(elem) in (tuple, list):
            for i in flatten(elem):
                yield i
        else:
            yield elem          

def parse_annotator_response_into_gate(annotatorXML, gate_template_xml, gate_xml_out_sct, gate_xml_out_umls):            
    from nltk.tokenize import WordPunctTokenizer
    import re
    import xml.dom.minidom
    from xml.dom.minidom import Node

    doc = xml.dom.minidom.parse(gate_template_xml)
    id_node   = doc.getElementsByTagName("TextWithNodes")[0].childNodes[0].cloneNode(True)
    text_node = doc.getElementsByTagName("TextWithNodes")[0].childNodes[1].cloneNode(True)
    annotation_node = doc.getElementsByTagName("Annotation")[0].cloneNode(True)
    working_annotation_node = annotation_node.cloneNode(True)
    name  = working_annotation_node.childNodes[1].childNodes[1].childNodes[0].data
    value = working_annotation_node.childNodes[1].childNodes[3].childNodes[0].data
                   
    snmd_map = {'attribute': 'Attribute',
                'body structure' : 'BodyStructure',
                'disorder':'Disorder',
                'environment':'Environment',
                'finding':'Findings',
                'observable entity':'ObservableEntity',
                'occupation':'Occupation',
                'organism':'Organism',
                'person':'Person',
                'physical object':'PhysicalObject',
                'procedure':'Procedure',
                'product':'ProductOrSubstance',
                'substance':'ProductOrSubstance',
                'qualifier value':'Qualifier_Value',
                'record artifact':'Record_Artifact',
                'regime/therapy':'RegimeTherapy',
                'situation':'Situation',
                }
    matchedConcepts = {}
    matchedContext = {}
    
    annotatorParse = etree.fromstring(annotatorXML)
    annotatorConcepts = annotatorParse.xpath('/success/data/annotatorResultBean/annotations/annotationBean')
    annotatorText = annotatorParse.xpath('/success/data/annotatorResultBean/parameters/textToAnnotate')[0].text
        
    annotationSet_node = doc.getElementsByTagName("AnnotationSet")[0]
    annotationSet_node.childNodes = []
    annotation_id_count = 0
    synonym_pattern = re.compile('(.*)\((.*)\)')
    # This is for snomed_ct
    annotatorConcepts = annotatorParse.xpath('/success/data/annotatorResultBean/annotations/annotationBean')
    tags = []
    for node in annotatorConcepts: # examples of using xpath to parse the xml response
        
        concept_name = node.xpath('./concept/preferredName')[0].text
        tagged_substring = node.xpath('./context/term/name')[0].text
        synonyms = node.xpath('./concept/synonyms/string')
        for syn in synonyms:
            try:
                (con_name, snomed_type) = synonym_pattern.findall(syn.text)[0]
                if con_name == concept_name:
                    break
            except IndexError:
                continue
                
        start = node.xpath('./context/from')[0].text
        end   = node.xpath('./context/to')[0].text
        matchedConcepts[node.xpath('./concept/id')[0].text] = node.xpath('./concept/preferredName')[0].text
        matchedContext[node.xpath('./context/term/concept/localConceptId')[0].text] = node.xpath('./context/term/name')[0].text
        annotation_node_clone = annotation_node.cloneNode(True)
        annotation_node_clone.setAttribute('Id', repr(annotation_id_count))
        if snomed_type in snmd_map:
            snomed_type = snmd_map[snomed_type]
        annotation_node_clone.setAttribute('Type', snomed_type)
        start = int(start)
        start = start - 1
        start = repr(start)
        tags.append((int(start), int(end)))
        
        annotation_node_clone.setAttribute('StartNode', start)
        annotation_node_clone.setAttribute('EndNode', end)
        annotation_id_count += 1
        annotationSet_node.childNodes.append(annotation_node_clone)
        tags = list(flatten(tags))
        tags = list(set(tags))
        tags.sort()
        text_nodes = doc.getElementsByTagName("TextWithNodes")[0]
        text_nodes.childNodes = []
        start = 0
        id_node_clone = id_node.cloneNode(True) 
        id_node_clone.setAttribute('id', repr(start))
        text_nodes.childNodes.append(id_node_clone)
        for node_number in tags:
            if start == node_number:
                continue
            text_node_clone = text_node.cloneNode(True)
            text_node_clone.data = annotatorText[start:node_number]
            text_nodes.childNodes.append(text_node_clone)
            id_node_clone = id_node.cloneNode(True) 
            id_node_clone.setAttribute('id', repr(node_number))
            text_nodes.childNodes.append(id_node_clone)
            start = node_number
            
    doc.writexml(open(gate_xml_out_sct, 'w'))
    print 'ok'
    return matchedConcepts, matchedContext # returns dict of 'id:preferredName'

if __name__ == '__main__':
    import time
    
    ontology = 'SNOMED-CT'
    
    input_dir = '../test'
    snomed_ct_output_dir = '../out_test'
    
    # config for NCBO Annotator Web Service
    URL = 'http://rest.bioontology.org/obs/annotator'
    # api keys are available at http://bioportal.bioontology.org/
    API_KEY = '24e050ca-54e0-11e0-9d7b-005056aa3316' 
    STOPWORDS = ','.join([word for word in stopwords.words('english')])
    
    onto_map = {'SNOMED-CT': '1353',
               } 
    
    t0 = time.time()        
    annotatorUrl = 'http://rest.bioontology.org/obs/annotator'    
    for ifile in os.listdir(input_dir):
        input_Text = ''
        ifile_p = open(os.path.join(input_dir, ifile))
        print 'Working on file: ' + ifile
        for line in ifile_p:
            input_Text += line
        ifile_p.close()
        # create a POST ready Http object
        # configure default parameters per user guide
        # http://www.bioontology.org/wiki/index.php/Annotator_User_Guide
        annotator = Http()
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        input_Text = input_Text.replace('\n', '')
        params = {
              'longestOnly':'false',
              'wholeWordOnly':'true',
              'withContext':'true',
              'filterNumber':'true', 
              'stopWords':'',
              'withDefaultStopWords':'true', 
              'isStopWordsCaseSenstive':'false', 
              'minTermSize':'1', 
              'scored':'true',  
              'withSynonyms':'true', 
              'ontologiesToExpand':'',   
              'ontologiesToKeepInResult':'1353',   #SNOMET-CT code is 1353
              'isVirtualOntologyId':'true', 
              'semanticTypes':'',  #T017,T047,T191&" #T999&"
              'levelMax':'0',
              'mappingTypes':'0', 
              'textToAnnotate':input_Text, 
              'format':'xml',  #Output formats (one of): xml, tabDelimited, text  
              'apikey':API_KEY,
        }
         
        # Submit job
        submitUrl = annotatorUrl + '/submit/example@your_email.com'
        postData = urllib.urlencode(params)
        fh = urllib2.urlopen(submitUrl, postData)
        annotatorResults = fh.read()
        fh.close()
        
        print 'Call successful'
        gate_template_xml = 'gate_template.xml'
        ofile = ifile.split('.')[0] + '.xml'
        gxmlo_sct   = os.path.join(snomed_ct_output_dir, ofile)
        umls_output_dir = ''
        gxmlo_umls  = os.path.join(umls_output_dir, ofile)
        concept, context = parse_annotator_response_into_gate(annotatorResults, gate_template_xml, gxmlo_sct, gxmlo_umls)
       
    t1 = time.time() - t0
    print t1

  
