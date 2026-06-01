#!/usr/bin/env python3
"""
Corrige timestamps de fotos e vídeos extraídos do WhatsApp.

Para cada arquivo IMG-YYYYMMDD-WAxxxx.jpg ou VID-YYYYMMDD-WAxxxx.mp4:
  1. Copia para o diretório de saída (originais nunca são alterados)
  2. Aplica timestamp de modificação baseado na data do nome
  3. Atualiza metadados internos (EXIF para imagens, MP4 para vídeos)
"""

import re
import os
import shutil
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint


# ── Constantes ──────────────────────────────────────────────────────────────────

# Regex para arquivos IMG e VID do WhatsApp
# Grupos: 1=tipo, 2=ano, 3=mês, 4=dia, 5=extensão
REGEX_ARQUIVO = re.compile(
    r'^(IMG|VID)-(\d{4})(\d{2})(\d{2})-WA\d+\.(jpg|jpeg|mp4)$',
    re.IGNORECASE,
)

EXTENSOES_IMAGEM = {'.jpg', '.jpeg'}
EXTENSOES_VIDEO = {'.mp4'}

HORA_PADRAO = (12, 0, 0)  # Meio-dia para evitar ambiguidade de fuso horário


# ── Funções auxiliares ──────────────────────────────────────────────────────────

def extrair_data_do_nome(nome_arquivo: str) -> tuple | None:
    """
    Extrai (tipo, ano, mês, dia, extensão) do nome do arquivo via regex.
    Retorna None se o nome não seguir o padrão IMG-YYYYMMDD-WAxxxx.jpg
    ou VID-YYYYMMDD-WAxxxx.mp4.
    """
    match = REGEX_ARQUIVO.match(nome_arquivo)
    if not match:
        return None
    tipo = match.group(1).upper()
    ano = int(match.group(2))
    mes = int(match.group(3))
    dia = int(match.group(4))
    extensao = match.group(5).lower()
    return tipo, ano, mes, dia, extensao


def aplicar_timestamp_fs(caminho: Path, dt: datetime) -> None:
    """Aplica timestamp de modificação no arquivo via os.utime."""
    timestamp = dt.timestamp()
    os.utime(caminho, (timestamp, timestamp))


def aplicar_exif_imagem(caminho: Path, dt: datetime) -> None:
    """
    Atualiza metadados EXIF de data em imagens JPEG.
    Modifica DateTimeOriginal, DateTimeDigitized e DateTime
    usando Pillow + piexif.
    """
    import piexif
    from PIL import Image

    data_str = dt.strftime("%Y:%m:%d %H:%M:%S")

    # Carrega EXIF existente ou cria dicionário vazio
    try:
        exif_dict = piexif.load(str(caminho))
    except Exception:
        exif_dict = {
            "0th": {},
            "Exif": {},
            "GPS": {},
            "Interop": {},
            "1st": {},
            "thumbnail": None,
        }

    exif_dict["0th"][piexif.ImageIFD.DateTime] = data_str
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = data_str
    exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = data_str

    exif_bytes = piexif.dump(exif_dict)

    with Image.open(str(caminho)) as img:
        img.save(str(caminho), exif=exif_bytes)


def aplicar_metadados_video(caminho: Path, dt: datetime) -> None:
    """
    Atualiza metadados de data em arquivos MP4.
    Usa mutagen para definir a tag ©day (data de criação).
    """
    from mutagen.mp4 import MP4

    data_str = dt.strftime("%Y-%m-%dT%H:%M:%S")

    video = MP4(str(caminho))
    video["\xa9day"] = data_str  # ©day em ASCII
    video.save()


def resolver_conflito(
    nome_arquivo: str,
    console: Console,
    acao_global: str | None,
) -> tuple:
    """
    Pergunta ao usuário como proceder quando o arquivo já existe no destino.

    Retorna (deve_sobrescrever: bool, nova_acao_global: str | None).
    acao_global pode ser: None (indeciso), 'overwrite' ou 'skip'.
    """
    if acao_global == 'overwrite':
        return True, acao_global
    if acao_global == 'skip':
        return False, acao_global

    console.print(
        f"\n[yellow][ATENCAO][/] O arquivo [cyan]'{nome_arquivo}'[/] ja existe no diretorio de saida."
    )
    escolha = Prompt.ask(
        "   [bold][S][/]obrescrever  [bold][T][/]odos  [bold][P][/]ular  [bold][Q][/]ular todos",
        choices=["S", "T", "P", "Q"],
        default="S",
        show_choices=False,
    )

    if escolha.upper() == "S":
        return True, None
    elif escolha.upper() == "T":
        return True, "overwrite"
    elif escolha.upper() == "P":
        return False, None
    else:  # Q
        return False, "skip"


# ── Função principal ────────────────────────────────────────────────────────────

