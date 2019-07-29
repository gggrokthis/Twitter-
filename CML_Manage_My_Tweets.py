# -*- coding: utf-8 -*- ##
#This script will execute following Twitter Account management (bulk) functions for you:
#	1. Delete any of your tweets 
#	2. Unfavorite any of your previously favorited tweets
#	3. Lookup your account's follower list
#       4. Lookup your account's friend list
#	5. Lookup users by their userid and return any available account information for that userid 
# (3-5  above can successfully execute for Twitter accounts that allow view permissions to your
#       account/Twitterlogin id - i.e. for any public account unblocked by yours etc. )
#Setup: 
# You will need to get the following 
# 1.  consumer key 
#     consumer secret token  
#     access token
#     access token secret 
#     A. To do so, register a twitter application at https://apps.twitter.com
#     B. Ensure the application has read AND write access to be able to delete
#     C. To use this script register the name of this script as the name of app 
#        (without the .py part)
#     D. It is recommended that you delete the app (and remove its access to 
#        your profile) when not in use for the sake of security and
#        recreate and regenerate the keys and secrets when needed and edit
#        the program file as needed (cut and paste will cause minimal errors)
#  
#
# 2. This script requires an input file. A file with comma delimitted fields is expected.  
#    This works best if the file is .csv
#    For tweet deletes a .csv file with at least 1st, 4th and 6th fields populated per row
#    using the same format and column order as that of the archive file
#    generated by Twitter is required by this program. 
#    For the unfavorite selected tweets option, a .csv file list of all relevant
#    tweet IDs is required by this program.
#    Generally the easiest way to generate above mentioned input files is to use Twitter
#    generated archive files (likes listed in json file) grep for all
#    needed Ids and massage them using sed/awk etc. to generate a 2 field file
#    separated by , and each field embedded in " for deletes and 1 field file for 
#    unfavorites
#    For the Followers, Friends and User lookup options, a .csv file list of all relevant
#    twitter userIDs is required by this program.
#
#     A. Curently the logfile name is hardcoded to "statfile" 
#     B. The logile is created in the current working directory
#
# 3. You may want to look at some simple Unix awk and grep scripts I wrote 
#    to post-process the output (stdout) file or logfile to do sanity checks that the 
#    desired results occurred e.g. Count status ids in both, check for failed messages, 
#    use some/all failed status ids to manually look up tweet and verify status
#    etc. File named “awkex” is checked in.
#
#
# Future: I wrote this quickly to meet my need. If I was trying to do this
#         properly the following updates would make sense:
#     1. Use the keys and secrets in a more secure fashion (store in DB
#        encrypt or pass as command line parameters etc.)
#     2. Allow the logfile name and output file as command line arguments
#     3. Enforce no size limit on the input file and manage rate limits inside the program
#        based on applicable current twitter rate limits and use wait/retry
#     4. Use an awk script wrapper to do all the set up work such as
#        generate input files(e.g. by date etc.), version and manage the output files 
#     5. For very large file sizes, utilize forked processes / multithreading
#
# While using the archive files to generate tweetIds for delete or unfavorite
# feels like an extra step it makes the code  run more efficiently for more use cases 
# (assuming no failure in Twitter's archive functionality) for the following reasons 
# 1. You get to select which tweets to not unfavorite or not delete by removing them from 
#    your copy of the archive file before executing the code. Ditto userids for lookups 
# 2. There are fewer api calls made as the script doesn't have to first
#    read the timeline or otherwise collect the tweetids from the server.
#    Note: If  you have really old tweets to unfavorite script makes additional
#          api calls to favorite and unfavorite them for it to work 
# 3. 1. Above is the only potentially time consuming forced manual step which could
#    be semi automated with custom unix scripts run on the .csv archive files as a 
#    pre-processing step
# 4. You can retain a copy of your archive (pre delete) and have it for posterity
#    Note: Archive won’t save your photos and some links may be unusable.
#
# Note: Since Twitter only guarantees "eventual consistency" Twitter archive files used to
#       generate tweetIds for deletion or userIds for lookups etc. maynot provide latest
#	userdata. However the user can work-around this issue by choosing to archive data 
#	at an appropriate time prior to executing this script. 


