# 🛠️ WhatsApp-Timestamp-Fixer

## 📋 Sobre

Ferramenta CLI em Python para corrigir timestamps e metadados de fotos e vídeos exportados do WhatsApp que perderam o carimbo de data/hora original.

## 🎯 Objetivo

Quando fotos e vídeos são extraídos do WhatsApp, os metadados de data são perdidos. No entanto, os nomes dos arquivos seguem o padrão `IMG-YYYYMMDD-WAxxxx.jpg` / `VID-YYYYMMDD-WAxxxx.mp4`.

Este script lê a data diretamente do nome do arquivo e:

1. **Copia** os arquivos para um diretório de saída (originais intactos)
2. **Aplica** o timestamp de modificação (`os.utime`)
3. **Atualiza** metadados internos:
   - 📷 **Imagens**: EXIF (`DateTimeOriginal`, `DateTimeDigitized`, `DateTime`)
   - 🎬 **Vídeos**: MP4 tag `©day`

## ⚙️ Requisitos

- Python **3.11** (criado e testado nesta versão)
- Dependências listadas em `requirements.txt`

## 📦 Instalação

```bash
git clone https://github.com/longstenc/WhatsApp-Timestamp-Fixer.git
cd WhatsApp-Timestamp-Fixer
python -m pip install -r requirements.txt
```

## 🚀 Uso

```bash
python whatsapp-timestamp-fixer.py
```

Ou, se preferir a versão sem emojis:

```bash
python whatsapp-timestamp-fixer_noemoji.py
```

O programa solicitará interativamente:

1. 📁 **Diretório de origem** — pasta com as fotos/vídeos originais
2. 📁 **Diretório de saída** — pasta para receber as cópias corrigidas
3. ⚠️ **Tratamento de conflitos** — se arquivos já existirem no destino:
   - `[S]` Sobrescrever este
   - `[T]` Sobrescrever todos
   - `[P]` Pular este
   - `[Q]` Pular todos

### Exemplo de execução

```
┌────────────────────────────────────────────────────────────┐
│  🔧 CORRECAO DE TIMESTAMPS - FOTOS E VIDEOS WHATSAPP      │
└────────────────────────────────────────────────────────────┘

📁 Diretorio de origem:  C:\Users\...\WhatsApp Images
📁 Diretorio de saida:   C:\Users\...\Fotos Corrigidas

📂 Arquivos encontrados: 200
   🖼️ Imagens (.jpg):  142
   🎬 Videos (.mp4):    58

✅ Nenhum conflito - diretorio de saida vazio.

🚀 Processar arquivos? [y/n] (y):

Processando... ████████████████████████████████ 100%  0:00:45

+------------------------------- RESUMO FINAL --------------------------------+
| ✅ Processados:                  198                                        |
| ⏭️ Pulados (fora do padrao):       2                                        |
| ⏭️ Pulados (conflito):             0                                        |
| ❌ Erros:                          0                                        |
|                                                                              |
| 📂  Diretorio:  C:\Users\...\Fotos Corrigidas                               |
+-----------------------------------------------------------------------------+
```

## 🧩 Funcionalidades

| Funcionalidade          | Detalhes                                            |
|-------------------------|-----------------------------------------------------|
| ✅ Cópia segura         | `shutil.copy2` — originais nunca são alterados      |
| ✅ Timestamp FS         | `os.utime` com data extraída ao meio-dia            |
| ✅ EXIF (JPEG)          | `Pillow` + `piexif` — 3 tags de data                |
| ✅ Metadados MP4        | `mutagen` — tag `©day`                              |
| ✅ Interface Rich       | Painéis, prompts, barra de progresso, tabela final  |
| ✅ Tratamento conflitos | Sobrescrever ou pular, por arquivo ou global        |
| ✅ Resumo final         | Tabela com processados, pulados e erros             |
| ✅ Segurança            | Arquivos originais nunca são modificados            |

## 📁 Estrutura do projeto

```
.
├── whatsapp-timestamp-fixer.py                # Versão com emojis (Unicode)
├── whatsapp-timestamp-fixer_noemoji           # Versão ASCII (terminais Windows clássicos)
├── requirements.txt                           # Dependências do projeto
└── README.md                                  # Este arquivo
```

## 🐍 Versão do Python

Criado e testado com **Python 3.11.0**. Compatível com Python 3.9+.
