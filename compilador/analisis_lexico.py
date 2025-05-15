import re

# Analisis Lexico
token_patron = {
    "KEYWORD": r"\b(if|else|while|return|int|float|void|for|print)\b",
    "IDENTIFIER": r"\b[a-zA-Z_][a-zA-Z0-9_]*\b",
    "NUMBER": r"\b\d+(\.\d+)?\b",
    "OPERATOR": r"(==|!=|<=|>=|&&|\|\||\+\+|--|[+\-*/=<>!&])",
    "STRING": r'"([^"]*)"',
    "DELIMITER": r"[(),;{}]",
    "WHITESPACE": r"\s+",
}

def identificar(text):
    patron_general = "|".join(f"(?P<{token}>{patron})" for token, patron in token_patron.items())
    patron_regex = re.compile(patron_general)
    tokens_encontrados = []
    for match in patron_regex.finditer(text):
        for token, valor in match.groupdict().items():
            if valor is not None and token != "WHITESPACE":
                tokens_encontrados.append((token, valor))
    return tokens_encontrados
