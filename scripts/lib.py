"""Library for typical functions used to process entities, in particular IRIs
Created on 14 October 2020

@author: matentzn

"""

import re
import json

obo_iri = "http://purl.obolibrary.org/obo/"


def load_json(obographs_file):
    with open(obographs_file) as json_file:
        data: dict = json.load(json_file)
    return data
    # print(data)


def save_json(solr, solr_out_file):
    with open(solr_out_file, 'w') as outfile:
        outfile.write(json.dumps(solr, indent=4, sort_keys=True))
    print(f"{solr_out_file} saved")


def get_id_variants(iri, curie_map):
    id_meta = dict()
    sorted_prefixes = list(curie_map.keys())
    sorted_prefixes.sort(reverse=True)
    # print("---------")
    for prefix_url in sorted_prefixes:
        # print(prefix_url)
        pre = curie_map[prefix_url]
        if iri.startswith(prefix_url):
            short_form = iri.replace(prefix_url,'')
            # Strip away all non-alphanumeric characters; this is important as Gepetto
            # uses the assumptions that shortforms can be used as java variables
            short_form = re.sub('[^0-9a-zA-Z_]+', '_', short_form)
            id_meta['obo_id'] = pre+":"+short_form

            # If the iri prefix ends with an _, that suggests that the IRI is obo style
            # If the short form starts with a number, this suggests id style, like DOI or ORCID
            if prefix_url.endswith(pre+"_") or short_form[0].isdigit():
                id_meta['short_form'] = pre+"_"+short_form
            else:
                id_meta['short_form'] = short_form
            break
    if 'short_form' not in id_meta:
        if iri.startswith(obo_iri):
            short_form = iri.replace(obo_iri, '')
            id_meta['obo_id'] = short_form.replace("_", ":")
            id_meta['short_form'] = short_form
        else:
            print("WARNING: ID "+iri+" does not have a prefixable IRI")
            short_form = re.sub('[^0-9a-zA-Z_]+', '_', iri)
            id_meta['obo_id'] = "NONAMESPACE:"+short_form
            id_meta['short_form'] = short_form
    return id_meta
