from __future__ import print_function 
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import json 
import urllib.request

import signal
import sys

import time
import urllib.request

import csv

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def create_service():

    creds = None

    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server()
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v2', credentials=creds)

    return service


def get_text(service, documentId, start, end):

    url = "https://docs.google.com/document/d/{}/showrevision?start={}&end={}&id={}".format(documentId, start, end, documentId)

    resp, content = service._http.request(url)
    status = resp['status']

    if status != '200': 
        return None


    text = content.decode('utf-8')[5:]

    try: 
        jsonData = json.loads(text)['chunkedSnapshot'][0][0]['s']
    except:
        return ''


    return jsonData


def get_time(service, documentId, start, end):
    # Get time in ms
    url = "https://docs.google.com/document/d/{}/revisions/tiles?id={}&start={}&end={}&showDetailedRevisions=true".format(documentId, documentId, start, end)
    
    resp, content = service._http.request(url)
    status = resp['status']

    if status != '200': 
        return None

    text = content.decode('utf-8')[5:]

    try: 
        jsonData = json.loads(text)['tileInfo'][0]['endMillis']
    except:
        return ''

    return jsonData


def main():

    service = create_service()

    documentIds = [ 
        "doc_id_1",
        "doc_id_2",
        "doc_id_3",
        "doc_id_4"
    ]

    for documentId in documentIds:
        get_data(service, documentId)

def get_data(service, documentId):
    results = service.revisions().list(fileId=documentId).execute()

    items = results['items']

    maxValue = 0

    for item in items:
        id = int(item['id'])

        if (id > maxValue):
            maxValue = id


    print("Total revisions: {}".format(maxValue))
    print()

    with open(documentId + '.csv', mode='w') as csvFile:

        writer = csv.writer(csvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for i in range(1, maxValue + 1):

            try: 
                revisionNumber = i
                text = get_text(service, documentId, revisionNumber, revisionNumber)
                time = get_time(service, documentId, revisionNumber, revisionNumber)

                para = text.split('\n')

                result = ''

                count = len(para)

                for i in range(len(para)):

                    paraLength = len(para[i])

                    if (paraLength == 0):
                        count -= 1
                        continue

                    result += str(len(para[i]))

                    result += ','

                if (result[-1] == ','):
                    result = result[:-1]
                
                print("{},{},{},{}".format(time, len(text), count, result))

                writer.writerow([time, len(text), len(para)] + result.split(','))

            except KeyboardInterrupt:
                sys.exit(0)

            except:
                print('failed');
                pass



if __name__ == '__main__':

    main()
