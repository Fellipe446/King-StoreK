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

# --- 1. CONFIGURAÇÃO SEGURA ---
# O Token não fica mais aqui. Ele deve ser colocado no Render em 'Environment Variables' com o nome DISCORD_TOKEN
TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = 'database.json'

def get_sp_time():
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

# --- 2. BANCO DE DADOS ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": 1}, f)
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

        await interaction.response.send_message(f"✅ HWID Resetado! Sua nova key é: `{nova_k}` (Enviada no seu privado)", ephemeral=True)
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
        print(f"✅ Comandos sincronizados para {self.user}")

bot = KingBot()

@bot.event
async def on_ready():
    print(f"🚀 Bot Online como {bot.user}")

@bot.tree.command(name="gerarkey", description="Gera chaves para o script")
@app_commands.choices(duracao=[
    app_commands.Choice(name="1 Dia", value=1),
    app_commands.Choice(name="30 Dias", value=30),
    app_commands.Choice(name="Permanente", value=0)
])
async def gerarkey(interaction: discord.Interaction, duracao: app_commands.Choice[int], quantidade: int = 1):
    db = load_db()
    novas = []
    for _ in range(quantidade):
        nk = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        venc = "PERMANENTE" if duracao.value == 0 else (get_sp_time() + datetime.timedelta(days=duracao.value)).strftime("%Y-%m-%d %H:%M:%S")
        db["keys"][nk] = {"hwid": None, "expira": venc}
        novas.append(nk)
    save_db(db)
    await interaction.response.send_message(f"💎 **Keys Geradas:**\n`" + "\n".join(novas) + "`")

@bot.tree.command(name="painel_hwid", description="Envia o botão de reset")
async def painel(interaction: discord.Interaction):
    await interaction.channel.send("♻️ Precisa resetar seu HWID? Use o botão abaixo:", view=ResetView())
    await interaction.response.send_message("Painel enviado!", ephemeral=True)

# --- 5. API FLASK (PARA O ROBLOX) ---
app = Flask(__name__)
@app.route('/auth')
def auth():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    db = load_db()
    if key not in db["keys"]: return "Invalida", 404
    info = db["keys"][key]
    if info["hwid"] is None:
        db["keys"][key]["hwid"] = hwid
        save_db(db)
        return "Vinculado", 200
    return "Sucesso" if info["hwid"] == hwid else ("HWID_Incorreto", 403)

def run():
    # Render usa a porta 10000 por padrão
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    t = threading.Thread(target=run)
    t.start()
    bot.run(TOKEN)
