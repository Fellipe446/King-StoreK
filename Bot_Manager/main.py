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
COR_ERRO = 0xFF2D2D

def get_sp_time():
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": "🟢 ONLINE"}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- 👤 INTERFACE DE CONFIRMAÇÃO DE CADASTRO ---
class ConfirmarCadastro(ui.View):
    def __init__(self, key, nick):
        super().__init__(timeout=60)
        self.key = key
        self.nick = nick

    @ui.button(label="CONFIRMAR", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        db = load_db()
        # Verificação dupla caso a key tenha sido usada enquanto o botão estava aberto
        if self.key not in db["keys"]:
            return await interaction.response.edit_message(content="❌ Erro: Key não encontrada.", view=None)
        
        db["keys"][self.key]["roblox_nick"] = self.nick
        save_db(db)

        embed = discord.Embed(title="👤 CADASTRO REALIZADO", color=COR_SUCESSO)
        embed.description = (
            f"• Nick Vinculado: **{self.nick}**\n"
            f"• Status: 🟢 Ativado com Sucesso\n\n"
            f"🛡️ *Sua licença agora está protegida e vinculada a este apelido.*"
        )
        embed.set_footer(text="King Store © 2026")
        await interaction.response.edit_message(embed=embed, view=None)

    @ui.button(label="CANCELAR", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="❌ Operação cancelada pelo usuário.", embed=None, view=None)

# --- 🔐 SISTEMA DE RESET ---
class ResetModal(ui.Modal, title="🛠️ PROTOCOLO DE RESET"):
    key_input = ui.TextInput(label="SISTEMA DE LICENÇA", placeholder="INSIRA SUA KEY...", min_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        db = load_db()
        key = self.key_input.value.upper().strip()
        if key not in db["keys"]:
            return await interaction.response.send_message("❌ **ERRO:** Key inválida.", ephemeral=True)
        
        info = db["keys"][key]
        nova_k = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nova_k] = {"hwid": None, "roblox_nick": info.get("roblox_nick"), "expira": info["expira"], "ativa": True}
        del db["keys"][key]
        save_db(db)

        embed = discord.Embed(title="♻️ RESET CONCLUÍDO", color=COR_SUCESSO, description="Sua nova chave foi enviada no seu **Privado (DM)**.")
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

# --- 👑 COMANDOS ---

@bot.tree.command(name="gerarkey", description="⚙️ Gera novas licenças")
@app_commands.choices(duracao=[
    app_commands.Choice(name="Minutos", value="minutos"),
    app_commands.Choice(name="Horas", value="horas"),
    app_commands.Choice(name="Dias", value="dias"),
    app_commands.Choice(name="Semanas", value="semanas"),
    app_commands.Choice(name="Meses", value="meses"),
    app_commands.Choice(name="Vitalício", value="vitalicio")
])
async def gerarkey(interaction: discord.Interaction, duracao: app_commands.Choice[str], tempo: int, quantidade: int):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db(); novas = []; agora = get_sp_time()

    if duracao.value == "minutos": exp = agora + datetime.timedelta(minutes=tempo)
    elif duracao.value == "horas": exp = agora + datetime.timedelta(hours=tempo)
    elif duracao.value == "dias": exp = agora + datetime.timedelta(days=tempo)
    elif duracao.value == "semanas": exp = agora + datetime.timedelta(weeks=tempo)
    elif duracao.value == "meses": exp = agora + datetime.timedelta(days=tempo*30)
    else: exp = None 

    data_f = exp.strftime("%d/%m/%Y %H:%M") if exp else "VITALÍCIO"
    for _ in range(quantidade):
        nk = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nk] = {"hwid": None, "roblox_nick": None, "expira": data_f, "ativa": True}
        novas.append(nk)
    save_db(db)
    
    lista = "\n".join([f"• Código: **{k}**" for k in novas])
    embed = discord.Embed(title="🔑 LICENÇA GERADA COM SUCESSO", color=COR_SUCESSO)
    embed.description = f"• Quantidade: **{quantidade} Key**\n{lista}\n• Status: 🟢 Ativa"
    embed.set_footer(text=f"Duração: {tempo} {duracao.name} | Expira: {data_f}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="cadastro", description="👤 Vincula seu apelido (Nick) à Key")
async def cadastro(interaction: discord.Interaction, key: str, nick: str):
    db = load_db()
    key = key.upper().strip()
    
    if key not in db["keys"]:
        return await interaction.response.send_message("❌ **ERRO:** Esta Key não existe no sistema.", ephemeral=True)
    
    if db["keys"][key].get("roblox_nick"):
        return await interaction.response.send_message(f"⚠️ **ALERTA:** Esta Key já está vinculada ao nick `{db['keys'][key]['roblox_nick']}`.", ephemeral=True)

    # Painel de Confirmação
    embed = discord.Embed(title="🛡️ CONFIRMAÇÃO DE IDENTIDADE", color=COR_TECH)
    embed.description = (
        f"Você está prestes a vincular sua licença ao apelido abaixo:\n\n"
        f"• Apelido: **{nick}**\n\n"
        f"**Tem certeza que este é o apelido correto da sua conta?**\n"
        f"*Não será possível alterar sem o suporte.*"
    )
    
    view = ConfirmarCadastro(key, nick)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="infokey", description="🔍 Consulta detalhes de uma licença")
async def infokey(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db(); key = key.upper().strip()
    if key not in db["keys"]: return await interaction.response.send_message("❌ Inexistente.", ephemeral=True)
    d = db["keys"][key]
    embed = discord.Embed(title="🔍 DETALHES", color=COR_TECH)
    embed.description = f"• Key: `{key}`\n• Nick: `{d['roblox_nick'] or 'Livre'}`\n• HWID: `{d['hwid'] or 'Vazio'}`\n• Expira: `{d['expira']}`"
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="status", description="📡 Verifica o sistema")
async def status(interaction: discord.Interaction):
    db = load_db(); st = db.get("script_status", "🟢 ONLINE")
    await interaction.response.send_message(embed=discord.Embed(title="📡 DIAGNÓSTICO", description=f"• Script: `{st}`\n• API: `🟢 OPERACIONAL`", color=COR_TECH))

@bot.tree.command(name="painelhwid", description="📟 Envia o Terminal de Reset")
async def painelhwid(interaction: discord.Interaction):
    embed = discord.Embed(title="📟 CENTRAL KING STORE", color=COR_TECH, description="**Protocolo de Gerenciamento**\nReset seu HWID abaixo.\n\n🛡️ *King Security*")
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
        db["keys"][key]["hwid"] = hwid; save_db(db); return "Vinculado", 200
    return "Sucesso" if info["hwid"] == hwid else "HWID_Incorreto"

def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()
bot.run(TOKEN)
