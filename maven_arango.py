import json
from pyArango.connection import *
from xml.etree import ElementTree
from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, Comment, tostring, ElementTree
import os
from os import path
import time

# Create document of repository in database
def create_maven_repo_document(repo, connection):
    
    connection.reload()
    repositoryCollection = connection['CATALOG']['REPOSITORY']
    
    try:
        if(check_docu_exists('REPOSITORY', repo['id'] ) == 0):
            # Fill information of document
            docu = repositoryCollection.createDocument()
            docu._key = repo['id']
            docu["origin"] = repo['origin']
            docu["packing_type"] = repo['packing_type']
            docu.save()
    except:
        print('Creation error in repo: {}'.format(repo['id']))
        
    
# Create document of dependency in database
def create_maven_depend_document(dep, connection):
    
    connection.reload()
    dependencyCollection = connection['CATALOG']['DEPENDENCY']

    try:
        
        if(check_docu_exists('DEPENDENCY', dep['id'] ) == 0):
            # Fill information of document
            docu = dependencyCollection.createDocument()
            docu._key = dep['id']
            docu["origin"] = dep['origin']
            docu["name"] = dep['name']
            docu["version"] = dep['version']
            docu["packing_type"] = dep['packing_type']
            docu.save()
    except:
        print('Creation error in dependency: {}'.format(dep['artifact']))
    
# Create document of relationship in database
def create_maven_edge_document(dep, types, connection):
    
    connection.reload()
    relationsCollection = connection['CATALOG']['CONTAINS']
    
    # Fill information of document
    edge = relationsCollection.createEdge()
    edge._from = '{}/{}'.format(types['sourceType'], dep['sourceID'])
    edge._to = '{}/{}'.format(types['targetType'], dep['targetID'])
    edge["branch"] = 'master'
    if(check_edge_exists('CONTAINS', edge) == 0):
        edge.save()
	
# Find if the edge is between repository or component
def findType(tree, elements):
    
    types = {"sourceType":"", "targetType":""}
    types = json.loads(json.dumps(types))
    
    for elem in tree.iter():
        if(elem.attrib.get('id') == elements['source']):
            for subelem in elem.iter():
                if(subelem.tag.split('}')[1] == 'NodeLabel'):
                    info = subelem.text.split(':')
                    if(len(info) == 4):
                        types['sourceType'] = "REPOSITORY"
                    else:
                        types['sourceType'] = "DEPENDENCY"
                        
        if(elem.attrib.get('id') == elements['target']):
            for subelem in elem.iter():
                if(subelem.tag.split('}')[1] == 'NodeLabel'):
                    info = subelem.text.split(':')
                    if(len(info) == 4):
                        types['targetType'] = "REPOSITORY"
                    else:
                        types['targetType'] = "DEPENDENCY"

    return types


def find_ids(tree, elements):
    types = {"sourceID":"", "targetID":""}
    types = json.loads(json.dumps(types))
    
    for elem in tree.iter():
        if(elem.attrib.get('id') == elements['source']):
            for subelem in elem.iter():
                if(subelem.tag.split('}')[1] == 'NodeLabel'):
                    info = subelem.text.split(':')
                    if(len(info) == 4):
                        types['sourceID'] = info[1]
                    else:
                        new_id = info[1]+'@'+info[3]
                        types['sourceID'] = new_id
                        
        if(elem.attrib.get('id') == elements['target']):
            for subelem in elem.iter():
                if(subelem.tag.split('}')[1] == 'NodeLabel'):
                    info = subelem.text.split(':')
                    if(len(info) == 4):
                        types['targetID'] = info[1]
                    else:
                        new_id = info[1]+'@'+info[3]
                        types['targetID'] = new_id

    return types

def read_GML(path_to_file, conn):

    # Parse the dependency tree
    tree = ET.parse(path_to_file)

    # For each element in the XML
    for elem in tree.iter():
        
        # If element is a Node
        if(elem.tag.split('}')[1] == 'node'):
            id = elem.attrib.get('id')
            #print('{}  {}'.format(elem.tag.split('}')[1], elem.attrib))
            for subelem in elem.iter():
                if(subelem.tag.split('}')[1] == 'NodeLabel'):
                    info = subelem.text.split(':')
                    
                    # If it is the repo info
                    if(len(info) == 4):
                        # Create repo document
                        docu = {"id":info[1], "origin":info[0], "packing_type":info[2]}
                        docu = json.loads(json.dumps(docu))
                        create_maven_repo_document(docu, conn)
                    elif(len(info) == 5):
                        # Create dependency Document
                        dep_id = info[1]+'@'+info[3]
                        docu = {"id":dep_id, "origin":info[0], "name":info[1], "packing_type":info[2], "version":info[3]}
                        docu = json.loads(json.dumps(docu))
                        create_maven_depend_document(docu, conn)

    for elem in tree.iter():
        if(elem.tag.split('}')[1] == 'edge'):
            atributos = json.loads(json.dumps(elem.attrib))
            types = findType(tree, atributos)
            elems_ids = find_ids(tree, atributos)
            create_maven_edge_document(elems_ids, types, conn)
            
# Check if document already exists in DB
def check_docu_exists(docu_type, docu_id):
    aql = "FOR doc IN {} FILTER doc._id == '{}' RETURN doc._id".format(docu_type, docu_type+'/'+docu_id)
    query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)
    if(len(query_result) > 0):
        return 1
    else:
        return 0
    
# Check if edge already exists in DB
def check_edge_exists(docu_type, edge):
    aql = "FOR doc IN {} FILTER doc._from == '{}' and doc._to == '{}' and doc.branch == '{}' RETURN doc._id".format(docu_type, 
                                                                                                                   edge['_from'], 
                                                                                                                   edge['_to'], 
                                                                                                                   edge['branch'])
    query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)
    if(len(query_result) > 0):
        return 1
    else:
        return 0
        
# Connection to ArangoDB
arango = Connection(arangoURL='http://localhost:8529', username="root", password="root")
# Clean the DB
#arango['CATALOG'].dropAllCollections()
#arango['CATALOG'].reload()

if (not arango['CATALOG'].hasCollection('CONTAINS')):
    arango['CATALOG'].createCollection(name='CONTAINS', className='Edges', waitForSync=True)
    print("Creating Edge <CONTAINS>")
    
if (not arango['CATALOG'].hasCollection('DEPENDENCY')):
    arango['CATALOG'].createCollection(name='DEPENDENCY')
    print("Creating Collection <DEPENDENCY>")
    
if (not arango['CATALOG'].hasCollection('REPOSITORY')):
    arango['CATALOG'].createCollection(name='REPOSITORY')
    print("Creating Collection <REPOSITORY>")

arango['CATALOG'].reload()

# Begin
read_GML('out.gml', arango)
