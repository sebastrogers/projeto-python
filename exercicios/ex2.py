# 2 - Pergunte ao usuário sua idade e, com base nisso, use uma estrutura if elif else para classificar a 
# idade em categorias de acordo com as seguintes condições:

# Criança: 0 a 12 anos;
# Adolescente: 13 a 18 anos;
# Adulto: acima de 18 anos.

idade = int(input("Qual sua idade? "))

if idade >= 0 and idade <= 12:
    print("Você é uma criança")
elif idade > 12 and idade <= 18:
    print("Você é um adolescente")
else:
    print("Você é um adulto")

