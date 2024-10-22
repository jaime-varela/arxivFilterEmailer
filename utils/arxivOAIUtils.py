# code modified from: https://github.com/mattbierbaum/arxiv-public-datasets/blob/1733af71c379ce8d69ac1204be140f07c535e250/arxiv_public_data/oai_metadata.py#L237

import os
import gzip
import glob
import json
import time
import datetime
import requests
import xml.etree.ElementTree as ET
from typing import List

URL_ARXIV_OAI = 'https://export.arxiv.org/oai2'

OAI_XML_NAMESPACES = {
    'OAI': 'http://www.openarchives.org/OAI/2.0/',
    'arXiv': 'http://arxiv.org/OAI/arXivRaw/'
}

def get_list_record_chunk(resumptionToken=None, 
                            harvest_url=URL_ARXIV_OAI,
                            metadataPrefix='arXivRaw',
                            set="math", # Arxiv handle
                            fromDate="2015-01-14",
                            toDate="2015-01-14"):
    """
    Query OIA API for the metadata of 1000 Arxiv article
    Parameters
    ----------
        resumptionToken : str
            Token for the API which triggers the next 1000 articles
    Returns
    -------
        record_chunks : str
            metadata of 1000 arXiv articles as an XML string
    """
    parameters = {'verb': 'ListRecords'}

    if resumptionToken:
        parameters['resumptionToken'] = resumptionToken
    else:
        parameters['metadataPrefix'] = metadataPrefix
        parameters['set']=set
        parameters['from']=fromDate
        parameters['until']=toDate

    response = requests.get(harvest_url, params=parameters)

    if response.status_code == 200:
        return response.text

    if response.status_code == 503:
        secs = int(response.headers.get('Retry-After', 20)) * 1.5
        print('Requested to wait, waiting {} seconds until retry...'.format(secs))

        time.sleep(secs)
        return get_list_record_chunk(resumptionToken=resumptionToken)
    else:
        raise Exception(
            'Unknown error in HTTP request {}, status code: {}'.format(
                response.url, response.status_code
            )
        )

def _record_element_text(elm, name):
    """ XML helper function for extracting text from leaf (single-node) elements """
    item = elm.find('arXiv:{}'.format(name), OAI_XML_NAMESPACES)
    return item.text if item is not None else None

def _record_element_all(elm, name):
    """ XML helper function for extracting text from queries with multiple nodes """
    return elm.findall('arXiv:{}'.format(name), OAI_XML_NAMESPACES)


def _record_subelement_text(elm, name, subname):
    """XML helper function for extracting text from queries with multiple sub-nodes"""
    return [
        subnode.text
        for node in elm.findall("arXiv:{}".format(name), OAI_XML_NAMESPACES)
        for subnode in node.findall("arXiv:{}".format(subname), OAI_XML_NAMESPACES)
    ]


def parse_record(elm):
    """
    Parse the XML element of a single ArXiv article into a dictionary of
    attributes
    Parameters
    ----------
        elm : xml.etree.ElementTree.Element
            Element of the record of a single ArXiv article
    Returns
    -------
        output : dict
            Attributes of the ArXiv article stored as a dict with the keys
            id, submitter, authors, title, comments, journal-ref, doi, abstract,
            report-no, categories, and version
    """
    text_keys = [
        'id', 'submitter', 'authors', 'title', 'comments',
        'journal-ref', 'doi', 'abstract', 'report-no'
    ]
    output = {key: _record_element_text(elm, key) for key in text_keys}
    output['categories'] = [
        i.text for i in (_record_element_all(elm, 'categories') or [])
    ]
    output['versions'] = [
        i.attrib['version'] for i in _record_element_all(elm, 'version')
    ]
    output["versions_dates"] = _record_subelement_text(elm, "version", "date")
    return output

def parse_xml_listrecords(root):
    """
    Parse XML of one chunk of the metadata of 1000 ArXiv articles
    into a list of dictionaries
    Parameters
    ----------
        root : xml.etree.ElementTree.Element
            Element containing the records of an entire chunk of ArXiv queries
    Returns
    -------
        records, resumptionToken : list, str
            records is a list of 1000 dictionaries, each containing the
            attributes of a single arxiv article
            resumptionToken is a string which is fed into the subsequent query
    """
    resumptionToken = root.find(
        'OAI:ListRecords/OAI:resumptionToken',
        OAI_XML_NAMESPACES
    )
    resumptionToken = resumptionToken.text if resumptionToken is not None else ''

    records = root.findall(
        'OAI:ListRecords/OAI:record/OAI:metadata/arXiv:arXivRaw',
        OAI_XML_NAMESPACES
    )
    records = [parse_record(p) for p in records]

    return records, resumptionToken

def check_xml_errors(root):
    """ Check for, log, and raise any OAI service errors in the XML """
    error = root.find('OAI:error', OAI_XML_NAMESPACES)

    if error is not None:
        raise RuntimeError(
            'OAI service returned error: {}'.format(error.text)
        )
    


def construct_arxiv_sets_from_meta_data(arxiv_meta_data: List[dict]):
    # taken from: http://export.arxiv.org/oai2?verb=ListSets
    non_physics_sets = set(["cs","econ","eess","math","q-bio","q-fin","stat"])
    sets = []
    for arxiv_meta in arxiv_meta_data:
        arxiv_site = arxiv_meta['arxivSite']
        if arxiv_site in non_physics_sets:
            sets.append(arxiv_site.strip())
        else:
            sets.append(f'physics:{arxiv_site.strip()}')
    return sets


def convert_arxiv_set_to_site(arxiv_set:str):
    return arxiv_set.split(':')[-1]

