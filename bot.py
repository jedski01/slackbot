import configparser
import json
import slackclient
import time

CONFIG = 'config.cfg'
BOT_SCRIPTS = 'scripts.json'
AT_BOT = None #TODO find another way to do this, it would be great to create a bot class

PUBLIC = 1
PRIVATE = 2
DM = 3

#load the bot settings
config = configparser.ConfigParser()
config.read(CONFIG)

#load the bot scripts
#TODO add a check if file is not found
script_file = open(BOT_SCRIPTS)
scripts = json.load(script_file)

#create the bot client using credentials
bot = slackclient.SlackClient(config['BOT']['token'])

def get_channel_type(channel):
    
    if channel[0] == 'D':
        return DM
    if channel[0] == 'C':
        return PUBLIC
    if channel[0] == 'G':
        return PRIVATE

    # return {
    #     'D' : DM,
    #     'C' : PUBLIC,
    #     'G' : PRIVATE
    # }[channel[0]]

    return None 


#create a simple reply to 'hi' when talking to bot
#reply should include user's name
def parse_slack_output(slack_output_list):
    
    if slack_output_list and len(slack_output_list) > 0:
        for output in slack_output_list:
            
            if output and 'text' in output:
                #check if the channel is DM or public/private
                ch_type = get_channel_type(output['channel'].strip())
                
                print('channel type is', ch_type)
                if ch_type == DM:
                    return output['text'], output['channel'], output['user']
                if ch_type == PUBLIC or ch_type == PRIVATE:
                    #if it is in public/private 
                    #check if the message is directed to the bot
                    if AT_BOT in output['text']:
                        return output['text'].strip(AT_BOT).strip().lower(), output['channel'], output['user']
                
    return None, None, None

def handle_command(command, channel, user):
    
    if command in scripts:
        user_by_name = getNameById(user)

        response = scripts[command].format(user=user_by_name)

        bot.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

    return

def getNameById(id):
   
    #get the user list by making an api call
    api_call = bot.api_call('users.list')
    if api_call.get('ok'):
        users = api_call.get('members')
        #traverse user list 
        for user in users:
            if user['id'] == id:
                return user['name']
    
    #return none if none found
    return None

def getIdByName(name):
    
    name = name.strip('\'')

    #get the user list by making an api call
    api_call = bot.api_call('users.list')
    if api_call.get('ok'):
        users = api_call.get('members')
        #traverse user list 
        for user in users:
            if user['name'] == name:
                #just return the first name
                return user['id']
    
    #return none if none found
    return None


#MAIN
#establish connection to slack using RTM
if __name__ == '__main__':
    READ_WEBSOCKET_DELAY = 1 #1 second delay between reading from firehose

    #get the bots name
    bot_id = getIdByName(config['BOT']['name'])

    if bot_id:
        AT_BOT = "<@" + bot_id + ">"
    else:
        print("Invalid bot id")
        exit()

    if bot.rtm_connect():
        print("Bot is up and running")
  
        #main loop
        while True:
            command, channel, user = parse_slack_output(bot.rtm_read())
            if command and channel:
                handle_command(command, channel, user)
            # print(bot.rtm_read())
          
            time.sleep(READ_WEBSOCKET_DELAY)

    else:
        print("Connection failed. Invalid Slack Token or bot ID")



