import json
from pyArango.connection import *
import os

# Get not validated dependencies
def check_fails(repo_name, arango):
    aql = "FOR doc IN DEPENDENCY FILTER doc.validated == false RETURN doc._id"
    query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)

    if(len(query_result) > 0):
        for dep in query_result:
            # Get depth of path
            aql = "RETURN LENGTH(FOR v IN ANY SHORTEST_PATH 'REPOSITORY/{}' TO '{}' CONTAINS RETURN v)".format(repo_name, dep)
            query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)
            
            # If exists a path
            if(len(query_result) > 0):
                get_path(repo_name, dep, query_result[0], arango)
        
def get_path(repo_name, dependency, depth, arango):
    i=1
    aql = "FOR v, e, p IN {} OUTBOUND 'REPOSITORY/{}' CONTAINS FILTER v._id == '{}' && e.branch == '{}' && v.validated == false RETURN p.edges".format(depth-1, repo_name, dependency, os.environ['BRANCH'], arango)
    query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)
    if(len(query_result) > 0):
        print("NOT VALIDATED DEPENDENCY: {}".format(dependency))
        print(repo_name)
        for step in query_result[0]:
            indent= i*"\t"
            if(step==repo_name):
                print("Repository: {}".format(step))
            else:
                print("{}{}".format(indent, "|"))
                print("{}{}".format(indent, step['_to']))
            i = i + 1
        
# Connection to ArangoDB
arango = Connection(arangoURL='http://192.168.56.1:8529', username="root", password="root")
#get_repo_dependencies('sample-project-maven', arango)
check_fails(os.environ['REPO_NAME'], arango)