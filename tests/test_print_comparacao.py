#!/usr/bin/env python3
"""Script de teste para a função print_comparacao()"""

from app.service.normalizacao_semantica import NormalizacaoSemantica

def main():
    # Criar instância do orquestrador
    normalizador = NormalizacaoSemantica()
    
    # Texto de teste
    texto_entrada = "Estou com dor de cabeça intensa há 2 dias, febre (38.5°C), tenho 5 anos. Tomo dipirona normalmente."
    
    print("\n" + "="*90)
    print("🧪 TESTE: print_comparacao()")
    print("="*90)
    
    # Processar entrada
    resultado = normalizador.processar(texto_entrada)
    
    # Chamadas de teste
    print("\n📌 Imprimindo comparação original vs normalizado:\n")
    resultado.print_comparacao()
    
    print("\n📌 Imprimindo resumo completo:\n")
    resultado.print_resumo()


if __name__ == "__main__":
    main()
