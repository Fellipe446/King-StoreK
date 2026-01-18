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

# --- CONFIGURAÇÕES DE AMBIENTE ---
TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = 'database.json'
LOG_CHANNEL_ID = 1234567890  # <--- COLOQUE O ID DO SEU CANAL DE LOGS AQUI
COR_TECH = 0x00FFFF  # Ciano Neon
COR_ERRO = 0xFF0000  # Vermelho

def get_sp_time():
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

# --- BANCO DE DADOS ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": 1}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- INTERFACE: MODAL DE RESET HWID ---
class ResetModal(ui.Modal, title="⚙️ SECURITY: HWID RESET"):
    key_input = ui.TextInput(
        label="LICENSE KEY", 
        placeholder="Insira sua chave KING-XXXX...", 
        min_length=8, 
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        db = load_db()
        k_antiga = self.key_input.value.upper().strip()
        
        if k_antiga not in db["keys"]:
            embed = discord.Embed(title="❌ ACESSO NEGADO", description="Chave inválida ou inexistente.", color=COR_ERRO)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        info = db["keys"][k_antiga]
        nova_k = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nova_k] = {"hwid": None, "expira": info["expira"]}
        del db["keys"][k_antiga]
        save_db(db)

        embed = discord.Embed(title="♻️ HWID PURIFICADO", color=COR_TECH)
        embed.description = f"O vínculo de hardware foi resetado com sucesso.\n\n**NOVA CHAVE:** `{nova_k}`"
        embed.set_footer(text="A chave antiga foi deletada por segurança.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            dm = discord.Embed(title="💎 KING STORE - DADOS DE ACESSO", color=COR_TECH)
            dm.add_field(name="Sua Nova Key", value=f"```\n{nova_k}\n```")
            dm.set_footer(text="Guarde esta chave em local seguro.")
            await interaction.user.send(embed=dm)
        except: pass

class ResetView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="RESETAR HWID", style=discord.ButtonStyle.secondary, custom_id="reset_btn", emoji="♻️")
    async def reset(self, interaction, button): await interaction.response.send_modal(ResetModal())

# --- BOT SETUP ---
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
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="🛡️ King Store Security"))

# --- COMANDOS PROFISSIONAIS ---

@bot.tree.command(name="gerar", description="Gera licenças criptografadas")
@app_commands.choices(duracao=[
    app_commands.Choice(name="24 Horas", value=1),
    app_commands.Choice(name="30 Dias", value=30),
    app_commands.Choice(name="Vitalício", value=0)
])
async def gerarkey(interaction: discord.Interaction, duracao: app_commands.Choice[int], quantidade: int = 1):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Acesso restrito a administradores.", ephemeral=True)
    
    db = load_db()
    novas = []
    venc = "LIFETIME" if duracao.value == 0 else (get_sp_time() + datetime.timedelta(days=duracao.value)).strftime("%d/%m/%Y")
    
    for _ in range(quantidade):
        nk = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nk] = {"hwid": None, "expira": venc}
        novas.append(nk)
    save_db(db)
    
    embed = discord.Embed(title="📦 LOTE DE LICENÇAS GERADO", color=0x00FF7F)
    embed.add_field(name="👤 Responsável", value=interaction.user.mention, inline=True)
    embed.add_field(name="⏳ Validade", value=f"`{duracao.name}`", inline=True)
    embed.description = f"**CHAVES:**\n```\n" + "\n".join(novas) + "\n```"
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="painel", description="Envia o terminal de gerenciamento")
async def painel(interaction: discord.Interaction):
    db = load_db()
    status_sys = "🟢 OPERACIONAL" if db.get("script_status", 1) == 1 else "🔴 MANUTENÇÃO"
    
    embed = discord.Embed(title="🛡️ KING STORE | TERMINAL DE ACESSO", color=COR_TECH)
    embed.description = (
        "Gerencie seu acesso ao nosso sistema de scripts.\n\n"
        "**COMO USAR:**\n"
        "1. Utilize o comando `/infokey` para ver sua validade.\n"
        "2. Caso troque de PC, use o botão de **Reset HWID** abaixo.\n"
        "3. Sua licença é pessoal e intransferível."
    )
    embed.add_field(name="🛰️ Status do Sistema", value=f"```diff\n+ {status_sys}\n```", inline=False)
    embed.set_footer(text="A King Store monitora tentativas de invasão.")
    
    await interaction.channel.send(embed=embed, view=ResetView())
    await interaction.response.send_message("Painel enviado!", ephemeral=True)

# --- API E LOGS (COMUNICAÇÃO ROBLOX) ---
app = Flask(__name__)

async def send_api_log(title, fields, color):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=f"🛰️ API MONITOR | {title}", color=color, timestamp=datetime.datetime.now())
        for name, value in fields.items():
            embed.add_field(name=name, value=f"`{value}`", inline=True)
        bot.loop.create_task(channel.send(embed=embed))

@app.route('/auth')
def auth():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    db = load_db()
    
    if key not in db["keys"]:
        bot.loop.create_task(send_api_log("TENTATIVA INVÁLIDA", {"Key": key, "HWID": hwid}, COR_ERRO))
        return "Invalida", 404
    
    info = db["keys"][key]
    if info["hwid"] is None:
        db["keys"][key]["hwid"] = hwid
        save_db(db)
        bot.loop.create_task(send_api_log("NOVO VÍNCULO", {"Key": key, "Status": "Ativado"}, 0x00FF00))
        return "Vinculado", 200
    
    if info["hwid"] == hwid:
        return "Sucesso"
    else:
        bot.loop.create_task(send_api_log("CONFLITO DE HWID", {"Key": key, "User": "Tentativa de Bypass"}, COR_ERRO))
        return "HWID_Incorreto", 403

def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()
bot.run(TOKEN)
