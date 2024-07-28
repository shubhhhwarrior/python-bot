from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo import MongoClient

# Initialize MongoDB client
mongo_client = MongoClient("mongodb+srv://tanjiro1564:tanjiro1564@cluster0.pp5yz4e.mongodb.net/?retryWrites=true&w=majority")  # Update with your MongoDB URI if needed
db = mongo_client["bot_database"]
users_collection = db["users"]

# Initialize the bot
app = Client(
    "my_bot",
    api_id="16542582",
    api_hash="c75e00f0ac7ce6f3273e073cb7f06ec2",
    bot_token="6451319497:AAFY-VXBYFX1zph0u9bj-NxvjWDth9DqYBg"
)

# Admin user ID
ADMIN_USER_ID = 5527170635  # Replace with the actual admin user ID

def add_user_to_db(user_id, username):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"username": username}},
        upsert=True
    )

def get_total_users():
    return users_collection.count_documents({})

@app.on_message(filters.command("start"))
async def start(client, message):
    mention = message.from_user.mention
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "No Username"
    
    # Add user info to the database
    add_user_to_db(user_id, username)
    
    # Define the inline keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴀʙᴏᴜᴛ", url="https://t.me/about_shubhhh")]
    ])
    
    # Send the welcome message with the inline button
    await message.reply(
        f"ʜᴇʟʟᴏ ᴛʜᴇʀᴇ {mention},\n\nᴛʜɪs ɪs ᴘᴇʀsᴏɴᴀʟ ᴀssɪsᴛᴀɴᴛ ᴏғ sʜᴜʙʜʜʜ 🇮🇳!\n\n ʏᴏᴜ ᴄᴀɴ ᴄᴏɴᴛᴀᴄᴛ ᴍʏ ᴍᴀsᴛᴇʀ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ!!\n\nᴅʀᴏᴘ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ʜᴇʀᴇ, ɪ ᴡɪʟʟ ᴅᴇʟɪᴠᴇʀ ɪᴛ ᴛᴏ ᴍᴀsᴛᴇʀ.😊",
        reply_markup=keyboard
    )

@app.on_message(filters.command("stats"))
async def total_users(client, message):
    total = get_total_users()
    await message.reply(f"Total number of users: {total}")

@app.on_message(filters.command("broadcast"))
async def broadcast_command(client, message):
    try:
        msg_text = message.text.split("/broadcast ", 1)[1]
    except IndexError:
        await message.reply("Please provide a message to broadcast using the command: /broadcast <message>")
        return

    chat_ids = ["-1002192186787", "5527170635"]  # Example chat IDs list

    success_count = 0
    failed_count = 0
    group_count = 0
    channel_count = 0

    for chat_id in chat_ids:
        try:
            chat = await client.get_chat(chat_id)
            chat_type = chat.type
            if chat_type == "group":
                group_count += 1
            elif chat_type == "channel":
                channel_count += 1
            await client.send_message(chat_id, msg_text)
            success_count += 1
        except Exception as e:
            print(f"Error sending message to {chat_id}: {e}")
            failed_count += 1

    report_text = (f"Broadcast complete!\n"
                   f"Successful: {success_count}\n"
                   f"Failed: {failed_count}\n"
                   f"Groups: {group_count}\n"
                   f"Channels: {channel_count}")
    await message.reply(report_text)

# Forward client messages to admin
@app.on_message(filters.private & ~filters.command(["start", "stats", "broadcast"]))
async def forward_to_admin(client, message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "No Username"
    text = message.text if message.text else "No text content"

    forward_text = f"Message from {username} (ID: {user_id}):\n\n{text}"
    await client.send_message(ADMIN_USER_ID, forward_text)

    # Inform the user that their message has been forwarded
    await message.reply("Your message has been forwarded to the admin.")

# Allow admin to reply to client
@app.on_message(filters.private & filters.reply & filters.user(ADMIN_USER_ID))
async def admin_reply(client, message):
    if message.reply_to_message:
        # Extract the original message text from the forwarded message
        original_message_text = message.reply_to_message.text
        try:
            # Extract user ID from the forwarded message
            user_id = int(original_message_text.split("ID: ")[1].split("):")[0])
            reply_text = message.text

            # Send the reply to the original user
            await client.send_message(user_id, f"Reply from admin:\n\n{reply_text}")
        except (IndexError, ValueError):
            await message.reply("Failed to extract user ID from the forwarded message.")

# Command for admin to reply to a user by ID
@app.on_message(filters.command("reply") & filters.user(ADMIN_USER_ID))
async def reply_command(client, message):
    try:
        command, user_id, reply_text = message.text.split(" ", 2)
        user_id = int(user_id)
        await client.send_message(user_id, f"Reply from admin:\n\n{reply_text}")
        await message.reply("Message sent successfully.")
    except ValueError:
        await message.reply("Invalid command format. Use: /reply <user_id> <message>")
    except Exception as e:
        await message.reply(f"Failed to send message: {e}")

# Run the bot
app.run()
