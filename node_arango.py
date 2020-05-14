import json
from pyArango.connection import *
import os

# Create document of repository in database
def create_node_repo_document(repo, connection):
    
    repositoryCollection = connection['CATALOG']['REPOSITORY']

    try:
        if(check_docu_exists('REPOSITORY', repo['name'] ) == 0):
            # Fill information of document
            docu = repositoryCollection.createDocument()
            docu._key = repo['name']
            docu["version"] = repo['version']
            docu["repository"] = os.environ['REPO_NAME']
            docu.save()
    except:
        print('Creation error in repo: {}'.format(repo))
        
# Create document of dependency in database
def create_node_depend_document(document, connection):
        
    dependencyCollection = connection['CATALOG']['DEPENDENCY']

    try:
        key = check_key_format(document['from'])

        if(check_docu_exists('DEPENDENCY', key ) == 0):
            # Fill information of document
            docu = dependencyCollection.createDocument()
            docu._key = key
#            docu["origin"] = document['resolved']
            docu["version"] = document['version']
            docu.save()
    except:
        print('Creation error in dependency: {}'.format(document))
    
# Create document of relationship in database
def create_node_edge_document(parent, origin, parent_type, connection):

    relationsCollection = connection['CATALOG']['CONTAINS']
    
    try:
        parent = check_key_format(parent)
        origin_key = check_key_format(origin['from'])
        
        # Fill information of document
        edge = relationsCollection.createEdge()
        edge._from = '{}/{}'.format(parent_type, parent)
        edge._to = '{}/{}'.format('DEPENDENCY', origin_key)
        edge["branch"] = os.environ['BRANCH']
        edge["technology"] = 'javascript'
        if(check_edge_exists('CONTAINS', edge) == 0):
            edge.save()
    except:
        print('Creation error in edge: {}'.format(edge))

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
    
# Check if key has '/'
def check_key_format(key):
    clave = key
    if("/" in key):
        clave = clave.replace("/", ":")
    return clave
    
def get_depend_depth(source, parent, from_type, conn):
        
    # Check if it has dependencies at this level
    if ('dependencies' in source):
        deps = source['dependencies']

        # For each dependency
        for dep in deps:
            create_node_depend_document(deps[dep], conn)
            create_node_edge_document(parent, deps[dep], from_type, conn)
            get_depend_depth(deps[dep], deps[dep]['from'], 'DEPENDENCY', conn)
            
def read_JSON(json_path, conn):

    with open(json_path) as f:
        data = json.load(f)

        create_node_repo_document(data, conn)
        get_depend_depth(data, data['name'], 'REPOSITORY', conn)
        
# Connection to ArangoDB
arango = Connection(arangoURL='http://192.168.56.1:8529', username="root", password="root")
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
read_JSON('outfile.json', arango)