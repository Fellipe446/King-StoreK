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

# --- 🛰️ CONFIGURAÇÕES DE NÚCLEO ---
TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = 'database.json'
LOG_CHANNEL_ID = 1234567890  # <--- COLOQUE O ID DO SEU CANAL DE LOGS
COR_TECH = 0x00FFFF          # Ciano Cyber
COR_ERRO = 0xFF2D2D          # Vermelho Neon
COR_SUCESSO = 0x00FF7F       # Verde Esmeralda

def get_sp_time():
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

# --- 💾 SISTEMA DE ARQUIVOS ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": 1}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- 🔐 INTERFACE: TERMINAL DE RESET ---
class ResetModal(ui.Modal, title="🛠️ PROTOCOLO DE PURIFICAÇÃO"):
    key_input = ui.TextInput(
        label="SISTEMA DE LICENÇA", 
        placeholder="INSIRA SUA KEY KING-XXXX...", 
        min_length=8,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        db = load_db()
        key = self.key_input.value.upper().strip()
        
        if key not in db["keys"]:
            embed = discord.Embed(title="⚠️ ACESSO NEGADO", description="Chave não localizada no banco de dados.", color=COR_ERRO)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        info = db["keys"][key]
        if not info.get("ativa", True):
            return await interaction.response.send_message("🚨 **ERRO:** Esta licença encontra-se bloqueada.", ephemeral=True)

        nova_k = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nova_k] = {"hwid": None, "expira": info["expira"], "ativa": True}
        del db["keys"][key]
        save_db(db)

        embed = discord.Embed(title="♻️ HARDWARE RESETADO", color=COR_SUCESSO)
        embed.description = (
            "### ✅ Vínculo de Hardware Limpo\n"
            "O sistema gerou uma nova credencial criptografada para você.\n\n"
            f"🔑 **NOVA KEY:** `{nova_k}`"
        )
        embed.set_footer(text="A chave antiga foi incinerada pelo sistema.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            await interaction.user.send(f"💎 **KING STORE - SECURITY**\nSua nova credencial é: `{nova_k}`")
        except: pass

class ResetView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="RESETAR HWID", style=discord.ButtonStyle.danger, custom_id="rst_btn", emoji="⚙️")
    async def reset(self, interaction, button): await interaction.response.send_modal(ResetModal())

