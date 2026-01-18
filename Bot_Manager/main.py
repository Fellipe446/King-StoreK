import discord
from discord.ext import commands
import random
import string
from github import Github  # Certifique-se de ter instalado: pip install PyGithub

# --- CONFIGURAÇÃO ---
TOKEN_DISCORD = "MTQ2MjE5Mjk1NDk2ODg5OTg1Mw.GtQxls.cHePCOzIP4ykJPWZOPxLK9lzJ7WIpMQ6Hu3BI4"
TOKEN_GITHUB = "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"
REPO_NOME = "Fellipe446/King-StoreK"
CAMINHO_ARQUIVO = "Bot_Manager/keys.txt"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# FUNÇÃO QUE ENVIA PARA O GITHUB
def salvar_key_no_github(nova_key):
    try:
        g = Github(TOKEN_GITHUB)
        repo = g.get_repo(REPO_NOME)
        contents = repo.get_contents(CAMINHO_ARQUIVO)
        
        # Pega o conteúdo atual e adiciona a nova key
        antigo_conteudo = contents.decoded_content.decode('utf-8')
        # Garante que comece em uma nova linha
        novo_conteudo = antigo_conteudo.strip() + f"\n{nova_key}"
        
        # Faz o update no arquivo
        repo.update_file(
            contents.path, 
            f"Bot: Nova key gerada {nova_key}", 
            novo_conteudo, 
            contents.sha
        )
        return True
    except Exception as e:
        print(f"Erro ao salvar no GitHub: {e}")
        return False

# COMANDO PARA GERAR KEY
@bot.command()
async def gerarkey(ctx):
    # Gera uma key aleatória: KING-XXXX
    letras = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    nova_key = f"KING-{letras}"
    
    await ctx.send(f"⏳ Gerando chave **{nova_key}** e salvando no banco de dados...")
    
    # Chama a função do GitHub
    if salvar_key_no_github(nova_key):
        await ctx.send(f"✅ **Sucesso!** Sua key é: `{nova_key}`\nEla já pode ser usada no Roblox.")
    else:
        await ctx.send("❌ **Erro:** Não foi possível salvar a key no GitHub. Verifique o console.")

bot.run(TOKEN_DISCORD)
