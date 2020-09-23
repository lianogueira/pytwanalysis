Data Dictionary - (MongoDB Collections)
=======================================

A collection was created to store the raw data from the Twitter json files and multiple collections were created to store cleaned and transformed data to facilitate the analysis process. Some of the collections share similar fields, which was designed that way to make queries easier and faster to run. Having collections with a focused purpose is also helpful in case other visualization tools are intended to be used in MongoDB. Having all data with all fields in one collection is helpful for cases where there is a need to deal with the unstructured nature of Twitter data, but having separate collections helps with the organization of the data in a more simple way to understand and aggregate the content. That is why a combination of the two approaches was used in this work.


Main
---------------

The following are the main collections in charge or saving and processing the data:

+ **tweet:** This collection will contain the full raw twitter data. The fields available will depend on the content of the json files. This collection might contain different structure depending on which Twitter api was used to retrieve the data. A few additional fields were created to this collection to keep track of what file the tweet came from, the load timestamp, and to facilitate the recovery process.

+ **focusedTweet:** This collection will contain only the most important information about the tweet. The definition of "interesting" can be different depending on what is being studied, so settings can be updated to drive what fields are interesting.  Some core fields will always be available no matter the settings. It is useful to have a separate collection for two main reasons, the first one is that it decreases the amount of data stored in one collection which increases the queries performance. The second reason is that it makes it possible to have core columns with a standard name without needing to add logic to the program when accessing the data. For example, depending on the Twitter input data, the field that contains the tweet message can have different names, so standardizing that name in the collection makes future processing easier.
	
	+ **Core Fields:**
	+  *id_str:* The tweet unique id. This will be a key field that will be used to connect other collections together.
	+  *text:* The tweet text.
	+  *text_lower:* The tweet text with all lower case.
	+  *quote_text:* The text of the quoted tweet, in case there is a quote associated to the tweet.
	+  *retweeted_text:* The original tweet text in case of retweets.
	+  *text_combined:* Tweet text combining the tweet text, original text, and quoted text. 
	+  *text_combined_clean:* Same as text_combined, but after going through a series of cleaning steps that will explain in subsection [...]. 
	+  *year:* The year the tweet was created.
	+  *month_name:* The name of the month that the tweet was created.
	+  *month_no:* The month the tweet was created.
	+  *day:* The day the tweet was created.
	+  *user_id:* The user id of the user that created the tweet.
	+  *hashtags:* A list of all hashtags that were included in the tweet, and quoted tweet.
	+  *created_at:* The timestamp the tweet was created.
	+  *lang:* The language used in the tweet text.
	+  *in_reply_to_status_id_str:* In case of replies, this field will show the id of the tweet that the person was replying to.
	+  *in_reply_to_screen_name:* In case of replies, this field will show the screen name of the user of the tweet that the person was replying to.
	+  *user_name:* The user name of the person that created the tweet.
	+  *user_screen_name:* The screen name of the person that created the tweet.        
	+ 
	+ **Added Fields**:
	+  *seq_no:* Field created to uniquely identify each of the tweets. This field is used in the recovery process to identify the tweets that have already been processed. 	
	+  *is_bot:* Identifies if the user that created the tweet is a bot or not. This field is not automatically calculated. A text file with the list of ids that are bots can be used to update this field.	
	+  *is_bot_connection:* Identifies if the tweet is part of an edge between users that are bots. For example, this will be set to 1 if the tweet was a reply or a retweet to a user that is a bot. This field is not automatically calculated. A text file with the list of ids that are bots can be used to update this field.


+  **tweetWords:** This collection will save each word separately for every tweet and some additional information about the tweet. It will also contain interesting tags about that word. (e.g English or not, verb or not, etc.)
	
	+ **Fields:**
	+  *word:* The original word
	+  *word_tag:* It identifies the type of word. ADJ, for adjectives, VERB, for verbs, NOUN, for nouns , and ADV for adverbs.
	+  *word_lemm:* The word after lemmatization.
	+  *word_syl:* The word broken down into syllables.
	+  *stop_word_fl:* It identifies if the word is a stop word or not.
	+  *en_word_fl:* It identifies if the word is in English or not.
	+  *tweet_id_str:* The tweet id where that word came from.
	+  *text:* The tweet text where that word came from.
	+  *user_id:* The user id of the tweet where that word came from.
	+  *tweet_created_at:* The timestamp of the tweet where that word came from.
	+  *tweet_seq_no:* The seq_no of the tweet where that word came from.
	+  *seq_no:* The word seq_no.
	+  *is_bot:* Same as in the focusedTweet collection.
	+  *is_bot_connection:* Same as in the focusedTweet collection.


