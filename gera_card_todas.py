import csv
from datetime import datetime
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DIR = Path(__file__).resolve().parent
SECOES = DIR / "secoes.csv"
VANTAGEM_LULA_FLAVIO = 4_430_191

LARGURA = 768
ALTURA_CABECALHO = 285
ALTURAS_LINHAS = (88, 75, 74, 75, 75, 74)
ALTURA_RODAPE = 419

VERDE = "#16b99c"
VERDE_ESCURO = "#0c9078"
LIMA = "#a8ec00"
AZUL = "#2c4053"
CINZA = "#607386"
CINZA_CLARO = "#e0e5e9"
BRANCO = "#ffffff"


def formatar_inteiro(valor):
    return f"{valor:,}".replace(",", ".")


def formatar_percentual(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",") + "%"


def largura_barra_proporcional(valor, maximo, largura):
    return min(largura, max(2, round(largura * valor / maximo)))


def carregar_metricas():
    metricas = {
        "urnas": 0,
        "urnas_estendidas": 0,
        "votos_estendidas": 0,
        "votos_tarde_todas": 0,
        "votos_total": 0,
    }
    campos = {
        "uf",
        "classe",
        "votos_apos_17h",
        "votos_apos_17h_estrito",
        "votos_total",
    }

    with SECOES.open(newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        if not campos.issubset(leitor.fieldnames or []):
            raise ValueError("secoes.csv não contém todas as colunas necessárias.")

        for linha in leitor:
            if linha["uf"] == "ZZ":
                continue

            metricas["urnas"] += 1
            metricas["votos_total"] += int(linha["votos_total"])
            metricas["votos_tarde_todas"] += int(linha["votos_apos_17h_estrito"])
            if linha["classe"] == "estendida":
                metricas["urnas_estendidas"] += 1
                metricas["votos_estendidas"] += int(linha["votos_apos_17h"])

    if not metricas["urnas"]:
        raise ValueError("secoes.csv não contém urnas do país.")
    if not metricas["votos_total"]:
        raise ValueError("secoes.csv não contém votos registrados no país.")

    return metricas


def main():
    metricas = carregar_metricas()
    pct_estendidas = 100 * metricas["urnas_estendidas"] / metricas["urnas"]
    peso_votos_tardios = 100 * metricas["votos_estendidas"] / metricas["votos_total"]
    pct_vantagem = 100 * metricas["votos_estendidas"] / VANTAGEM_LULA_FLAVIO

    altura_estatisticas = sum(ALTURAS_LINHAS)
    altura = ALTURA_CABECALHO + altura_estatisticas + ALTURA_RODAPE
    topo_rodape = ALTURA_CABECALHO + altura_estatisticas
    imagem = Image.new("RGB", (LARGURA, altura), BRANCO)
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle((0, 0, LARGURA, ALTURA_CABECALHO), fill=VERDE)
    desenho.rectangle((0, topo_rodape, LARGURA, altura), fill=AZUL)

    fonte_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    fonte_titulo = ImageFont.truetype(str(fonte_dir / "ariblk.ttf"), 39)
    fonte_subtitulo = ImageFont.truetype(str(fonte_dir / "arial.ttf"), 18)
    fonte_label = ImageFont.truetype(str(fonte_dir / "arial.ttf"), 20)
    fonte_label_negrito = ImageFont.truetype(str(fonte_dir / "arialbd.ttf"), 20)
    fonte_auxiliar = ImageFont.truetype(str(fonte_dir / "arial.ttf"), 16)
    fonte_valor = ImageFont.truetype(str(fonte_dir / "ariblk.ttf"), 36)
    fonte_valor_medio = ImageFont.truetype(str(fonte_dir / "ariblk.ttf"), 29)
    fonte_rodape_titulo = ImageFont.truetype(str(fonte_dir / "ariblk.ttf"), 21)
    fonte_rodape = ImageFont.truetype(str(fonte_dir / "arial.ttf"), 16)
    fonte_rodape_negrito = ImageFont.truetype(str(fonte_dir / "arialbd.ttf"), 17)

    centro_x = LARGURA // 2
    desenho.text((centro_x, 49), "QUANTOS VOTOS", font=fonte_titulo, fill=BRANCO, anchor="mt")
    desenho.text((centro_x, 91), "ENTRARAM DEPOIS DAS", font=fonte_titulo, fill=BRANCO, anchor="mt")
    desenho.text((centro_x, 133), "17H NA PRORROGAÇÃO?", font=fonte_titulo, fill=BRANCO, anchor="mt")
    desenho.text(
        (centro_x, 192),
        "O STF estendeu a votação até as 19h, mas a ordem",
        font=fonte_subtitulo,
        fill=BRANCO,
        anchor="mt",
    )
    desenho.text(
        (centro_x, 219),
        "chegou quando a maioria das urnas já tinha fechado.",
        font=fonte_subtitulo,
        fill=BRANCO,
        anchor="mt",
    )

    linhas = [
        ("Urnas no país", formatar_inteiro(metricas["urnas"]), AZUL, "grande", None),
        (
            "Urnas estendidas",
            formatar_inteiro(metricas["urnas_estendidas"]),
            VERDE_ESCURO,
            "grande",
            (
                "fecharam depois das 17h45",
                formatar_percentual(pct_estendidas, 2),
            ),
        ),
        (
            "Votos após as 17h nas urnas estendidas até 19h",
            formatar_inteiro(metricas["votos_estendidas"]),
            VERDE_ESCURO,
            "grande",
            None,
        ),
        (
            "Votos após as 17h em todas as urnas",
            formatar_inteiro(metricas["votos_tarde_todas"]),
            VERDE_ESCURO,
            "medio",
            None,
        ),
        (
            "Votos registrados nas urnas",
            formatar_inteiro(metricas["votos_total"]),
            AZUL,
            "grande",
            None,
        ),
        (
            "Peso dos votos tardios",
            formatar_percentual(peso_votos_tardios, 3),
            AZUL,
            "grande",
            None,
        ),
    ]

    y = ALTURA_CABECALHO
    for altura_linha, (rotulo, valor, cor_valor, tamanho, complemento) in zip(ALTURAS_LINHAS, linhas):
        centro_y = y + altura_linha // 2
        fonte = fonte_valor_medio if tamanho == "medio" else fonte_valor
        cor_rotulo = AZUL if complemento else CINZA
        desenho.text((51, centro_y), rotulo, font=fonte_label_negrito if complemento else fonte_label, fill=cor_rotulo, anchor="lm")
        x_valor = 645 if complemento else 717
        desenho.text((x_valor, centro_y), valor, font=fonte, fill=cor_valor, anchor="rm")

        if complemento:
            texto, percentual = complemento
            desenho.text((51, centro_y + 19), texto, font=fonte_auxiliar, fill=CINZA, anchor="lm")
            desenho.text((660, centro_y + 17), percentual, font=fonte_label_negrito, fill=CINZA, anchor="lm")

        y += altura_linha
        if y < topo_rodape:
            desenho.line((51, y, 717, y), fill=CINZA_CLARO, width=1)

    chamada = "VOTOS TARDIOS ="
    percentual_chamada = formatar_percentual(pct_vantagem, 2)
    chamada_y = topo_rodape + 31
    desenho.text((51, chamada_y), chamada, font=fonte_rodape_titulo, fill=BRANCO, anchor="lm")
    largura_chamada = desenho.textbbox((0, 0), chamada, font=fonte_rodape_titulo)[2]
    x_percentual = 51 + largura_chamada + 8
    desenho.text((x_percentual, chamada_y), percentual_chamada, font=fonte_rodape_titulo, fill=LIMA, anchor="lm")
    largura_percentual = desenho.textbbox((0, 0), percentual_chamada, font=fonte_rodape_titulo)[2]
    desenho.text(
        (x_percentual + largura_percentual + 8, chamada_y),
        "DA VANTAGEM DE LULA",
        font=fonte_rodape_titulo,
        fill=BRANCO,
        anchor="lm",
    )

    desenho.text(
        (51, topo_rodape + 75),
        "Vantagem de Lula sobre Flávio",
        font=fonte_rodape,
        fill="#d2dae2",
        anchor="lm",
    )
    desenho.text(
        (717, topo_rodape + 75),
        formatar_inteiro(VANTAGEM_LULA_FLAVIO),
        font=fonte_rodape_negrito,
        fill=BRANCO,
        anchor="rm",
    )
    largura_barra = 666
    desenho.rounded_rectangle(
        (51, topo_rodape + 97, 51 + largura_barra, topo_rodape + 126),
        radius=3,
        fill=VERDE,
    )

    desenho.text(
        (51, topo_rodape + 152),
        "Votos após as 17h nas urnas estendidas",
        font=fonte_rodape,
        fill="#d2dae2",
        anchor="lm",
    )
    desenho.text(
        (717, topo_rodape + 152),
        formatar_inteiro(metricas["votos_estendidas"]),
        font=fonte_rodape_negrito,
        fill=BRANCO,
        anchor="rm",
    )
    largura_estendidas = largura_barra_proporcional(
        metricas["votos_estendidas"],
        VANTAGEM_LULA_FLAVIO,
        largura_barra,
    )
    desenho.rounded_rectangle(
        (51, topo_rodape + 170, 51 + largura_estendidas, topo_rodape + 198),
        radius=1,
        fill=LIMA,
    )
    desenho.text(
        (51, topo_rodape + 217),
        "Votos após as 17h em todas as urnas",
        font=fonte_rodape,
        fill="#d2dae2",
        anchor="lm",
    )
    desenho.text(
        (717, topo_rodape + 217),
        formatar_inteiro(metricas["votos_tarde_todas"]),
        font=fonte_rodape_negrito,
        fill=BRANCO,
        anchor="rm",
    )
    largura_todas_urnas = largura_barra_proporcional(
        metricas["votos_tarde_todas"],
        VANTAGEM_LULA_FLAVIO,
        largura_barra,
    )
    desenho.rounded_rectangle(
        (51, topo_rodape + 235, 51 + largura_todas_urnas, topo_rodape + 263),
        radius=1,
        fill=LIMA,
    )
    desenho.line((51, topo_rodape + 282, 717, topo_rodape + 282), fill="#405367", width=1)

    desenho.text(
        (51, topo_rodape + 306),
        "Fonte: TSE",
        font=fonte_rodape_titulo,
        fill=BRANCO,
        anchor="lm",
    )
    desenho.text(
        (51, topo_rodape + 339),
        f"Base: {formatar_inteiro(metricas['urnas'])} urnas com dados no CSV.",
        font=fonte_rodape,
        fill="#b5c0cc",
        anchor="lm",
    )
    desenho.text(
        (51, topo_rodape + 359),
        "Horários de Brasília; votos depois das 17h. Exterior excluído.",
        font=fonte_rodape,
        fill="#b5c0cc",
        anchor="lm",
    )
    desenho.text(
        (51, topo_rodape + 394),
        "https://github.com/melviserpa/urnas-tardias, fork de apolinario/urnas-tardias",
        font=fonte_rodape_negrito,
        fill=LIMA,
        anchor="lm",
    )

    while True:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        destino = DIR / f"card-todas-{timestamp}.png"
        try:
            with destino.open("xb") as arquivo:
                imagem.save(arquivo, format="PNG")
            break
        except FileExistsError:
            continue

    print(f"Card criado: {destino.name}")
    print(
        "Métricas calculadas do CSV: "
        f"{formatar_inteiro(metricas['urnas'])} urnas, "
        f"{formatar_inteiro(metricas['urnas_estendidas'])} estendidas, "
        f"{formatar_inteiro(metricas['votos_estendidas'])} votos nas estendidas, "
        f"{formatar_inteiro(metricas['votos_tarde_todas'])} votos >17h em todas."
    )


if __name__ == "__main__":
    main()
