from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pymongo import MongoClient
import logging

mongo_client = MongoClient("mongodb+srv://tanjiro1564:tanjiro1564@cluster0.pp5yz4e.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["bot_database"]
users_collection = db["users_database"]
forwarded_messages_collection = db["forwarded_messages"]

app = Client(
    "my_bot",
    api_id="16542582",
    api_hash="c75e00f0ac7ce6f3273e073cb7f06ec2",
    bot_token="6451319497:AAFY-VXBYFX1zph0u9bj-NxvjWDth9DqYBg"
)

ADMIN_USER_IDS = [5527170635]
ADMIN = 5527170635

logging.basicConfig(level=logging.INFO)

def add_user_to_db(user_id, username):
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"username": username}},
            upsert=True
        )
        logging.info(f"User {user_id} added/updated in database with username: {username}.")
    except Exception as e:
        logging.error(f"Error adding/updating user {user_id} in database: {e}")

def get_total_users():
    try:
        total_users = users_collection.count_documents({})
        logging.info(f"Total users: {total_users}")
        return total_users
    except Exception as e:
        logging.error(f"Error getting total users: {e}")
        return 0

def add_forwarded_message(reference_id, forwarded_message_id):
    try:
        forwarded_messages_collection.update_one(
            {"forwarded_message_id": forwarded_message_id},
            {"$set": {"reference_id": reference_id}},
            upsert=True
        )
        logging.info(f"Forwarded message {forwarded_message_id} mapped to user ID {reference_id}.")
    except Exception as e:
        logging.error(f"Error mapping forwarded message {forwarded_message_id}: {e}")

def get_reference_id(forwarded_message_id):
    try:
        record = forwarded_messages_collection.find_one({"forwarded_message_id": forwarded_message_id})
        if record:
            logging.info(f"Reference ID for forwarded message {forwarded_message_id} is {record.get('reference_id')}.")
            return record.get("reference_id")
        else:
            logging.warning(f"No record found for forwarded message ID {forwarded_message_id}.")
            return None
    except Exception as e:
        logging.error(f"Error retrieving reference ID for forwarded message {forwarded_message_id}: {e}")
        return None

@app.on_message(filters.command("start"))
async def start(client, message):
    mention = message.from_user.mention
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "No Username"
    
    add_user_to_db(user_id, username)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴀʙᴏᴜᴛ", url="https://t.me/about_shubhhh"),
        InlineKeyboardButton("ᴍʏ ʟᴏᴠᴇ ❤️", url="tg://settings")],
        [InlineKeyboardButton("ᴍʏ ᴄᴏɴᴛᴀᴄᴛ", url="tg://need_update_for_some_feature")]
    ])
    
    await message.reply(
        f"ʜᴇʟʟᴏ ᴛʜᴇʀᴇ {mention},\n\nᴛʜɪs ɪs ᴘᴇʀsᴏɴᴀʟ ᴀssɪsᴛᴀɴᴛ ᴏғ sʜᴜʙʜʜʜ 🇮🇳!\n\n ʏᴏᴜ ᴄᴀɴ ᴄᴏɴᴛᴀᴄᴛ ᴍʏ ᴍᴀsᴛᴇʀ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ!!\n\nᴅʀᴏᴘ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ʜᴇʀᴇ, ɪ ᴡɪʟʟ ᴅᴇʟɪᴠᴇʀ ɪᴛ ᴛᴏ ᴍᴀsᴛᴇʀ.😊",
        reply_markup=keyboard
    )

@app.on_message(filters.command("stats"))
async def total_users(client, message):
    total = get_total_users()
    await message.reply(f"Total number of users: {total}")

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_USER_IDS))
async def broadcast_command(client, message):
    try:
        msg_text = message.text.split("/broadcast ", 1)[1]
    except IndexError:
        await message.reply("Please provide a message to broadcast using the command: /broadcast <message>")
        return

    chat_ids = [user["user_id"] for user in users_collection.find({})]

    success_count = 0
    failed_count = 0

    for chat_id in chat_ids:
        try:
            await client.send_message(chat_id, msg_text)
            success_count += 1
        except Exception as e:
            logging.error(f"Error sending message to {chat_id}: {e}")
            failed_count += 1

    report_text = (f"Broadcast complete!\n"
                   f"Successful: {success_count}\n"
                   f"Failed: {failed_count}")
    await message.reply(report_text)

@app.on_message(filters.private & filters.text)
async def pm_text(bot, message):
    if message.from_user.id == ADMIN:
        await reply_text(bot, message)
        return

    info = await bot.get_users(user_ids=message.from_user.id)
    reference_id = message.chat.id

    forwarded_message = await bot.forward_messages(
        chat_id=ADMIN,
        from_chat_id=message.chat.id,
        message_ids=[message.id]
    )

    logging.info(f"Forwarded message object: {forwarded_message}")

    if isinstance(forwarded_message, list):
        forwarded_message_id = forwarded_message[0].id
    else:
        forwarded_message_id = forwarded_message.id

    if forwarded_message_id:
        add_forwarded_message(reference_id, forwarded_message_id)
    else:
        logging.error("Failed to obtain forwarded message ID.")

@app.on_message(filters.private & filters.media)
async def pm_media(bot, message):
    if message.from_user.id in ADMIN_USER_IDS:
        await reply_media(bot, message)
        return

    info = await bot.get_users(user_ids=message.from_user.id)
    reference_id = message.chat.id

    forwarded_message = await bot.forward_messages(
        chat_id=ADMIN,
        from_chat_id=message.chat.id,
        message_ids=[message.id]
    )

    logging.info(f"Forwarded media object: {forwarded_message}")

    if isinstance(forwarded_message, list):
        forwarded_message_id = forwarded_message[0].id
    else:
        forwarded_message_id = forwarded_message.id

    if forwarded_message_id:
        add_forwarded_message(reference_id, forwarded_message_id)
    else:
        logging.error("Failed to obtain forwarded media ID.")

@app.on_message(filters.user(ADMIN_USER_IDS) & filters.text)
async def reply_text(bot, message):
    reference_id = None
    if message.reply_to_message:
        reference_id = get_reference_id(message.reply_to_message.id)
        logging.info(f"Replying to reference ID {reference_id} with message ID {message.reply_to_message.id}.")

    if reference_id:
        await bot.send_message(
            chat_id=reference_id,
            text=message.text
        )
        logging.info(f"Message sent to user ID {reference_id}.")
    else:
        await message.reply("Failed to find reference ID.")
        logging.error(f"Failed to find reference ID for text reply.")

@app.on_message(filters.user(ADMIN_USER_IDS) & filters.media)
async def reply_media(bot, message):
    reference_id = None
    if message.reply_to_message:
        reference_id = get_reference_id(message.reply_to_message.id)
        logging.info(f"Replying with media to reference ID {reference_id} with message ID {message.reply_to_message.id}.")

    if reference_id:
        await bot.copy_message(
            chat_id=reference_id,
            from_chat_id=message.chat.id,
            message_id=message.id,
            parse_mode=ParseMode.HTML
        )
        logging.info(f"Media copied to user ID {reference_id}.")
    else:
        await message.reply("Failed to find reference ID.")
        logging.error(f"Failed to find reference ID for media reply.")

app.run()
