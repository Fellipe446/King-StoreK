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
COR_SUCESSO = 0x00FF7F       
COR_TECH = 0x00FFFF          
COR_ERRO = 0xFF2D2D
LOG_CHANNEL_ID = 1234567890  # COLOQUE O ID DO SEU CANAL DE LOGS AQUI

def get_sp_time():
    return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

# --- 💾 SISTEMA DE DADOS ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: 
            json.dump({"keys": {}, "script_status": "🟢 ONLINE"}, f)
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- 🔐 SISTEMA DE RESET (MODAL + VIEW) ---
class ResetModal(ui.Modal, title="🛠️ PROTOCOLO DE RESET"):
    key_input = ui.TextInput(label="SISTEMA DE LICENÇA", placeholder="INSIRA SUA KEY...", min_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        db = load_db()
        key = self.key_input.value.upper().strip()
        if key not in db["keys"]:
            return await interaction.response.send_message("❌ **ERRO:** Key inválida ou inexistente.", ephemeral=True)
        
        info = db["keys"][key]
        nova_k = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Migração de dados para a nova key
        db["keys"][nova_k] = {
            "hwid": None, 
            "roblox_nick": info.get("roblox_nick"), 
            "expira": info["expira"], 
            "ativa": True
        }
        del db["keys"][key]
        save_db(db)

        embed = discord.Embed(title="♻️ RESET CONCLUÍDO", color=COR_SUCESSO, description="Sua nova chave de acesso foi gerada e enviada para o seu **Privado (DM)**.")
        embed.set_footer(text="King Store © 2026")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        try: 
            await interaction.user.send(f"💎 **KING STORE - SEGURANÇA**\nAqui está sua nova credencial: `{nova_k}`\n*O nick vinculado continua o mesmo.*")
        except: 
            await interaction.followup.send("⚠️ Não consegui te enviar a DM. Verifique se suas mensagens privadas estão abertas!", ephemeral=True)

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

# --- 👑 COMANDOS DE ADMINISTRAÇÃO (FULL) ---

@bot.tree.command(name="gerarkey", description="⚙️ Gera novas licenças personalizadas")
@app_commands.choices(unidade=[
    app_commands.Choice(name="Minutos", value="minutos"),
    app_commands.Choice(name="Horas", value="horas"),
    app_commands.Choice(name="Dias", value="dias"),
    app_commands.Choice(name="Semanas", value="semanas"),
    app_commands.Choice(name="Meses", value="meses"),
    app_commands.Choice(name="Vitalício", value="vitalicio")
])
async def gerarkey(interaction: discord.Interaction, quantidade: int, tempo: int, unidade: app_commands.Choice[str]):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db(); novas = []; agora = get_sp_time()

    if unidade.value == "minutos": exp = agora + datetime.timedelta(minutes=tempo)
    elif unidade.value == "horas": exp = agora + datetime.timedelta(hours=tempo)
    elif unidade.value == "dias": exp = agora + datetime.timedelta(days=tempo)
    elif unidade.value == "semanas": exp = agora + datetime.timedelta(weeks=tempo)
    elif unidade.value == "meses": exp = agora + datetime.timedelta(days=tempo*30)
    else: exp = None 

    data_formatada = exp.strftime("%d/%m/%Y %H:%M") if exp else "VITALÍCIO"
    
    for _ in range(quantidade):
        nk = 'KING-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db["keys"][nk] = {"hwid": None, "roblox_nick": None, "expira": data_formatada, "ativa": True}
        novas.append(nk)
    
    save_db(db)
    lista_keys = "\n".join([f"• Código: **{k}**" for k in novas])
    
    embed = discord.Embed(title="🔑 LICENÇA GERADA COM SUCESSO", color=COR_SUCESSO)
    embed.description = f"• Quantidade: **{quantidade} Key**\n{lista_keys}\n• Status: 🟢 Ativa\n• Duração: **{tempo} {unidade.name}**"
    embed.set_footer(text=f"Expiração: {data_formatada} | King Store")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="infokey", description="🔍 Consulta detalhes técnicos de uma licença")