+  **tweetConnections:** This collection will contain the edges that connect two tweets together, either by retweets, quotes, replies, or mentions. It will have information about the tweet where the connection happened, and about the two users that connected. This collection will later be used to build the edges for the graph analysis.
	
	+ **Fields:**
	+  *tweet_id_str:* The id of the tweet that has this connection.
	+  *type_of_connection:* The type of connection. It could be retweet, quote, reply, or mention.
	+  *user_id_str_a:* The user id of the user that initiated the connection. For example, the user that replied to another user.
	+  *screen_name_a:* The screen name of the user that initiated the connection. For example, the user that replied to another user.
	+  *user_id_str_b:* The user id of the user that received the connection. For example, another user retweets their tweet.
	+  *screen_name_b:* The user screen name of the user that received the connection. For example, another user retweets their tweet.
	+  *desc:* Describes the connection for easy understanding. Example of a possible value would be "user a mentioned user b".
	+  *retweeted_status_id:* The id of the original tweet in case of retweets.
	+  *quoted_status_id:* The id of the original tweet in case of quotes.
	+  *in_reply_to_status_id:* The id of the original tweet in case of replies.
	+  *edge_screen_name_directed_key:* A key created to help with directed graphs queries. It basically concatenates the user_a and user_b screen names.
	+  *edge_screen_name_undirected_key:* A key created to help with undirected graphs queries. It concatenates the user_a and user_b screen names in alphabetical order.
	+  *tweet_created_at:* The timestamp of the tweet that created this connection.
	+  *tweet_seq_no:* The seq_no of the tweet that created this connection.
	+  *is_bot:* Identifies if this connection is for a bot or not.  For example, this will be set to 1 if either user a or b is a bot. This field is not automatically calculated. A text file with the list of ids that are bots can be used to update this field.	
	

+  **tweetHTConnections:** This collection will contain the edges that connect two hashtags together. If two hashtags were used in the same tweet, a record will be created in this collection. It will have information about the tweet where the connection happened, and about the two hashtags. This collection will later be used to build the edges for the graph analysis.
	
	+ **Fields:**
	+  *tweet_id_str:* The id of the tweet that has this connection.
	+  *ht_a:* The first hashtag 
	+  *ht_b:* The second first hashtag 
	+  *ht_key:* A key created to help with the graphs queries. It concatenates the ht_a and ht_b. 
	+  *tweet_created_at:* The timestamp of the tweet that created this connection.
	+  *tweet_seq_no:* The seq_no of the tweet that has this connection.
	+  *is_bot:* Identifies if this connection is for a tweet created by a bot or not.

	
+  **users:** This collection will contain interesting information about the tweet user. Some core fields will always exist, but similar to the *focusedTweet collection, settings will be available in the pipeline to drive what fields are considered interesting. The same user can appear multiple times in a dataset with different values, for example, the same user can exist with two separate descriptions. This collection will not create multiple records for the same user and it will have the first values found for each user, other records for the same user will be ignored.
	
	+ **Fields:**
	+  *screen_name:* The screen name of the user
	+  *user_id:* The unique id for that user that was generated in Twitter.
	+  *name:* The name of the user
	+  *user_created_at:* The date and time the user was created in Twitter.
	+  *location:* The description the user used to identify their location. 
	+  *location_clean:* Same as *location, but cleaning the special characters.
	+  *description:* The description the users decided to give themselves. 
	+  *description_clean:* Same as *description, but cleaning the special characters.
	+  *user_type:* The method used to extract the information about this user. Twitter's documents have user information in the main document, but also under the information about the original tweet in case of retweets and quotes. This field will identify where the user was extracted from. The values available will be *tweet, *retweet, *quote, *reply, and *mention.
	+  *is_bot:* Identifies if the user is a bot or not. This field is not automatically calculated. A text file with the list of ids that are bots can be used to update this field.


Admin
---------------

The following are the administrative collections created to control the recovery process:

+ **adm_loadStatus**: This collection will save the status of each collection's load and how many tweets have already been inserted in each of them. In case of a failure, it will be used to know which records have already been inserted and which ones haven't. This was created as part of the recovery process.

+ **adm_loadedFiles:** This collection will save the directory and file names that have already been loaded. The load timestamp and the path will be the columns available. This is to make sure the same file doesn't get loaded multiple times. This was created as part of the recovery process. 



The following is the collection used to keep all the searches done to the Twitter APIs:

+ **searches:** This collection will save all the searches done to the Twitter APIs. The fields in this collection will not always be the same. The results from the API return different information depending on the API used. Some core field will always exist to identify the time of the search and which API was used. 
	
	+ **Core Fields:**	
	+ *search_time:* the time the search was execute
	+ *api:* the api was used for the search. The possible values are: *30day*, *fullarchive*, and *7day*.
	


Aggregated
---------------

The following are the optional aggregate collection to keep summary data for easy EDA:
   
+ **agg_tweetCountByFile:** This collection will contain the count of all tweets in the dataset by files loaded.

+ **agg_tweetCountByLanguage:** This collection will contain the count of all tweets in the dataset by language.

+ **agg_tweetCountByMonth:** This collection will contain the count of all tweets in the dataset by month and year.



Tmp Collections
---------------
The following are the temporary collections that get dropped and re-created to facilitate analysis and improve aggregate queries performance. It would be possible to create queries without these temporary tables and get the same results, but when querying high volume of data it becomes nearly impossible to return aggregate queries using lookups to multiple tables in a reasonable amount of time.

+ **tmpEdges:** Temporarily saves the edges of a graph so it can be used as lookup values in different queries.

+ **tmpEdgesTweetIds:** Temporarily saves the tweets ids that refer to the edges saved on tmpEdges. This collection will be used as lookup values in different queries.

+ **tmpEdgesHTFreq:** Saves the hashtags used in tweets for certain edges (ids saved on tmpEdgesTweetIds). This is used in aggregate queries to count the frequency of hashtags for specific edges.

+ **tmpEdgesWordFreq:** Saves the words used in tweets for certain edges (ids saved on tmpEdgesTweetIds). This is used in aggregate queries to count the frequency of words for specific edges. 



