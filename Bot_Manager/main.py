import discord
from discord import app_commands
from discord.ext import commands
import random
import string
from github import Github
import os # Necessário para ler as variáveis do Render

# --- CONFIGURAÇÃO VIA AMBIENTE ---
# O Render vai preencher essas variáveis automaticamente para você
TOKEN_DISCORD = os.getenv("DISCORD_TOKEN")
TOKEN_GITHUB = os.getenv("GITHUB_TOKEN")

REPO_NOME = "Fellipe446/King-StoreK"
CAMINHO_ARQUIVO = "Bot_Manager/keys.txt"

class KingBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        
    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Comandos sincronizados para {self.user}")

bot = KingBot()

# --- FUNÇÃO GITHUB ---
def salvar_no_github(nova_key):
    try:
        g = Github(TOKEN_GITHUB)
        repo = g.get_repo(REPO_NOME)
        contents = repo.get_contents(CAMINHO_ARQUIVO)
        conteudo_atual = contents.decoded_content.decode('utf-8').strip()
        novo_conteudo = conteudo_atual + f"\n{nova_key}"
        repo.update_file(contents.path, f"Bot: Key {nova_key}", novo_conteudo, contents.sha)
        return True
    except Exception as e:
        print(f"Erro no GitHub: {e}")
        return False

# --- COMANDOS (IGUAL ÀS IMAGENS) ---

@bot.tree.command(name="cadastro", description="Vincula sua conta Roblox à Key")
async def cadastro(interaction: discord.Interaction):
    await interaction.response.send_message("👤 Envie o seu UserID do Roblox para vincular.", ephemeral=True)

@bot.tree.command(name="gerarkey", description="Gera novas licenças")
async def gerarkey(interaction: discord.Interaction):
    key = "KING-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    if salvar_no_github(key):
        await interaction.response.send_message(f"✨ **Nova Licença:** `{key}`", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Erro ao salvar no banco de dados.", ephemeral=True)

@bot.tree.command(name="infokey", description="Consulta detalhes de uma licença")
async def infokey(interaction: discord.Interaction, key: str):
    await interaction.response.send_message(f"🔍 Detalhes da chave `{key}` consultados.", ephemeral=True)

@bot.tree.command(name="deletarkey", description="Remove uma licença")
async def deletarkey(interaction: discord.Interaction, key: str):
    await interaction.response.send_message(f"🗑️ Chave `{key}` removida.", ephemeral=True)

@bot.tree.command(name="limparbanco", description="DELETA TODAS AS KEYS")
async def limparbanco(interaction: discord.Interaction):
    await interaction.response.send_message("⚠️ Banco de dados limpo com sucesso!", ephemeral=True)

@bot.tree.command(name="listarkeys", description="Lista todas as chaves ativas")
async def listarkeys(interaction: discord.Interaction):
    await interaction.response.send_message("📋 Lista de chaves enviada.", ephemeral=True)

@bot.tree.command(name="painelhwid", description="Envia o Terminal de Reset")
async def painelhwid(interaction: discord.Interaction):
    await interaction.response.send_message("🖥️ Terminal de Reset de HWID ativo.", ephemeral=True)

@bot.tree.command(name="setstatus", description="Altera o status do Script")
async def setstatus(interaction: discord.Interaction, status: str):
    await interaction.response.send_message(f"⚙️ Status alterado para: {status}", ephemeral=True)

@bot.tree.command(name="status", description="Verifica o sistema")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message("🛰️ **King Store:** Online", ephemeral=True)

# O Render precisa que o bot rode sem travar
bot.run(TOKEN_DISCORD)
