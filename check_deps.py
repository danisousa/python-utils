import json
from pyArango.connection import *
import os

# Get not validated dependencies
def check_fails(repo_name, arango):
    aql = "FOR doc IN DEPENDENCY FILTER doc.validated == false RETURN doc._id"
    query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)
    if(len(query_result) > 0):
        for dep in query_result:
            get_path(repo_name, dep, arango)
        
def get_path(repo_name, dependency, arango):
    i=1
    aql = "FOR v, e IN ANY SHORTEST_PATH 'REPOSITORY/{}' TO '{}' CONTAINS FILTER e.branch=='{}' RETURN v._key".format(repo_name, dependency, os.environ['BRANCH'], arango)
    query_result = arango['CATALOG'].AQLQuery(aql, rawResults=True, batchSize=100)
    if(len(query_result) > 0):
        print("NOT VALIDATED DEPENDENCY: {}".format(dependency))
        for step in query_result:
            indent= i*"\t"
            if(step==repo_name):
                print("Repository: {}".format(step))
            else:
                print("{}{}".format(indent, "|"))
                print("{}{}".format(indent, step))
            i = i + 1
        print("")
        
# Connection to ArangoDB
arango = Connection(arangoURL='http://192.168.56.1:8529', username="root", password="root")
#get_repo_dependencies('sample-project-maven', arango)
check_fails(os.environ['REPO_NAME'], arango)