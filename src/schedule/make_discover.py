import asyncio

from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from apify_client import ApifyClient
from apify_client.clients import ActorClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Config
from src.schema import Tweet


async def construct_search_terms(usernames: list[str], date: str) -> list[str]:
    return [
        f"from:{username}, since:{date}, include:nativeretweets"
        for username in usernames
    ]


async def send_tweet(bot: Bot, main_chat_id, thread_id, tweet, parse=True):
    if not parse:
        if tweet.retweet:
            await bot.send_message(
                chat_id=main_chat_id,
                message_thread_id=thread_id,
                text=(
                    f"<b> {tweet.createdAt} </b>\n"
                    f'<b> <a href="{tweet.url}"> Retweet from {tweet.retweet.author.name} </a> </b>\n\n'
                    f"{tweet.retweet.text}\n\n"
                ),
                disable_web_page_preview=True,
                parse_mode=None
            )
        elif tweet.quote:
            await bot.send_message(
                chat_id=main_chat_id,
                message_thread_id=thread_id,
                text=(
                    f"<b> {tweet.createdAt} </b>\n"
                    f'<b><a href="{tweet.url}"> Quote on {tweet.quote.author.name}: </a></b>\n'
                    f"<blockquote> {tweet.quote.text} </blockquote>\n\n"
                    f"<b> {tweet.author.name} </b>: {tweet.text}\n\n"
                ),
                disable_web_page_preview=True,
                parse_mode=None
            )
        else:
            await bot.send_message(
                chat_id=main_chat_id,
                message_thread_id=thread_id,
                text=(
                    f"<b> {tweet.createdAt} </b>\n"
                    f'<b><a href="{tweet.url}"> Tweet from {tweet.author.name} </a></b>\n\n'
                    f"{tweet.text}\n"
                ),
                disable_web_page_preview=True,
                parse_mode=None
            )
    else:
        if tweet.retweet:
            await bot.send_message(
                chat_id=main_chat_id,
                message_thread_id=thread_id,
                text=(
                    f"<b> {tweet.createdAt} </b>\n"
                    f'<b> <a href="{tweet.url}"> Retweet from {tweet.retweet.author.name} </a> </b>\n\n'
                    f"{tweet.retweet.text}\n\n"
                ),
                disable_web_page_preview=True
            )
        elif tweet.quote:
            await bot.send_message(
                chat_id=main_chat_id,
                message_thread_id=thread_id,
                text=(
                    f"<b> {tweet.createdAt} </b>\n"
                    f'<b><a href="{tweet.url}"> Quote on {tweet.quote.author.name}: </a></b>\n'
                    f"<blockquote> {tweet.quote.text} </blockquote>\n\n"
                    f"<b> {tweet.author.name} </b>: {tweet.text}\n\n"
                ),
                disable_web_page_preview=True
            )
        else:
            await bot.send_message(
                chat_id=main_chat_id,
                message_thread_id=thread_id,
                text=(
                    f"<b> {tweet.createdAt} </b>\n"
                    f'<b><a href="{tweet.url}"> Tweet from {tweet.author.name} </a></b>\n\n'
                    f"{tweet.text}\n"
                ),
                disable_web_page_preview=True
            )


async def send_tweets_by_threads(
    tweets: dict[str, list[Tweet]], config: Config, bot: Bot
):
    for idx, twitter_object in enumerate(config.twitter_objects, start=1):
        if idx % 20 == 0:
            await asyncio.sleep(61)

        tweets_by_thread = tweets.get(twitter_object.twitter_username, [])
        for tweet in tweets_by_thread:
            await asyncio.sleep(1.2)

            main_chat_id = config.main_chat_id
            thread_id = twitter_object.thread_id

            try:
                await send_tweet(bot, main_chat_id, thread_id, tweet)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                await send_tweet(bot, main_chat_id, thread_id, tweet)
            except TelegramBadRequest as e:
                if 'too long' in e.message:
                    print('=============too long============')

                for twt in split_tweet(tweet):
                    await send_tweet(bot, main_chat_id, thread_id, twt, False)
                    await asyncio.sleep(4)
                    continue


                print(f"bad request happened: {e}")
                print(f"TWEET:\n\n\n{tweet.text}\n\n\n")
                await send_tweet(bot, main_chat_id, thread_id, tweet, False)
                continue