# --- 🤖 NÚCLEO DO BOT ---
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
    print(f"✅ SISTEMA OPERACIONAL: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="🛡️ Protegendo King Store"))

# --- 👑 COMANDOS ADMINISTRATIVOS DE ELITE ---

@bot.tree.command(name="gerar", description="⚙️ Gera novas licenças de acesso")
@app_commands.choices(duracao=[
    app_commands.Choice(name="⏳ 24 Horas", value=1), 
    app_commands.Choice(name="🗓️ 30 Dias", value=30), 
    app_commands.Choice(name="💎 Vitalício", value=0)
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
    embed = discord.Embed(title="📦 LOTE DE PRODUÇÃO LIBERADO", color=COR_SUCESSO)
    embed.add_field(name="🛰️ Validade", value=f"`{duracao.name}`", inline=True)
    embed.add_field(name="👥 Quantidade", value=f"`{quantidade}`", inline=True)
    embed.description = f"### 🔑 LICENÇAS GERADAS:\n```\n" + "\n".join(novas) + "\n```"
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="deletar", description="🗑️ Remove uma licença do banco de dados")
async def deletar(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    key = key.upper().strip()
    if key in db["keys"]:
        del db["keys"][key]
        save_db(db)
        await interaction.response.send_message(f"✅ **SISTEMA:** Licença `{key}` deletada com sucesso.", ephemeral=True)
    else: await interaction.response.send_message("❌ **ERRO:** Chave inexistente.", ephemeral=True)

@bot.tree.command(name="estender", description="⏳ Adiciona tempo extra a uma licença")
async def estender(interaction: discord.Interaction, key: str, dias: int):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    key = key.upper().strip()
    if key in db["keys"] and db["keys"][key]["expira"] != "LIFETIME":
        atual = datetime.datetime.strptime(db["keys"][key]["expira"], "%d/%m/%Y")
        nova = (atual + datetime.timedelta(days=dias)).strftime("%d/%m/%Y")
        db["keys"][key]["expira"] = nova
        save_db(db)
        await interaction.response.send_message(f"✅ **SISTEMA:** Licença `{key}` estendida para `{nova}`.", ephemeral=True)
    else: await interaction.response.send_message("❌ **ERRO:** Não é possível alterar esta licença.", ephemeral=True)

@bot.tree.command(name="pausar", description="🔒 Bloqueia ou desbloqueia uma licença")
async def pausar(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    key = key.upper().strip()
    if key in db["keys"]:
        db["keys"][key]["ativa"] = not db["keys"][key].get("ativa", True)
        save_db(db)
        st = "🟢 ATIVA" if db["keys"][key]["ativa"] else "🔴 PAUSADA"
        await interaction.response.send_message(f"🛡️ **SISTEMA:** Chave `{key}` agora está **{st}**.", ephemeral=True)

@bot.tree.command(name="infokey", description="🔍 Consulta auditoria completa de uma key")
async def infokey(interaction: discord.Interaction, key: str):
    db = load_db()
    key = key.upper().strip()
    if key not in db["keys"]: return await interaction.response.send_message("❌ **ERRO:** Key não encontrada.", ephemeral=True)
    
    data = db["keys"][key]
    embed = discord.Embed(title="🔍 AUDITORIA DE SEGURANÇA", color=COR_TECH)
    embed.add_field(name="🔑 CHAVE", value=f"`{key}`", inline=False)
    embed.add_field(name="💻 DISPOSITIVO (HWID)", value=f"```\n{data['hwid'] or 'Aguardando Login...'}\n```", inline=False)
    embed.add_field(name="📅 EXPIRAÇÃO", value=f"`{data['expira']}`", inline=True)
    embed.add_field(name="🛡️ STATUS", value="✅ Operacional" if data.get("ativa", True) else "❌ Bloqueada", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="painelhwid", description="📟 Envia o Terminal de HWID para clientes")
async def painelhwid(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📟 CENTRAL DE LICENCIAMENTO | KING STORE", 
        description=(
            "### 🛠️ Protocolo de Gerenciamento\n"
            "Se você trocou de hardware ou formatou seu PC, utilize o terminal abaixo para resetar seu vínculo.\n\n"
            "**⚠️ ATENÇÃO:**\n"
            "> Ao clicar no botão, sua chave antiga será deletada e uma nova será enviada no seu **Privado (DM)**.\n\n"
            "🛡️ *Proteção de dados ativada via King Security.*"
        ), 
        color=COR_TECH
    )
    embed.set_image(url="https://i.imgur.com/wVdYq8p.png") # Opcional: Banner decorativo
    embed.set_footer(text="King Store © 2024 - Protocolo Criptografado")
    await interaction.channel.send(embed=embed, view=ResetView())
    await interaction.response.send_message("✅ Terminal de Comando implantado!", ephemeral=True)

# --- 🕸️ API DE CONEXÃO (ROBLOX <-> BOT) ---
app = Flask(__name__)

async def log_event(title, fields, color):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=f"📡 LOG: {title}", color=color, timestamp=get_sp_time())
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
        bot.loop.create_task(log_event("🆕 NOVO ACESSO", {"Key": key, "HWID": hwid}, COR_SUCESSO))
        return "Vinculado", 200
    
    if info["hwid"] == hwid:
        return "Sucesso"
    else:
        bot.loop.create_task(log_event("⚠️ TENTATIVA DE INVASÃO", {"Key": key, "HWID_Tentado": hwid}, COR_ERRO))
        return "HWID_Incorreto", 403

def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()
bot.run(TOKEN)
