import os
import json
import datetime
from pymongo import MongoClient
import pymongo
from pymongo.collation import Collation
from time import strptime,sleep
import datetime
import re
import nltk
from nltk.corpus import words, stopwords, wordnet
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk import pos_tag
from nltk.tokenize import word_tokenize
import csv
import string
from sklearn.decomposition import NMF, LatentDirichletAllocation, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import itertools 

dictionary_words = dict.fromkeys(words.words(), None)

import pyphen
pyphen_dic = pyphen.Pyphen(lang='en')
    
stopWords = set(stopwords.words('english'))
tokenizer = RegexpTokenizer(r'\w+')

stemmer = PorterStemmer()
lemmatiser = WordNetLemmatizer()

stop = set(stopwords.words('english'))
exclude = set(string.punctuation) 
lemma = WordNetLemmatizer()

topic_doc_complete = []



class TwitterDB:

    def __init__(self, mongoDB_database, 
                 strFocusedTweetFields="id_str;created_at;lang;retweet_count;in_reply_to_status_id_str;in_reply_to_screen_name", 
                 strFocusedTweetUserFields="name;screen_name;description;location;followers_count;friends_count;statuses_count;lang;verified"):
        #Inititalizing MongoDB collections        
        self.db = mongoDB_database                
        self.db.dc_bSettings = self.db.adm_dbSettings
        self.c_loadedFiles = self.db.adm_loadedFiles
        self.c_twitterSearches = self.db.adm_twitterSearches
        self.c_tweet = self.db.tweet
        self.c_focusedTweet = self.db.focusedTweet
        self.c_tweetWords = self.db.tweetWords
        self.c_tweetSentences = self.db.tweetSentences
        self.c_topicsByHashTag = self.db.topicsByHashTag
        self.c_tweetCountByFileAgg = self.db.agg_tweetCountByFile
        self.c_tweetCountByPeriodAgg = self.db.agg_tweetCountByMonth
        self.c_tweetCountByLanguageAgg = self.db.agg_tweetCountByLanguage
        self.c_tweetCountByUserAgg = self.db.agg_tweetCountByUser
        self.c_wordCountAgg = self.db.agg_wordCount
        self.c_hashTagCountAgg = self.db.agg_hashTagCount
        self.c_userLocationCountAgg = self.db.agg_userLocationCount
        self.c_loadStatus = self.db.adm_loadStatus
        self.c_htTopics = self.db.htTopics
        self.c_tweetHashTags = self.db.tweetHashTags
        self.c_tweetConnections = self.db.tweetConnections
        self.c_users = self.db.users
        self.c_tweetHTConnections = self.db.tweetHTConnections
        #temp collections to help with query performance
        self.c_tmpEdges = self.db.tmpEdges
        self.c_tmpEdgesTweetIds = self.db.tmpEdgesTweetIds
        self.c_tmpEdgesHTFreq = self.db.tmpEdgesHTFreq
        self.c_tmpEdgesWordFreq = self.db.tmpEdgesWordFreq
        
        
        #load these settings from DB. If no settings yet, use default        
        self.strFocusedTweetFields = strFocusedTweetFields
        self.periodGrain = "month"         
        self.add_lowerCase_fields_FL = 'Y'
        self.label_EnWords_FL = 'N'
        self.pos_tag_label_FL = 'Y'
        self.lemm_word_FL = 'Y'
        self.ignore_stop_words_FL = 'Y'        
                
        # Put fields chosen into an array of fields. 
        # These fields will be the ones used in the FocusedTweet collection.             
        self.strFocusedTweetFieldsArr = strFocusedTweetFields.split(";")        
        self.strFocusedTweetUserFieldsArr = strFocusedTweetUserFields.split(";")
            
        # Create unique index on users table to only allow one users with same user_id and screen_name. 
        # (Collation strength=2 garantees case insensitive)
        try:
            resp = self.c_users.create_index([('user_id_str', pymongo.ASCENDING), 
                                              ('screen_name', pymongo.ASCENDING) ], 
                                             unique = True, 
                                             collation=Collation(locale="en_US", strength=2))
        except Exception as e:
            print('Could not create index in users' + str(e))
                  

    #####################################
    # Method: loadDocFromFile
    # Description: This method will load tweet .json files into the DB (tweet collection)
    # It goes through all .json files in the directory and load them one by one. 
    # It also saves the files already loaded into the 'loadedFiles' collection 
    # to make sure we don't load the same file twice
    # Parameters: 
    #   -directory = the directory where the files are stored
    def loadDocFromFile(self, directory):
        seq_no = 1

        starttime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print ("loading process started..." + starttime)
        
        #find the current max sequence number
        select_cTweet = self.c_tweet.aggregate( 
            [{"$group": {"_id": "seq_agg" , "count": { "$max": "$seq_no" } }}])
        for tweetCount in select_cTweet:
            seq_no = tweetCount["count"] + 1                

        #loops through the files in the dictory
        for filename in os.listdir(directory):
            if filename.endswith(".json"):                
                strpath = os.path.join(directory, filename)                               

                #find if file already loaded
                isFileLoaded = self.c_loadedFiles.count_documents({"file_path": strpath.replace("\\", "/") })        

                if isFileLoaded > 0:
                    #if the processing of that file did not finish. Deletes every record for that file so we can start over
                    select_cLoadedFiles = self.c_loadedFiles.find({ "file_path": strpath.replace("\\", "/")})                
                    if select_cLoadedFiles[0]["end_load_time"] == "loading":            
                        self.c_tweet.delete_many({"file_path": strpath.replace("\\", "/")})
                        self.c_loadedFiles.delete_many({"file_path": strpath.replace("\\", "/")})            
                        isFileLoaded=0

                #if file has already been loaded, ignores the file
                if isFileLoaded == 0:

                    #save path in loaded files collection to track which files have already been processed
                    data_loadedfiles = '{"start_load_time":"' \
                                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") \
                                        + '","end_load_time":"' \
                                        + "loading" \
                                        + '","file_path":"' \
                                        + strpath.replace("\\", "/") \
                                        + '"}'        
                    self.c_loadedFiles.insert_one(json.loads(data_loadedfiles))

                    #open file and goes through each document to insert tweet into DB (inserts into tweet collection)                    
                    with open(strpath, encoding="utf8") as f:
                        for line in f:        
                            data = json.loads(line)

                            #adding extra fields to document to suport future logic (processed_fl, load_time, file_path )
                            a_dict = {'processed_fl': 'N', 
                                      'seq_no': seq_no, 
                                      'seq_agg': "A", 
                                      'load_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                      'file_path': strpath.replace("\\", "/")}    
                            data.update(a_dict)                                        

                            #ignores documents that are just status
                            if 'info' not in data:
                                self.c_tweet.insert_one(data)
                                seq_no = seq_no+1

                    #update end load time 
                    self.c_loadedFiles.update_one(
                        { "file_path" : strpath.replace("\\", "/") },
                        { "$set" : { "end_load_time" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") } });            

                continue        
            else:
                print ("Error loading into tweet collection")        

                
        try:
            resp = self.c_tweet.create_index([('seq_no', pymongo.ASCENDING)])            
        except Exception as e:
            print('Could not create index ' + str(e))    
            
        endtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print ("loading process completed " + endtime)
        
        
    
    # this method will use Twitter API to extract data and save into DB 
    # Parameters: twitterBearer = Bearer from you Twitter developer account
    #             apiName = (30day/fullarchive)
    #             devEnviroment = name of your deve enviroment
    #             query = query to select data from Twitter API
    #             dateStart = period start date
    #             dateEnd = period end date
    #             nextToken = token to start from 
    #             maxResults = maximum number of results that you want to return
    def extractDocFromAPI (self, twitterBearer, apiName, devEnviroment, query, dateStart, dateEnd, nextToken, maxResults):        
        print("Code for extractDocFromAPI. Details for this code on https://git.txstate.edu/l-n63/CS7311 ")        
                  
           
        
    #####################################
    # Method: loadCollection_UpdateStatus
    # Description: This method controls the progress the insertions into other collections. 
    # It calls other methods to load the collections
    # It keeps the progress stored in the db, so that if something fails, 
    #  we can know where to start back up.
    # The progress is stored on collections "adm_loadStatus"
    # Parameters: 
    #   -collection_name = the collections you want to load. 
    #    (Options: focusedTweet, tweetWords, tweetHashTags and tweetConnections)
    #   -inc = how many tweet records you want to load at the time. 
    #    (Large number may cause memory errors, low number may take too long to run)
    #   -type_filter = used only for users collections. 
    #    (Options: tweet, retweet, quote, reply or mention) - Default = None
    def loadCollection_UpdateStatus(self, collection_name, inc, type_filter=None):

        starttime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print ('loading process started (' + collection_name + ('-' + type_filter if type_filter is not None else '')  +  ')... ' + starttime)
            
        last_seq_no = -1
        max_seq_no = 0
        minV = 0

        #get the max sequence number from the tweet collection
        select_cTweet = self.c_tweet.aggregate( [{"$group": {"_id": "seq_agg" , "count": { "$max": "$seq_no" } } } ])
        for tweetCount in select_cTweet:
            max_seq_no = tweetCount["count"]

        #check if the process has already been run or not. This is to make sure we can restart a process from where we stopped
        if type_filter is not None: 
            hasStarted = self.c_loadStatus.count_documents({"collection_name": collection_name, "type_filter": type_filter })        
        else:
            hasStarted = self.c_loadStatus.count_documents({"collection_name": collection_name })
            
        if hasStarted > 0:
            select_cLoadStatus = self.c_loadStatus.find({"collection_name": collection_name })                
            if select_cLoadStatus[0]["status"] == "loading":
                last_seq_no = select_cLoadStatus[0]["min_seq"]-1
                if collection_name == 'focusedTweet':                    
                    self.c_focusedTweet.delete_many({ "seq_no" : { "$gte" : select_cLoadStatus[0]["min_seq"] } })
                elif collection_name == 'tweetWords':
                    self.c_tweetWords.delete_many({ "tweet_seq_no" : { "$gte" : select_cLoadStatus[0]["min_seq"] } })
                elif collection_name == 'tweetHashTags':                    
                    self.c_tweetHashTags.delete_many({ "tweet_seq_no" : { "$gte" : select_cLoadStatus[0]["min_seq"] } })
                elif collection_name == 'tweetConnections':
                    self.c_tweetConnections.delete_many({ "tweet_seq_no" : { "$gte" : select_cLoadStatus[0]["min_seq"] } })
                elif collection_name == 'tweetHTConnections':
                    self.c_tweetHTConnections.delete_many({ "tweet_seq_no" : { "$gte" : select_cLoadStatus[0]["min_seq"] } })                
                                
            elif select_cLoadStatus[0]["status"] == "success":
                last_seq_no = select_cLoadStatus[0]["max_seq"] 
        else:
            if type_filter is not None: 
                data = '{"collection_name":"' + collection_name + '", "type_filter":"' + type_filter + '"}'
            else:
                data = '{"collection_name":"' + collection_name + '"}'
            doc = json.loads(data)
            self.c_loadStatus.insert_one(doc)


        # try:
        # loop through tweet sequence numbers to insert into DB. 
        # The variable "inc" will dictate how many tweet we will isert at a time int DB
        minV = last_seq_no+1
        while minV <= max_seq_no: 
            
            if type_filter is not None: 
                self.c_loadStatus.update_one(
                    {"collection_name": collection_name, "type_filter": type_filter }, 
                    { "$set" : { "min_seq" : minV, "max_seq" : minV+inc, "status" : "loading" } } )
            else:
                self.c_loadStatus.update_one(
                    {"collection_name": collection_name }, 
                    { "$set" : { "min_seq" : minV, "max_seq" : minV+inc, "status" : "loading" } } )
                
            if collection_name == 'focusedTweet':                    
                self.loadFocusedDataMinMax(minV, minV+inc)
            elif collection_name == 'tweetWords':
                self.breakTextIntoWords(minV, minV+inc)                    
            elif collection_name == 'tweetHashTags':
                self.loadTweetHashTagsMinMax(minV, minV+inc)                
            elif collection_name == 'tweetConnections':
                self.loadTweetConnectionsMinMax(minV, minV+inc)
            elif collection_name == 'tweetHTConnections':
                self.loadTweetHTConnectionsMinMax(minV, minV+inc)                
            elif collection_name == 'users':
                self.loadUsersDataMinMax(minV, minV+inc, type_filter)

            minV=minV+inc

        #if everyhting was successfull, saves status as "success"
        if type_filter is not None: 
            self.c_loadStatus.update_one(
                {"collection_name": collection_name, "type_filter": type_filter }, 
                { "$set" : { "max_seq" : max_seq_no, "status" : "success" } } )
        else:
            self.c_loadStatus.update_one(
                {"collection_name": collection_name }, 
                { "$set" : { "max_seq" : max_seq_no, "status" : "success" } } )
                                  
        endtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print ('loading process completed (' + collection_name + ')... ' + endtime)
        
    
    #####################################
    # Method: loadFocusedData
    # Description: This method will call loadCollection_UpdateStatus to load the focusedtweet collection
    # Parameter:  
    #   -inc = how many tweet records you want to load at the time. 
    #   (Large number may cause memory errors, low number may take too long to run)
    def loadFocusedData(self, inc):
        
        self.loadCollection_UpdateStatus('focusedTweet', inc )
        
    
    #####################################
    # Method: loadFocusedDataMinMax
    # Description: This method will load the focusedtweet collection with the interesting information we want to study
    # It filters by a interval number of tweets. 
    # This is because loading everything at once might cause out of memory errors
    # Parameters:   
    #   -minV & maxV = the tweet seq_no interval you want to run this analysis for
    def loadFocusedDataMinMax(self, minV, maxV):     

        file_data = []

        select_cTweet = self.c_tweet.find({"seq_no":{ "$gt":minV,"$lte":maxV}})
        #select_cTweet = self.c_tweet.find({"seq_no":{ "$gt":2,"$lte":3}})

        #loop through tweets
        for tweet in select_cTweet:    
            
            #Get all the basic info about the tweet. (These will always be saved independet of configurations)    
            seq_no = tweet['seq_no']
            id_str = tweet['id_str']
            created_at = datetime.datetime.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
            year =  tweet['created_at'][26:30]
            month_name =  tweet['created_at'][4:7]
            month_no =  str(strptime(month_name,'%b').tm_mon)
            day =  tweet['created_at'][8:10]
            user_id =  tweet['user']['id_str']
            
            
            
            ## ***************************************************
            ## *** Getting the text information from differnt fields and different formats ****    

            # when the tweet is large, the full text is saved ion the field extended_tweet
            if 'extended_tweet' in tweet:                   
                text = tweet['extended_tweet']['full_text']
            elif 'full_text' in tweet:
                text =  tweet['full_text']
            else:
                text =  tweet['text']                   
                
            text = text.replace("\\", "").replace('\"', "").replace("\r","")    
            text = text.replace("\n","").replace("\t", "").rstrip()
            text_lower = text.lower()

            # text from the quoted text
            quote_text = ""
            if 'quoted_status' in tweet:
                if 'extended_tweet' in tweet['quoted_status']:
                    quote_text = tweet['quoted_status']['extended_tweet']['full_text']
                elif 'full_text' in tweet['quoted_status']:
                    quote_text = tweet['quoted_status']['full_text']
                else:
                    quote_text = tweet['quoted_status']['text']
                    
            quote_text = quote_text.replace("\\", "").replace('\"', "").replace("\r","")  
            quote_text = quote_text.replace("\n","").replace("\t", "").rstrip()
            quote_text = quote_text.lower()

            # text from original tweet if this is a retweet
            retweeted_text = ""
            if 'retweeted_status' in tweet:                      
                if 'extended_tweet' in tweet['retweeted_status']:
                    retweeted_text = tweet['retweeted_status']['extended_tweet']['full_text']
                elif 'full_text' in tweet['retweeted_status']:
                    retweeted_text = tweet['retweeted_status']['full_text']
                else:
                    retweeted_text = tweet['retweeted_status']['text']                       
            
            retweeted_text = retweeted_text.replace("\\", "").replace('\"', "").replace("\r","")
            retweeted_text = retweeted_text.replace("\n","").replace("\t", "").rstrip()
            retweeted_text = retweeted_text.lower()
                        
            
            text_combined = text_lower + ' ' + quote_text
            
            # removing hashtahs, mentions and links from clean text    
            text_combined_clean = text_combined.replace("http", " http").replace("#", " #")        
            text_combined_clean = text_combined_clean.replace("@", " @").replace("  ", " ").strip()
            words = text_combined_clean.split()
            text_combined_clean = ''            
            for word in list(words):            
                if word[0:1] != '#' and word[0:1] != '@' and word[0:4] != 'http'and word[0:2] != 'rt':
                    text_combined_clean = text_combined_clean + word + ' '                                    
            
            text_combined_clean = text_combined_clean.replace("\\", "").replace("@","").replace("!", "")
            text_combined_clean = text_combined_clean.replace("/", "").replace("*", "").replace("&amp;", "")
            text_combined_clean = text_combined_clean.replace("-", "").replace("~", "").replace("`", "")
            text_combined_clean = text_combined_clean.replace("#", "").replace("$", "").replace("…", "")
            text_combined_clean = text_combined_clean.replace("%", "").replace("^", "").replace("&", "")
            text_combined_clean = text_combined_clean.replace("(", "").replace(")", "").replace("—", "")
            text_combined_clean = text_combined_clean.replace("=", "").replace("+", "").replace("{", "")
            text_combined_clean = text_combined_clean.replace("}", "").replace("[", "").replace("“", "")
            text_combined_clean = text_combined_clean.replace("’", "").replace("]", "").replace("|", "")
            text_combined_clean = text_combined_clean.replace("'", "").replace('"', "").replace("?", "")
            text_combined_clean = text_combined_clean.replace(":", "").replace(";", "").replace("<", "")
            text_combined_clean = text_combined_clean.replace(">", "").replace(",", "").replace(".", "")
            text_combined_clean = text_combined_clean.replace("_", "").replace("\\\\", "")
            text_combined_clean = text_combined_clean.replace("  ", " ").strip()

            ## ***************************************************************************
            
            
            
                                    
            ## ***************************************************************************
            ## *** Getting the hashtag information - (original tweets, and quotes)

            ht_children = []

            def addHTToList(ht, type_ht):                    

                ht_children.append({
                    'ht': ht, 'ht_lower': ht.lower(), 'type_ht' : type_ht
                })


            # get Hashtags            
            type_ht = 'original'             
            if 'extended_tweet' in tweet:
                for gt_tweet in tweet['extended_tweet']['entities']['hashtags']:
                    ht = gt_tweet['text'] 
                    addHTToList(ht,type_ht)
            else:        
                for gt_tweet in tweet['entities']['hashtags']:                    
                    ht = gt_tweet['text']
                    addHTToList(ht,type_ht)                                    

            if 'quoted_status' in tweet:                
                type_ht = 'quote'
                if 'extended_tweet' in tweet['quoted_status']:     
                    if 'entities' in tweet['quoted_status']['extended_tweet']:
                        for gt_tweet in tweet['quoted_status']['extended_tweet']['entities']['hashtags']:
                            ht = gt_tweet['text']
                            addHTToList(ht,type_ht)

                elif 'entities' in tweet['quoted_status']:
                    for gt_tweet in tweet['quoted_status']['entities']['hashtags']:
                        ht = gt_tweet['text']     
                        addHTToList(ht,type_ht)

            ## ***************************************************************************
    
                

            # creating the json doc
            data = '{"id_str":"' + id_str + \
                    '", "text":"' + text + \
                    '", "text_lower":"' + text_lower + \
                    '", "quote_text":"' + quote_text + \
                    '", "retweeted_text":"' + retweeted_text + \
                    '", "text_combined":"' + text_combined + \
                    '", "text_combined_clean":"' + text_combined_clean + \
                    '", "year":"' + year + \
                    '", "month_name":"' + month_name + \
                    '", "month_no":"' + month_no + \
                    '", "day":"' + day + \
                    '", "user_id":"' + user_id + \
                    '", "hashtags":"' + "" + '"}'
            doc = json.loads(data)
            doc['hashtags'] = ht_children
            

            
            # ***** adding other fields to collection based on the list of fields from configuration - 
            # (configuration is set on the instantiation of the class object)
            def addFieldToDoc(field_name, field_content):
                #if it is a string, clean tab and enter characters
                if isinstance(field_content,str):
                    field_content.replace("\\", "").replace('\"', "").replace("\r","")
                    field_content = field_content.replace("\n","").replace("\t", "").rstrip()

                if field_content is None:
                    field_content = "None"            

                a_dict = {field_name : field_content}    
                doc.update(a_dict)     

            # go through the list of fields from configuration and add to the document
            for i in self.strFocusedTweetFieldsArr:         
                field_name = i
                field_content = tweet[i]
                addFieldToDoc(field_name, field_content)

            #go through the list of user fields from configuration and add to the document
            for i in self.strFocusedTweetUserFieldsArr:         
                field_name = 'user_' + i
                field_content = tweet['user'][i]
                addFieldToDoc(field_name, field_content)                        
            
            # **************************
            

            # add created_at
            a_dict = {'tweet_created_at': created_at}
            doc.update(a_dict)     
                
            # add seq number to the end
            a_dict = {'seq_no': seq_no, 'seq_agg': "A"}    
            doc.update(a_dict)  

            # Add this tweet doc to the array. the array of all 
            # tweets will be used to insertMany into mongoDB 
            file_data.append(doc)

        # insert records into collection
        try:
            self.c_focusedTweet.insert_many(file_data)
        except Exception as e:
            print("Error loading focused tweet | " +str(e) )  

        
        # Create indexes in collection. This will help performance later
        try:
            resp = self.c_focusedTweet.create_index([('seq_no', pymongo.ASCENDING)])            
        except Exception as e:
            print('Could not create index in focusedTweet' + str(e))

        try:
            resp = self.c_focusedTweet.create_index([('id_str', pymongo.ASCENDING)])            
        except Exception as e:
            print('Could not create index in focusedTweet' + str(e))
            

 

    #####################################
    # Method: loadUsersData
    # Description: This method will call loadCollection_UpdateStatus to load the users collection
    # Users are store in different part of the tweet. 
    # In the tweet itself, in the retweet branch, in the quote branch, in the field in_reply_to_user and in the mention branch. 
    # Use parameter "user_type_filter" to select which type you want to load. 
    # IMPORTANT: Types reply and mention do not contain full user information
    # This method also creates a index to prevent duplicate user information. 
    # If a user already exists, it just rejects the insertion. 
    # Parameters:  
    #   -inc = how many tweet records you want to load at the time. 
    #    (Large number may cause memory errors, low number may take too long to run)
    #   -user_type_filter = the type of user you want to load - 
    #    (Options: tweet, retweet, quote, reply and mention)
    def loadUsersData(self, inc, user_type_filter):
        self.loadCollection_UpdateStatus('users', inc, user_type_filter)
        

    #####################################
    # Method: loadUsersDataMinMax
    # Description: This method will load the users collection 
    # It filters by a interval number of tweets. 
    # This is because loading everything at once might cause out of memory errors
    # Parameters:   
    #   -minV & maxV = the tweet seq_no interval you want to run this analysis for
    #   -user_type_filter = the type of user you want to to load - 
    #    (Options: tweet, retweet, quote, reply and mention) 
    def loadUsersDataMinMax(self, minV, maxV, user_type_filter):
        
        file_data = []        
        
        select_cTweet = self.c_tweet.find({"seq_no":{ "$gt":minV,"$lte":maxV}})

        # add another json record to the array of records to insert
        def addToList(user_type, user_id_str, screen_name, name, location, 
                      description, created_at, protected, verified, followers_count, 
                      friends_count, listed_count, favourites_count, statuses_count):

            location_clean = ''
            description_clean = ''

            if location is not None:
                location_clean = location.replace("\\", "").replace('\"', "").replace("\r","")
                location_clean = location_clean.replace("\n","").replace("\t", "").rstrip()
            if description is not None:
                description_clean = description.replace("\\", "").replace('\"', "").replace("\r","")
                description_clean = description_clean.replace("\n","").replace("\t", "").rstrip()

                
            data = '{"screen_name":"' + screen_name  + '"}'
            doc = json.loads(data)
            add_col = {'user_id_str': user_id_str}
            doc.update(add_col)
            add_col = {'name': name}
            doc.update(add_col)  
            add_col = {'user_created_at': created_at}
            doc.update(add_col)
            add_col = {'location': location}
            doc.update(add_col)
            add_col = {'location_clean': location_clean}
            doc.update(add_col)  
            add_col = {'description': description}
            doc.update(add_col)  
            add_col = {'description_clean': description_clean}
            doc.update(add_col)  
            add_col = {'protected': protected}
            doc.update(add_col)  
            add_col = {'verified': verified}
            doc.update(add_col)  
            add_col = {'followers_count': followers_count}
            doc.update(add_col)  
            add_col = {'friends_count': friends_count}
            doc.update(add_col)  
            add_col = {'listed_count': listed_count}
            doc.update(add_col)  
            add_col = {'favourites_count': favourites_count}
            doc.update(add_col)  
            add_col = {'statuses_count': statuses_count}
            doc.update(add_col)  
            add_col = {'user_type': user_type}
            doc.update(add_col)

            file_data.append(doc)
            
            
        #loop through tweets
        for tweet in select_cTweet:    

            if user_type_filter == 'tweet':                
                user_id_str = tweet['user']['id_str']
                name = tweet['user']['name']
                screen_name = tweet['user']['screen_name']
                location = tweet['user']['location']
                description = tweet['user']['description']
                protected = tweet['user']['protected']
                followers_count = tweet['user']['followers_count']
                friends_count = tweet['user']['friends_count']
                listed_count = tweet['user']['listed_count']
                created_at = tweet['user']['created_at']
                favourites_count =tweet['user']['favourites_count']
                verified = tweet['user']['verified']
                statuses_count = tweet['user']['statuses_count']        
                addToList(user_type_filter, user_id_str, screen_name, name, location, 
                          description, created_at, protected, verified, followers_count, 
                          friends_count, listed_count, favourites_count, statuses_count)


            #user from the retweet original tweet
            if user_type_filter == 'retweet':
                if 'retweeted_status' in tweet:                      
                    if 'user' in tweet['retweeted_status']:                        
                        user_id_str = tweet['retweeted_status']['user']['id_str']
                        name = tweet['retweeted_status']['user']['name']
                        screen_name = tweet['retweeted_status']['user']['screen_name']
                        location = tweet['retweeted_status']['user']['location']
                        description = tweet['retweeted_status']['user']['description']
                        protected = tweet['retweeted_status']['user']['protected']
                        followers_count = tweet['retweeted_status']['user']['followers_count']
                        friends_count = tweet['retweeted_status']['user']['friends_count']
                        listed_count = tweet['retweeted_status']['user']['listed_count']
                        created_at = tweet['retweeted_status']['user']['created_at']
                        favourites_count =tweet['retweeted_status']['user']['favourites_count']
                        verified = tweet['retweeted_status']['user']['verified']
                        statuses_count = tweet['retweeted_status']['user']['statuses_count']
                        addToList(user_type_filter, user_id_str, screen_name, name, location, 
                                  description, created_at, protected, verified, followers_count, 
                                  friends_count, listed_count, favourites_count, statuses_count)


            #user from the quoted tweet
            if user_type_filter == 'quote':
                if 'quoted_status' in tweet:                      
                    if 'user' in tweet['quoted_status']:                        
                        user_id_str = tweet['quoted_status']['user']['id_str']
                        name = tweet['quoted_status']['user']['name']
                        screen_name = tweet['quoted_status']['user']['screen_name']
                        location = tweet['quoted_status']['user']['location']
                        description = tweet['quoted_status']['user']['description']
                        protected = tweet['quoted_status']['user']['protected']
                        followers_count = tweet['quoted_status']['user']['followers_count']
                        friends_count = tweet['quoted_status']['user']['friends_count']
                        listed_count = tweet['quoted_status']['user']['listed_count']
                        created_at = tweet['quoted_status']['user']['created_at']
                        favourites_count =tweet['quoted_status']['user']['favourites_count']
                        verified = tweet['quoted_status']['user']['verified']
                        statuses_count = tweet['quoted_status']['user']['statuses_count']
                        addToList(user_type_filter, user_id_str, screen_name, name, location, 
                                  description, created_at, protected, verified, followers_count, 
                                  friends_count, listed_count, favourites_count, statuses_count)

            #in reply to user
            if user_type_filter == 'reply':
                if tweet['in_reply_to_user_id'] != None:                            
                    user_id_str = tweet['in_reply_to_user_id_str']        
                    screen_name = tweet['in_reply_to_screen_name']
                    addToList(user_type_filter, user_id_str, screen_name, name=None, location=None, 
                              description=None, created_at=None, protected=None, verified=None, 
                              followers_count=None, friends_count=None, listed_count=None, favourites_count=None, statuses_count=None)



            #find mentioned user
            if user_type_filter == 'mention':                
                if 'extended_tweet' in tweet:                
                    for gt_tweet in tweet['extended_tweet']['entities']['user_mentions']:                    
                        user_id_str = gt_tweet['id_str']        
                        screen_name = gt_tweet['screen_name']
                        addToList(user_type_filter, user_id_str, screen_name, name=None, location=None, 
                                  description=None, created_at=None, protected=None, verified=None, followers_count=None, 
                                  friends_count=None, listed_count=None, favourites_count=None, statuses_count=None)
                else:                       
                    for gt_tweet in tweet['entities']['user_mentions']:                                        
                        user_id_str = gt_tweet['id_str']        
                        screen_name = gt_tweet['screen_name']
                        addToList(user_type_filter, user_id_str, screen_name, name=None, location=None, 
                                  description=None, created_at=None, protected=None, verified=None, 
                                  followers_count=None, friends_count=None, listed_count=None, favourites_count=None, statuses_count=None)

                #find retweets mentions
                if 'retweeted_status' in tweet:
                    if 'extended_tweet' in tweet['retweeted_status']:     
                        if 'entities' in tweet['retweeted_status']['extended_tweet']:                        
                            for gt_tweet in tweet['retweeted_status']['extended_tweet']['entities']['user_mentions']:                            
                                user_id_str = gt_tweet['id_str']        
                                screen_name = gt_tweet['screen_name']
                                addToList(user_type_filter, user_id_str, screen_name, name=None, location=None, 
                                          description=None, created_at=None, protected=None, verified=None, 
                                          followers_count=None, friends_count=None, listed_count=None, favourites_count=None, statuses_count=None)

                    elif 'entities' in tweet['retweeted_status']:
                        for gt_tweet in tweet['retweeted_status']['entities']['user_mentions']:                       
                            user_id_str = gt_tweet['id_str']        
                            screen_name = gt_tweet['screen_name']
                            addToList(user_type_filter, user_id_str, screen_name, name=None, location=None, 
                                      description=None, created_at=None, protected=None, verified=None, followers_count=None, 
                                      friends_count=None, listed_count=None, favourites_count=None, statuses_count=None)

                #find quote mentions
                if 'quoted_status' in tweet:                                              
                    #find mentions in a quote
                    if 'extended_tweet' in tweet['quoted_status']:     
                        if 'entities' in tweet['quoted_status']['extended_tweet']:                        
                            for gt_tweet in tweet['quoted_status']['extended_tweet']['entities']['user_mentions']:                            
                                user_id_str = gt_tweet['id_str']        
                                screen_name = gt_tweet['screen_name']
                                addToList(user_type_filter, user_id_str, screen_name, name=None, location=None, 
                                          description=None, created_at=None, protected=None, verified=None, followers_count=None, 
                                          friends_count=None, listed_count=None, favourites_count=None, statuses_count=None)

                    elif 'entities' in tweet['quoted_status']:
                        for gt_tweet in tweet['quoted_status']['entities']['user_mentions']:
                            user_id_str = gt_tweet['id_str']        
                            screen_name = gt_tweet['screen_name']
                            addToList(user_type_filter, user_id_str, screen_name, name=None, location=None, 
                                      description=None, created_at=None, protected=None, verified=None, followers_count=None, 
                                      friends_count=None, listed_count=None, favourites_count=None, statuses_count=None)
                                
            
        # insert user into  db
        try:
            self.c_users.insert_many(file_data, ordered=False)
        except Exception as e:
            if str(type(e).__name__) == "BulkWriteError":  #igones if just failed when trying to insert duplicate users
                pass
            else:
                print('Error in insert many user - ' + str(type(e).__name__))        
        
        
        
            
    #####################################
    # Method: loadTweetHashTags
    # Description: This method will call loadCollection_UpdateStatus to load the hashtag collection    
    # Parameter:  
    #   -inc = how many tweet records you want to load at the time. 
    #    (Large number may cause memory errors, low number may take too long to run)        
    def loadTweetHashTags(self, inc):
        
        self.loadCollection_UpdateStatus('tweetHashTags', inc )        
        
    
    #####################################
    # Method: loadTweetHashTagsMinMax
    # Description: This method will load the hashtags associated to each tweet
    # It filters by a interval number of tweets. 
    # This is because loading everything at once might cause out of memory errors
    # Parameters:   
    #   -minV & maxV = the tweet seq_no interval you want to run this analysis for    
    def loadTweetHashTagsMinMax(self, minV, maxV):     

        file_data = []

        select_cTweet = self.c_focusedTweet.find({"seq_no":{ "$gt":minV,"$lte":maxV}})
        
        # add another json record to the array of records to insert
        def addToList(id_str, type_ht, ht, ht_lower, created_at):                                 

            #creating the json doc
            data = '{"tweet_id_str":"' + id_str + \
                    '", "type_ht":"' + type_ht + \
                    '", "ht":"' + ht + \
                    '", "ht_lower":"' + ht_lower + '"}'
            doc = json.loads(data)

            #add created_at
            a_dict = {'tweet_created_at': created_at}
            doc.update(a_dict)
            
            #add seq number to the end
            a_dict = {'tweet_seq_no': seq_no, 'seq_agg': "A"}
            doc.update(a_dict)

            # Add this tweet doc to the array. the array of all tweets 
            # will be used to insertMany into mongoDB 
            file_data.append(doc)


        #loop through tweets
        for tweet in select_cTweet:
            
            id_str = tweet['id_str']
            seq_no = tweet['seq_no']
            created_at = tweet['tweet_created_at']
                        
            #get Hashtags            
            if 'hashtags' in tweet:
                for gt_tweet in tweet['hashtags']:
                    
                    ht = gt_tweet['ht']
                    ht_lower = gt_tweet['ht_lower']                    
                    type_ht = gt_tweet['type_ht']             
                    
                    #creating the json doc
                    data = '{"tweet_id_str":"' + id_str + \
                            '", "type_ht":"' + type_ht + \
                            '", "ht":"' + ht + \
                            '", "ht_lower":"' + ht_lower + '"}'
                    doc = json.loads(data)

                    #add created_at
                    a_dict = {'tweet_created_at': created_at}
                    doc.update(a_dict)

                    #add seq number to the end
                    a_dict = {'tweet_seq_no': seq_no, 'seq_agg': "A"}
                    doc.update(a_dict)

                    # Add this tweet doc to the array. the array of all 
                    # tweets will be used to insertMany into mongoDB 
                    file_data.append(doc)
                    

        # insert hashtags into db
        try:
            self.c_tweetHashTags.insert_many(file_data)
        except:
            print("Error loading c_tweetHashTags ")
            
                                
    
    #####################################
    # Method: loadTweetConnections
    # Description: This method will call loadCollection_UpdateStatus to load the tweetConnections collection    
    # Parameter:  
    #   -inc = how many tweet records you want to load at the time. 
    #    (Large number may cause memory errors, low number may take too long to run)     
    def loadTweetConnections(self, inc):
        
        self.loadCollection_UpdateStatus('tweetConnections', inc)
                

    #####################################
    # Method: loadTweetConnectionsMinMax
    # Description: This method will load the tweet connections (edges) associated to each tweet        
    # It filters by a interval number of tweets. 
    # This is because loading everything at once might cause out of memory errors
    # Parameters:  
    #   -minV & maxV = the tweet seq_no interval you want to run this analysis for      
    def loadTweetConnectionsMinMax(self, minV, maxV):

        file_data = []
        user_id_str_b = ''     
        desc = ''
        
        select_cTweet = self.c_tweet.find({"seq_no":{ "$gt":minV,"$lte":maxV}})
                        
        # add another json record to the array of records to insert
        def addToList(id_str, type_conn, user_id_str_a, screen_name_a, 
                      user_id_str_b, screen_name_b, desc, tweet_created_dt, 
                      retweeted_status_id=None, quoted_status_id=None, in_reply_to_status_id=None):

            if user_id_str_a is None:
                user_id_str_a = '' 
            if user_id_str_b is None:
                user_id_str_b = ''
            if retweeted_status_id is None:
                retweeted_status_id = ''
            if quoted_status_id is None: 
                quoted_status_id = ''
            if in_reply_to_status_id is None:
                in_reply_to_status_id = ''
                
            #to set the edge_screen_name_directed_key
            if screen_name_a > screen_name_b:
                screen_name_a_un = screen_name_a
                screen_name_b_un = screen_name_b
            else:
                screen_name_a_un = screen_name_b
                screen_name_b_un = screen_name_a
                
            #creating the json doc
            data = '{"tweet_id_str":"' + id_str + \
                    '", "type_of_connection":"' + type_conn + \
                    '", "user_id_str_a":"' + user_id_str_a + \
                    '", "screen_name_a":"' + screen_name_a + \
                    '", "user_id_str_b":"' + user_id_str_b + \
                    '", "screen_name_b":"' + screen_name_b + \
                    '", "desc":"' + desc + \
                    '", "retweeted_status_id":"' + str(retweeted_status_id) + \
                    '", "quoted_status_id":"' + str(quoted_status_id) + \
                    '", "in_reply_to_status_id":"' + str(in_reply_to_status_id) + \
                    '", "edge_screen_name_directed_key":"' + screen_name_a.lower() + '-' + screen_name_b.lower() + \
                    '", "edge_screen_name_undirected_key":"' + screen_name_a_un.lower() + '-' + screen_name_b_un.lower() + '"}'
                    
            doc = json.loads(data)            
            
            #add tweet_created_dt
            a_dict = {'tweet_created_at': tweet_created_dt}
            doc.update(a_dict)
            
            #add seq number to the end
            a_dict = {'tweet_seq_no': seq_no, 'seq_agg': "A"}
            doc.update(a_dict)  

            #add this tweet doc to the array. the array of all tweets will be used to insertMany into mongoDB 
            file_data.append(doc)
        
        
        #loop through tweets
        for tweet in select_cTweet:    

            #Get all the basic info about the tweet. 
            id_str = tweet['id_str']
            user_id_str_a = tweet['user']['id_str']
            screen_name_a = tweet['user']['screen_name']
            seq_no = tweet['seq_no']            
            tweet_created_dt = datetime.datetime.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
                 
            #find replies
            type_conn = 'reply'
            desc = 'user a replied to user b'
            if tweet['in_reply_to_status_id'] is not None or tweet['in_reply_to_user_id_str'] is not None:
                in_reply_to_status_id = tweet['in_reply_to_status_id_str']
                user_id_str_b = tweet['in_reply_to_user_id_str']
                screen_name_b = tweet['in_reply_to_screen_name']                                
                addToList(id_str, type_conn, user_id_str_a, 
                          screen_name_a, user_id_str_b, screen_name_b, desc, 
                          tweet_created_dt, retweeted_status_id=None, quoted_status_id=None, 
                          in_reply_to_status_id=in_reply_to_status_id)
                                
            #find mentions
            type_conn = 'mention'
            desc = 'user a mentioned user b'
            if 'extended_tweet' in tweet:                
                for gt_tweet in tweet['extended_tweet']['entities']['user_mentions']:                    
                    user_id_str_b = gt_tweet['id_str']
                    screen_name_b = gt_tweet['screen_name']
                    addToList(id_str, type_conn, user_id_str_a, 
                              screen_name_a, user_id_str_b, screen_name_b, desc, 
                              tweet_created_dt, retweeted_status_id=None, quoted_status_id=None)
            else:                       
                for gt_tweet in tweet['entities']['user_mentions']:                                        
                    user_id_str_b = gt_tweet['id_str']
                    screen_name_b = gt_tweet['screen_name']
                    addToList(id_str, type_conn, user_id_str_a, 
                              screen_name_a, user_id_str_b, screen_name_b, desc, 
                              tweet_created_dt, retweeted_status_id=None, quoted_status_id=None)
                       
            #find retweets
            if 'retweeted_status' in tweet:
                type_conn = 'retweet'      
                desc = 'user a retweeted a tweet from user b'                
                
                retweeted_status_id = tweet['retweeted_status']['id_str']
                user_id_str_b = tweet['retweeted_status']['user']['id_str']
                screen_name_b = tweet['retweeted_status']['user']['screen_name']                
                addToList(id_str, type_conn, user_id_str_a, 
                          screen_name_a, user_id_str_b, screen_name_b, desc, 
                          tweet_created_dt, retweeted_status_id=retweeted_status_id, quoted_status_id=None)
                                 
            #find quotes
            if 'quoted_status' in tweet:                                
                type_conn = 'quote'
                desc = 'user a quoted a tweet from user b'
                
                quote_status_id = tweet['quoted_status']['id_str']
                user_id_str_b = tweet['quoted_status']['user']['id_str']
                screen_name_b = tweet['quoted_status']['user']['screen_name']                
                addToList(id_str, type_conn, user_id_str_a, 
                          screen_name_a, user_id_str_b, screen_name_b, desc, 
                          tweet_created_dt, retweeted_status_id=None, quoted_status_id=quote_status_id)                     
                    
                #find mentions in a quote
                type_conn = 'mention_quote'
                if 'extended_tweet' in tweet['quoted_status']:     
                    if 'entities' in tweet['quoted_status']['extended_tweet']:                        
                        for gt_tweet in tweet['quoted_status']['extended_tweet']['entities']['user_mentions']:                            
                            user_id_str_b = gt_tweet['id_str']
                            screen_name_b = gt_tweet['screen_name']
                            addToList(id_str, type_conn, user_id_str_a, 
                                      screen_name_a, user_id_str_b, screen_name_b, desc, 
                                      tweet_created_dt, retweeted_status_id=None, quoted_status_id=quote_status_id)
                            
                elif 'entities' in tweet['quoted_status']:
                    for gt_tweet in tweet['quoted_status']['entities']['user_mentions']:
                        user_id_str_b = gt_tweet['id_str']
                        screen_name_b = gt_tweet['screen_name']
                        addToList(id_str, type_conn, user_id_str_a, 
                                  screen_name_a, user_id_str_b, screen_name_b, desc, 
                                  tweet_created_dt, retweeted_status_id=None, quoted_status_id=quote_status_id)
            
        # insert connections(directed edges) into db
        try:
            self.c_tweetConnections.insert_many(file_data)
        except:
            print("Error loading tweetConnections ")
            

        # create indexes to improve performance
        try:
            resp = self.c_tweetConnections.create_index([('tweet_id_str', pymongo.ASCENDING)])            
        except Exception as e:
            print('Could not create index in tweetConnections' + str(e))

        try:
            resp = self.c_tweetConnections.create_index([('edge_screen_name_directed_key', pymongo.ASCENDING)])            
        except Exception as e:
            print('Could not create index in tweetConnections' + str(e))  
            
        try:
            resp = self.c_tweetConnections.create_index([('edge_screen_name_undirected_key', pymongo.ASCENDING)])            
        except Exception as e:
            print('Could not create index in tweetConnections' + str(e))             
                                
            

            
            
            
    #####################################
    # Method: loadTweetHTConnections
    # Description: This method will call loadCollection_UpdateStatus to load the tweetHTConnections collection        
    # Parameter:  
    #   -inc = how many tweet records you want to load at the time. 
    #    (Large number may cause memory errors, low number may take too long to run)     
    def loadTweetHTConnections(self, inc):
        
        self.loadCollection_UpdateStatus('tweetHTConnections', inc)
                

    #####################################
    # Method: loadTweetHTConnectionsMinMax
    # Description: This method will load the tweet hashtags connections (edges) associated to each hashtag for each tweet        
    # It filters by a interval number of tweets. This is because loading everything at once might cause out of memory errors
    # Parameters:  
    #   -minV & maxV = the tweet seq_no interval you want to run this analysis for      
    def loadTweetHTConnectionsMinMax(self, minV, maxV):

        file_data = []
        
        select_cTweet = self.c_focusedTweet.find({"seq_no":{ "$gt":minV,"$lte":maxV}})
                        
        #loop through tweets
        for tweet in select_cTweet:

            id_str = tweet['id_str']
            seq_no = tweet['seq_no']
            created_at = tweet['tweet_created_at']

            #get Hashtags            
            if 'hashtags' in tweet:

                #build array with all hashtags for this one tweet
                ht_arr = []
                for gt_tweet in tweet['hashtags']:
                    ht_arr.append(gt_tweet['ht_lower'])

                #loops through the combinations between the hashtags and insert one records for each combination
                for element in itertools.combinations(ht_arr, 2):   

                    if element[0] < element[1]:
                        ht_a = element[0]
                        ht_b = element[1]                
                    else:
                        ht_a = element[1]
                        ht_b = element[0]            
                    ht_key = ht_a + '-'  + ht_b

                    #creating the json doc
                    data = '{"tweet_id_str":"' + id_str + \
                            '", "ht_a":"' + ht_a + \
                            '", "ht_b":"' + ht_b + \
                            '", "ht_key":"' + ht_key + '"}'
                    doc = json.loads(data)

                    #add created_at
                    a_dict = {'tweet_created_at': created_at}
                    doc.update(a_dict)

                    #add seq number to the end
                    a_dict = {'tweet_seq_no': seq_no, 'seq_agg': "A"}
                    doc.update(a_dict)

                    #add this tweet doc to the array. the array of all tweets will be used to insertMany into mongoDB 
                    file_data.append(doc)


        #insert hashtags into db
        try:
            self.c_tweetHTConnections.insert_many(file_data)
        except:
            print("Error loading tweetHTConnections ")                            

        # create indexes to improve performance
        try:
            resp = self.c_tweetHTConnections.create_index([('tweet_id_str', pymongo.ASCENDING)])            
        except Exception as e:
            print('Could not create index in tweetHTConnections' + str(e))
            
        try:
            resp = self.c_tweetHTConnections.create_index([('ht_key', pymongo.ASCENDING)])            
        except Exception as e:
            print('Could not create index in tweetHTConnections' + str(e))  


            
    #####################################
    # Method: loadWordsData
    # Description: This method will call loadCollection_UpdateStatus to load the tweetWords collection        
    # Parameters:  
    #   -inc = how many tweet records you want to load at the time. 
    #          (Large number may cause memory errors, low number may take too long to run)    
    def loadWordsData(self, inc):
        
        self.loadCollection_UpdateStatus('tweetWords', inc )        
            
           
    #####################################
    # Method: breakTextIntoWords
    # Description: This method will break text from tweet into words and tag them        
    # It filters by a interval number of tweets. 
    # This is because loading everything at once might cause out of memory errors
    # Parameters:  minV & maxV = the tweet seq_no interval you want to run this analysis for    
    def breakTextIntoWords(self, minV, maxV):

        file_data = []
        seq_no = 0
        
        select_cTweetWords = self.c_tweetWords.aggregate( 
            [{"$group": {"_id": "seq_agg" , "maxSeqNo": { "$max": "$seq_no" } } } ])
        for tweetCount in select_cTweetWords:
            max_seq_no = tweetCount["maxSeqNo"] 
            seq_no = max_seq_no                                
        
        select_cFocusedTweet = self.c_focusedTweet.find({"seq_no":{ "$gt":minV,"$lte":maxV}})        
        
        
        
        #loop through tweets
        for tweet in select_cFocusedTweet:
            
            #Get all the basic info about the tweet. 
            # (These will always be saved independet of configurations)    
            id_str = tweet['id_str']
            text =  tweet['text_combined_clean']           
            year =  tweet['year']
            month_name =  tweet['month_name']
            month_no =  tweet['month_no']
            day =  tweet['day']
            user_id =  tweet['user_id']
            seq_no_tweet = tweet['seq_no']                       
            created_at = tweet['tweet_created_at']            

            try:                            
                
                for word in pos_tag(tokenizer.tokenize(text)):                                                                                                                                

                    cleanWordLw = word[0]                    
                    
                    stop_word_fl = 'F'
                    if cleanWordLw in stopWords:
                        stop_word_fl = 'T'                                            
                    
                    en_word_fl = 'T'
                    try:
                        x = dictionary_words[cleanWordLw]
                    except KeyError:
                        en_word_fl = 'F'                           
                                            
                    word_syl = pyphen_dic.inserted(cleanWordLw)
                                            
                    seq_no = seq_no+1                                                            

                    #lemmatize word
                    tag = word[1].lower()[0]                    

                    if tag == 'j':
                        tag = wordnet.ADJ
                    elif tag == 'v':
                        tag = wordnet.VERB
                    elif tag == 'n':
                        tag = wordnet.NOUN
                    elif tag == 'r':
                        tag = wordnet.ADV
                    else:
                        tag  = ''                    
                        
                    if tag in ("j", "n", "v", "r"):
                        lemm_word = lemmatiser.lemmatize(cleanWordLw, pos=tag)
                    else:
                        lemm_word = lemmatiser.lemmatize(cleanWordLw)
                                            
                    data = '{"word":"' + cleanWordLw + \
                            '","word_tag":"' + word[1]  + \
                            '","word_lemm":"' + lemm_word + \
                            '","word_syl":"' + word_syl + \
                            '","stop_word_fl":"' + stop_word_fl + \
                            '","en_word_fl":"' + en_word_fl + \
                            '","tweet_id_str":"' + id_str  + \
                            '", "text":"' + text + \
                            '", "year":"' + year + \
                            '", "month_name":"' + month_name + \
                            '", "month_no":"' + month_no + \
                            '", "day":"' + day + \
                            '", "user_id":"' + user_id + '"}'
                    
                    doc = json.loads(data)                                                                        
                    
                    #add created_at
                    a_dict = {'tweet_created_at': created_at}
                    doc.update(a_dict)  

                    a_dict = {'tweet_seq_no': seq_no_tweet, 'seq_no': seq_no, 'seq_agg': "A"}    
                    doc.update(a_dict)
                    
                    #add this tweet doc to the array. the array of all tweets will be used to insertMany into mongoDB 
                    file_data.append(doc)                                               

            except Exception as e:
                print("Error on loadWordsData. " +str(e) + " | err tweet_id: " + id_str)

        
        #insert words into db
        try:
            self.c_tweetWords.insert_many(file_data)
        except Exception as e:
            print("Error on loadWordsData | " +str(e) ) 
            
        
        # create index to improve performance
        try:
            resp = self.c_tweetWords.create_index([('tweet_seq_no', pymongo.ASCENDING)])            
        except Exception as e:
            print('Could not create index in tweetWords' + str(e))

        try:
            resp = self.c_tweetWords.create_index([('tweet_id_str', pymongo.ASCENDING)])            
        except Exception as e:
            print('Could not create index in tweetWords' + str(e))
            

                
    #####################################
    # Method: loadAggregations
    # Description: load aggregations
    # Parameters:  
    #  -aggType = the type of aggreagation you want to run - 
    #   (Options: tweetCountByFile, hashtagCount, tweetCountByLanguageAgg, 
    #             tweetCountByMonthAgg, tweetCountByUser)
    def loadAggregations(self, aggType):
    
        print ("loading " + aggType + " process started....")
        
        if (aggType == 'tweetCountByFile'):
            self.tweetCountByFileAgg()
        elif (aggType == 'hashtagCount'):
            self.hashtagCountAgg()
        elif (aggType == 'tweetCountByLanguageAgg'):
            self.tweetCountByLanguageAgg()
        elif (aggType == 'tweetCountByMonthAgg'):
            self.tweetCountByPeriodAgg()
        elif (aggType == 'tweetCountByUser'):
            self.tweetCountByUser()    
            
        print ("loading " + aggType + " process completed.")


    
    #####################################
    # Method: tweetCountByFileAgg
    # Description: load aggregation on tweetCountByFileAgg collection
    def tweetCountByFileAgg(self):
    
        #delete everything from the collection because we will repopulate it
        result = self.c_tweetCountByFileAgg.delete_many({}) 
        select_cTweet = self.c_tweet.aggregate( 
            [{"$group": {"_id": {"file_path": "$file_path"}, "count": { "$sum": 1 } } } ])

        for tweetCount in select_cTweet:            
            try:        
                if tweetCount["_id"]["file_path"] is not None:
                    data = '{"file_path":"' + tweetCount["_id"]["file_path"] + \
                    '", "count":"' + str(tweetCount["count"]) + '"}'                

                    x = json.loads(data)
                    result = self.c_tweetCountByFileAgg.insert_one(x)

            except Exception as e:            
                print("Error running aggregation: tweetCountByFile | " +str(e))
                continue                 
                
                
    
    #####################################
    # Method: hashtagCountAgg
    # Description: load aggregation on hashTagCountAgg collection
    def hashtagCountAgg(self):     

        result = self.c_hashTagCountAgg.delete_many({}) 
        select_cfocusedTweet = self.c_focusedTweet.aggregate( 
            [ {"$unwind": '$hashtags'}, 
            {"$project": { "hashtags": 1, "ht": '$hashtags.ht'} },
            {"$group": { "_id": { "ht": '$hashtags.ht_lower' }, "count": { "$sum": 1 } } } ])

        for tweetCount in select_cfocusedTweet:

            try:    
                data = '{"hashtag":"' + tweetCount["_id"]["ht"] + '"}'
                x = json.loads(data)        

                a_dict = {'count': tweetCount["count"]}    
                x.update(a_dict)

                result = self.c_hashTagCountAgg.insert_one(x)

            except Exception as e:            
                print("Error running aggregation: hashtagCount | " +str(e))
                continue   
            
                    

    #####################################
    # Method: tweetCountByLanguageAgg
    # Description: load aggregation on tweetCountByLanguageAgg collection
    def tweetCountByLanguageAgg(self):

        result = self.c_tweetCountByLanguageAgg.delete_many({}) 
        select_cfocusedTweet = self.c_focusedTweet.aggregate( 
            [{"$group": {"_id": {"lang": "$lang"}, "count": { "$sum": 1 } } } ])

        for tweetCount in select_cfocusedTweet:
            try:        
                data = '{"lang":"' + tweetCount["_id"]["lang"] + \
                '", "count":"' + str(tweetCount["count"]) + '"}'                

                x = json.loads(data)
                result = self.c_tweetCountByLanguageAgg.insert_one(x)

            except Exception as e:            
                print("Error running aggregation: tweetCountByLanguageAgg | " +str(e))
                continue
                
                    
    #####################################
    # Method: tweetCountByPeriodAgg
    # Description: load aggregation on tweetCountByPeriodAgg collection 
    def tweetCountByPeriodAgg(self):

        result = self.c_tweetCountByPeriodAgg.delete_many({}) 
        select_cfocusedTweet = self.c_focusedTweet.aggregate( 
            [{"$group": {"_id": {"year": "$year", "month_no": "$month_no"}, "count": { "$sum": 1 } } } ])

        for tweetCount in select_cfocusedTweet:

            try:        
                data = '{"year":"' + tweetCount["_id"]["year"] + \
                      '","month_no":"' + tweetCount["_id"]["month_no"]  + \
                      '", "count":"' + str(tweetCount["count"]) + '"}'                

                x = json.loads(data)
                result = self.c_tweetCountByPeriodAgg.insert_one(x)

            except Exception as e:            
                print("Error running aggreagation: tweetCountByPeriodAgg | " +str(e))
                continue                                         

    
    #####################################
    # Method: tweetCountByUser
    # Description: load aggregation on tweetCountByUserAgg collection
    def tweetCountByUser(self):

        result = self.c_tweetCountByUserAgg.delete_many({})         
        select_cfocusedTweet = self.c_focusedTweet.aggregate( 
            [{"$group": {"_id": {"user_id": "$user_id", "user_screen_name" : "$user_screen_name"}, 
                         "count": { "$sum": 1 } } } ],
            allowDiskUse = True, collation=Collation(locale="en_US", strength=2))
        
        for tweetCount in select_cfocusedTweet:
            try:        
                data = '{"user_id":"' + tweetCount["_id"]["user_id"] + \
                '", "user_screen_name":"' + tweetCount["_id"]["user_screen_name"]  + \
                '", "count":"' + str(tweetCount["count"]) + '"}'                        

                x = json.loads(data)
                result = self.c_tweetCountByUserAgg.insert_one(x)

            except Exception as e:            
                print("Error running aggregation: tweetCountByUser | " +str(e))
                continue
                  

                    
    #####################################
    # Method: create_tmp_edge_collections
    # Description: This method will create temporary collections to help improve 
    # query performance when filtering data by a list of edges
    # Creating some temp collections, we can create indexes that will increase the lookup performance
    # This method was created to allow performance improvements
    # Parameters:  
    #  -arr_edges = the list of edges you want to search for - 
    #   (format "screen_name"-"screen_name")
    #  -startDate_filter & endDate_filter = if you want to filter your query by a period - (Default=None)
    #  -is_bot_Filter = if you want to filter by a connections being for a bot or not
    def create_tmp_edge_collections(self, arr_edges, arr_ht_edges, query_filter):
                                
        if arr_ht_edges is not None:
            arr_edges = arr_ht_edges                                     
        
        arr_ids = []
        self.c_tmpEdges.delete_many({})
        self.c_tmpEdgesTweetIds.delete_many({})

        # *** creating tmp collection with given edges
        file_data = []
        for x in arr_edges:
            data = '{"edge":"' + x + '"}'
            doc = json.loads(data)
            file_data.append(doc)                                               

        self.c_tmpEdges.insert_many(file_data)
        resp = self.c_tmpEdges.create_index([('edge', pymongo.ASCENDING)])  #creating index on tmp collection
        # **********************


        # *** creating tmp collection for tweet ids for the given edges            
        if arr_edges is not None:
            pipeline = [ {"$lookup":{"from":"tweetConnections",
                                     "localField": "edge",
                                     "foreignField": "edge_screen_name_undirected_key",
                                     "as":"fromItems"}},
                         {"$unwind": "$fromItems" },
                         {"$match": query_filter },
                         {"$project": { "tweet_id_str": "$fromItems.tweet_id_str"} }]
        if arr_ht_edges is not None:
            pipeline = [ {"$lookup":{"from":"tweetHTConnections",
                                     "localField": "edge",
                                     "foreignField": "ht_key",
                                     "as" : "fromItems"}},
                         {"$unwind": "$fromItems" },
                         {"$match": query_filter },
                         {"$project": { "tweet_id_str": "$fromItems.tweet_id_str"} }]
        
        select = self.c_tmpEdges.aggregate(pipeline, allowDiskUse=True)
        for x in select:                             
            arr_ids.append(x['tweet_id_str'])


        file_data = []
        arr_no_dups = list(dict.fromkeys(arr_ids)) 

        for id_str in arr_no_dups :
            data = '{"tweet_id_str":"' + id_str + '"}'
            doc = json.loads(data)
            file_data.append(doc)

        # insert data into tmp collection
        if file_data != []:
            self.c_tmpEdgesTweetIds.insert_many(file_data)
            resp = self.c_tmpEdgesTweetIds.create_index([('tweet_id_str', pymongo.ASCENDING)]) 

        # ******************************
            

    #####################################
    # Method: set_bot_flag_based_on_arr
    # Description: This method will update collections focusedTweet, users,
    # and tweetConnections to identify is a user or tweet connections are from bots.
    # The bot list is passed as parameter
    # Parameters: 
    #   -bots_list_id_str = a list of user_ids that are bots
    #   -inc = how many tweets we want to update at the time for field is_bot_connection.
    #    Default=10000 (High number might take too long to run)
    def set_bot_flag_based_on_arr(self, bots_list_id_str, inc=10000):
        
        print("updating bot flag...")
        
        # set all records to be is_bot = 0 at first
        self.c_users.update_many({}, {"$set": {"is_bot": "0"}})
        self.c_tweetConnections.update_many({}, {"$set": {"is_bot": "0"}})
        self.c_tweetHTConnections.update_many({}, {"$set": {"is_bot": "0"}})
        self.c_focusedTweet.update_many({}, {"$set": {"is_bot": "0", "is_bot_connection": "0"}})
        self.c_tweetWords.update_many({}, {"$set": {"is_bot": "0", "is_bot_connection": "0"}})        

        #updates collections based on the given list of bots user_ids
        self.c_users.update_many({'user_id_str': {'$in': bots_list_id_str}}, {'$set': {'is_bot':'1'}})
        self.c_focusedTweet.update_many({'user_id': {'$in': bots_list_id_str}}, {'$set': {'is_bot':'1'}})
        self.c_tweetWords.update_many({'user_id': {'$in': bots_list_id_str}}, {'$set': {'is_bot':'1'}})        
        self.c_tweetConnections.update_many({'user_id_str_a': {'$in': bots_list_id_str}}, {'$set': {'is_bot':'1'}})        
                
        # **** Updating the tweets that are bots or connected to bots                
        i=0; arr_bot_conn = []                
        
        #find all the ids that are connected to bots (replies, retweets, quotes or mentions)
        select = self.c_tweetConnections.find({"is_bot" : "1"})
        for x in select:
            i = i + 1
            arr_bot_conn.append(x['tweet_id_str'])
            # updating records using the $in operator can take a long time if the array is too big. That is why we do it in increments
            if i > inc:
                self.c_focusedTweet.update_many({'id_str': {'$in': arr_bot_conn}}, {'$set': {'is_bot_connection':'1'}})
                self.c_tweetWords.update_many({'id_str': {'$in': arr_bot_conn}}, {'$set': {'is_bot_connection':'1'}})
                self.c_tweetHTConnections.update_many({'id_str': {'$in': arr_bot_conn}}, {'$set': {'is_bot_connection':'1'}})
                arr_bot_conn= []; i = 0

        self.c_focusedTweet.update_many({'id_str': {'$in': arr_bot_conn}}, {'$set': {'is_bot_connection':'1'}})
        self.c_tweetWords.update_many({'id_str': {'$in': arr_bot_conn}}, {'$set': {'is_bot_connection':'1'}})
        self.c_tweetHTConnections.update_many({'id_str': {'$in': arr_bot_conn}}, {'$set': {'is_bot':'1'}})
        # **************************** 
            
        print("updating bot flag completed")
        
       
    # Method: build_filter
    # Description: Build filter for queries. 
    # This is called by method queryData to create the filter that will by used in method
    # Parameters: 
    #  -startDate_filter & endDate_filter: coming from method queryData
    #  -is_bot_Filter: coming from method queryData
    #  -ht_to_filter: coming from method queryData 
    #  -user_conn_filter: coming from method queryData
    #  -exportType: coming from method queryData
    def build_filter(
            self, 
            startDate_filter=None, 
            endDate_filter=None, 
            is_bot_Filter=None, 
            ht_to_filter=None, 
            user_conn_filter=None, 
            exportType=None):                                                      

        # set correct format for start and end dates
        if startDate_filter is not None and endDate_filter is not None:
            start_date = datetime.datetime.strptime(startDate_filter, '%m/%d/%Y %H:%M:%S')
            end_date = datetime.datetime.strptime(endDate_filter, '%m/%d/%Y %H:%M:%S')  
        
        #set the comparison operator for bots queries    
        if is_bot_Filter is not None:            
            if is_bot_Filter == '0':
                bot_filter_comp_operator = "$and"                
            elif is_bot_Filter == '1':
                bot_filter_comp_operator = "$or"
                
        #set up the query filter base on the given parameters
        date_filter = {}        
        bot_filter = {}        
        ht_filter = {}        
        conn_filter = {}
        date_filter_for_edges = {}
        bot_filter_for_edges = {}
        ht_filter_for_edges = {}
        conn_filter_edges = {}
        
        #date filter
        if startDate_filter is not None and endDate_filter is not None:
            date_filter = { "tweet_created_at" : { "$gte": start_date, "$lt": end_date } }
            date_filter_for_edges = { "fromItems.tweet_created_at" : { "$gte": start_date, "$lt": end_date } }
        #bot filter
        if is_bot_Filter is not None:
            bot_filter = { "$or": [ { "is_bot": { "$eq": str(is_bot_Filter) } } , { "is_bot_connection": { "$eq": str(is_bot_Filter) } }]}
            bot_filter_for_edges = { "fromItems.is_bot": { "$eq": str(is_bot_Filter) } }
        #ht filter
        if ht_to_filter is not None:
            ht_filter = {"hashtags.ht_lower": ht_to_filter.lower()}
            ht_filter_for_edges = {}  ##### ***need to address this later            
        if user_conn_filter is not None:
            if exportType == 'edges':
                conn_filter = {"type_of_connection": user_conn_filter.lower()}
            conn_filter_edges = {"type_of_connection": user_conn_filter.lower()}
                
        query_filter = { "$and": [ date_filter, bot_filter, ht_filter, conn_filter ]}
        query_filter_for_edges = { "$and": [ date_filter_for_edges, bot_filter_for_edges, ht_filter_for_edges, conn_filter_edges ]}
        
        return query_filter, query_filter_for_edges
                            
    
    
    #####################################
    # Method: exportData
    # Description: Exports data into \t delimited file
    def exportData(
            self, 
            exportType, 
            filepath, 
            inc, 
            startDate_filter=None, 
            endDate_filter=None, 
            is_bot_Filter=None, 
            arr_edges=None,
            arr_ht_edges=None,
            top_no_filter=None, 
            ht_to_filter=None, 
            include_hashsymb_FL='Y',  
            replace_existing_file=True, 
            user_conn_filter=None):
                
        
        #export edges   
        if (exportType == 'edges'):        
            file = filepath + 'edges.txt'
        #export text for topic analysis
        elif (exportType == 'text_for_topics'):
            file = filepath + 'T_tweetTextsForTopics.txt'
        #export ht frequency list
        elif (exportType == 'ht_frequency_list'):
            file = filepath + 'T_HT_FrequencyList.txt'
        #export words frequency list - (TOP 5000)
        elif (exportType == 'word_frequency_list'):                            
            file = filepath + 'T_Words_FrequencyList.txt'            
        #export text for topic analysis
        elif (exportType == 'tweet_ids_timeseries'):                                                                              
            file = filepath + 'T_tweetIdswithDates.txt'                        
        #export tweetCountByUser
        elif (exportType == 'tweetCount'):
            file = filepath + 'tweetCount.txt'                                    
        #export tweetCountByUser
        elif (exportType == 'userCount'):            
            file = filepath + 'userCount.txt'
        #export tweetCountByUser
        elif (exportType == 'tweetCountByUser'):            
            file = filepath + 'tweetCountByUser.txt'                                
        #export tweetCountByLanguage
        elif (exportType == 'tweetCountByLanguage'):
            file = filepath + '\\tweetCountByLanguage.txt'                                        
        #export tweetCountByFile
        elif (exportType == 'tweetCountByFile'):
            file = filepath + 'tweetCountByFile.txt'
        #export tweetCountByMonth
        elif (exportType == 'tweetCountByMonth'):          
            file = filepath + 'tweetCountByMonth.txt'        
        #export hashtagCount
        elif (exportType == 'hashtagCount'): 
            file = filepath + 'hashtagCount.txt'
        #export topics by hashtag
        elif (exportType == 'topicByHashtag'): 
            file = filepath + 'topicByHashtag.txt'        
        elif (exportType == 'ht_edges'): 
            file = filepath + 'ht_edges.txt'
            
        #export tweetTextAndPeriod
        #if (exportType == 'tweetTextAndPeriod'):                                
        #export tweetDetails
        #if (exportType == 'tweetDetails'):                
        #export words
        #if (exportType == 'wordsOnEachTweet'):  
        #user details on Each Tweet
        #if (exportType == 'userDetailsOnEachTweet'):        
        
        if replace_existing_file==True or not os.path.exists(file):
            arr, file = self.queryData(exportType, 
                                       filepath, inc, 
                                       startDate_filter, 
                                       endDate_filter, 
                                       is_bot_Filter, 
                                       arr_edges, 
                                       arr_ht_edges, 
                                       top_no_filter, 
                                       ht_to_filter, 
                                       user_conn_filter=user_conn_filter)
    
            #export in array into txt file
            self.exportToFile(arr, file)
        
        

    #####################################
    # Method: set_bot_flag_based_on_arr
    # Description: Exports data into \t delimited file
    # Parameters: 
    #   -exportType: (Options: edges, 
    #                          text_for_topics, 
    #                          ht_frequency_list, 
    #                          word_frequency_list 
    #                          tweetCountByUser 
    #                          tweetCountByLanguage, 
    #                          tweetCountByFile, 
    #                          tweetCountByMonth, 
    #                          hashtagCount, 
    #                          tweetTextAndPeriod, 
    #                          wordsOnEachTweet 
    #                          userDetailsOnEachTweet)    
    #   -filepath: the file path where the files will be saved  
    #   -inc: To set how many lines per files we want to save. 
    #    This is for collection that have too many records to be saved. 
    #    Memory issues can happens if this number is too big
    #    Only works when exporting for types tweetTextAndPeriod, wordsOnEachTweet,
    #    userDetailsOnEachTweet, we can set how many lines per file    
    #   -startDate_filter & endDate_filter: Date period you want to filter the tweets by.
    #    Only available for options "edges", "text_for_topics", 
    #    and "ht_frequency_list". (Defaul=None)    
    #   -is_bot_Filter: Filter tweets and connections by being bots or not.
    #    Only available for options "edges", "text_for_topics",
    #    and "ht_frequency_list". (Defaul=None)    
    #   -arr_edges: Filter tweet connections by this array of edges. 
    #    Only available for options "text_for_topics", 
    #    and "ht_frequency_list". (Defaul=None)    
    #   -top_no_filter: Filter top frequent words based on the number of this parameter.
    #    Only available for option "word_frequency_list" (Defaul=None)
    def queryData(
            self, exportType, filepath, inc, 
            startDate_filter=None, 
            endDate_filter=None, 
            is_bot_Filter=None, 
            arr_edges=None, 
            arr_ht_edges=None,
            top_no_filter=None, 
            ht_to_filter=None, 
            include_hashsymb_FL='Y', 
            user_conn_filter=None):

        arr = []
        
        # set correct format for start and end dates
        if startDate_filter is not None and endDate_filter is not None:
            start_date = datetime.datetime.strptime(startDate_filter, '%m/%d/%Y %H:%M:%S')
            end_date = datetime.datetime.strptime(endDate_filter, '%m/%d/%Y %H:%M:%S')
            
        
        #build a variable with all filter based on parameters        
        query_filter, query_filter_for_edges = self.build_filter(startDate_filter, 
                                                                 endDate_filter, 
                                                                 is_bot_Filter, 
                                                                 ht_to_filter, 
                                                                 user_conn_filter, 
                                                                 exportType)

                
        #export edges
        if (exportType == 'edges'):
                
            pipeline =  [ {"$match": query_filter },
                          {"$group": {"_id": {"screen_name_a": "$screen_name_a", 
                                              "screen_name_b": "$screen_name_b"},
                                      "count": { "$sum": 1 }}} ]
                            
            #get data from database, loop through records and insert into array
            select_edges = self.c_tweetConnections.aggregate(pipeline, 
                                                             allowDiskUse=True, 
                                                             collation=Collation(locale="en_US", strength=2))
            for x in select_edges:                
                arr.append([ x["_id"]['screen_name_a'], x["_id"]['screen_name_b'],  x['count']])
                                
            #set file path
            file = filepath + 'edges.txt'
            
            
            
        #export hashtag edges
        if (exportType == 'ht_edges'):                        
                
            #in case we don't have an array of edges to filter by
            if arr_edges is None:
                pipeline =  [ {"$match": query_filter },
                              {"$group": {"_id": {"ht_a": "$ht_a", "ht_b": "$ht_b"},
                                          "count": { "$sum": 1 }}} 
                            ]              
                select_edges = self.c_tweetHTConnections.aggregate(pipeline, allowDiskUse=True)

            else:                
                
                #create temp collection for edges                
                self.create_tmp_edge_collections(arr_edges, arr_ht_edges, query_filter_for_edges)                                
                
                #create temp collection for ht
                self.c_tmpEdgesHTFreq.delete_many({})
                pipeline = [ {"$lookup":{
                                       "from": "tweetHTConnections",
                                       "localField": "tweet_id_str",
                                       "foreignField": "tweet_id_str",
                                       "as" : "tweetHTConnections"}},
                              {"$unwind": "$tweetHTConnections"},
                              {"$group": {"_id": {"ht_a": "$tweetHTConnections.ht_a", "ht_b": "$tweetHTConnections.ht_b"},
                                          "count": { "$sum": 1 }}}
                           ]
                select_edges = self.c_tmpEdgesTweetIds.aggregate(pipeline, allowDiskUse=True)
                            
            #get data from database, loop through records and insert into array            
            for x in select_edges:                                
                arr.append([x["_id"]['ht_a'], x["_id"]['ht_b'],  x['count']])
                                
            #set file path
            file = filepath + 'ht_edges.txt'



        #export text for topic analysis
        if (exportType == 'text_for_topics'):                                                                  
                
            #in case we don't have an array of edges to filter by
            if arr_edges is None and arr_ht_edges is None:
                         
                select_texts = self.c_focusedTweet.find(query_filter, { "text_combined_clean": 1} )                                

            #in case we have an array of edges to filter by
            else:
                
                self.create_tmp_edge_collections(arr_edges, arr_ht_edges, query_filter_for_edges)
                
                pipeline = [ {"$lookup":{
                                       "from": "focusedTweet",
                                       "localField": "tweet_id_str",
                                       "foreignField": "id_str",
                                       "as" : "focusedTweet"}},    
                              {"$unwind": "$focusedTweet" },                              
                              {"$project": { "text_combined_clean": "$focusedTweet.text_combined_clean" }}]
                
                select_texts = self.c_tmpEdgesTweetIds.aggregate(pipeline, allowDiskUse=True)
                                


            #get data from database, loop through records and insert into array
            for x in select_texts:
                arr.append([x['text_combined_clean']])                
            
            #set file path
            file = filepath + 'T_tweetTextsForTopics.txt'


                        
        #export ht frequency list
        if (exportType == 'ht_frequency_list'):                
                                    
            #in case we don't have an array of edges to filter by
            if arr_edges is None and arr_ht_edges is None:
                
                pipeline = [  {"$match": query_filter },
                              { "$unwind": '$hashtags' },                                                                    
                              {"$group": { "_id": { "ht": '$hashtags.ht' }, "count": { "$sum": 1 } } }]

                select_ht = self.c_focusedTweet.aggregate(pipeline, allowDiskUse=True, collation=Collation(locale="en_US", strength=2))


            #in case we have an array of edges to filter by
            else:
                
                
                #*************************************************************************************
                # Creating a temporary collection with all hashtags for each tweet for the given edges
                # This is possible without creating temp collections, 
                #   but it was done this way to improve performance. 
                # Running with a different Collation can take a LONG time - 
                #  (We need to run with Collation strength=2 to get canse insensitive counts )
                
                #create temp collection for edges                
                self.create_tmp_edge_collections(arr_edges, arr_ht_edges, query_filter_for_edges)                                
                
                #create temp collection for ht
                self.c_tmpEdgesHTFreq.delete_many({})
                pipeline = [ {"$lookup":{
                                       "from": "focusedTweet",
                                       "localField": "tweet_id_str",
                                       "foreignField": "id_str",
                                       "as" : "focusedTweet"}},
                              {"$unwind": "$focusedTweet" },
                              {"$unwind": '$focusedTweet.hashtags' },
                              {"$project": { "ht": '$focusedTweet.hashtags.ht', "tweet_id_str": '$tweet_id_str'  } }]
                file_data = []
                select_ht = self.c_tmpEdgesTweetIds.aggregate(pipeline, allowDiskUse=True)
                for x in select_ht:    
                    data = '{"tweet_id_str":"' + x['tweet_id_str'] + \
                            '", "ht":"' + x['ht'] + '"}'
                    doc = json.loads(data)
                    file_data.append(doc)
                if file_data != []:
                    self.c_tmpEdgesHTFreq.insert_many(file_data)
                #**************************************************************************************
                
                
                #getting counts for each hashtag
                pipeline = [  {"$group": { "_id": { "ht": '$ht' }, "count": { "$sum": 1 } } }]                                
                select_ht = self.c_tmpEdgesHTFreq.aggregate(pipeline, allowDiskUse=True, collation=Collation(locale="en_US", strength=2))
                
                

            hash_symbol = "#"
            if include_hashsymb_FL==False:
                hash_symbol=""

            #get data from database, loop through records and insert into array
            for x in select_ht:
                arr.append([hash_symbol + x['_id']['ht'], x['count']])

            #sort array in count descending order
            def sortSecond(val): 
                return val[1] 
            arr.sort(key=sortSecond,reverse=True) 

            if top_no_filter != None:
                arr = arr[:top_no_filter]
                
                
                                    
            #set file path
            file = filepath + 'T_HT_FrequencyList.txt'
            
            
        #export words frequency list - (TOP 5000)
        if (exportType == 'word_frequency_list'):                
                                                       
            # This variable will get set to True for options where we want to create 
            #  a separate tmp collection to save the words. 
            #  (This was done this way to allow some performance improvements)
            bln_GetWords_From_Text = False             
            
            #in case we don't have an array of edges to filter by
            if arr_edges is None and arr_ht_edges is None:
                                                                                                     
                #if we are filtering by period and by is_bot
                if startDate_filter is not None and endDate_filter is not None and is_bot_Filter is not None:
                    bln_GetWords_From_Text = True
                    select_texts = self.c_focusedTweet.find(query_filter, { "text_combined_clean": 1, "id_str": 1} )
                                        

                #if we are filtering by period only
                elif startDate_filter is not None and endDate_filter is not None:
                    pipeline = [{"$match": {"$and": 
                                            [{"tweet_created_at" : {"$gte": start_date, "$lt": end_date}},
                                             {"stop_word_fl" : {"$eq": "F"} } ]}},
                                {"$group": {"_id": {"word": '$word'}, "count": {"$sum": 1}}}]
                    select_word = self.c_tweetWords.aggregate(pipeline, allowDiskUse=True)
                    

                #if we are filtering by is_bot
                elif is_bot_Filter is not None:  #wrong                                      
                    bln_GetWords_From_Text = True
                    select_texts = self.c_focusedTweet.find(query_filter, 
                                                            { "text_combined_clean": 1, "id_str": 1 })
                

                #if there is no filter
                else:                        
                    pipeline = [{"$match": {"stop_word_fl" :  { "$eq": "F" }}}, 
                                {"$group": {"_id": {"word": '$word'}, "count": {"$sum": 1}}}]
                    
                    select_word = self.c_tweetWords.aggregate(pipeline, allowDiskUse=True)
                                                                                                    

            #in case we have an array of edges to filter by
            else:                
                
                #**************************************************************************************
                # Creating a temporary collection with all hashtags for each tweet for the given edges
                # This is possible without creating temp collections, but it was done this way to improve performance. 
                # Running with a different Collation can take a LONG time - 
                # (We need to run with Collation strength=2 to get canse insensitive counts )
                                
                #create temp collection for edges                
                self.create_tmp_edge_collections(arr_edges, arr_ht_edges, query_filter_for_edges)
                
                pipeline = [ {"$lookup":{
                                       "from": "focusedTweet",
                                       "localField": "tweet_id_str",
                                       "foreignField": "id_str",
                                       "as" : "focusedTweet"}},
                              {"$unwind": "$focusedTweet" },
                              {"$project": {"id_str": "$tweet_id_str", 
                                            "text_combined_clean": "$focusedTweet.text_combined_clean" }}]
                select_texts = self.c_tmpEdgesTweetIds.aggregate(pipeline, allowDiskUse=True)
                
                bln_GetWords_From_Text = True
                


            # If we want to create a tmp collection to save the words after spliting the words from text. 
            # (This was done this way to allow some performance improvements)
            # this option is being used when we are filtering by is_bot or by edges
            if bln_GetWords_From_Text == True:
                self.c_tmpEdgesWordFreq.delete_many({})                
                file_data = []                
                for x in select_texts:                         
                    for word in pos_tag(tokenizer.tokenize(x['text_combined_clean'])):
                        if word[0] not in stopWords:
                            data = '{"tweet_id_str":"' + x['id_str'] + \
                                    '", "word":"' + word[0] + '"}'
                            doc = json.loads(data)
                            file_data.append(doc)
                                            
                if file_data != []:
                    self.c_tmpEdgesWordFreq.insert_many(file_data)
                #**************************************************************************************                

                #getting counts for each word
                pipeline = [  {"$group": { "_id": { "word": '$word' }, "count": { "$sum": 1 } } }]                
                select_word = self.c_tmpEdgesWordFreq.aggregate(pipeline, allowDiskUse=True)
                
                

            #get data from database, loop through records and insert into array            
            for x in select_word:
                arr.append([x['_id']['word'], x['count']])

            #sort array in count descending order
            def sortSecond(val): 
                return val[1] 
            arr.sort(key=sortSecond,reverse=True) 
            
            arr = arr[:top_no_filter]
            
   
            #set file path
            file = filepath + 'T_Words_FrequencyList.txt'            
            
          
        
        #export text for topic analysis
        if (exportType == 'tweet_ids_timeseries'):                                                                  
                
            #in case we don't have an array of edges to filter by
            if arr_edges is None and arr_ht_edges is None:
                         
                select_ids = self.c_focusedTweet.find(query_filter, { "id_str": 1, "tweet_created_at": 1} )                                

            #in case we have an array of edges to filter by
            else:
                
                self.create_tmp_edge_collections(arr_edges, arr_ht_edges, query_filter_for_edges)                                
                
                if ht_to_filter is None:                
                    pipeline = [ {"$lookup":{
                                           "from": "focusedTweet",
                                           "localField": "tweet_id_str",
                                           "foreignField": "id_str",
                                           "as" : "focusedTweet"}},    
                                  {"$unwind": "$focusedTweet" },   
                                  {"$project": {"id_str": "$focusedTweet.id_str", 
                                                "tweet_created_at": "$focusedTweet.tweet_created_at" }}]
                else:
                    pipeline = [ {"$lookup":{
                                           "from": "focusedTweet",
                                           "localField": "tweet_id_str",
                                           "foreignField": "id_str",
                                           "as" : "focusedTweet"}},    
                                  {"$unwind": "$focusedTweet" },   
                                  {"$match": {"focusedTweet.hashtags.ht_lower": ht_to_filter.lower()} },
                                  {"$project": {"id_str": "$focusedTweet.id_str", 
                                                "tweet_created_at": "$focusedTweet.tweet_created_at" }}]
                    
                select_ids = self.c_tmpEdgesTweetIds.aggregate(pipeline, allowDiskUse=True)


            #get data from database, loop through records and insert into array
            for x in select_ids:
                arr.append([x['tweet_created_at'], x['id_str']]) 
                
            
            #set file path
            file = filepath + 'T_tweetIdswithDates.txt'
            
            
        #export tweetCountByUser
        if (exportType == 'tweetCount'):
            
            total_tweets = 0    
            total_retweets = 0
            total_replies = 0

            select_cTweet = self.c_focusedTweet.aggregate([{"$match" : {"retweeted_text" : {"$ne": ""} }}, 
                                                           {"$group": {"_id": {"seq_agg": "$seq_agg"}, 
                                                                       "count": { "$sum": 1 } } } ])
            for tweetCount in select_cTweet:   
                total_retweets = tweetCount["count"]     


            select_cTweet = self.c_focusedTweet.aggregate([{"$group": {"_id": {"seq_agg": "$seq_agg"}, 
                                                                       "count": { "$sum": 1 } } } ])
            for tweetCount in select_cTweet:            
                total_tweets = tweetCount["count"]


            select_cTweet = self.c_focusedTweet.aggregate([{"$match" : {"in_reply_to_screen_name" : {"$ne": "None"} }}, 
                                                           {"$group": {"_id": {"seq_agg": "$seq_agg"}, 
                                                                       "count": { "$sum": 1 } } } ])
            for tweetCount in select_cTweet:            
                total_replies = tweetCount["count"]

            arr.append([ 'Total Original Tweets', str(total_tweets-total_retweets-total_replies)])
            arr.append([ 'Total Replies', str(total_replies)])
            arr.append([ 'Total Retweets', str(total_retweets)])
            arr.append([ 'Total Tweets', str(total_tweets)])

            #set file path
            file = filepath + 'tweetCount.txt'
            
            
            
        #export tweetCountByUser
        if (exportType == 'userCount'):
                                   
            tweet_user_count = 0
            reply_user_count = 0
            quote_user_count = 0
            retweet_user_count = 0

            select_cTweet = self.c_users.aggregate( [{"$group": {"_id": {"user_type": "$user_type"}, "count": { "$sum": 1 } } } ])
            for tweetCount in select_cTweet:                   
                if tweetCount["_id"]["user_type"] == 'tweet':
                    arr.append(['1', tweetCount["_id"]["user_type"], 'Users with at least one document in this db', str(tweetCount["count"]) ])                                
                elif tweetCount["_id"]["user_type"] == 'retweet':
                    arr.append([ '2', tweetCount["_id"]["user_type"], 'Users that were retweeted, but are not part of previous group', str(tweetCount["count"]) ])
                elif tweetCount["_id"]["user_type"] == 'quote':
                    arr.append([ '3', tweetCount["_id"]["user_type"], 'Users that were quoted, but are not part of previous groups', str(tweetCount["count"]) ])                
                elif tweetCount["_id"]["user_type"] == 'reply':
                    arr.append([ '4', tweetCount["_id"]["user_type"], 'Users that were replied to, but are not part of previous groups', str(tweetCount["count"]) ])
                elif tweetCount["_id"]["user_type"] == 'mention':
                    arr.append([ '5', tweetCount["_id"]["user_type"], 'Users that were mentioned, but are not part of previous groups', str(tweetCount["count"]) ])
                else:
                    arr.append([ '6', tweetCount["_id"]["user_type"], '', str(tweetCount["count"]) ])    
            
            #set file path
            file = filepath + 'userCount.txt'
            
        

        #export tweetCountByUser
        if (exportType == 'tweetCountByUser'):

            #set header of txt file
            arr.append([ 'user_id', 'user_screen_name', 'count'])

            #get data from database and loop through records and insert into array
            select_tweetCountByUser = self.c_tweetCountByUserAgg.find()        
            for x in select_tweetCountByUser:
                arr.append([ x['user_id'], x['user_screen_name'],  x['count']])        

            #set file path
            file = filepath + 'tweetCountByUser.txt'
            
            

        
        #export tweetCountByLanguage
        if (exportType == 'tweetCountByLanguage'):

            #set header of txt file
            arr.append([ 'lang', 'count'])

            #get data from database and loop through records and insert into array
            select_tweetCountByLang = self.c_tweetCountByLanguageAgg.find()        
            for x in select_tweetCountByLang:
                arr.append([ x['lang'],  x['count']])

            #set file path
            file = filepath + '\\tweetCountByLanguage.txt'
            
                    

        
        #export tweetCountByFile
        if (exportType == 'tweetCountByFile'):

            #set header of txt file
            arr.append([ 'file_path', 'count'])

            #get data from database and loop through records and insert into array
            select_tweetCountByFile = self.c_tweetCountByFileAgg.find()        
            for x in select_tweetCountByFile:
                arr.append([ x['file_path'],  x['count']])        

            #set file path
            file = filepath + 'tweetCountByFile.txt'



        #export tweetCountByMonth
        if (exportType == 'tweetCountByMonth'):

            #set header of txt file
            arr.append([ 'year', 'month_no', 'count'])   

            #get data from database and loop through records and insert into array
            select_tCountByPeriod = self.c_tweetCountByPeriodAgg.find()        
            for x in select_tCountByPeriod:
                arr.append([ x['year'], x['month_no'], x['count']])         

            #set file path
            file = filepath + 'tweetCountByMonth.txt'        



        #export hashtagCount
        if (exportType == 'hashtagCount'): 

            #set header of txt file
            arr.append([ 'hashtag', 'count'])            

            #get data from database and loop through records and insert into array
            select_hashtagCountByDay = self.c_hashTagCountAgg.find()        
            for x in select_hashtagCountByDay:
                arr.append([ x['hashtag'],  x['count']])

            #set file path
            file = filepath + 'hashtagCount.txt'


            
        #export topics by hashtag
        if (exportType == 'topicByHashtag'): 

            #set header of txt file
            arr.append([ 'ht', 'ht_count', 'lib', 'model', 'no_words', 'topic_no', 'topic'])       

            #get data from database and loop through records and insert into array
            select_cHTTopics = self.c_htTopics.find()        
            for x in select_cHTTopics:
                arr.append([ x['ht'], x['ht_count'],  x['lib'],  x['model'],  
                             x['no_tweets'],  x['topic_no'],  x['topic']])

            #set file path
            file = filepath + 'topicByHashtag.txt'


        #export tweetTextAndPeriod
        if (exportType == 'tweetTextAndPeriod'):

            i = 0                

            #get data from database and loop through records and insert into array
            select_focusedTweet = self.c_focusedTweet.find() 
            for x in select_focusedTweet:

                if (i % inc == 0 and i != 0):                                                
                    self.exportToFile(arr, file) #export in array into txt file

                if (i==0 or i % inc==0):
                    arr = []
                    file = filepath + 'tweetTextAndPeriod_' + str(i) + '.txt' #set file path
                    arr.append([ 'text', 'text_lower', 'year', 'month_no', 'day', 'user_id'])

                arr.append([ x['text'], x['text_lower'], x['year'],  
                             x['month_no'],  x['day'],  x['user_id']])

                i = i +1
                
                
        #export tweetDetails
        if (exportType == 'tweetDetails'):

            i = 0                

            #get data from database and loop through records and insert into array
            select_focusedTweet = self.c_focusedTweet.find() 
            for x in select_focusedTweet:

                if (i % inc == 0 and i != 0):                                                
                    self.exportToFile(arr, file) #export in array into txt file


                if (i==0 or i % inc==0):                
                    arr = []
                    file = filepath + 'tweetTextAndPeriod_' + str(i) + '.txt' #set file path
                    arr.append([ 'text', 'text_lower', 'year', 'month_no', 'day', 'user_id'])

                arr.append([ x['text'], x['text_lower'], x['year'],
                             x['month_no'],  x['day'],  x['user_id']])

                i = i +1   
                


        #export words
        if (exportType == 'wordsOnEachTweet'):  

            i = 0                

            #get data from database
            select_tweetWords = self.c_tweetWords.find()
            for x in select_tweetWords:

                if (i % inc == 0 and i != 0):                                                
                    self.exportToFile(arr, file) #export in array into txt file                

                if (i==0 or i % inc==0):                
                    arr = []
                    file = filepath + 'wordsOnEachTweet_' + str(i)  + '.txt' #set file path
                    arr.append(['word_orig', 'word', 'word_lower', 'word_tag', 'word_lemm', 
                                'id_str', 'text', 'seq_no_tweet', 'seq_no'])


                arr.append([ x['word_orig'],  x['word'],  x['word_lower'],  x['word_tag'],  
                             x['word_lemm'],  x['id_str'],  x['text'],  x['seq_no_tweet'],  x['seq_no']])

                i = i +1



        #user details on Each Tweet
        if (exportType == 'userDetailsOnEachTweet'):

            i = 0                

            #get data from database
            select_Tweet = self.c_tweet.find()
            for tweet in select_Tweet:

                if (i % inc == 0 and i != 0):                                                
                    self.exportToFile(arr, file) #export in array into txt file                

                if (i==0 or i % inc==0):
                    arr = []
                    file = filepath + 'userDetailsOnEachTweet_' + str(i)  + '.txt' #set file path
                    arr.append(['id_str', 'user_id', 'user_location', 'user_name', 
                                'user_screen_name', 'user_description', 'user_verified', 
                                'user_followers_count', 'user_friends_count', 
                                'user_statuses_count', 'user_created_at', 'user_time_zone', 
                                'user_lang', 'user_geo_enabled'])


                #get relevant information from tweet
                id_str = tweet['id_str'] 
                user_id = tweet['user']['id_str']
                user_location = tweet['user']['location']
                user_name = tweet['user']['name']
                user_screen_name = tweet['user']['screen_name']
                user_description = tweet['user']['description']                                
                user_verified = tweet['user']['verified']
                user_followers_count = tweet['user']['followers_count']
                user_friends_count = tweet['user']['friends_count']
                user_statuses_count = tweet['user']['statuses_count']
                user_created_at = tweet['user']['created_at']
                user_time_zone = tweet['user']['time_zone']
                user_lang = tweet['user']['lang']        
                user_geo_enabled = tweet['user']['geo_enabled']        

                if user_description is not None:            
                    user_description = user_description.replace("|", "").strip().replace("\n", "").replace("\r", "")

                if user_location is not None:            
                    user_location = user_location.replace("|", "").strip().replace("\n", "").replace("\r", "")

                if user_name is not None:        
                    user_name = user_name.replace("|", "").strip().replace("\n", "").replace("\r", "")

                if user_screen_name is not None: 
                    user_screen_name = user_screen_name.replace("|", "").strip().replace("\n", "").replace("\r", "")


                arr.append([id_str, user_id, user_location, user_name, user_screen_name, 
                            user_description, user_verified, user_followers_count, 
                            user_friends_count, user_statuses_count, 
                            user_created_at, user_time_zone, user_lang, user_geo_enabled])  

                i = i +1    

        #export in array into txt file
        #self.exportToFile(arr, file)
        return arr, file
    
    
    
    #####################################
    # Method: exportToFile
    # Description: Method used to export an array to a t\ delimited file
    # Parameters: arrData = the array with the data you want to export
    # file = the path and name of the file you want to export
    def exportToFile(self, arrData, file): 

        myFile = open(file, 'w', encoding="utf-8")
        with myFile:
            writer = csv.writer(myFile, delimiter='\t', lineterminator='\n')
            writer.writerows(arrData)
                                    
        
    
    
    ######### Topic Analysis ###############################################
    # *This was just an initital analysis. refer to pyTwitterTopics for more.
        
    #####################################
    # Method: get_docs
    # Description: create one array with all tweets of one hashtag for topic analysis
    def get_docs(self, ht, max_doc_ctn):    
        
        ctn=0
        doc = ""
        topic_doc_complete.append(doc)
        
        select_cTweet = self.c_focusedTweet.find({"hashtags.ht_lower" : ht }) 
        #loop through tweets
        for tweet in select_cTweet:     
            if ctn < max_doc_ctn:
                doc = tweet['text_lower']
                topic_doc_complete.append(doc)
            ctn=ctn+1    
            
    
    #####################################
    # Method: clean_1
    # Description: clean documents for topic analysis
    def clean_1(self, doc): 
        stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
        punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
        normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
        return normalized
    
    
    #topic analysis using gensim model 
    def gensim_model(self, num_topics_lda, num_topics_lsi, ht, tc):

        import gensim
        from gensim import corpora

        doc_clean = [self.clean_1(doc).split() for doc in topic_doc_complete]   

        # Creating the term dictionary of our courpus, where every unique term is assigned an index. dictionary = corpora.Dictionary(doc_clean)
        dictionary = corpora.Dictionary(doc_clean)            

        # Converting list of documents (corpus) into Document Term Matrix using dictionary prepared above.
        doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]

        # Creating the object for LDA model using gensim library
        Lda = gensim.models.ldamodel.LdaModel    

        # Build the LDA model
        lda_model = gensim.models.LdaModel(corpus=doc_term_matrix, num_topics=num_topics_lda, id2word=dictionary)    

        # Build the LSI model
        lsi_model = gensim.models.LsiModel(corpus=doc_term_matrix, num_topics=num_topics_lsi, id2word=dictionary)    


        file_data = []     
        for idx in range(num_topics_lda):                
            topic = idx+1
            strtopic = str(topic)

            data = '{"ht":"' + ht + \
                    '", "ht_count":"' + str(tc) + \
                    '", "lib":"' + "gensim" + \
                    '", "model":"' + "lda" + \
                    '", "no_tweets":"' + str(tc) + \
                    '", "topic_no":"' + strtopic + \
                    '", "topic":"' + str(lda_model.print_topic(idx, num_topics_lda)).replace('"', "-") + '"}'

            x = json.loads(data)
            file_data.append(x)



        for idx in range(num_topics_lsi):        
            data = '{"ht":"' + ht + \
                '", "ht_count":"' + str(tc) + \
                '", "lib":"' + "gensim" + \
                '", "model":"' + "lsi" + \
                '", "no_tweets":"' + str(tc) + \
                '", "topic_no":"' + str(idx+1) +\
                '", "topic":"' + str(lsi_model.print_topic(idx, num_topics_lsi)).replace('"', "-") + '"}'

            x = json.loads(data)
            file_data.append(x)


        self.c_htTopics.insert_many(file_data)        
        

            
    #topic analysis using sklearn model 
    def skl_model(self, num_topics_lda, num_topics_lsi, num_topics_nmf, ht, tc):    

        vectorizer = CountVectorizer(min_df=0.009, max_df=0.97, stop_words='english', lowercase=True, token_pattern='[a-zA-Z\-][a-zA-Z\-]{2,}')

        data_vectorized = vectorizer.fit_transform(topic_doc_complete)

        # Build a Latent Dirichlet Allocation Model
        lda_model = LatentDirichletAllocation(n_components=num_topics_lda, max_iter=5,learning_method='online',learning_offset=50.,random_state=0)
        lda_Z = lda_model.fit_transform(data_vectorized)

        # Build a Non-Negative Matrix Factorization Model
        nmf_model = NMF(num_topics_nmf)
        nmf_Z = nmf_model.fit_transform(data_vectorized)

        # Build a Latent Semantic Indexing Model
        lsi_model = TruncatedSVD(1)
        lsi_Z = lsi_model.fit_transform(data_vectorized)


        file_data = []

        for idx, topic in enumerate(lda_model.components_):  
            topic = str([( str(topic[i]) + "*" + vectorizer.get_feature_names()[i] + " + " )
                            for i in topic.argsort()[:-num_topics_lda - 1:-1]]).replace("[", "").replace("]", "").replace("'", "").replace(",", "")

            data = '{"ht":"' + ht + \
                '", "ht_count":"' + tc + \
                '", "lib":"' + "sklearn" + \
                '", "model":"' + "lda" + \
                '", "no_tweets":"' + str(tc) + \
                '", "topic_no":"' + str(idx+1) +\
                '", "topic":"' + topic + '"}'

            x = json.loads(data)
            file_data.append(x)



        for idx, topic in enumerate(lsi_model.components_):  
            topic = str([( str(topic[i]) + "*" + vectorizer.get_feature_names()[i] + " + " )
                            for i in topic.argsort()[:-num_topics_lsi - 1:-1]]).replace("[", "").replace("]", "").replace("'", "").replace(",", "")

            data = '{"ht":"' + ht + \
                '", "ht_count":"' + tc + \
                '", "lib":"' + "sklearn" + \
                '", "model":"' + "lsi" + \
                '", "no_tweets":"' + str(tc) + \
                '", "topic_no":"' + str(idx+1) +\
                '", "topic":"' + topic + '"}'

            x = json.loads(data)
            file_data.append(x)




        for idx, topic in enumerate(nmf_model.components_):  
            topic = str([( str(topic[i]) + "*" + vectorizer.get_feature_names()[i] + " + ")
                            for i in topic.argsort()[:-num_topics_nmf - 1:-1]]).replace("[", "").replace("]", "").replace("'", "").replace(",", "")

            data = '{"ht":"' + ht + \
                '", "ht_count":"' + tc + \
                '", "lib":"' + "sklearn" + \
                '", "model":"' + "nmf" + \
                '", "no_tweets":"' + str(tc) + \
                '", "topic_no":"' + str(idx+1) +\
                '", "topic":"' + topic + '"}'

            x = json.loads(data)
            file_data.append(x)        


        self.c_htTopics.insert_many(file_data)            
        
        

    #find topics for each hashtag  
    def findTopics(self, num_topics_lda, num_topics_lsi, num_topics_nmf, max_no_tweets_perHT, model):

        starttime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print ("loading process started...." + starttime)
        
        #find all hashtag and their count
        select_cHashtagCount = self.c_hashTagCountAgg.find().sort("count", -1)
                

        try:
            #loop through hashtags
            for tweet in  select_cHashtagCount: 

                ht = tweet['hashtag']
                count = tweet['count']

                if ht != "metoo" and count > 500:                                

                    #get all tweets for that hashtag
                    topic_doc_complete.clear()
                    self.get_docs(ht, max_no_tweets_perHT) 

                    #run topic models
                    try:
                        if model == "gensim":
                            self.gensim_model(num_topics_lda, num_topics_lsi, ht, str(count))        
                        elif model == "sklearn":
                            self.skl_model(num_topics_lda, num_topics_lsi, num_topics_nmf, ht, str(count))                 
                    except Exception as e:                                      
                        print("Error finding topics for hashtag " + ht + ", using model " + model +". Err msg: " + str(e)) 
                        continue  
        
        except Exception as e:
            print("Error finding topics. Err msg: " + str(e))             
                    

        endtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print ("loading process completed. " + endtime)