#@requirements:Python 3.0,Tweepy (http://pypi.python.org/pypi/tweepy/1.7.1)
#@author: Ms Gitanjali "Gigi" GulveSehgal (A.K.A Gitanjali Gulve Sehgal nee' Gulve)
#!/usr/bin/python

import csv
import tweepy
import tweepy.error
import datetime

logfile = open("statfile","a")

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''

### Validate input file is accessible and return file pointer if valid 
def validate_inputfile(user_action):
	inp_status = -1
	num_attempts = 0

	if (user_action.lower() == 'delete') :
		action_comment = "of tweetIDs to be Deleted "
	elif (user_action.lower() == 'unfave') :
		action_comment = "of tweetIDs to be Unfavorited "
	elif (user_action.lower() == 'followers') :
		action_comment = "of UserIDs who's Followers need to be looked up "
	elif (user_action.lower() == 'friends') :
		action_comment = "of UserIDs who's Friends need to be looked up "
	elif (user_action.lower() == 'user') :
		action_comment = "of UserIDs who's information needs to be looked up "
	elif (user_action.lower() == 'help') :
		print("Type Exit to exit ")
		print(" .......... Type Delete to delete tweets listed by tweetid in input file ")
		print(" .......... Type Unfave to unfavorite tweets listed by tweetid in input file ")
		print(" .......... Type Followers to lookup followers for account userids listed in input file ")
		print(" .......... Type Friends to lookup friends for account userids listed in input file ")
		print(" .......... Type User to lookup details for userids listed in input file ")
		print("Type Help to get help using this application ")
		return(-1)
		
	else :
		print ("Invalid action %s selected , please reselect " % user_action.lower())
		return(-1)



	while (( inp_status == -1 ) and ( num_attempts < 5)) : 
			print("Please provide input file name which contains the list  %s " % action_comment)
			print("NOTE: Make sure file is readable, has the correct format (SEE Help.txt) and exists in current directory")
			input_file = input("> ")
			logfile.write("Input file provided %s \n" % input_file)
			try :
				mycsvfile = open(input_file,"r")
			except :
				print(" No such file %s or user does not have access, please provide valid input file name" % input_file)
			else :
				inp_status = 0
				print ("id_file set to %s " % mycsvfile)
				logfile.write("id_file set to %s \n" % mycsvfile)
			num_attempts = num_attempts + 1
	if ( inp_status != -1 ) :
		print(" input file pointer %s " % mycsvfile)
		return(mycsvfile)
	else :
		print ("Error opening input file. Too many tries, quitting")
		return(-1)



#### Authenticate with twitter using OAuth and return access
def oauth_login(consumer_key, consumer_secret): 

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth_url = auth.get_authorization_url()

    auth.set_access_token(ACCESS_TOKEN,ACCESS_TOKEN_SECRET)

    return tweepy.API(auth)


