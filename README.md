# steem-deutschbot

This is a fork of:

https://github.com/emre/deutschbot

steem-deutschbot is a discord/steem bot to curate content under pre-defined tags in the steem blockchain.
The discord interface is to edit a list of curators, blacklist users and adjust a threshold.
The bot will calculate a score for each post, based on the votes of the curators and their vote's weights.
Once the score reaches the threshold, the bot will vote for the post, too.
( vote_weight = 100%  ^= score += 10000 )

Custom additions:

The first webhook in the list of webhooks will be used as 'private', all following hooks are 'public'.

All webhooks will broadcast on a bot vote; post, weight, score

The private webhook broadcasts on every vote also; post, curators, score

#### Installation

Make sure you have created a virtual environment with python3.6 venv. It's not
required for bot to work, however it's highly suggested.

```
$ git clone https://github.com/emre/deutschbot.git
$ cd deutschbot
$ pip install -r requirements.txt
$ cd communitybot
$ vim settings.py # edit accordingly
```

#### Running

##### 1. Discord Bot

Make sure you have edited

- BOT\_TOKEN
- DB\_CONNECTION\_URI (Compatible w/ databases [dataset](https://dataset.readthedocs.io/en/latest/) supports.

in the settings.py

To run it:

```
$ python deutschbot.py --run discordbot
```

**Bot commands**

```
$help - Display this help message.
$blacklist - Blacklists a user, or removes them from the blacklist; Usage: $blacklist add username or $blacklist remove username
$curators - Puts users in the list of curators, or removes them; Usage: $curators add username or $curators remove username
$threshold - Regulate the threshold for the bot. $threshold set 100 to set it or $threshold get to current value. to trigger. 100 = 1% VP
```

**Adding authorized users to bot**

This can be done via command line.

```
$ python deutschbot.py --add-discord-user emre#9263
```

Make sure you include the discord ID.

##### 2. Curator Bot

**Running**

First, make you sure you have edit:

- BOT\_ACCOUNT
- BOT\_POSTING\_KEY
- TAGS
- HOOKS

in the settings.py.

```
$ python deutschbot.py --run curate
```

This will start listening transactions on the network. If a trusted curator votes on something,
bot will calculate a score and if the score is greater then the threshold, it will upvote the post. 

After upvoting, it will also post to discord about it.

**Starting from a specific block**

By default, curator bot will start listening from the last block generated. If you need to start it from a
specific block height, you should run the bot as:

```
$python deutschbot.py  --run curate --start-block 12312333
```










