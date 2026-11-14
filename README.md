# ⏱ FrameTick — Precision Video Captures

[![Built with AI](https://img.shields.io/badge/Built%20with-AI%20🤖-informational.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![OpenCV](https://img.shields.io/badge/CV-OpenCV-green.svg)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> [!NOTE]
> **Aviso de Projeto:**  
> Este projeto foi **100% desenvolvido por Inteligência Artificial** como uma ferramenta utilitária simples, direta e prática para o dia a dia. É disponibilizado publicamente "no estado em que se encontra" (*as-is*), sem pretensão de ser um produto comercial complexo ou de contar com suporte ativo contínuo, servindo como uma solução funcional e aberta para uso e adaptação.

**FrameTick** é uma aplicação desktop moderna e nativa em Python (**CustomTkinter** + **OpenCV**) para extração precisa e automatizada de frames e prints de vídeos, com múltiplos modos de captura cronológica, refinamento inteligente, suporte a WebP e galeria com Lightbox integrado.

---

## ✨ Funcionalidades

- 🌓 **Interface Gráfica Desktop Moderna**: Desenvolvida em CustomTkinter com suporte a tema escuro nativo, visual responsivo e sem dependência de navegadores.
- 🎬 **Ampla Compatibilidade de Formatos**: Suporta `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.flv` e `.wmv`.
- ⏱ **Três Modos Inteligentes de Captura**:
  - **Modo 1 (Espaçamento Uniforme)**:
    - *Por Intervalo Fixo*: Extrai prints a cada $X$ segundos (ex: a cada 5s).
    - *Por Quantidade Total*: Distribui $N$ prints de forma matematicamente uniforme ao longo de todo o vídeo.
  - **Modo 2 (Rajadas Periódicas / Concentrações)**:
    - *Ciclo Principal*: Dispara um bloco de concentração a cada $X$ segundos (ex: a cada 30s).
    - *Prints por Rajada*: Quantidade $Y$ de fotos em sequência em cada concentração (ex: 5 frames).
    - *Espaçamento Interno*: Intervalo $Z$ em segundos entre cada foto da mesma rajada (ex: 0.5s).
    - *Momento Inicial*: Ponto de início configurável (*offset*).
  - **Modo 3 (Amostragem Aleatória & Refinamento ao Redor)**:
    - *Etapa 1 (Amostragem Estratificada)*: Sorteia instantes distribuídos cobrindo todo o vídeo sem repetições aglomeradas.
    - *Etapa 2 (Refinamento ao Redor)*: Permite selecionar os melhores prints na galeria e extrair $K$ novos frames em uma janela temporal ao redor deles (ex: $\pm 2.0\text{s}$ ao redor de cada instante selecionado).
- 🖼 **Galeria de Miniaturas & Visualizador Interno (Lightbox)**:
  - Renderização instantânea $O(1)$ dos prints conforme são extraídos, com geração de miniatura assíncrona em RAM.
  - **Lightbox Interno**: Clique em qualquer miniatura para abrir um visualizador rápido ampliado, permitindo navegar com as setas do teclado, selecionar e excluir sem depender do visualizador externo do Windows.
  - Ordenação cronológica dinâmica de aparição no vídeo.
  - Caixas de seleção individuais e botões para marcar/desmarcar todos.
  - **Transferência e Organização**: Mova ou copie prints selecionados para uma subpasta interna (padrão `selecionados/`) ou qualquer outro diretório (botão `📁 Mover` ou atalho `Ctrl+M`), com proteção contra sobrescrita.
  - **Exclusão Rápida**: Exclua prints individuais diretamente no card (botão `✕`), no Lightbox (`Del`) ou em lote (botão `🗑 Apagar` ou tecla `Delete`), apagando o arquivo físico do disco e atualizando a interface instantaneamente.
- 🎯 **Estimativa Dinâmica**: Calcula e exibe previamente a quantidade estimada de prints que serão gerados ao alterar qualquer parâmetro ou vídeo (com filtragem inteligente contra prints repetidos no refinamento).
- 📁 **Opções de Exportação e Redimensionamento**:
  - Formatos **PNG** (sem perdas), **JPEG** e **WEBP** (moderno, leve e com controle deslizante de qualidade).
  - **Seletor de Resolução Máxima**: Escolha entre resolução `Original`, `1080p (Full HD)`, `720p (HD)` ou `480p (SD)` com interpolação `cv2.INTER_AREA` (anti-aliasing sem upscaling forçado).
  - Nomenclatura com carimbo de tempo estritamente cronológico (`prefixo_00h01m23s_450ms.png` ou `00h01m23s_450ms.png`).
  - Botão direto para **"Abrir Pasta"** no Windows Explorer.
- ⚡ **Processamento Assíncrono**: Execução em thread separada com suporte a **Cancelamento** a qualquer momento sem travar a interface.

---

## 📁 Estrutura do Projeto

```text
gerador_prints/
├── assets/                 # Ícones da aplicação
│   ├── icon.ico
│   └── icon.png
├── src/
│   ├── core/               # Lógica de processamento e vídeo
│   │   ├── config_manager.py
│   │   ├── utils.py
│   │   └── video_processor.py
│   └── gui/                # Interface gráfica CustomTkinter
│       ├── components/     # Componentes visuais (galeria, abas de modo, diálogos)
│       │   ├── dialog_move.py
│       │   ├── gallery.py
│       │   ├── mode_burst.py
│       │   ├── mode_random.py
│       │   ├── mode_uniform.py
│       │   ├── progress_bar.py
│       │   └── stepper_entry.py
│       └── app.py
├── .gitignore
├── iniciar.bat             # Atalho de inicialização rápida no Windows
├── LICENSE                 # Licença do projeto (MIT)
├── README.md               # Documentação
├── requirements.txt        # Dependências Python
└── run.py                  # Ponto de entrada da aplicação
```

---

## 🛠 Pré-requisitos

- **Python 3.10** ou superior instalado no seu sistema.
- Gerenciador de pacotes **pip**.

---

## 🚀 Instalação e Execução

### 1. Clonar o Repositório

```bash
git clone https://github.com/cff100/gerador_prints.git
cd gerador_prints
```

### 2. Criar e Ativar um Ambiente Virtual

**No Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**No Windows (CMD):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**No Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as Dependências

```bash
pip install -r requirements.txt
```

### 4. Executar a Aplicação

**Pelo Terminal:**
```bash
python run.py
```

**No Windows:**
Você também pode simplesmente dar um duplo clique no arquivo `iniciar.bat`.

> [!TIP]
> Suas preferências (formato, prefixo, parâmetros dos modos) são salvas localmente em `config.json`, criado automaticamente ao clicar em "Salvar padrões". Esse arquivo não é versionado; em uma instalação nova, o app inicia com os valores padrão.

---

## ⌨️ Atalhos Úteis

### Na Janela Principal / Galeria:
| Atalho | Ação |
|---|---|
| <kbd>Delete</kbd> | Exclui todos os prints marcados na galeria (protegido contra digitação) |
| <kbd>Ctrl</kbd> + <kbd>M</kbd> | Abre o diálogo para mover/copiar os prints selecionados |

### No Visualizador Rápido (Lightbox):
| Atalho | Ação |
|---|---|
| <kbd>←</kbd> / <kbd>→</kbd> | Navega para o print anterior / próximo |
| <kbd>Espaço</kbd> | Alterna a seleção (marca/desmarca) do print atual |
| <kbd>Delete</kbd> | Apaga o print atual do disco e avança para o próximo |
| <kbd>Enter</kbd> | Abre a imagem original no aplicativo de fotos padrão do sistema |
| <kbd>Esc</kbd> | Fecha o Lightbox |

---

## 📄 Licença

Este projeto está licenciado sob os termos da licença [MIT](LICENSE).