### Wrapper function to call specific batch function for user selected action 
def perform_batch(api,user_action,inp_csv_file):
	batch_error = 0


	if (user_action.lower() == 'delete') :
		action_pre_comment = "delete selected list of tweets from account "
		action_success_comment = "Deleted all user selected tweets "
		action_fail_comment = " tweet delete "

	elif (user_action.lower() == 'unfave') :
		action_pre_comment = "unfavorite selected list of tweets from account "
		action_success_comment = "Unfavorited all user selected tweets "
		action_fail_comment = " tweet unfavorite "

	elif (user_action.lower() == 'followers') :
		action_pre_comment = "lookup followers of selected list of accounts as visible to your account "
		action_success_comment = "Looked up Followers of all user selected UserIDs "
		action_fail_comment = " look up followers "

	elif (user_action.lower() == 'friends') :
		action_pre_comment = "lookup friends of selected list of accounts as visible to your account "
		action_success_comment = "Looked up Friends of all user selected UserIDs"
		action_fail_comment = " look up friends "

	elif (user_action.lower() == 'user') :
		action_pre_comment = "lookup information on selected list of accounts as visible to your account "
		action_success_comment = "Looked up information for all  user selected UserIDs "
		action_fail_comment = " look up user info "

	else :
		print("Invalid action selected please reselect ")
		return(-1)
		

	csv_reader = csv.reader(inp_csv_file, delimiter=',')
	print("About to %s %s . " % (action_pre_comment, api.verify_credentials().screen_name))

	if (user_action.lower() == 'delete') :
		batch_error = batch_delete(api,csv_reader)

	elif (user_action.lower() == 'unfave') :
		batch_error = batch_unfavorite(api,csv_reader)

	elif (user_action.lower() == 'followers') :
		batch_error = batch_lookup_followers(api,csv_reader)

	elif (user_action.lower() == 'friends') :
		batch_error = batch_lookup_friends(api,csv_reader)

	elif (user_action.lower() == 'user') :
		batch_error = batch_lookup_users(api,csv_reader)


	if ( batch_error  == 0 ) :
			print("%s as requested" % action_success_comment)
			logfile.write("%s as requested \n" % action_success_comment)
	elif ( batch_error > 0 ) :
			print("Found %d errors in bulk %s attempt " % (batch_error, action_fail_comment))
			logfile.write("Found %d errors in bulk %s attempt \n" % (batch_error, action_fail_comment))

	mycsvfile.close()
	return(0)






### Delete selected tweets
def batch_delete(api, del_file):

    print ("You are about to Delete all selected tweets posted from account @%s . " % api.verify_credentials().screen_name)
    print ("Please confirm all details and only if certain type yes - there is NO UNDO!")
    do_delete = input("> ")

    errors = 0
    if do_delete.lower() == 'yes':
        for row in del_file:
               print ("calling api.destroy_status tweetid =", row[0], " created on", row[3], " with text ", row[5] )
               logfile.write("calling api.destroy_status with tweetid = %s created on %s with text %s\n" %(row[0], row[3], row[5]))
               try:
                        api.destroy_status(row[0]) 
                        print ("Deleted: tweet with tweetid = ", row[0]) 
                        logfile.write("Deleted: tweet with tweetid = %s\n"  %(row[0]))
                        errors = errors
               except tweepy.error.TweepError as e:
                        errors = errors + 1
                        print ("Failed to delete tweet got TweepError with tweetid = ", row[0], " created on", row[3], " with text ", row[5] )
                        print ("Error code reported : " )
                        print (e.api_code)
                        logfile.write("Failed to delete: tweet with tweetid = %s and error code %d and error message %s \n" %(row[0], e.api_code, e.response.text))
    else:
        print ("Didn't understand input %s, quitting " % do_delete )
        errors = -1 
    return(errors)




