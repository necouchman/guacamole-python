#!/usr/bin/env python

import json
import urllib
import urllib2
import sys
import pandas
import argparse

guacbase = "https://localhost/guacamole"

# Parse arguments
def parse_args(args=None):
    parser = argparse.ArgumentParser(description='Guacamole Command Line Utility.')
    parser.add_argument('-a', dest='active', action='store_true', help='Show active connections')
    parser.add_argument('-l', dest='history', action='store_true', help='List session history')
    parser.add_argument('-k', '--kill', dest='kill', type=str, metavar='UUID', help='Kill the session with the specified UUID.')

    return parser.parse_args()

# Login to Guacamole with username/password
def login(username, password):
    loginData = urllib.urlencode({ u'username' : username, u'password' : password })
    loginHeaders = { 'Content-type' : 'application/x-www-form-urlencoded', 'Accept' : 'application/json' }
    loginRequest = urllib2.Request(guacbase + '/api/tokens', data=loginData, headers=loginHeaders)
    loginResponse = urllib2.urlopen(loginRequest)

    if loginResponse.code > 299:
        return -1

    else:
        return json.loads(loginResponse.read())

# Logout of Guacamole with token
def logout(token):
    logoutOpener = urllib2.build_opener(urllib2.HTTPHandler)
    logoutRequest = urllib2.Request(guacbase + '/api/tokens/' + token)
    logoutRequest.get_method = lambda: 'DELETE'
    
    return logoutOpener.open(logoutRequest)

# Retrieve the list of active connections
def getActiveConnections(token, dataSources):
    activeConnections = {}
    for datasource in dataSources:
        activeRequest = urllib2.Request(guacbase + '/api/session/data/' + datasource + '/activeConnections?token=' + token)
        activeResponse = urllib2.urlopen(activeRequest)
        if activeResponse.code > 299:
            break
        activeConnections[datasource] = json.loads(activeResponse.read())

    return activeConnections

# Retrieve the list of historical connections
def getConnectionHistory(token, dataSources):
    connectionHistory = {}
    for datasource in dataSources:
        historyRequest = urllib2.Request(guacbase + '/api/session/data/' + datasource + '/history/connections?token=' + token)
        historyResponse = urllib2.urlopen(historyRequest)
        if historyResponse.code > 299:
            break
        connectionHistory[datasource] = json.loads(historyResponse.read())

    return connectionHistory

# Look for and kill the session specified by identifier
def killActiveSession(token, dataSources, identifier):
    activeConnections = getActiveConnections(token, dataSources)
    for datasource in dataSources:
        if identifier in activeConnections[datasource]:
            killBody = json.dumps([{ 'op' : 'remove', 'path' : '/' + identifier }])
            killHeaders = { 'Content-type' : 'application/json', 'Accept' : 'application/json' }
            killOpener = urllib2.build_opener(urllib2.HTTPHandler)
            killRequest = urllib2.Request(guacbase + '/api/session/data/' + datasource + '/activeConnections?token=' + token, data=killBody, headers=killHeaders)
            killRequest.get_method = lambda: 'PATCH'

            return killOpener.open(killRequest)
    print "No connection found with identifier " + identifier

# Login
myLoginData = login('guacuser','guacpass')

# If login failed, exit with failure code
if isinstance(myLoginData, (int,long)):
    sys.exit(myLoginData)

# Parse arguments
myArgs = parse_args(sys.argv[1:])

TOKEN = myLoginData['authToken']
DATASOURCES = myLoginData['availableDataSources']

# If asked for active connections, get them and print them
if myArgs.active:
    ACTIVE = getActiveConnections(TOKEN, DATASOURCES)
    for datasource in DATASOURCES:
        if len(ACTIVE[datasource]) > 0:
            print ACTIVE[datasource].items()

# If asked for history, get historical connections and print them
if myArgs.history:
    HISTORY = getConnectionHistory(TOKEN, DATASOURCES)
    for datasource in DATASOURCES:
        if len(HISTORY[datasource]) > 0:
            pandas.set_option('display.width', 1000)
            print pandas.DataFrame(HISTORY[datasource], columns=['username','startDate','endDate','remoteHost','connectionName','active'])

# If asked to kill a session, pass info over to kill it
if myArgs.kill:
    killActiveSession(TOKEN, DATASOURCES, myArgs.kill)

# Log out when done
logout(TOKEN)
