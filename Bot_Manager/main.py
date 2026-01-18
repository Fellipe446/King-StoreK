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
LOG_CHANNEL_ID = 1234567890  # <--- COLOQUE O ID DO SEU CANAL DE LOGS AQUI
COR_TECH = 0x00FFFF          # Ciano Cyber
COR_ERRO = 0xFF2D2D          # Vermelho Neon
COR_SUCESSO = 0x00FF7F       # Verde Esmeralda

def get_sp_time():
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

# --- 💾 SISTEMA DE ARQUIVOS ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": "ONLINE"}, f)
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
            return await interaction.response.send_message("❌ Chave inválida!", ephemeral=True)
        
        info = db["keys"][key]
        nova_k = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nova_k] = {"hwid": None, "expira": info["expira"], "ativa": True}
        del db["keys"][key]
        save_db(db)
        await interaction.response.send_message(f"♻️ HWID Resetado! Nova Key enviada na DM.", ephemeral=True)
        try: await interaction.user.send(f"🔑 Nova Key: `{nova_k}`")
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

# --- 👑 COMANDOS ADMINISTRATIVOS ---

@bot.tree.command(name="status", description="📡 Verifica a integridade do sistema e API")
async def status(interaction: discord.Interaction):
    db = load_db()
    uptime = "ESTÁVEL"
    script_st = db.get("script_status", "ONLINE")
    
    embed = discord.Embed(title="🛰️ DIAGNÓSTICO DE SISTEMA", color=COR_TECH)
    embed.add_field(name="🌐 Servidor API", value="```diff\n+ OPERACIONAL\n```", inline=True)
    embed.add_field(name="📜 Script Lua", value=f"```diff\n+ {script_st}\n```", inline=True)
    embed.add_field(name="🗄️ Banco de Dados", value=f"```\n{len(db['keys'])} Chaves Ativas\n```", inline=False)
    embed.set_footer(text=f"Check realizado às {get_sp_time().strftime('%H:%M:%S')}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="keylist", description="📋 Lista todas as chaves filtradas por uso")
@app_commands.choices(filtro=[
    app_commands.Choice(name="Não Usadas (Sem HWID)", value="disponivel"),
    app_commands.Choice(name="Usadas (Com HWID)", value="usada"),
    app_commands.Choice(name="Todas", value="todas")
])
async def keylist(interaction: discord.Interaction, filtro: app_commands.Choice[str]):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    keys = db["keys"]
    
    texto = ""
    contador = 0
    
    for k, v in keys.items():
        hwid_vinculado = v.get("hwid")
        
        if filtro.value == "disponivel" and hwid_vinculado is None:
            texto += f"🔹 `{k}` | Exp: `{v['expira']}`\n"
            contador += 1
        elif filtro.value == "usada" and hwid_vinculado is not None:
            texto += f"🔸 `{k}` | PC: `{hwid_vinculado[:10]}...`\n"
            contador += 1
        elif filtro.value == "todas":
            status_emoji = "🔸" if hwid_vinculado else "🔹"
            texto += f"{status_emoji} `{k}` | Exp: `{v['expira']}`\n"
            contador += 1

    if not texto: texto = "Nenhuma chave encontrada neste filtro."
    
    # Discord tem limite de 4096 caracteres, se tiver muita key, cortamos o texto.
    if len(texto) > 3800: texto = texto[:3800] + "\n... (lista muito longa)"

    embed = discord.Embed(title=f"📋 LISTAGEM: {filtro.name.upper()}", description=texto, color=COR_TECH)
    embed.set_footer(text=f"Total: {contador} chaves encontradas.")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- (Outros comandos administrativos: gerar, deletar, pausar, infokey, painelhwid permanecem iguais) ---

@bot.tree.command(name="gerar", description="⚙️ Gera novas licenças")
@app_commands.choices(duracao=[app_commands.Choice(name="24h", value=1), app_commands.Choice(name="30d", value=30), app_commands.Choice(name="Vitalício", value=0)])
async def gerar(interaction: discord.Interaction, duracao: app_commands.Choice[int], quantidade: int = 1):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db(); novas = []
    venc = "LIFETIME" if duracao.value == 0 else (get_sp_time() + datetime.timedelta(days=duracao.value)).strftime("%d/%m/%Y")
    for _ in range(quantidade):
        nk = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nk] = {"hwid": None, "expira": venc, "ativa": True}
        novas.append(nk); save_db(db)
    await interaction.response.send_message(f"✅ **Lote Gerado:**\n```\n" + "\n".join(novas) + "\n```")

@bot.tree.command(name="painelhwid", description="📟 Envia o Terminal de HWID")
async def painelhwid(interaction: discord.Interaction):
    embed = discord.Embed(title="📟 CENTRAL DE LICENCIAMENTO", description="### 🛠️ Protocolo de Gerenciamento\nReset seu HWID abaixo.\n\n🛡️ *King Security 2026*", color=COR_TECH)
    embed.set_footer(text="King Store © 2026")
    await interaction.channel.send(embed=embed, view=ResetView())
    await interaction.response.send_message("✅ Painel Online!", ephemeral=True)

# --- 🕸️ API DE CONEXÃO ---
app = Flask(__name__)
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
        return "Vinculado", 200
    return "Sucesso" if info["hwid"] == hwid else "HWID_Incorreto"

def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()
bot.run(TOKEN)
