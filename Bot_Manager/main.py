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

# --- 1. CONFIGURAÇÕES TÉCNICAS ---
TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = 'database.json'
LOG_CHANNEL_ID = 123456789012345678 # <--- COLOQUE O ID DO SEU CANAL DE LOGS AQUI
COR_TECH = 0x00FFFF # Ciano Neon
COR_ERRO = 0xFF0000 # Vermelho
COR_SUCESSO = 0x00FF7F # Verde

def get_sp_time():
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

# --- 2. GESTÃO DE DADOS ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": 1}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- 3. INTERFACE DE RESET (HWID) ---
class ResetModal(ui.Modal, title="⚙️ PROTOCOLO: RESET HWID"):
    key_input = ui.TextInput(label="LICENSE KEY", placeholder="KING-XXXX...", min_length=8)

    async def on_submit(self, interaction: discord.Interaction):
        db = load_db()
        key = self.key_input.value.upper().strip()
        if key not in db["keys"]:
            return await interaction.response.send_message("❌ Chave inválida ou inexistente!", ephemeral=True)
        
        info = db["keys"][key]
        if not info.get("ativa", True):
            return await interaction.response.send_message("❌ Esta chave está pausada e não pode ser resetada.", ephemeral=True)

        nova_k = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nova_k] = {"hwid": None, "expira": info["expira"], "ativa": True}
        del db["keys"][key]
        save_db(db)

        embed = discord.Embed(title="♻️ HWID PURIFICADO", color=COR_TECH)
        embed.description = f"Vínculo resetado com sucesso.\n\nSua nova chave de acesso:\n`{nova_k}`"
        embed.set_footer(text="A chave antiga foi deletada por segurança.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try: 
            await interaction.user.send(f"💎 **KING STORE - NOVO ACESSO**\nGuarde sua nova Key: `{nova_k}`")
        except: 
            pass

class ResetView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="RESETAR HWID", style=discord.ButtonStyle.secondary, custom_id="rst_btn", emoji="♻️")
    async def reset(self, interaction, button): await interaction.response.send_modal(ResetModal())

# --- 4. ENGINE DO BOT ---
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

# --- 5. COMANDOS ADMINISTRATIVOS ---

@bot.tree.command(name="gerar", description="Gera novas licenças para clientes")
@app_commands.choices(duracao=[
    app_commands.Choice(name="1 Dia", value=1), 
    app_commands.Choice(name="30 Dias", value=30), 
    app_commands.Choice(name="Vitalício", value=0)
])
async def gerar(interaction: discord.Interaction, duracao: app_commands.Choice[int], quantidade: int = 1):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    novas = []
    venc = "LIFETIME" if duracao.value == 0 else (get_sp_time() + datetime.timedelta(days=duracao.value)).strftime("%d/%m/%Y")
    for _ in range(quantidade):
        nk = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nk] = {"hwid": None, "expira": venc, "ativa": True}
        novas.append(nk)
    save_db(db)
    embed = discord.Embed(title="📦 LOTE GERADO", description=f"```\n" + "\n".join(novas) + "\n```", color=COR_SUCESSO)
    embed.add_field(name="Validade", value=duracao.name)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="deletar", description="Remove uma key do banco de dados")
async def deletar(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    key = key.upper().strip()
    if key in db["keys"]:
        del db["keys"][key]
        save_db(db)
        await interaction.response.send_message(f"✅ Licença `{key}` deletada com sucesso.")
    else: await interaction.response.send_message("❌ Chave não encontrada.", ephemeral=True)

@bot.tree.command(name="estender", description="Adiciona dias extras a uma key existente")
async def estender(interaction: discord.Interaction, key: str, dias: int):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    key = key.upper().strip()
    if key in db["keys"] and db["keys"][key]["expira"] != "LIFETIME":
        atual = datetime.datetime.strptime(db["keys"][key]["expira"], "%d/%m/%Y")
        nova = (atual + datetime.timedelta(days=dias)).strftime("%d/%m/%Y")
        db["keys"][key]["expira"] = nova
        save_db(db)
        await interaction.response.send_message(f"✅ Prazo de `{key}` estendido para `{nova}`")
    else: await interaction.response.send_message("❌ Não é possível estender (Key Vitalícia ou inexistente).", ephemeral=True)

@bot.tree.command(name="pausar", description="Bloqueia temporariamente o acesso de uma key")
async def pausar(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    key = key.upper().strip()
    if key in db["keys"]:
        db["keys"][key]["ativa"] = not db["keys"][key].get("ativa", True)
        save_db(db)
        status = "ATIVA" if db["keys"][key]["ativa"] else "PAUSADA"
        await interaction.response.send_message(f"🔒 A chave `{key}` agora está **{status}**.")

@bot.tree.command(name="infokey", description="Consulta auditoria e dados de uma licença")
async def infokey(interaction: discord.Interaction, key: str):
    db = load_db()
    key = key.upper().strip()
    if key not in db["keys"]: return await interaction.response.send_message("❌ Key inexistente.", ephemeral=True)
    data = db["keys"][key]
    embed = discord.Embed(title="🔍 AUDITORIA: " + key, color=COR_TECH)
    embed.add_field(name="💻 HWID VINCULADO", value=f"`{data['hwid'] or 'Aguardando uso'}`", inline=False)
    embed.add_field(name="📅 EXPIRAÇÃO", value=f"`{data['expira']}`", inline=True)
    embed.add_field(name="🛡️ STATUS", value="🟢 Ativa" if data.get("ativa", True) else "🔴 Pausada", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="painelhwid", description="Envia o painel de gerenciamento de HWID")
async def painelhwid(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡️ CENTRAL DE LICENÇAS | KING STORE", 
        description=(
            "Precisa trocar de computador ou resetar seu vínculo?\n\n"
            "**Instruções:**\n"
            "1. Clique no botão abaixo.\n"
            "2. Insira sua Key atual.\n"
            "3. O bot enviará uma **Nova Key** no seu PV."
        ), 
        color=COR_TECH
    )
    embed.set_footer(text="Segurança King Store")
    await interaction.channel.send(embed=embed, view=ResetView())
    await interaction.response.send_message("Painel gerado!", ephemeral=True)

# --- 6. API DE COMUNICAÇÃO ROBLOX ---
app = Flask(__name__)

async def log_event(title, fields, color):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=title, color=color, timestamp=get_sp_time())
        for n, v in fields.items(): embed.add_field(name=n, value=f"`{v}`", inline=True)
        bot.loop.create_task(channel.send(embed=embed))

@app.route('/auth')
def auth():
    key, hwid = request.args.get('key'), request.args.get('hwid')
    db = load_db()
    if key not in db["keys"]: 
        return "Invalida", 404
    
    info = db["keys"][key]
    if not info.get("ativa", True): 
        return "Pausada", 403
    
    if info["hwid"] is None:
        db["keys"][key]["hwid"] = hwid
        save_db(db)
        bot.loop.create_task(log_event("🆕 VÍNCULO DETECTADO", {"Key": key, "Dispositivo": hwid}, 0x00FF00))
        return "Vinculado", 200
    
    if info["hwid"] == hwid:
        return "Sucesso"
    else:
        bot.loop.create_task(log_event("⚠️ TENTATIVA DE BYPASS", {"Key": key, "HWID Tentado": hwid}, COR_ERRO))
        return "HWID_Incorreto", 403

def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()
bot.run(TOKEN)
