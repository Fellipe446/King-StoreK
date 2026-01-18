import string
import random
from github import Github # pip install PyGithub

# --- CONFIGURAÇÃO ---
TOKEN_GITHUB = "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" # Seu token
REPO_NOME = "Fellipe446/King-StoreK"
CAMINHO_ARQUIVO = "Bot_Manager/keys.txt"

def gerador_de_keys(quantidade=1):
    keys = []
    for _ in range(quantidade):
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        keys.append(f"KING-{codigo}")
    return keys

def atualizar_github():
    try:
        g = Github(TOKEN_GITHUB)
        repo = g.get_repo(REPO_NOME)
        contents = repo.get_contents(CAMINHO_ARQUIVO)
        
        print("--- Gerador King Hub ---")
        qtd = int(input("Quantas chaves deseja gerar e enviar? "))
        novas_keys = gerador_de_keys(qtd)
        
        # Pega o que já existe no GitHub
        conteudo_atual = contents.decoded_content.decode('utf-8').strip()
        
        # Une com as novas chaves
        lista_final = conteudo_atual + "\n" + "\n".join(novas_keys)
        
        # Faz o upload
        repo.update_file(
            contents.path, 
            f"Update: +{qtd} keys geradas", 
            lista_final, 
            contents.sha
        )
        
        print("\n✅ SUCESSO!")
        print("As seguintes chaves foram adicionadas ao GitHub:")
        for k in novas_keys:
            print(f" -> {k}")
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")

if __name__ == "__main__":
    atualizar_github()