### Unfavorite selected tweets
def batch_unfavorite(api, id_file):
    print("You are about to Unfavorite all selected tweets posted from account @%s . " % api.verify_credentials().screen_name)
    print("Please confirm all details and only if certain type yes - there is NO UNDO!")
    do_unfavorite = input("> ")

    errors = 0
    num_calls = 0
    if do_unfavorite.lower() == 'yes':
        for row in id_file:
               print("Calling api.destroy_favorite with tweetid =", row[0])
               logfile.write("Calling api.destroy_favorite with tweetid = %s \n" % row[0])
               try:
                        api.destroy_favorite(row[0]) 
                        print("... Unfavorited: tweet with tweetid = ", row[0])
                        logfile.write("... Unfavorited: tweet with tweetid = %s\n"  % row[0])
                        errors = errors
               except tweepy.error.TweepError as e:
                        print("... Failed to unfavorite tweet got TweepError for tweetid = ", row[0])
                        logfile.write("... Failed to unfavorite tweet got TweepError for tweetid = %s\n" % row[0])
                        if (num_calls <= 1000 ) :
                           print("...... Attempting like+unlike for tweetid = ", row[0])
                           logfile.write("...... Attempting like+unlike for tweetid = %s\n" % row[0])
                           try:    
                               api.create_favorite(row[0])
                               api.destroy_favorite(row[0]) 
                               print("...... refavorited and unfavorited tweetid = ", row[0])
                               logfile.write("...... refavorited and unfavorited tweetid = %s\n" % row[0])
                               num_calls = num_calls + 1
                           except tweepy.error.TweepError as e:
                               errors = errors + 1
                               print("...... Error code reported : ")
                               print (e.api_code)
                               logfile.write("...... Failed to unfavorite tweet with tweetid = %s and error code %d and error message %s \n" %(row[0], e.api_code, e.response.text))
                        else:
                           print ("...... Over the rate limit, marking as error and quitting\n")
                           errors = errors + 1
                           print("Error code reported : ")
                           print (e.api_code)
                           logfile.write("...... Failed to unfavorite tweet with tweetid = %s and error code %d and error message %s and rate_limit hit at %d \n" %(row[0], e.api_code, e.response.text, num_calls))
                           logfile.write ("Total calls made %d \n" % num_calls)
                           return(errors)
    else:
        print("Didn't understand input %s, quitting " % do_unfavorite)
        errors = -1 
    logfile.write ("Total calls made %d \n" % num_calls)
    return(errors)



### Lookup followers of requested user_id(s)
def batch_lookup_followers(api, id_file):
    print("You are about to lookup all followers of selected account. You are  @%s . " % api.verify_credentials().screen_name)
    print("Please confirm all details and only if certain type yes - there is NO UNDO!")
    do_lookup_followers = input("> ")

    errors = 0
    num_calls = 0
    if do_lookup_followers.lower() == 'yes':
        for row in id_file:
               print("calling api.followers_ids for user_id =", row[0])
               logfile.write("calling api.followers_ids for user_id = %s \n" % row[0])
               try:
                        ids = api.followers_ids(user_id=row[0]) 
                        print("Lookedup all followers for user_id = ", row[0])
                        logfile.write("... Looked up all followers for user_id = %s\n"  % row[0])
                        print("ids are... ", ids)
                        errors = errors
                        num_calls = num_calls + 1
               except tweepy.error.TweepError as e:
                        print("Failed to lookup followers got TweepError for user_id = ", row[0])
                        logfile.write("... Failed to lookup followers got TweepError for user_id = %s\n" % row[0])
                        errors = errors + 1
                        print("... Error code reported : ")
                        print (e.api_code)
                        logfile.write("Failed to lookup followers for user_id = %s and error code %d and error message %s \n" %(row[0], e.api_code, e.response.text))
    else:
        print("Didn't understand input %s, quitting " % do_lookup_followers)
        errors = -1 
    logfile.write ("Total calls made %d \n" % num_calls)
    return(errors)


### Lookup friends of requested user_id(s)
def batch_lookup_friends(api, id_file):
    print("You are about to lookup all friends of chosen account. You are @%s . " % api.verify_credentials().screen_name)
    print("Please confirm all details and only if certain type yes - there is NO UNDO!")
    do_lookup_friends = input("> ")

    errors = 0
    num_calls = 0
    if do_lookup_friends.lower() == 'yes':
        for row in id_file:
               print("calling api.friends_ids for user_id =", row[0])
               logfile.write("calling api.friends_ids for user_id = %s \n" % row[0])
               try:
                        ids = api.friends_ids(user_id=row[0])
                        print("Lookedup all friends for user_id = ", row[0])
                        logfile.write("... Looked up all friends for user_id = %s\n"  % row[0])
                        print("ids are... ", ids)
                        errors = errors
                        num_calls = num_calls + 1
               except tweepy.error.TweepError as e:
                        print("Failed to lookup friends got TweepError for user_id = ", row[0])
                        logfile.write("... Failed to lookup friends got TweepError for user_id = %s\n" % row[0])
                        errors = errors + 1
                        print("... Error code reported : ")
                        print (e.api_code)
                        logfile.write("Failed to lookup friends for userid = %s and error code %d and error message %s \n" %(row[0], e.api_code, e.response.text))
    else:
        print("Didn't understand input %s, quitting " % do_lookup_friends)
        errors = -1 
    logfile.write ("Total calls made %d \n" % num_calls)
    return(errors)



