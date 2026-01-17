import discord
from discord import app_commands, ui
from flask import Flask, request
import json
import os
import threading
import random
import string
import datetime
import pytz
import re

# --- 1. CONFIGURAÇÃO ---
TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = 'database.json'
# Coloque o ID do canal onde você quer receber os LOGS de vendas e segurança
LOG_CHANNEL_ID = 123456789012345678  # <--- TROQUE PELO ID DO SEU CANAL DE LOGS

def get_sp_time():
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

# --- 2. BANCO DE DADOS ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": 1, "config": {"anti_invite": True}}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- 3. INTERFACE RESET HWID ---
class ResetModal(ui.Modal, title="♻️ Resetar HWID - King Store"):
    key_input = ui.TextInput(label="Sua Key Atual", placeholder="Digite sua key aqui...", min_length=8)

    async def on_submit(self, interaction: discord.Interaction):
        db = load_db()
        k_antiga = self.key_input.value.upper().strip()
        if k_antiga not in db["keys"]:
            return await interaction.response.send_message("❌ Key não encontrada!", ephemeral=True)
        
        info = db["keys"][k_antiga]
        nova_k = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        db["keys"][nova_k] = {"hwid": None, "expira": info["expira"]}
        del db["keys"][k_antiga]
        save_db(db)

        await interaction.response.send_message(f"✅ HWID Resetado! Sua nova key é: `{nova_k}`", ephemeral=True)
        try: await interaction.user.send(f"💎 **King Store**\nSua nova key: `{nova_k}`")
        except: pass

class ResetView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="Resetar HWID", style=discord.ButtonStyle.blurple, custom_id="reset_king")
    async def reset(self, interaction, button): await interaction.response.send_modal(ResetModal())

# --- 4. BOT SETUP ---
class KingBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        self.add_view(ResetView())
        await self.tree.sync()

bot = KingBot()

@bot.event
async def on_ready():
    print(f"🚀 King Store Online: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="Protegendo a King Store 💎"))

# --- 🛡️ SISTEMA DE PROTEÇÃO (ANTI-INVITE) ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # Detecta links de convite do Discord
    if "discord.gg/" in message.content.lower() or "discord.com/invite/" in message.content.lower():
        if not message.author.guild_permissions.administrator:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, não é permitido enviar convites aqui!", delete_after=5)
            
            # Log de Segurança
            log_ch = bot.get_channel(LOG_CHANNEL_ID)
            if log_ch:
                embed = discord.Embed(title="🛡️ Tentativa de Anti-Invite", color=discord.Color.red())
                embed.add_field(name="Usuário", value=message.author.name)
                embed.add_field(name="Conteúdo", value=f"||{message.content}||")
                await log_ch.send(embed=embed)

# --- 🔑 COMANDOS DE KEYS ---
@bot.tree.command(name="gerarkey", description="Gera chaves para o script")
@app_commands.choices(duracao=[
    app_commands.Choice(name="1 Dia", value=1),
    app_commands.Choice(name="30 Dias", value=30),
    app_commands.Choice(name="Permanente", value=0)
])
async def gerarkey(interaction: discord.Interaction, duracao: app_commands.Choice[int], quantidade: int = 1):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        
    db = load_db()
    novas = []
    for _ in range(quantidade):
        nk = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        venc = "PERMANENTE" if duracao.value == 0 else (get_sp_time() + datetime.timedelta(days=duracao.value)).strftime("%Y-%m-%d %H:%M:%S")
        db["keys"][nk] = {"hwid": None, "expira": venc}
        novas.append(nk)
    save_db(db)
    
    await interaction.response.send_message(f"💎 **Keys Geradas com Sucesso!**")
    await interaction.channel.send(f"```\n" + "\n".join(novas) + "\n```")

@bot.tree.command(name="painel_hwid", description="Envia o botão de reset")
async def painel(interaction: discord.Interaction):
    await interaction.channel.send("♻️ **Central de HWID**\nClique no botão abaixo para resetar seu vínculo.", view=ResetView())
    await interaction.response.send_message("Painel enviado!", ephemeral=True)

# --- 🌐 API FLASK (Logs de Autenticação) ---
app = Flask(__name__)
@app.route('/auth')
def auth():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    db = load_db()
    
    if key not in db["keys"]: return "Invalida", 404
    
    # Lógica de Logs no Discord via Thread para não travar a API
    def send_api_log(status):
        log_ch = bot.get_channel(LOG_CHANNEL_ID)
        if log_ch:
            cor = discord.Color.green() if "Sucesso" in status else discord.Color.orange()
            embed = discord.Embed(title="🔑 Log de Autenticação", color=cor)
            embed.add_field(name="Key", value=f"`{key}`")
            embed.add_field(name="Status", value=status)
            embed.add_field(name="HWID", value=f"`{hwid}`")
            # Usando bot.loop para enviar de dentro de uma thread
            bot.loop.create_task(log_ch.send(embed=embed))

    info = db["keys"][key]
    if info["hwid"] is None:
        db["keys"][key]["hwid"] = hwid
        save_db(db)
        send_api_log("✅ Primeiro Vínculo (Sucesso)")
        return "Vinculado", 200
    
    if info["hwid"] == hwid:
        send_api_log("✅ Login Realizado")
        return "Sucesso"
    else:
        send_api_log("❌ Tentativa de Login (HWID Incorreto)")
        return "HWID_Incorreto", 403

def run():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    threading.Thread(target=run).start()
    bot.run(TOKEN)
