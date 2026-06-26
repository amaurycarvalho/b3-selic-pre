TEMPLATES: dict[str, dict[str, str]] = {
    "pt": {
        # Level 1
        "osc_primary": "A curva apresenta oscilacoes frequentes, sem padrao direcional claro.",
        "vale_primary": "Observa-se uma depressao na parte curta da curva, seguida por recuperacao gradual das taxas.",
        "pico_primary": "A curva apresenta um pico na parte inicial, seguido por reducao gradual das taxas.",
        "sig_primary": "A curva apresenta multiplas mudancas de curvatura, configurando um formato sigmoide na estrutura a termo.",
        "asc_primary": "A curva apresenta tendencia global ascendente, com taxas progressivamente maiores para os vencimentos mais longos.",
        "desc_primary": "A curva apresenta tendencia global descendente.",
        "flat_primary": "A curva permanece praticamente plana ao longo dos vencimentos.",
        "und_primary": "A curva nao apresenta um padrao geometrico claramente definido.",
        "fallback_primary": "A curva nao atende plenamente a nenhuma classe geometrica, mas apresenta evidencias parciais de {classe} (confianca: {pct}).",

        # Level 2
        "rec_struct": "A recuperacao observada na parte curta se mantem ao longo dos vencimentos medios e longos.",
        "flat_struct": "A parte curta se move com mais intensidade que a longa, reduzindo a inclinacao da curva (flattening).",
        "steep_struct": "A parte longa se move com mais intensidade que a curta, aumentando a inclinacao da curva (steepening).",
        "twist_struct": "A parte curta apresenta elevacao enquanto a parte longa recua, configurando uma torcao na estrutura a termo.",
        "step_struct": "A curva apresenta degraus (staircasing), com segmentos de taxas estaveis intercalados por saltos.",
        "mono_struct": "A estrutura evolui de forma praticamente monotonica.",
        "longrec_struct": "Observa-se uma recuperacao longa e sustentada ao longo de parte significativa da curva, indicando persistencia direcional.",

        # Level 3
        "smooth_qual": "A evolucao entre os vertices ocorre de forma suave, sem oscilacoes abruptas.",
        "rough_qual": "Observam-se oscilacoes frequentes entre vertices consecutivos.",
        "lowvol_qual": "A volatilidade da curva e baixa, indicando estabilidade nas expectativas.",
        "highvol_qual": "A volatilidade da curva e alta, indicando incerteza nas expectativas.",
        "osc_qual": "A curva apresenta oscilacoes relevantes entre os vertices.",
        "envup_qual": "A amplitude reduzida da curva indica forte consenso do mercado sobre o nivel das taxas.",
        "envdown_qual": "A amplitude elevada da curva sugere dispersao significativa nas expectativas de mercado.",
        "volmod_qual": "A volatilidade da curva e moderada, indicando nivel intermediario de oscilacao nas expectativas.",
    },
    "en": {},
}


def resolve_template(template_id: str, locale: str = "pt") -> str:
    locale_templates = TEMPLATES.get(locale, TEMPLATES.get("pt", {}))
    return locale_templates.get(template_id, "")
