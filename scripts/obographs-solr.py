"""OBOGraphs JSON to VFB SOLR document converter
Created on July 26, 2020

@author: matentzn

This script translates the obographs json format to the native VFB solr format.
"""

import sys
import yaml
import re
from lib import get_id_variants, load_json, save_json

n2o_nodelabel_iri = "http://n2o.neo/property/nodeLabel"
n2o_uniquelabel_iri = "http://n2o.neo/property/uniqueFacets"
n2o_filename_iri = "http://n2o.neo/custom/filename"
n2o_thumbnail_iri = "http://n2o.neo/custom/thumbnail"
obo_iri = "http://purl.obolibrary.org/obo/"


def parse_config(curie_map_file):
    with open(curie_map_file, 'r') as stream:
        config = yaml.safe_load(stream)
    x = config['curie_map']
    config_out = dict()
    config_out['curie_map'] = {k: v for k, v in sorted(x.items(), key=lambda item: item[1], reverse=True)}
    filters = dict()
    if 'filters' in config:
        if 'solr' in config['filters']:
            if 'exclusion' in config['filters']['solr']:
                filters['exclusion']=config['filters']['solr']['exclusion']
            if 'inclusion' in config['filters']['solr']:
                filters['inclusion']=config['filters']['solr']['inclusion']
    config_out['filters'] = filters
    return config_out


def get_string_derivatives(label):
    label_alpha = re.sub('[^0-9a-zA-Z ]+', ' ', label)
    label_alpha = re.sub('\s+', ' ', label_alpha)
    label_split_numerics_alpha = re.sub('(?<=\d)(?!\d)|(?<!\d)(?=\d)', ' ', label_alpha)
    label_split_numerics_alpha_camel = re.sub("([a-z])([A-Z])","\g<1> \g<2>",label_split_numerics_alpha)
    label_split_numerics_alpha = re.sub('\s+', ' ', label_split_numerics_alpha)
    label_split_numerics_alpha_camel = re.sub('\s+', ' ', label_split_numerics_alpha_camel)
    #label_split_numerics = re.sub('(?<=\d)(?!\d)|(?<!\d)(?=\d)', ' ', label)
    #label_split_numerics = re.sub('\s+', ' ', label_split_numerics)
    return [label_alpha.strip(), label_split_numerics_alpha.strip(),label_split_numerics_alpha_camel.strip()]


def filter_out_solr(e, filters):
    if 'iri_prefix' in filters['exclusion']:
        for iri in filters['exclusion']['iri_prefix']:
            if iri in e['iri']:
                return True
    if 'neo4j_node_label' in filters['exclusion']:
        for neo4j_label in filters['exclusion']['neo4j_node_label']:
            if neo4j_label in e['facets_annotation']:
                return True
    return False


def construct_edge_dict(nodes: dict, edges: dict) -> dict:
    edge = {}
    node = {}
    for n in nodes:
        if 'lbl' in n:
            node.update({n['id']: n['lbl']})
    for e in edges:
        subject = e.get('sub')
        predicate = e.get('pred')
        obj = e.get('obj')
        # Considering only subClassOf, is_a, relation for parents
        # Should I be considering part_of, 'http://purl.obolibrary.org/obo/BFO_0000050', as well?
        if predicate == 'is_a':
            if edge.get(subject):
                edge.get(subject).update({obj: node.get(obj)})
            else:
                edge.update({subject: {obj: node.get(obj)}})
    return edge


