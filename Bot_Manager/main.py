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

# --- 🛰️ CONFIGURAÇÕES ---
TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = 'database.json'
COR_SUCESSO = 0x00FF7F       
COR_TECH = 0x00FFFF          

def get_sp_time():
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": "🟢 ONLINE"}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- 🔐 SISTEMA DE RESET ---
class ResetModal(ui.Modal, title="🛠️ PROTOCOLO DE RESET"):
    key_input = ui.TextInput(label="SISTEMA DE LICENÇA", placeholder="INSIRA SUA KEY...", min_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        db = load_db()
        key = self.key_input.value.upper().strip()
        if key not in db["keys"]:
            return await interaction.response.send_message("❌ **ERRO:** Key inválida.", ephemeral=True)
        
        info = db["keys"][key]
        nova_k = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        db["keys"][nova_k] = {"hwid": None, "roblox_nick": info.get("roblox_nick"), "expira": info["expira"], "ativa": True}
        del db["keys"][key]
        save_db(db)

        embed = discord.Embed(title="♻️ RESET CONCLUÍDO", color=COR_SUCESSO, description="Sua nova chave foi enviada no seu **Privado (DM)**.")
        embed.set_footer(text="King Store © 2026")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try: await interaction.user.send(f"💎 **KING STORE**\nNova Key: `{nova_k}`")
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

# --- 👑 COMANDOS PADRONIZADOS ---

@bot.tree.command(name="gerar", description="⚙️ Gera novas licenças")
async def gerar(interaction: discord.Interaction, dias: int, quantidade: int = 1):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    novas = []
    venc = (get_sp_time() + datetime.timedelta(days=dias)).strftime("%d/%m/%Y")
    
    for _ in range(quantidade):
        nk = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        db["keys"][nk] = {"hwid": None, "roblox_nick": None, "expira": venc, "ativa": True}
        novas.append(nk)
    save_db(db)
    
    # Visual exatamente como você pediu:
    lista_keys = "\n".join([f"• Código: **{k}**" for k in novas])
    
    embed = discord.Embed(title="🔑 LICENÇA GERADA COM SUCESSO", color=COR_SUCESSO)
    embed.description = (
        f"• Quantidade: **{quantidade} Key**\n"
        f"{lista_keys}\n"
        f"• Status: 🟢 Ativa"
    )
    embed.set_footer(text=f"Validade: {venc} - King Store © 2026")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="cadastro", description="👤 Vincula Nick à Key")
async def cadastro(interaction: discord.Interaction, key: str, nick: str):
    db = load_db()
    key = key.upper().strip()
    if key not in db["keys"]:
        return await interaction.response.send_message("❌ **ERRO:** Key inexistente.", ephemeral=True)
    
    db["keys"][key]["roblox_nick"] = nick
    save_db(db)
    
    embed = discord.Embed(title="👤 CADASTRO REALIZADO", color=COR_SUCESSO)
    embed.description = (
        f"• Nick: **{nick}**\n"
        f"• Status: 🟢 Cadastrado com Sucesso"
    )
    embed.set_footer(text="King Store © 2026")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="painelhwid", description="📟 Envia o Terminal de HWID")
async def painelhwid(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📟 CENTRAL DE LICENCIAMENTO | KING STORE", 
        description=(
            "**Protocolo de Gerenciamento**\n\n"
            "Se você trocou de hardware ou formatou seu PC, utilize o terminal abaixo para resetar seu vínculo.\n\n"
            "**ATENÇÃO:**\n"
            "Ao clicar no botão, sua chave antiga será deletada e uma nova será enviada no seu **Privado (DM)**.\n\n"
            "🛡️ *Proteção de dados ativada via King Security.*"
        ), 
        color=COR_TECH
    )
    embed.set_footer(text="King Store © 2026 - Protocolo Criptografado")
    await interaction.channel.send(embed=embed, view=ResetView())
    await interaction.response.send_message("✅ Painel enviado.", ephemeral=True)

# --- 🕸️ API ---
app = Flask(__name__)
@app.route('/auth')
def auth():
    key, hwid, nick = request.args.get('key'), request.args.get('hwid'), request.args.get('nick')
    db = load_db()
    if key not in db["keys"]: return "Invalida", 404
    info = db["keys"][key]
    if info["roblox_nick"] != nick: return "NickIncorreto", 403
    if info["hwid"] is None:
        db["keys"][key]["hwid"] = hwid
        save_db(db); return "Vinculado", 200
    return "Sucesso" if info["hwid"] == hwid else "HWID_Incorreto"

def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()
bot.run(TOKEN)
