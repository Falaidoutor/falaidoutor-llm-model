"""Printer formatado para resultados de normalização semântica.

Responsável por exibir de forma clara e visual os dados
de normalização processados.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .normalizacao_semantica import NormalizedInput


class PrintNormalizacao:
    """Classe especializada em imprimir dados de normalização."""

    # Cores ANSI (terminal)
    VERDE = "\033[92m"
    VERMELHO = "\033[91m"
    AMARELO = "\033[93m"
    AZUL = "\033[94m"
    CINZA = "\033[90m"
    RESET = "\033[0m"
    NEGRITO = "\033[1m"

    LARGURA = 90

    @classmethod
    def imprimir_resumo(cls, normalized: "NormalizedInput") -> None:
        """Imprime um resumo visual completo da normalização.

        Args:
            normalized: Objeto NormalizedInput processado
        """
        cls._print_header()
        cls._print_entrada_original(normalized)
        cls._print_sintomas_normalizados(normalized)
        cls._print_red_flags(normalized)
        cls._print_dados_clinicos(normalized)
        cls._print_demograficos(normalized)
        cls._print_sinais_vitais(normalized)
        cls._print_comorbidades(normalized)
        cls._print_medicacoes(normalized)
        cls._print_cid10(normalized)
        cls._print_alertas(normalized)
        cls._print_confianca(normalized)
        cls._print_footer()

    @classmethod
    def _print_header(cls) -> None:
        """Cabeçalho do relatório."""
        print("\n" + "=" * cls.LARGURA)
        print(f"{cls.NEGRITO}📋 RESUMO DA NORMALIZAÇÃO SEMÂNTICA{cls.RESET}")
        print("=" * cls.LARGURA)

    @classmethod
    def _print_footer(cls) -> None:
        """Rodapé do relatório."""
        print("=" * cls.LARGURA + "\n")

    @classmethod
    def _print_entrada_original(cls, normalized: "NormalizedInput") -> None:
        """Imprime a entrada original."""
        print(f"\n{cls.NEGRITO}🔹 ENTRADA ORIGINAL:{cls.RESET}")
        # Limitar a 2 linhas se muito longo
        texto = normalized.sintomas_originais
        if len(texto) > cls.LARGURA - 10:
            print(f"   {texto[:cls.LARGURA - 10]}...")
        else:
            print(f"   {texto}")

    @classmethod
    def _print_sintomas_normalizados(cls, normalized: "NormalizedInput") -> None:
        """Imprime sintomas em forma canônica."""
        print(f"\n{cls.NEGRITO}🔹 SINTOMAS NORMALIZADOS ({len(normalized.sintomas_normalizados)}):{cls.RESET}")
        if normalized.sintomas_normalizados:
            for sintoma in normalized.sintomas_normalizados:
                print(f"   {cls.VERDE}✓{cls.RESET} {sintoma}")
        else:
            print(f"   {cls.AMARELO}⚠️  Nenhum sintoma reconhecido{cls.RESET}")

    @classmethod
    def _print_red_flags(cls, normalized: "NormalizedInput") -> None:
        """Imprime red flags detectadas."""
        if not normalized.red_flags:
            return

        print(f"\n{cls.NEGRITO}{cls.VERMELHO}⚠️  RED FLAGS - URGÊNCIA DETECTADA:{cls.RESET}")
        for flag in normalized.red_flags:
            color = cls.VERMELHO if flag["color"] == "VERMELHO" else cls.AMARELO
            print(f"   {color}🔴 {flag['flag']} [{flag['color']}]{cls.RESET}")

    @classmethod
    def _print_dados_clinicos(cls, normalized: "NormalizedInput") -> None:
        """Imprime dados clínicos estruturados."""
        print(f"\n{cls.NEGRITO}🔹 DADOS CLÍNICOS:{cls.RESET}")

        # Severidade
        sev = normalized.severidade or "?"
        sev_icon = "🔴" if sev == "intensa" else "🟡" if sev == "moderada" else "🟢"
        print(f"   {sev_icon} Severidade: {cls.AZUL}{sev}{cls.RESET}")

        # Duração
        dur = normalized.duracao or "?"
        print(f"   ⏱️  Duração: {cls.AZUL}{dur}{cls.RESET}")

        # Onset
        onset_map = {
            "agudo": "⚡",
            "subagudo": "⚠️ ",
            "crônico": "📅"
        }
        onset_icon = onset_map.get(normalized.onset or "", "❓")
        onset_text = normalized.onset or "?"
        print(f"   {onset_icon} Onset: {cls.AZUL}{onset_text}{cls.RESET}")

    @classmethod
    def _print_demograficos(cls, normalized: "NormalizedInput") -> None:
        """Imprime dados demográficos."""
        print(f"\n{cls.NEGRITO}🔹 DEMOGRÁFICOS:{cls.RESET}")

        # Idade
        age_map = {
            "pediatria": "👶",
            "adulto": "👤",
            "idoso": "👴"
        }
        age_icon = age_map.get(normalized.idade_grupo or "adulto", "❓")
        age_text = normalized.idade_grupo or "adulto (default)"
        print(f"   {age_icon} Faixa etária: {cls.AZUL}{age_text}{cls.RESET}")

        # Gestante
        if normalized.gestante:
            ig_text = f"{normalized.idade_gestacional_semanas} semanas" \
                if normalized.idade_gestacional_semanas else "não especificada"
            print(f"   🤰 Gestante: {cls.VERDE}SIM{cls.RESET} (IG: {ig_text})")

    @classmethod
    def _print_sinais_vitais(cls, normalized: "NormalizedInput") -> None:
        """Imprime sinais vitais extraídos."""
        vitals = normalized.sinais_vitais

        if not any([
            vitals.temperatura,
            vitals.frequencia_cardiaca,
            vitals.frequencia_respiratoria,
            vitals.pressao_arterial,
            vitals.saturacao_oxigenio,
        ]):
            return

        print(f"\n{cls.NEGRITO}🔹 SINAIS VITAIS:{cls.RESET}")

        if vitals.temperatura:
            # Classificar temperatura
            if vitals.temperatura >= 38.5:
                color = cls.VERMELHO
            elif vitals.temperatura >= 37.5:
                color = cls.AMARELO
            else:
                color = cls.VERDE
            print(f"   {color}🌡️  Temperatura: {vitals.temperatura}°C{cls.RESET}")

        if vitals.frequencia_cardiaca:
            # Classificar FC
            if vitals.frequencia_cardiaca > 120 or vitals.frequencia_cardiaca < 60:
                color = cls.AMARELO
            else:
                color = cls.VERDE
            print(f"   {color}💓 FC: {vitals.frequencia_cardiaca} bpm{cls.RESET}")

        if vitals.frequencia_respiratoria:
            # Classificar FR
            if vitals.frequencia_respiratoria > 24 or vitals.frequencia_respiratoria < 12:
                color = cls.AMARELO
            else:
                color = cls.VERDE
            print(f"   {color}💨 FR: {vitals.frequencia_respiratoria} irpm{cls.RESET}")

        if vitals.pressao_arterial:
            print(f"   {cls.AZUL}📊 PA: {vitals.pressao_arterial} mmHg{cls.RESET}")

        if vitals.saturacao_oxigenio:
            # Classificar SpO2
            if vitals.saturacao_oxigenio < 94:
                color = cls.VERMELHO
            elif vitals.saturacao_oxigenio < 96:
                color = cls.AMARELO
            else:
                color = cls.VERDE
            print(f"   {color}🫁 SpO2: {vitals.saturacao_oxigenio}%{cls.RESET}")

    @classmethod
    def _print_comorbidades(cls, normalized: "NormalizedInput") -> None:
        """Imprime comorbidades."""
        if not normalized.comorbidades:
            return

        print(f"\n{cls.NEGRITO}🔹 COMORBIDADES ({len(normalized.comorbidades)}):{cls.RESET}")
        for com in normalized.comorbidades:
            print(f"   {cls.AMARELO}•{cls.RESET} {com}")

    @classmethod
    def _print_medicacoes(cls, normalized: "NormalizedInput") -> None:
        """Imprime medicações."""
        if not normalized.medicacoes:
            return

        print(f"\n{cls.NEGRITO}🔹 MEDICAÇÕES ({len(normalized.medicacoes)}):{cls.RESET}")
        for med in normalized.medicacoes:
            print(f"   {cls.AZUL}💊 {med}{cls.RESET}")

    @classmethod
    def _print_cid10(cls, normalized: "NormalizedInput") -> None:
        """Imprime códigos CID-10."""
        if not normalized.cid10_suspeitas:
            return

        print(f"\n{cls.NEGRITO}🔹 CÓDIGOS CID-10 ({len(normalized.cid10_suspeitas)}):{cls.RESET}")
        for cid in normalized.cid10_suspeitas:
            conf_pct = int(cid.confianca * 100)
            # Conferença visual por cores
            if conf_pct >= 90:
                color = cls.VERDE
            elif conf_pct >= 70:
                color = cls.AZUL
            else:
                color = cls.AMARELO
            print(f"   {color}{cid.cid}: {cid.descricao} ({conf_pct}%){cls.RESET}")

    @classmethod
    def _print_alertas(cls, normalized: "NormalizedInput") -> None:
        """Imprime alertas e dados faltantes."""
        if not normalized.alertas:
            return

        print(f"\n{cls.NEGRITO}{cls.AMARELO}⚠️  ALERTAS (INFORMAÇÕES FALTANTES):{cls.RESET}")
        for alerta in normalized.alertas:
            print(f"   {cls.AMARELO}⚠️  {alerta}{cls.RESET}")

    @classmethod
    def _print_confianca(cls, normalized: "NormalizedInput") -> None:
        """Imprime barra de confiança."""
        conf_pct = int(normalized.confianca_normalizacao * 100)

        # Escolher cor baseado na confiança
        if conf_pct >= 80:
            color = cls.VERDE
            emoji = "✓"
        elif conf_pct >= 60:
            color = cls.AZUL
            emoji = "○"
        else:
            color = cls.AMARELO
            emoji = "!"

        # Criar barra
        barra_cheia = int(conf_pct / 5)
        barra_vazia = 20 - barra_cheia
        barra = "█" * barra_cheia + "░" * barra_vazia

        print(f"\n{cls.NEGRITO}📊 CONFIANÇA GERAL:{cls.RESET}")
        print(f"   {color}{emoji} {conf_pct}% [{barra}]{cls.RESET}")
        print(f"   {cls.CINZA}(qualidade da normalização){cls.RESET}")

    @classmethod
    def imprimir_comparacao(cls, original: str, normalized: "NormalizedInput") -> None:
        """Imprime uma comparação antes/depois lado-a-lado.

        Args:
            original: Texto original do usuário
            normalized: Dados normalizados
        """
        print("\n" + "=" * cls.LARGURA)
        print(f"{cls.NEGRITO}🔄 COMPARAÇÃO: ANTES vs DEPOIS{cls.RESET}")
        print("=" * cls.LARGURA)

        # Antes
        print(f"\n{cls.NEGRITO}{cls.CINZA}ANTES (Entrada original):{cls.RESET}")
        print(f"   {original}")

        # Depois
        print(f"\n{cls.NEGRITO}{cls.VERDE}DEPOIS (Normalizado):{cls.RESET}")
        sintomas_str = ", ".join(normalized.sintomas_normalizados) if normalized.sintomas_normalizados else "(nenhum)"
        print(f"   Sintomas: {sintomas_str}")

        if normalized.idade_grupo:
            print(f"   Idade: {normalized.idade_grupo}")

        if normalized.severidade:
            print(f"   Severidade: {normalized.severidade}")

        if normalized.duracao:
            print(f"   Duração: {normalized.duracao}")

        if normalized.sinais_vitais.temperatura:
            print(f"   Temperatura: {normalized.sinais_vitais.temperatura}°C")

        print("=" * cls.LARGURA + "\n")
