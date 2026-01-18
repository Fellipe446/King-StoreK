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
LOG_CHANNEL_ID = 123456789012345678 # <--- SUBSTITUA PELO ID DO SEU CANAL DE LOGS
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
            return await interaction.response.send_message("❌ Chave inválida!", ephemeral=True)
        
        info = db["keys"][key]
        nova_k = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nova_k] = {"hwid": None, "expira": info["expira"], "ativa": True}
        del db["keys"][key]
        save_db(db)

        embed = discord.Embed(title="♻️ HWID PURIFICADO", color=COR_TECH)
        embed.description = f"Vínculo resetado. Sua nova chave:\n`{nova_k}`"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try: await interaction.user.send(f"💎 **KING STORE**\nNova Key: `{nova_k}`")
        except: pass

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

# --- 5. COMANDOS ADMINISTRATIVOS ---

@bot.tree.command(name="gerar", description="Gera novas licenças")
@app_commands.choices(duracao=[app_commands.Choice(name="1 Dia", value=1), app_commands.Choice(name="30 Dias", value=30), app_commands.Choice(name="Vitalício", value=0)])
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

@bot.tree.command(name="deletar", description="Remove uma key do sistema")
async def deletar(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    key = key.upper().strip()
    if key in db["keys"]:
        del db["keys"][key]
        save_db(db)
        await interaction.response.send_message(f"✅ Key `{key}` deletada.")
    else: await interaction.response.send_message("❌ Não encontrada.", ephemeral=True)

@bot.tree.command(name="estender", description="Adiciona dias a uma key")
async def estender(interaction: discord.Interaction, key: str, dias: int):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    key = key.upper().strip()
    if key in db["keys"] and db["keys"][key]["expira"] != "LIFETIME":
        atual = datetime.datetime.strptime(db["keys"][key]["expira"], "%d/%m/%Y")
        nova = (atual + datetime.timedelta(days=dias)).strftime("%d/%m/%Y")
        db["keys"][key]["expira"] = nova
        save_db(db)
        await interaction.response.send_message(f"✅ `{key}` estendida para `{nova}`")
    else: await interaction.response.send_message("❌ Erro ao estender.", ephemeral=True)

@bot.tree.command(name="pausar", description="Bloqueia/Desbloqueia uma key")
async def pausar(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    key = key.upper().strip()
    if key in db["keys"]:
        db["keys"][key]["ativa"] = not db["keys"][key].get("ativa", True)
        save_db(db)
        status = "ATIVA" if db["keys"][key]["ativa"] else "PAUSADA"
        await interaction.response.send_message(f"🔒 `{key}` agora está **{status}**")

@bot.tree.command(name="infokey", description="Consulta auditoria da key")
async def infokey(interaction: discord.Interaction, key: str):
    db = load_db()
    key = key.upper().strip()
    if key not in db["keys"]: return await interaction.response.send_message("Inexistente.")
    data = db["keys"][key]
    embed = discord.Embed(title="🔍 INFO: " + key, color=COR_TECH)
    embed.add_field(name="HWID", value=f"`{data['hwid'] or 'Livre'}`")
    embed.add_field(name="Expira", value=f"`{data['expira']}`")
    embed.add_field(name="Status", value="🟢 Ativa" if data.get("ativa", True) else "🔴 Pausada")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="painel", description="Envia o painel de suporte")
async def painel(interaction: discord.Interaction):
    embed = discord.Embed(title="🛡️ CENTRAL KING STORE", description="Clique abaixo para resetar seu HWID em caso de troca de PC.", color=COR_TECH)
    await interaction.channel.send(embed=embed, view=ResetView())
    await interaction.response.send_message("Enviado.", ephemeral=True)

# --- 6. API DE COMUNICAÇÃO ROBLOX ---
app = Flask(__name__)

async def log_event(title, fields, color):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=title, color=color, timestamp=get_sp_time())
        for n, v in fields.items(): embed.add_field(name=n, value=f"`{v}`")
        bot.loop.create_task(channel.send(embed=embed))

@app.route('/auth')
def auth():
    key, hwid = request.args.get('key'), request.args.get('hwid')
    db = load_db()
    if key not in db["keys"]: return "Invalida", 404
    info = db["keys"][key]
    if not info.get("ativa", True): return "Pausada", 403
    if info["hwid"] is None:
        db["keys"][key]["hwid"] = hwid
        save_db(db)
        bot.loop.create_task(log_event("🆕 VÍNCULO", {"Key": key, "HWID": hwid}, 0x00FF00))
        return "Vinculado", 200
    return "Sucesso" if info["hwid"] == hwid else "HWID_Incorreto"

def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()
bot.run(TOKEN)
