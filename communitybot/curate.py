import time
import logging
import requests
import json

from communitybot.utils import (
    get_curators, get_option, url, set_option, is_blacklisted
)
from communitybot.settings import THRESHOLD_OPTION_ID, HOOKS, LAST_BLOCK_ID
from communitybot.embeds import Webhook

from steem.post import Post
from steem.account import Account

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()


MESSAGE_TEMPLATES = {
    "ON_VOTE": "**Voted**: %s\n**Weight:**: %s\n**Score**: "
               "%s (Curated by %s with weight(s): %%%s)",
}


class Curator:

    def __init__(self, steemd_instance, expected_tags, bot_account):
        self.s = steemd_instance
        self.expected_tags = expected_tags
        self.bot_account = bot_account

    def get_last_block_height(self):
        props = self.s.get_dynamic_global_properties()
        return props['last_irreversible_block_num']

    def handle_curation(self, op_type, op_value):

        curators = [c["account"] for c in get_curators()]

        # we're only interested in votes
        if op_type != "vote":
            return

        # if the voter is not a trusted curator, skip it.
        if op_value.get("voter") not in curators:
            return

        # check the post if we have already voted?
        p = Post("%s/%s" % (
            op_value.get("author"), op_value.get("permlink")),
                 steemd_instance=self.s)

        # we're only interested in main posts
        if not p.is_main_post():
            return

        # the post is tagged with the tags we defined?
        if len(set(self.expected_tags).intersection(p.get("tags"))) == 0:
            return

        # is the author in the blacklist?
        if is_blacklisted(op_value.get("author")):
            return

        score = 0
        already_voted = False
        curators_on_the_post = []
        for active_vote in p.get("active_votes", []):
            if active_vote.get("voter") == self.bot_account:
                already_voted = True
            if active_vote.get("voter") in curators:
                score += active_vote.get("percent")
                curators_on_the_post.append({
                    "curator": active_vote.get("voter"),
                    "weight": active_vote.get("percent"),
                })

        # if we already voted on that, skip.
        if already_voted:
            return

        # if the score is lower then the threshold, skip.
        if score < int(get_option(THRESHOLD_OPTION_ID)["value"]):
            return

        bot_account = Account(self.bot_account, steemd_instance=self.s)
        weight = bot_account.voting_power()
        self.upvote(p, weight, self.bot_account)
        self.post_to_webhooks(
            p,
            curators_on_the_post,
            score,
            weight
        )

    def upvote(self, post, weight, voter, try_count=None):
        if not try_count:
            try_count = 0

        try:
            post.vote(weight, voter)
            logger.info("Voted w/ %s to %s.", weight, post.identifier)
        except Exception as error:
            logger.error(error)
            if try_count < 3:
                logger.info("Failed but trying again: %s", post.identifier)
                time.sleep(3)
                return self.upvote(post, weight, voter, try_count + 1)
            else:
                logger.info("Tried 3 times but failed. %s ", post.identifier)

    def post_to_webhooks(self, p, curators, score, weight):

        hook = Webhook(None)
        hook.set_author(
            name=self.bot_account,
            url="http://steemit.com/tag/@%s" % self.bot_account,
            icon="https://img.busy.org/@%s?height=100&width=100" %
                 self.bot_account,
        )

        hook.add_field(
            name="Voted (%%%s)" % str(weight),
            value=url(p),
        )

        hook.add_field(
            name="Score",
            value=score,
        )

        hook.add_field(
            name="Curators",
            value=",".join(c["curator"] for c in curators)
        )

        hook.add_field(
            name="Curator weights",
            value=",".join(str(c["weight"]) for c in curators)
        )

        for hook_url in HOOKS:
            hook.url = hook_url
            hook.post()

    def parse_block(self, block_id):
        logger.info("Parsing %s", block_id)

        # get all operations in the related block id
        operation_data = self.s.get_ops_in_block(
            block_id, virtual_only=False)

        for operation in operation_data:
            self.handle_curation(*operation['op'][0:2])

    def listen_blocks(self, starting_point=None):
        if not starting_point:
            starting_point = self.get_last_block_height()
        while True:
            while (self.get_last_block_height() - starting_point) > 0:
                starting_point += 1
                self.parse_block(starting_point)
                set_option(LAST_BLOCK_ID, starting_point)

            print("Sleeping for 3 seconds...")
            time.sleep(3)