def split_tweet(tweet: Tweet) -> list[Tweet]:
    message = tweet.text

    tweet_copy = tweet.model_copy(deep=True)

    tweet.text = message[:len(message)//2] 
    tweet_copy.text = message[len(message)//2:]
    return [tweet, tweet_copy]

# TODO: make discovering more efficient with async
async def discover_tweets(session: Session, bot: Bot) -> None:
    # here i need to select all twitter_objects per api_key
    stmt = select(Config)
    configs = session.scalars(stmt).all()

    for config in configs:
        usernames = [user.twitter_username for user in config.twitter_objects]
        if config.log_thread_id:
            await bot.send_message(
                chat_id=config.main_chat_id,
                message_thread_id=config.log_thread_id,
                text=(
                    f"Started discovering tweets for users: \n\n{', '.join(usernames)}\n\n"
                    f"last discovering date: {config.last_discovering_date}"
                ),
            )

        last_date_str = datetime.strftime(config.last_discovering_date, "%Y-%m-%d")
        apify_key = config.apify_key
        if not apify_key:
            await bot.send_message(
                chat_id=config.main_chat_id,
                message_thread_id=config.log_thread_id,
                text="API key was not provided for this chat, "
                "make sure to run /set_api_key to enable tweets discovering",
            )
            continue

        if not config.twitter_objects:
            await bot.send_message(
                chat_id=config.main_chat_id,
                message_thread_id=config.log_thread_id,
                text="You have not added any twitter users to config, "
                "make sure to run /xadd to start watching for tweets",
            )
            continue

        client = ApifyClient(apify_key)
        actor: ActorClient = client.actor("apidojo/tweet-scraper")

        search_terms = await construct_search_terms(usernames, last_date_str)

        run_input = {
            "searchTerms": search_terms,
            "sort": "Latest",
        }
        print(run_input)

        run = actor.call(
            run_input=run_input, max_items=1000, memory_mbytes=256, wait_secs=60
        )

        if config.log_thread_id:
            log = client.run(run["id"]).log().get()

            await bot.send_message(
                chat_id=config.main_chat_id,
                message_thread_id=config.log_thread_id,
                text=log,
            )

        latest_run = (
            client.runs().list(desc=True, limit=10).items[0]["defaultDatasetId"]
        )

        # ==how to get run==
        # latest_run = client.runs().list(desc=True, limit=100).items[0]['defaultDatasetId']

        # ==How to abort run==
        # concrete_run = client.run("cAsXrrAoy3s70ANKb")
        # concrete_run.abort()

        # dataset = client.dataset(latest_run).list_items().items
        #
        # with open('tweets.json', 'w') as f:
        #     f.write(json.dumps(dataset, indent=4, ensure_ascii=False))

        dataset_iterator = client.dataset(latest_run).iterate_items()

        tweets = {}
        count = 0
        count_relevant = 0
        for raw_tweet in dataset_iterator:
            count += 1

            if raw_tweet.get("noResults"):
                print("+++++NO RESULTS+++++")
                continue

            twt = Tweet(**raw_tweet)

            if twt.createdAt >= config.last_discovering_date:
                author_username = twt.author.userName
                count_relevant += 1
                author_tweets = tweets.get(author_username, [])
                author_tweets.insert(0, twt)
                tweets[author_username] = author_tweets

        if config.log_thread_id:
            await bot.send_message(
                chat_id=config.main_chat_id,
                message_thread_id=config.log_thread_id,
                text=f"Tweets discovered: {count} | Relevant: {count_relevant}",
            )

        await send_tweets_by_threads(tweets, config, bot)

        config.last_discovering_date = datetime.now()
        session.add(config)
        session.commit()


async def start_discovering_schedule(session: Session, bot: Bot):
    while True:
        current_time = datetime.now()
        target_time = datetime(
            year=current_time.year,
            month=current_time.month,
            day=current_time.day,
            hour=current_time.hour,
            minute=59,
            second=55,
        )
        await asyncio.sleep((target_time - current_time).seconds)
        await discover_tweets(session, bot)
