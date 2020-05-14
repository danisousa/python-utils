import json
from pyArango.connection import *
import os

# Get first level dependencies of the given repo
def get_repo_dependencies(repo_name, arango):
    # Get id of repo
    aql = "FOR doc IN REPOSITORY FILTER doc.repository == '{}' RETURN doc._id".format(repo_name)
    query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)

    # Get all edges of repo
    aql = "FOR edge IN CONTAINS FILTER edge._from == '{}' RETURN edge._to".format(query_result[0])
    query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)
    
    # Check each dependency
    for dep in query_result:
        check_dep(dep, arango)
    
# Recursive method to get all dependencies of a given dependency
def check_dep(dep_name, arango):
    aql = "FOR doc IN DEPENDENCY FILTER doc._id == '{}' RETURN doc.validated".format(dep_name)
    query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)
    if ((len(query_result) > 0) and (query_result[0] == False)):
        print('{}'.format(dep_name))
        
    aql = "FOR edge IN CONTAINS FILTER edge._from == '{}' RETURN edge._to".format(dep_name)
    query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)
    
    for dep in query_result:
        check_dep(dep, arango)
    
# Connection to ArangoDB
arango = Connection(arangoURL='http://192.168.56.1:8529', username="root", password="root")
get_repo_dependencies(os.environ['REPO_NAME'], arango)