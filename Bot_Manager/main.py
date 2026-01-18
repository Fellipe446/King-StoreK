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

# --- 🛰️ CONFIGURAÇÕES DE NÚCLEO (2026) ---
TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = 'database.json'
COR_TECH = 0x00FFFF          # Ciano Cyber
COR_ERRO = 0xFF2D2D          # Vermelho Neon
COR_SUCESSO = 0x00FF7F       # Verde Esmeralda

def get_sp_time():
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": "🟢 ONLINE", "blacklist": []}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- 🔐 INTERFACE: TERMINAL DE RESET HWID ---
class ResetModal(ui.Modal, title="🛠️ PROTOCOLO DE PURIFICAÇÃO"):
    key_input = ui.TextInput(label="SISTEMA DE LICENÇA", placeholder="INSIRA SUA KEY...", min_length=8)

    async def on_submit(self, interaction: discord.Interaction):
        db = load_db()
        key = self.key_input.value.upper().strip()
        if key not in db["keys"]:
            return await interaction.response.send_message("❌ **ERRO:** Chave não localizada.", ephemeral=True)
        
        info = db["keys"][key]
        nova_k = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nova_k] = {"hwid": None, "roblox_nick": info.get("roblox_nick"), "expira": info["expira"], "ativa": True}
        del db["keys"][key]
        save_db(db)

        embed = discord.Embed(title="♻️ RESET DE HARDWARE CONCLUÍDO", color=COR_SUCESSO)
        embed.description = "### ✅ Vínculo Purificado\n> Sua nova chave foi enviada para o seu **Privado (DM)**."
        embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try: await interaction.user.send(f"💎 **KING STORE - SEGURANÇA**\nNova Key: `{nova_k}`")
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

# --- 👑 COMANDOS DE GESTÃO ---

@bot.tree.command(name="gerar", description="⚙️ Gera novas licenças de acesso")
async def gerar(interaction: discord.Interaction, dias: int, quantidade: int = 1):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db(); novas = []
    venc = (get_sp_time() + datetime.timedelta(days=dias)).strftime("%d/%m/%Y")
    for _ in range(quantidade):
        nk = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nk] = {"hwid": None, "roblox_nick": None, "expira": venc, "ativa": True}
        novas.append(nk)
    save_db(db)
    
    lista_keys = "\n".join([f"• Código: `{k}`" for k in novas])
    embed = discord.Embed(title="🔑 LICENÇA GERADA COM SUCESSO", color=COR_SUCESSO)
    embed.description = (
        f"• **Quantidade:** {quantidade} Key{'s' if quantidade > 1 else ''}\n"
        f"{lista_keys}\n"
        f"• **Status:** 🟢 Ativa\n"
        f"• **Validade:** `{venc}`"
    )
    embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="cadastro", description="👤 Vincula seu Nick do Roblox à sua Key")
async def cadastro(interaction: discord.Interaction, key: str, nick: str):
    db = load_db()
    key = key.upper().strip()
    if key not in db["keys"]:
        return await interaction.response.send_message("❌ **ERRO:** Licença inexistente.", ephemeral=True)
    if db["keys"][key].get("roblox_nick"):
        return await interaction.response.send_message(f"⚠️ **ALERTA:** Key já vinculada ao nick `{db['keys'][key]['roblox_nick']}`", ephemeral=True)
    
    db["keys"][key]["roblox_nick"] = nick
    save_db(db)
    embed = discord.Embed(title="👤 VÍNCULO DE IDENTIDADE | KING STORE", color=COR_SUCESSO)
    embed.description = f"### ✅ Cadastro Finalizado\n• **Nick:** `{nick}`\n• **Status:** `AUTORIZADO`"
    embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="status", description="📡 Verifica a integridade do sistema")
async def status(interaction: discord.Interaction):
    db = load_db()
    st = db.get("script_status", "🟢 ONLINE")
    embed = discord.Embed(title="📡 DIAGNÓSTICO DE REDE | KING STORE", color=COR_TECH)
    embed.description = f"### 🛡️ Status do Ecossistema\n• **Script Lua:** `{st}`\n• **API Auth:** `🟢 OPERACIONAL`"
    embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setstatus", description="🔧 Altera o status público do Script")
async def setstatus(interaction: discord.Interaction, status: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    db["script_status"] = status
    save_db(db)
    await interaction.response.send_message(f"✅ **SISTEMA:** Status atualizado para: `{status}`", ephemeral=True)

@bot.tree.command(name="painelhwid", description="📟 Envia o Terminal de HWID")
async def painelhwid(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📟 CENTRAL DE LICENCIAMENTO | KING STORE", 
        description=(
            "### 🛠️ Protocolo de Gerenciamento\n"
            "Se você trocou de hardware ou formatou seu PC, utilize o terminal abaixo para resetar seu vínculo. "
            "**ATENÇÃO:** Ao clicar no botão, sua chave antiga será deletada e uma nova será enviada no seu Privado (DM).\n\n"
            "🛡️ *Proteção de dados ativada via King Security.*"
        ), 
        color=COR_TECH
    )
    embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
    await interaction.channel.send(embed=embed, view=ResetView())
    await interaction.response.send_message("✅ Painel Implantado.", ephemeral=True)

# --- 🕸️ API DE CONEXÃO ---
app = Flask(__name__)
@app.route('/auth')
def auth():
    key, hwid, nick = request.args.get('key'), request.args.get('hwid'), request.args.get('nick')
    db = load_db()
    if key not in db["keys"]: return "Invalida", 404
    info = db["keys"][key]
    if not info.get("roblox_nick"): return "FaltaCadastro", 403
    if info["roblox_nick"] != nick: return "NickIncorreto", 403
    if info["hwid"] is None:
        db["keys"][key]["hwid"] = hwid
        save_db(db); return "Vinculado", 200
    return "Sucesso" if info["hwid"] == hwid else "HWID_Incorreto"

def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()
bot.run(TOKEN)
