# -*- coding: utf-8 -*-
"""
Created on Fri May 19 16:56:40 2022

@author: vbras
"""
# ------------------------------------------
# Funções de regras de negócio auxiliares
# ------------------------------------------

# definindo função de compra
def status_compra(dados):
    if ((dados["condition"] >=3) & (dados["grade"] >= 7) | (dados["waterfront"] == 1)) \
        & (dados["price"] <= dados["price_median"]) & (dados["sqft_living"] >= dados["sqft_living_median"]):
        return "Comprar"
    else:
        return "Não Comprar"

# definindo função de faixa atual
def faixa_atual(dados):
    if dados["price"] < dados["faixa_inf"]:
        return "faixa_0"
    elif (dados["price"] >= dados["faixa_inf"]) & (dados["price"] < dados["price_median"]):
        return "faixa_1"
    elif  (dados["price"] >= dados["price_median"]) & (dados["price"] < dados["faixa_sup"]):
        return "faixa_2"
    else:
        return "faixa_3"

# definindo função de preço de venda
def preco_venda(dados):
    if dados["faixa_atual"] == "faixa_0":
        return (dados["faixa_inf"] - dados["price"]) + dados["price"]
    elif dados["faixa_atual"] == "faixa_1":
        return (dados["price_median"] - dados["price"]) + dados["price"]
    elif dados["faixa_atual"] == "faixa_2":
        return (dados["faixa_sup"] - dados["price"]) + dados["price"]
    else:
        return dados["price"]

# definindo função de ajuste de preço
def preco_ajuste(dados):
    if dados["preco_venda"] > dados["price"] * 1.3:
        return dados["price"] * 1.3
    elif dados["preco_venda"] < dados["price"] * 1.05:
        return dados["price"] * 1.05 
    else:
        return dados["preco_venda"]