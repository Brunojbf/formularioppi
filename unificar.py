import pandas as pd
from rapidfuzz import process, fuzz

# ==== CONFIGURAÇÕES ====
arquivo = "requisicao.xlsx"  # nome do arquivo
coluna = "Texto do pedido"         # nome da coluna com os itens
saida = "saida_unificada.xlsx"
similaridade_minima = 85     # % de semelhança mínima para considerar igual

# ==== LEITURA DO ARQUIVO ====
df = pd.read_excel(arquivo)

# Lista única de descrições
itens_unicos = df[coluna].dropna().unique().tolist()

# Dicionário para armazenar correspondências
mapeamento = {}

# Itera sobre cada item e tenta achar correspondência já existente
for item in itens_unicos:
    if not mapeamento:  # primeiro item vira base
        mapeamento[item] = item
    else:
        melhor, score, _ = process.extractOne(
            item, list(mapeamento.keys()), scorer=fuzz.token_sort_ratio
        )
        if score >= similaridade_minima:
            # usa a versão já existente como padrão
            mapeamento[item] = mapeamento[melhor]
        else:
            # se não for parecido com nenhum, vira novo padrão
            mapeamento[item] = item

# Cria nova coluna padronizada
df["Descricao_Padronizada"] = df[coluna].map(mapeamento)

# Exporta resultado
df.to_excel(saida, index=False)

print("Arquivo salvo como:", saida)