def main() -> None:
    console = Console()

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    console.print()
    console.print(
        Panel.fit(
            "[bold blue]CORRECAO DE TIMESTAMPS - FOTOS E VIDEOS WHATSAPP[/]",
            border_style="blue",
        )
    )
    console.print()

    # ── Diretorio de origem ────────────────────────────────────────────────────
    while True:
        origem_str = Prompt.ask("[bold yellow][PASTA][/] Diretorio de origem")
        dir_origem = Path(origem_str).resolve()
        if dir_origem.is_dir():
            break
        console.print("[bold red][ERRO][/] Diretorio invalido. Tente novamente.")

    # ── Diretorio de saida ─────────────────────────────────────────────────────
    while True:
        saida_str = Prompt.ask("[bold yellow][PASTA][/] Diretorio de saida")
        dir_saida = Path(saida_str).resolve()

        if dir_origem == dir_saida:
            console.print(
                "[bold red][ERRO][/] O diretorio de saida deve ser diferente do de origem."
            )
            continue

        if not dir_saida.exists():
            criar = Confirm.ask(
                f"[yellow][ATENCAO][/] O diretorio '[cyan]{dir_saida}[/]' nao existe. Deseja cria-lo?",
                default=True,
            )
            if criar:
                dir_saida.mkdir(parents=True, exist_ok=True)
                break
        elif dir_saida.is_dir():
            break
        else:
            console.print("[bold red][ERRO][/] Caminho invalido. Tente novamente.")

    # ── Buscar arquivos (nao recursivo) ────────────────────────────────────────
    console.print()
    with console.status("[bold green][BUSCA] Escaneando arquivos..."):
        arquivos_origem = sorted(
            [
                p for p in dir_origem.glob("*")
                if p.is_file() and p.suffix.lower() in {'.jpg', '.jpeg', '.mp4'}
            ],
            key=lambda p: p.name,
        )

    if not arquivos_origem:
        console.print("[bold yellow][ATENCAO][/] Nenhum arquivo .jpg, .jpeg ou .mp4 encontrado.")
        return

    qtd_img = sum(1 for p in arquivos_origem if p.suffix.lower() in EXTENSOES_IMAGEM)
    qtd_vid = sum(1 for p in arquivos_origem if p.suffix.lower() in EXTENSOES_VIDEO)

    console.print()
    console.print(f"[bold][INFO][/] Arquivos encontrados: [cyan]{len(arquivos_origem)}[/]")
    console.print(f"   [IMAGEM] Imagens ([cyan].jpg[/]): [green]{qtd_img}[/]")
    console.print(f"   [VIDEO]  Videos ([cyan].mp4[/]): [green]{qtd_vid}[/]")

    # ── Pre-verificar conflitos para informar o usuario ────────────────────────
    console.print()
    conflitos_existentes = [
        p for p in arquivos_origem
        if (dir_saida / p.name).exists()
    ]
    if conflitos_existentes:
        console.print(
            f"[yellow][ATENCAO][/] [cyan]{len(conflitos_existentes)}[/] arquivo(s) ja existe(m) no destino."
        )
    else:
        console.print("[green][OK][/] Nenhum conflito - diretorio de saida vazio.")

    # ── Confirmacao final antes de iniciar ──────────────────────────────────────
    console.print()
    if not Confirm.ask("[bold][INICIAR] Processar arquivos?[/]", default=True):
        console.print("[yellow]Operacao cancelada pelo usuario.[/]")
        return

    # ── Processamento com barra de progresso ────────────────────────────────────
    console.print()

    processados = 0
    pulados_padrao = 0
    pulados_conflito = 0
    erros = 0
    acao_conflito = None  # None | 'overwrite' | 'skip'

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        task_principal = progress.add_task(
            "[cyan]Processando...", total=len(arquivos_origem)
        )

        for arquivo_origem in arquivos_origem:
            nome_arquivo = arquivo_origem.name

            # Extrai data do nome do arquivo
            dados = extrair_data_do_nome(nome_arquivo)
            if dados is None:
                progress.console.print(
                    f"  [yellow][PULAR][/] [dim]{nome_arquivo}[/] - fora do padrao"
                )
                pulados_padrao += 1
                progress.advance(task_principal)
                continue

            tipo, ano, mes, dia, extensao = dados

            # Verifica conflito no destino
            destino = dir_saida / nome_arquivo
            if destino.exists():
                sobrescrever, acao_conflito = resolver_conflito(
                    nome_arquivo, console, acao_conflito
                )
                if not sobrescrever:
                    progress.console.print(
                        f"  [yellow][PULAR][/] [dim]{nome_arquivo}[/] - conflito, pulado"
                    )
                    pulados_conflito += 1
                    progress.advance(task_principal)
                    continue

            try:
                # 1) Copia o arquivo sem modificar o original
                shutil.copy2(arquivo_origem, destino)

                # 2) Cria datetime com a data extraida (meio-dia)
                dt = datetime(ano, mes, dia, *HORA_PADRAO)

                # 3) Aplica timestamp de modificacao no arquivo copiado
                aplicar_timestamp_fs(destino, dt)

                # 4) Atualiza metadados internos da copia
                if tipo == "IMG":
                    aplicar_exif_imagem(destino, dt)
                else:
                    aplicar_metadados_video(destino, dt)

                processados += 1

            except Exception as e:
                progress.console.print(
                    f"  [red][ERRO][/] [dim]{nome_arquivo}[/] - erro: {e}"
                )
                erros += 1

            progress.advance(task_principal)

    # ── Tabela de resumo final ──────────────────────────────────────────────────
    console.print()

    tabela = Table.grid(padding=1)
    tabela.add_column(justify="right", style="bold")
    tabela.add_column()

    tabela.add_row("[green][OK][/]", f"Processados:  [green]{processados}[/]")
    tabela.add_row("[yellow][PULAR][/]", f"Pulados (fora do padrao):  [yellow]{pulados_padrao}[/]")
    tabela.add_row("[yellow][PULAR][/]", f"Pulados (conflito):  [yellow]{pulados_conflito}[/]")
    tabela.add_row("[red][ERRO][/]", f"Erros:  [red]{erros}[/]")
    tabela.add_row("", "")
    tabela.add_row("[blue][SAIDA][/]", f"Diretorio:  [cyan]{dir_saida}[/]")

    console.print(
        Panel.fit(
            tabela,
            title="[bold]RESUMO FINAL[/]",
            border_style="green",
        )
    )
    console.print()


if __name__ == "__main__":
    main()