#### Print all the fields of other user object neatly
def print_and_save_user_info(usr_id, usr_info):
	# Trying to figure out all attributes as we go
	print("Details for user id %s are: \n" % usr_id)
	logfile.write("Details for user id %s are: \n" % usr_id)
	print("		screen_name: %s\n" % usr_info.screen_name)	
	logfile.write("		screen_name: %s\n" % usr_info.screen_name)	
	print("		profile_location: %s\n" % usr_info.profile_location)	
	logfile.write("		profile_location: %s\n" % usr_info.profile_location)	
	print("		location: %s\n" % usr_info.location)	
	logfile.write("		location: %s\n" % usr_info.location)	
	print("		description: %s\n" % usr_info.description)	
	logfile.write("		description: %s\n" % usr_info.description)	
	print("		url: %s\n" % usr_info.url)	
	logfile.write("		url: %s\n" % usr_info.url)	
	print("		entities: %s\n" % usr_info.entities)	
	logfile.write("		entities: %s\n" % usr_info.entities)	
	print("		protected: %s\n" % usr_info.protected)	
	logfile.write("		protected: %s\n" % usr_info.protected)	
	print("		followers_count: %d \n" % usr_info.followers_count)
	logfile.write("		followers_count: %d \n" % usr_info.followers_count)
	print("		friends_count: %d \n" % usr_info.friends_count)
	logfile.write("		friends_count: %d \n" % usr_info.friends_count)
	print("		favourites_count: %d \n" % usr_info.favourites_count)
	logfile.write("		favourites_count: %d \n" % usr_info.favourites_count)
	print("		listed_count: %d \n" % usr_info.listed_count)
	logfile.write("		listed_count: %d \n" % usr_info.listed_count)
	print("		created_at: %s \n" % usr_info.created_at)
	logfile.write("		created_at: %s \n" % usr_info.created_at)
	print("		utc_offset : %s \n" % usr_info.utc_offset)
	logfile.write("		utc_offset : %s \n" % usr_info.utc_offset)
	print("		time_zone : %s \n" % usr_info.time_zone)
	logfile.write("		time_zone : %s \n" % usr_info.time_zone)
	print("		geo_enabled : %s \n" % usr_info.geo_enabled)
	logfile.write("		geo_enabled : %s \n" % usr_info.geo_enabled)
	print("		verified : %s \n" % usr_info.verified)
	logfile.write("		verified : %s \n" % usr_info.verified)
	print("		statuses_count : %d \n" % usr_info.statuses_count)
	logfile.write("		statuses_count : %d \n" % usr_info.statuses_count)
	print("		lang: %s \n" % usr_info.lang)
	logfile.write("		lang: %s \n" % usr_info.lang)
	print("		contributors_enabled: %s \n" % usr_info.contributors_enabled)
	logfile.write("		contributors_enabled: %s \n" % usr_info.contributors_enabled)
	print("		is_translator: %s \n" % usr_info.is_translator)
	logfile.write("		is_translator: %s \n" % usr_info.is_translator)
	print("		is_translation_enabled: %s \n" % usr_info.is_translation_enabled)
	logfile.write("		is_translation_enabled: %s \n" % usr_info.is_translation_enabled)
	print("		translator_type: %s \n" % usr_info.translator_type)
	logfile.write("		translator_type: %s \n" % usr_info.translator_type)
	print("		notifications: %s \n" % usr_info.notifications)
	logfile.write("		notifications: %s \n" % usr_info.notifications)
	print("		follow_request_sent: %s \n" % usr_info.follow_request_sent)
	logfile.write("		follow_request_sent: %s \n" % usr_info.follow_request_sent)
	print("		following: %s \n" % usr_info.following)
	logfile.write("		following: %s \n" % usr_info.following)
	print("		profile_image_url: %s \n" % usr_info.profile_image_url)
	logfile.write("		profile_image_url: %s \n" % usr_info.profile_image_url)
	print("		profile_image_url_https: %s \n" % usr_info.profile_image_url_https)
	logfile.write("		profile_image_url_https: %s \n" % usr_info.profile_image_url_https)
	print("		profile_use_background_image: %s \n" % usr_info.profile_use_background_image)
	logfile.write("		profile_use_background_image: %s \n" % usr_info.profile_use_background_image)
	print("		has_extended_profile: %s \n" % usr_info.has_extended_profile)
	logfile.write("		has_extended_profile: %s \n" % usr_info.has_extended_profile)
	print("		default_profile: %s \n" % usr_info.default_profile)
	logfile.write("		default_profile: %s \n" % usr_info.default_profile)
	print("		default_profile_image: %s \n" % usr_info.default_profile_image)
	logfile.write("		default_profile_image: %s \n" % usr_info.default_profile_image)

	return



