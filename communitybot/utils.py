import dataset
from datetime import datetime
import re
from communitybot.settings import DB_CONNECTION_URI, NODES, BOT_POSTING_KEY
from steem import Steem

_db_conn = None
_steem_conn = None


def get_db_conn():
    global _db_conn

    if _db_conn is None:
        _db_conn = dataset.connect(DB_CONNECTION_URI)

    return _db_conn


def get_steem_conn():
    global _steem_conn
    if _steem_conn is None:
        _steem_conn = Steem(nodes=NODES, keys=[BOT_POSTING_KEY, ])

    return _steem_conn

blacklist_table = get_db_conn()["blacklist"]
curators_table = get_db_conn()["curators"]
options_table = get_db_conn()["options"]
discord_users_table = get_db_conn()["discord_users"]


def is_authorized(author):
    return bool(discord_users_table.find_one(
        nickname=author.name,
        discord_id=author.discriminator
    ))


def add_discord_user(nickname, discord_id):
    if discord_users_table.find_one(
        nickname=nickname,
        discord_id=discord_id
    ):
        return False

    discord_users_table.insert(dict(
        nickname=nickname,
        discord_id=discord_id
    ))

    return True


def add_to_blacklist(account, author):
    if blacklist_table.find_one(
        account=account,
    ):
        return False

    blacklist_table.insert(dict(
        account=account,
        created_at=str(datetime.now()),
        added_by=author,
    ))

    return True


def remove_from_blacklist(account):

    if blacklist_table.find_one(
        account=account,
    ):
        blacklist_table.delete(
            account=account,
        )
        return True

    return False


def is_blacklisted(author):
    return bool(blacklist_table.find_one(account=author))


def add_to_curators(account, author):
    if curators_table.find_one(
        account=account,
    ):
        return False

    curators_table.insert(dict(
        account=account,
        created_at=str(datetime.now()),
        added_by=author,
    ))

    return True


def remove_from_curators(account):

    if curators_table.find_one(
        account=account,
    ):
        curators_table.delete(
            account=account,
        )
        return True

    return False


def username_is_valid(username):
    return len(re.findall('([a-z][a-z0-9\-]+[a-z0-9])', username)) > 0


def get_help_message(description):
    helpmsg = description
    helpmsg += '**$help** - ``Display this help message.``\n'
    helpmsg += '**$blacklist** - ``Blacklists a user, or removes them from' \
               ' the blacklist; Usage: $blacklist add username or $blacklist ' \
               'remove username``\n'
    helpmsg += '**$curators** - ``Puts users in the list of curators, or' \
               ' removes them; Usage: $curators add username or $curators ' \
               'remove username``\n'
    helpmsg += '**$threshold** - ``Regulate the threshold for the bot. ' \
               '$threshold set 100 to set it or $threshold get to ' \
               'current value. to trigger. 100 = 1% VP``\n'

    return helpmsg


def set_option(option_id, value):
    data = {
        "option_id": option_id,
        "value": str(value),
    }
    options_table.upsert(data, ['option_id'])


def get_option(option_id):
    option = options_table.find_one(
        option_id=option_id,
    )

    return option


def get_curators():
    return curators_table.find()


def url(p):
    return "https://steemit.com/@%s/%s" % (p.get("author"), p.get("permlink"))