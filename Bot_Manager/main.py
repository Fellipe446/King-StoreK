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
COR_TECH = 0x00FFFF          # Ciano Cyber
COR_ERRO = 0xFF2D2D          # Vermelho Neon
COR_SUCESSO = 0x00FF7F       # Verde Esmeralda

def get_sp_time():
    """Retorna o horário atual de Brasília."""
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

# --- 💾 SISTEMA DE DADOS ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": "🟢 ONLINE"}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- 🔐 INTERFACE: TERMINAL DE RESET HWID ---
class ResetModal(ui.Modal, title="🛠️ PROTOCOLO DE PURIFICAÇÃO"):
    key_input = ui.TextInput(
        label="SISTEMA DE LICENÇA", 
        placeholder="INSIRA SUA CREDENCIAL KING-XXXX...", 
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
        nova_k = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Migração de dados para a nova chave
        db["keys"][nova_k] = {
            "hwid": None, 
            "roblox_nick": info.get("roblox_nick"), 
            "expira": info["expira"], 
            "ativa": True
        }
        del db["keys"][key]
        save_db(db)

        embed = discord.Embed(title="♻️ RESET DE HARDWARE CONCLUÍDO", color=COR_SUCESSO)
        embed.description = (
            "### ✅ Vínculo Purificado\n"
            "> Sua nova chave de acesso foi gerada e enviada para o seu **Privado (DM)**.\n\n"
            "**Protocolo:** `RESET_SUCCESS`"
        )
        embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try: 
            await interaction.user.send(f"💎 **KING STORE - SEGURANÇA**\nSua nova credencial exclusiva: `{nova_k}`")
        except: 
            pass

class ResetView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="RESETAR HWID", style=discord.ButtonStyle.danger, custom_id="rst_btn", emoji="⚙️")
    async def reset(self, interaction, button): 
        await interaction.response.send_modal(ResetModal())

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
    print(f"✅ SISTEMA KING STORE ONLINE: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="🛡️ King Security 2026"))

# --- 👑 COMANDOS DE ELITE (GERENCIAMENTO) ---

@bot.tree.command(name="cadastro", description="👤 Vincula seu Nick do Roblox à sua Key")
async def cadastro(interaction: discord.Interaction, key: str, nick: str):
    db = load_db()
    key = key.upper().strip()
    
    if key not in db["keys"]:
        return await interaction.response.send_message("❌ **ERRO:** Licença inexistente no sistema.", ephemeral=True)
    
    if db["keys"][key].get("roblox_nick"):
        return await interaction.response.send_message(f"⚠️ **ALERTA:** Esta Key já possui um nick vinculado: `{db['keys'][key]['roblox_nick']}`", ephemeral=True)
    
    db["keys"][key]["roblox_nick"] = nick
    save_db(db)
    
    embed = discord.Embed(title="👤 VÍNCULO DE IDENTIDADE | KING STORE", color=COR_SUCESSO)
    embed.description = (
        f"### ✅ Cadastro Finalizado\n"
        f"A licença foi vinculada com sucesso ao usuário indicado.\n\n"
        f"**Nick Cadastrado:** `{nick}`\n"
        f"**Status:** `AUTORIZADO`"
    )
    embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="status", description="📡 Verifica a integridade da rede")
async def status(interaction: discord.Interaction):
    db = load_db()
    st = db.get("script_status", "🟢 ONLINE")
    embed = discord.Embed(title="📡 DIAGNÓSTICO DE REDE | KING STORE", color=COR_TECH)
    embed.description = (
        f"### 🛡️ Status do Ecossistema\n"
        f"**Script Lua:** `{st}`\n"
        f"**API Auth:** `🟢 OPERACIONAL`\n"
        f"**Banco de Dados:** `CONECTADO`"
    )
    embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="gerar", description="⚙️ Gera novas licenças mestre")
async def gerar(interaction: discord.Interaction, dias: int, quantidade: int = 1):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db(); novas = []
    venc = (get_sp_time() + datetime.timedelta(days=dias)).strftime("%d/%m/%Y")
    
    for _ in range(quantidade):
        nk = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nk] = {"hwid": None, "roblox_nick": None, "expira": venc, "ativa": True}
        novas.append(nk)
    
    save_db(db)
    embed = discord.Embed(title="📦 LOTE DE LICENÇAS | KING STORE", color=COR_SUCESSO)
    embed.description = f"### ✅ Produção Concluída\n```\n" + "\n".join(novas) + "\n```\n**Validade:** `{dias} Dias`"
    embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="painelhwid", description="📟 Envia o Terminal de HWID")
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
    embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
    await interaction.channel.send(embed=embed, view=ResetView())
    await interaction.response.send_message("✅ Painel Implantado.", ephemeral=True)

# --- 🕸️ API DE CONEXÃO (AUTH) ---
app = Flask(__name__)

@app.route('/auth')
def auth():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    nick = request.args.get('nick')
    
    db = load_db()
    if key not in db["keys"]: return "Invalida", 404
    
    info = db["keys"][key]
    if not info.get("roblox_nick"): return "FaltaCadastro", 403
    if info["roblox_nick"] != nick: return "NickIncorreto", 403
    
    if info["hwid"] is None:
        db["keys"][key]["hwid"] = hwid
        save_db(db)
        return "Vinculado", 200
    
    return "Sucesso" if info["hwid"] == hwid else "HWID_Incorreto"

def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()
bot.run(TOKEN)