def obographs2solr(obo, curie_map, filters):
    solr = []
    # I assume there is only one graph in the graphs section.
    # Constructing a dictionary from edges list for fast lookup for parents of given terms.
    edge = construct_edge_dict(obo['graphs'][0]['nodes'], obo['graphs'][0]['edges'])
    for g in obo['graphs']:
        for e in g["nodes"]:
            se = dict()
            id = e["id"]
            id_meta = get_id_variants(id, curie_map)

            se["id"] = id
            se["iri"] = id
            se["short_form"] = id_meta['short_form']
            se["obo_id"] = id_meta['obo_id']

            se["obo_id_autosuggest"] = []
            se["obo_id_autosuggest"].append(id_meta['obo_id'])
            se["obo_id_autosuggest"].append(id_meta['short_form'])

            se["shortform_autosuggest"] = []
            se["shortform_autosuggest"].extend(se["obo_id_autosuggest"])

            se["label_autosuggest"] = []
            se["synonym"] = []

            if 'lbl' in e:
                se["label"] = e["lbl"]
                se["label_autosuggest"].append(e["lbl"])
                if "\\'" in e["lbl"]:
                    se["synonym"].append(e["lbl"])
                    se["label"] = e["lbl"].replace("\\'","'")
                    se["label_autosuggest"].append(e["lbl"].replace("\\'","'"))
            else:
                se["label"] = ""  # Should this be done?

            se["synonym"].append(se["label"])
            se["synonym_autosuggest"] = []
            se["synonym_autosuggest"].extend(se["label_autosuggest"])

            se["facets_annotation"] = []
            se["unique_facets"] = []
            se["filename"] = []
            se["thumbnail"] = []

            if 'type' in e:
                entity_type = e['type'].capitalize()
                se["facets_annotation"].append(entity_type)

            if 'meta' in e:
                if 'basicPropertyValues' in e['meta']:
                    for annotation in e['meta']['basicPropertyValues']:
                        if annotation['pred'] == n2o_nodelabel_iri:
                            se["facets_annotation"].append(annotation['val'])
                        if annotation['pred'] == n2o_uniquelabel_iri:
                            se["unique_facets"].append(annotation['val'])
                        if annotation['pred'] == n2o_filename_iri:
                            se["filename"].append(annotation['val'])
                        if annotation['pred'] == n2o_thumbnail_iri:
                            se["thumbnail"].append(annotation['val'])
                if 'synonyms' in e['meta']:
                    for syn in e['meta']['synonyms']:
                        se["synonym"].append(syn['val'])
                        se["synonym_autosuggest"].append(syn['val'])

                        syntype = syn['pred']
                        if 'synonym_'+syntype not in se:
                            se['synonym_'+syntype] = []
                            se['synonym_' + syntype+'_autosuggest'] = []
                        se['synonym_'+syntype].append(syn['val'])
                        se['synonym_' + syntype+'_autosuggest'].append(syn['val'])

                        # Removed as discussed https://github.com/VirtualFlyBrain/vfb-pipeline-dumps/issues/9
                        #if 'xrefs' in syn:
                        #    se["synonym"].extend(syn['xrefs'])
                        #    se["synonym_autosuggest"].extend(syn['xrefs'])

                if 'definition' in e['meta']:
                    se['definition'] = e['meta']['definition']['val']
                    se['definition'] = (se['definition'][:98] + '..') if len(se['definition']) > 100 else se['definition']

            # Adding parent information
            # Do you want to see IRI or Short form?
            se["parent"] = {}
            if 'Animal_cell' in se['facets_annotation']:
                se["parent"] = edge.get(id)

            for key in se:
                if isinstance(se[key], list) and ('autosuggest' in key):
                    derivatives = []
                    for l in se[key]:
                        derivatives.extend(get_string_derivatives(l))
                    se[key].extend(derivatives)
                se[key] = list(set(se[key])) if isinstance(se[key], list) else se[key]
            if not filter_out_solr(se, filters):
                solr.append(se)
    return solr


# obographs_file = "/Users/matentzn/vfb/vfb-pipeline-dumps/test/obographs.json"
# solr_out_file = "/Users/matentzn/vfb/vfb-pipeline-dumps/test/solr.json"
# curie_map_file = "/Users/matentzn/vfb/vfb-prod/neo4j2owl-config.yaml"
obographs_file = sys.argv[1]
curie_map_file = sys.argv[2]
solr_out_file = sys.argv[3]

obo = load_json(obographs_file)
config = parse_config(curie_map_file)
curie_map = config['curie_map']
curie_map_rev = {v: k for k, v in curie_map.items()}
filters = config['filters']
solr = obographs2solr(obo, curie_map_rev, filters)
save_json(solr, solr_out_file)