### Look up user details such as screen_name etc.  of selected users
def batch_lookup_users(api, id_file):
    print("You are about to lookup details of all selected users. You are account @%s . " % api.verify_credentials().screen_name)
    print("Please confirm all details and only if certain type yes - there is NO UNDO!")
    do_lookup_users = input("> ")

    errors = 0
    num_calls = 0
    if do_lookup_users.lower() == 'yes':
        for row in id_file:
               print("calling api.get_user for user_id =", row[0])
               logfile.write("calling api.get_user for user_id = %s \n" % row[0])
               try:
                        user_info = api.get_user(row[0]) 
                        print("Lookedup all details for user_id = ", row[0])
                        logfile.write("... Looked up all details for user_id = %s\n"  % row[0])
                        print_and_save_user_info(row[0],user_info)
                        errors = errors
                        num_calls = num_calls + 1
               except tweepy.error.TweepError as e:
                        print("Failed to lookup user details got TweepError for user_id = ", row[0])
                        logfile.write("... Failed to lookup user details got TweepError for user_id = %s\n" % row[0])
                        errors = errors + 1
                        print("... Error code reported : ")
                        print (e.api_code)
                        logfile.write("Failed to lookup user details for userid = %s and error code %d and error message %s \n" %(row[0], e.api_code, e.response.text))
    else:
        print("Didn't understand input %s, quitting " % do_lookup_users)
        errors = -1 
    logfile.write ("Total calls made %d \n" % num_calls)
    return(errors)



logfile.write("New batch session started at %s \n" % datetime.datetime.now())
api = oauth_login(CONSUMER_KEY, CONSUMER_SECRET)
print("Authenticated as: %s" % api.me().screen_name)


print("Please select action intended on account @%s . " % api.verify_credentials().screen_name)
print("Please confirm all details and if uncertain type Exit to exit - there is NO UNDO!")
print(" .......... Type Delete to delete tweets listed by tweetid in input file ")
print(" .......... Type Unfave to unfavorite tweets listed by tweetid in input file ")
print(" .......... Type Followers to lookup followers for account userids listed in input file ")
print(" .......... Type Friends to lookup friends for account userids listed in input file ")
print(" .......... Type User to lookup details for userids listed in input file ")
print(" .......... Type Help to get help using this application ")
do_action = input("> ")

while (do_action.lower() != 'exit') :
	mycsvfile = validate_inputfile( do_action.lower() )
	if (mycsvfile != -1 ) :
		perform_batch(api,do_action,mycsvfile)
	print(" Please select next action or Exit to exit")
	do_action = input("> ")
#end-while	

print("Exiting as requested ")
logfile.close()