async def infokey(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db(); key = key.upper().strip()
    if key not in db["keys"]: return await interaction.response.send_message("❌ Key não encontrada.", ephemeral=True)
    
    data = db["keys"][key]
    embed = discord.Embed(title="🔍 DETALHES DA LICENÇA", color=COR_TECH)
    embed.add_field(name="🔑 Chave", value=f"`{key}`", inline=False)
    embed.add_field(name="👤 Nick Roblox", value=f"`{data['roblox_nick'] or 'Não vinculado'}`", inline=True)
    embed.add_field(name="🖥️ HWID", value=f"`{data['hwid'] or 'Aguardando login'}`", inline=True)
    embed.add_field(name="⏳ Expiração", value=f"`{data['expira']}`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="listarkeys", description="📋 Lista todas as chaves ativas no banco")
async def listarkeys(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db()
    if not db["keys"]: return await interaction.response.send_message("📭 Banco de dados vazio.", ephemeral=True)
    
    texto = "\n".join([f"• `{k}` | Nick: `{v['roblox_nick'] or 'Livre'}`" for k, v in db["keys"].items()])
    if len(texto) > 2000: texto = texto[:1990] + "..."
    
    embed = discord.Embed(title="📋 RELATÓRIO DE LICENÇAS", description=texto, color=COR_TECH)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="deletarkey", description="🗑️ Remove permanentemente uma licença")
async def deletarkey(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db(); key = key.upper().strip()
    if key in db["keys"]:
        del db["keys"][key]; save_db(db)
        await interaction.response.send_message(f"✅ Key `{key}` removida com sucesso.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Key não encontrada.", ephemeral=True)

@bot.tree.command(name="limparbanco", description="⚠️ DELETA TODAS AS KEYS DO BANCO")
async def limparbanco(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db(); db["keys"] = {}; save_db(db)
    await interaction.response.send_message("💣 **DATABASE RESETADA!** Todas as keys foram apagadas.", ephemeral=True)

@bot.tree.command(name="setstatus", description="🔧 Altera o status público do script")
async def setstatus(interaction: discord.Interaction, status: str):
    if not interaction.user.guild_permissions.administrator: return
    db = load_db(); db["script_status"] = status; save_db(db)
    await interaction.response.send_message(f"✅ Status atualizado para: `{status}`", ephemeral=True)

# --- 👤 COMANDOS PÚBLICOS (CLIENTES) ---

@bot.tree.command(name="cadastro", description="👤 Vincula seu Nick do Roblox à sua Key")
async def cadastro(interaction: discord.Interaction, key: str, nick: str):
    db = load_db(); key = key.upper().strip()
    if key not in db["keys"]: return await interaction.response.send_message("❌ **ERRO:** Esta Key não existe.", ephemeral=True)
    if db["keys"][key].get("roblox_nick"): return await interaction.response.send_message(f"⚠️ **ALERTA:** Esta Key já está vinculada ao nick `{db['keys'][key]['roblox_nick']}`.", ephemeral=True)
    
    db["keys"][key]["roblox_nick"] = nick; save_db(db)
    embed = discord.Embed(title="👤 CADASTRO REALIZADO", color=COR_SUCESSO)
    embed.description = f"• Nick: **{nick}**\n• Status: 🟢 Cadastrado com Sucesso\n\n*Inicie o script no Roblox agora.*"
    embed.set_footer(text="King Store © 2026")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="status", description="📡 Verifica a integridade do sistema")
async def status(interaction: discord.Interaction):
    db = load_db(); st = db.get("script_status", "🟢 ONLINE")
    embed = discord.Embed(title="📡 DIAGNÓSTICO DE REDE", color=COR_TECH)
    embed.description = f"• Script Lua: `{st}`\n• API Auth: `🟢 OPERACIONAL`"
    embed.set_footer(text="King Store © 2026")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="painelhwid", description="📟 Envia o Terminal de Reset")
async def painelhwid(interaction: discord.Interaction):
    embed = discord.Embed(title="📟 CENTRAL DE LICENCIAMENTO | KING STORE", color=COR_TECH)
    embed.description = (
        "**Protocolo de Gerenciamento**\n\n"
        "Se você trocou de hardware ou formatou seu PC, utilize o terminal abaixo para resetar seu vínculo.\n\n"
        "**ATENÇÃO:**\n"
        "Ao clicar no botão, sua chave antiga será deletada e uma nova será enviada no seu **Privado (DM)**.\n\n"
        "🛡️ *Proteção de dados ativada via King Security.*"
    )
    await interaction.channel.send(embed=embed, view=ResetView())
    await interaction.response.send_message("✅ Painel enviado com sucesso.", ephemeral=True)

# --- 🕸️ API DE AUTENTICAÇÃO (FLASK) ---
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
    
    # Registro de HWID no primeiro login
    if info["hwid"] is None:
        db["keys"][key]["hwid"] = hwid
        save_db(db)
        return "Vinculado", 200
    
    if info["hwid"] == hwid:
        return "Sucesso", 200
    else:
        return "HWID_Incorreto", 403

def run(): app.run(host='0.0.0.0', port=10000)
threading.Thread(target=run).start()

bot.run(TOKEN)
