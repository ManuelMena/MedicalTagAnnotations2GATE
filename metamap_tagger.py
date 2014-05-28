#!/usr/local/bin/python

import os

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

def parse_annotator_response_into_gate(metamapinput_file, gate_template_xml, gate_xml_out_metamap):        
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
   
    annotationSet_node = doc.getElementsByTagName("AnnotationSet")[0]
    annotationSet_node.childNodes = []
    
    metamap_content = open(metamapinput_file)
    total_text = ''
    current_text = ''
    reading_tag_flag        = False
    reading_annotation_flag = False
    
    get_phrase         = re.compile('.*"(.*)".*')
    get_tag_with_rb    = re.compile('.*\d+ (.*) \(.*\) \[(.*)\]')
    get_tag_without_rb = re.compile('.*\d+ (.*) \[(.*)\]')
    tags = []
    count = 1
    annotation_id_count = 1
    reading_text = False
    text_length_done = 0
    for line in metamap_content:
        if line == '\n':
            continue
        if 'Processing' in line:
            # Get rid of new line char otherwise it will mess up the code
            line = line.replace('\n','')
            text_length_done += len(current_text)
            current_text = ''
            reading_text = True
            text_tag = 'Processing 00000000.tx.%d: ' % count
            text_start_ind = line.find(text_tag)
            start_ind = text_start_ind + len(text_tag)
            current_text += line[start_ind:].lower()
            total_text += current_text
            count += 1
            continue
        
        if 'Phrase: ' in line:    
            reading_text = False
            reading_annotation_flag = True
            phrase = get_phrase.findall(line)[0].lower()
            phrase_start = current_text.find(phrase)
            phrase_text_length_done = text_length_done + phrase_start
                
        if 'Meta Mapping' in line:
            reading_tag_flag = True
            reading_annotation_flag  = False
            continue
        
        if '<<<<< Mappings' in line:
            reading_tag_flag = False
            continue    
        
        if reading_tag_flag:
            if '(' in line and ')' in line:
                (sub_phrase, tag) = get_tag_with_rb.findall(line)[0]
            else:
                (sub_phrase, tag) = get_tag_without_rb.findall(line)[0]
            
            start = phrase.find(sub_phrase.lower())
            if start >= 0:
                start = phrase_text_length_done + start
                end = start + len(sub_phrase)
                if sub_phrase.lower() != total_text[start:end]:
                    # Something wrong if this info is printed
                    print 'Error: ' + sub_phrase + '  ' + total_text[start:end]
                tags.append((int(start), int(end)))                
                annotation_node_clone = annotation_node.cloneNode(True)
                annotation_node_clone.setAttribute('Id', repr(annotation_id_count))
                annotation_node_clone.setAttribute('Type', tag)
                annotation_node_clone.setAttribute('StartNode', repr(start))
                annotation_node_clone.setAttribute('EndNode', repr(end))
                annotation_node_clone.childNodes[1].childNodes[1].childNodes[0].data = sub_phrase
                annotationSet_node.childNodes.append(annotation_node_clone)
                annotation_id_count += 1
            
        # Get the node counts from the tags nodes        
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
            text_node_clone.data = total_text[start:node_number]
            text_nodes.childNodes.append(text_node_clone)
            id_node_clone = id_node.cloneNode(True) 
            id_node_clone.setAttribute('id', repr(node_number))
            text_nodes.childNodes.append(id_node_clone)
            start = node_number
            
    doc.writexml(open(gate_xml_out_metamap, 'w'))
    print 'Done'

if __name__ == '__main__':    
    input_dir = '/tmp/metamap_annotation_files'   
    for ifile in os.listdir(input_dir):
        if ifile.split('.')[1] == 'xml':
            continue
        print 'Working on file: ' + ifile
        gate_template_xml = 'gate_template.xml'
        ofile = ifile.split('.')[0] + '.xml'
        gxmlo_metamap   = os.path.join(input_dir, ofile)
        metamap_file    = os.path.join(input_dir, ifile)       
        parse_annotator_response_into_gate(metamap_file, gate_template_xml, gxmlo_metamap)
    
