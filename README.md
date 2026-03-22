# Spotify Manager

Aplicação web local em Python/Flask para gerenciar suas playlists do Spotify: exporte para CSV, remova músicas pela interface, adicione novas músicas via arquivos de texto e gerencie uma área de staging antes de aplicar as alterações.

**Nota / Autor:** Embora feito com com Claude Code e todas as suas firulas, o projeto foi feito não como portfólio e sim como solução pessoal para gerenciar minhas playlists e publiquei para compartilhar com quem quiser. Não mantenho esse repositório.

---

## Funcionalidades

- **Playlists** — visualize todas as suas playlists, veja as faixas e exporte para CSV
- **Remoção de faixas** — remova músicas individualmente ou em lote diretamente pela interface
- **Refresh manual** — botão para recarregar a lista de faixas sem sair da página
- **Músicas Curtidas** — visualize e exporte todas as músicas curtidas no Spotify
- **Staging** — adicione músicas a uma playlist colando texto ou enviando um arquivo `.txt`, com busca automática no Spotify antes de aplicar
- **Exportação CSV** — exporte qualquer playlist ou as músicas curtidas com colunas: nome, artista, álbum, duração e URI

---

## Pré-requisitos

### Linux / macOS

- Python 3.10+
- `virtualenv` instalado (`pip install virtualenv`)
- Conta no Spotify e acesso ao [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

### Windows

- **Python 3.10+** — baixe em [python.org/downloads](https://www.python.org/downloads/)
  - Durante a instalação, marque a opção **"Add Python to PATH"**
  - Para verificar após instalar: abra o Prompt de Comando e rode `python --version`
- **virtualenv** — após instalar o Python, rode no Prompt de Comando:
  ```
  pip install virtualenv
  ```
- **Git** (opcional, para clonar o repositório) — [git-scm.com](https://git-scm.com/download/win)
- Conta no Spotify e acesso ao [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

---

## Configuração inicial (uma única vez)

### 1. Criar uma conta no Spotify (se ainda não tiver)

1. Acesse [spotify.com](https://www.spotify.com) e clique em **Cadastre-se**
2. Crie sua conta com e-mail ou pelo Google/Facebook
3. Confirme o e-mail se solicitado
4. Uma conta gratuita já é suficiente para usar este app

### 2. Criar um app no Spotify Developer Dashboard

A API do Spotify exige um "app" registrado para gerar as credenciais de acesso. Isso é necessário mesmo para uso pessoal.

1. Acesse [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) e faça login com a **mesma conta** do Spotify
2. Clique em **Create app**
3. Preencha os campos:
   - **App name**: qualquer nome (ex: `Meu Gerenciador`)
   - **App description**: qualquer descrição
   - **Redirect URIs**: clique em **Add** e insira exatamente `http://127.0.0.1:5000/callback`
   - **Which API/SDKs are you planning to use?**: marque **Web API**
4. Marque a caixa de concordância com os termos e clique em **Save**
5. Na página do app, clique em **Settings**
6. Você verá o **Client ID** — copie e guarde
7. Clique em **View client secret**, copie e guarde também

> O **Client ID** identifica seu app publicamente. O **Client Secret** é equivalente a uma senha — nunca o compartilhe nem o suba para repositórios.

### 3. Onde usar cada credencial

| Credencial | O que é | Onde colocar no projeto |
|---|---|---|
| **Client ID** | Identificador público do seu app Spotify | Campo `SPOTIPY_CLIENT_ID` no `.env` |
| **Client Secret** | Senha secreta do app Spotify | Campo `SPOTIPY_CLIENT_SECRET` no `.env` |
| **Redirect URI** | URL para onde o Spotify redireciona após o login | Campo `SPOTIPY_REDIRECT_URI` no `.env` (deve ser idêntica à cadastrada no Dashboard) |
| **Secret Key** | Chave para assinar as sessões do Flask (gerada por você) | Campo `SECRET_KEY` no `.env` |

O arquivo `.env` **nunca deve ser versionado** (já está no `.gitignore`). Todas as credenciais ficam exclusivamente nele e são lidas pela aplicação em tempo de execução — nenhuma delas aparece no código-fonte.

### 4. Configurar o arquivo `.env`

Ao rodar pela primeira vez, o script cria o `.env` automaticamente a partir do `.env.example`. Edite o arquivo com suas credenciais:

```env
SPOTIPY_CLIENT_ID=cole_seu_client_id_aqui
SPOTIPY_CLIENT_SECRET=cole_seu_client_secret_aqui
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/callback
SECRET_KEY=uma_string_longa_e_aleatoria
```

Para gerar um `SECRET_KEY` seguro:

**Linux/macOS:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Windows (Prompt de Comando):**
```
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Como executar

### Linux / macOS

```bash
./run.sh
```

Se necessário, dê permissão de execução antes:
```bash
chmod +x run.sh
```

### Windows

Dê um duplo clique no arquivo `run.bat` **ou** abra o Prompt de Comando na pasta do projeto e rode:

```
run.bat
```

> **Dica no Windows:** Para abrir o Prompt de Comando na pasta certa, navegue até a pasta no Explorador de Arquivos, clique na barra de endereço, digite `cmd` e pressione Enter.

---

O script (em ambos os sistemas):
1. Cria o ambiente virtual (`venv/`) se não existir
2. Instala/atualiza as dependências do `requirements.txt`
3. Valida se as credenciais do Spotify estão preenchidas no `.env`
4. Sobe o servidor Flask em `http://127.0.0.1:5000`

Abra o navegador em **http://127.0.0.1:5000**.

---

## Uso

### Login

Na primeira vez, você será redirecionado para a página de autorização do Spotify. Clique em **Connect with Spotify** e autorize as permissões solicitadas:

| Permissão | Finalidade |
|---|---|
| `playlist-read-private` | Ler playlists privadas |
| `playlist-read-collaborative` | Ler playlists colaborativas |
| `playlist-modify-public` | Modificar playlists públicas |
| `playlist-modify-private` | Modificar playlists privadas |
| `user-library-read` | Ler músicas curtidas |

> **Atenção:** Se você adicionar permissões novas (ou fizer logout), o Spotify solicitará autorização novamente. Isso é esperado.

---

### Playlists

A página inicial lista todas as suas playlists com capa, nome e quantidade de faixas.

- Clique em **View** para ver as músicas de uma playlist
- Clique em **Export CSV** para baixar a playlist como arquivo `.csv`

#### Dentro de uma playlist

| Ação | Como fazer |
|---|---|
| Remover uma música | Botão **Remove** na linha da faixa |
| Remover várias músicas | Marque os checkboxes e clique em **Remove Selected** |
| Selecionar todas | Checkbox no cabeçalho da tabela |
| Atualizar a lista | Botão **⟳ Refresh** (nova chamada à API do Spotify) |
| Exportar CSV | Botão **Export CSV** no topo |

O arquivo CSV exportado contém as colunas:

```
name, artist, album, duration_ms, uri
```

---

### Músicas Curtidas

A aba **Curtidas** exibe todas as músicas salvas na sua biblioteca do Spotify com data de adição.

- Clique em **Export CSV** para baixar o arquivo `curtidas.csv`

> A lista de curtidas pode ser grande (milhares de músicas). O carregamento inicial faz chamadas paginadas à API. Após o primeiro acesso, o resultado fica em cache por 5 minutos.

---

### Staging — Adicionar músicas em lote

O Staging é uma área intermediária onde você cola ou envia uma lista de músicas, o sistema busca no Spotify e você confirma antes de aplicar à playlist.

#### Formatos aceitos no campo de texto (um por linha)

```
Artista - Nome da Música
Nome da Música by Artista
Nome da Música
```

Exemplos:

```
Evanescence - My Immortal
Bohemian Rhapsody by Queen
Hotel California
Nightwish - Nemo
```

#### Fluxo completo

1. Na aba **Staging**, selecione a **playlist de destino**
2. Cole as músicas no campo de texto **ou** envie um arquivo `.txt`
3. Clique em **Search & Stage**
4. O sistema busca cada música no Spotify e atribui um status:

| Status | Significado |
|---|---|
| `resolved` (verde) | Música encontrada com URI válida |
| `not_found` (vermelho) | Música não encontrada no Spotify |
| `pending` (cinza) | Busca não concluída (limite de requisições atingido) |

5. Para músicas `not_found`, você pode colar manualmente o URI do Spotify (formato `spotify:track:xxxxx`) no campo da linha
6. Para músicas `pending`, clique em **Retry Pending** para tentar a busca novamente
7. Quando todas as músicas desejadas estiverem como `resolved`, clique em **Apply to Spotify**
8. As músicas são adicionadas à playlist e removidas do staging

#### Botões do Staging

| Botão | Ação |
|---|---|
| **Apply to Spotify** | Adiciona todas as faixas `resolved` à playlist |
| **Retry Pending** | Tenta resolver as faixas `pending` (aparece somente se houver pendentes) |
| **Clear** | Remove todas as faixas do staging para aquela playlist |
| **✕** (por linha) | Remove uma faixa individual do staging |

---

## Rate Limit do Spotify

### O que é

A API do Spotify impõe limites no número de requisições por janela de tempo. Quando o limite é excedido, a API retorna `HTTP 429` com um cabeçalho `Retry-After` indicando quantos segundos aguardar.

Existem dois tipos de limite:

| Tipo | `Retry-After` típico | Causa |
|---|---|---|
| **Limite por endpoint** | 1 a 30 segundos | Muitas requisições em pouco tempo |
| **Limite de app** | Horas a mais de 20 horas | Volume excessivo de requisições acumuladas |

### Como o app trata o rate limit

O sistema foi projetado para não travar nem retornar erros 500 quando o limite é atingido:

**Pacing proativo**
Um intervalo mínimo de 100ms é respeitado entre qualquer chamada à API, reduzindo a chance de acionar o limite.

**Budget de 20 segundos por requisição**
Cada chamada à API tem um orçamento de 20 segundos para tentativas. Se o `Retry-After` do Spotify for menor que o orçamento restante, o app aguarda e tenta novamente automaticamente. Se for maior, o app **não** trava — lança um `RateLimitError` imediatamente.

**Mensagem amigável**
Em vez de um erro 500, você vê um aviso amarelo:
> *"Limite de requisições do Spotify atingido. Aguarde X segundo(s) e tente novamente."*

**Staging com commit parcial**
Se o limite for atingido no meio de uma busca em lote (Staging), as músicas já processadas são salvas normalmente. As restantes ficam com status `pending` e podem ser retentadas com o botão **Retry Pending** após o limite expirar.

**Cache TTL**
Para reduzir o número de chamadas à API:

| Dado | TTL |
|---|---|
| Lista de playlists | 5 minutos |
| Faixas de uma playlist | 2 minutos |
| Músicas curtidas | 5 minutos |
| Resultado de busca (staging) | 1 hora |

O cache é limpo automaticamente ao remover ou adicionar faixas.

### Se o `Retry-After` for muito alto (horas ou mais de 20 horas)

Isso indica que o Spotify aplicou um **bloqueio de app** por volume excessivo de requisições. Nesse caso:

- O app exibe a mensagem de aviso e **não trava** o servidor
- Você precisará aguardar o período indicado antes de usar a API novamente
- Para evitar que isso aconteça, não recarregue páginas pesadas repetidamente (como Curtidas ou playlists grandes) — o cache cuida disso após o primeiro acesso

---

## Estrutura do projeto

```
spotify/
├── run.sh                  # Script de inicialização
├── run.py                  # Entry point Flask
├── requirements.txt
├── .env                    # Credenciais (não versionar)
├── .env.example
├── .gitignore
│
├── app/
│   ├── __init__.py         # App factory + error handler global
│   ├── config.py           # Leitura de variáveis de ambiente
│   ├── extensions.py       # SQLAlchemy + Flask-Session
│   │
│   ├── auth/               # Login, callback, logout
│   ├── playlists/          # Listagem, detalhes, remoção, export
│   ├── liked/              # Músicas curtidas + export
│   ├── staging/            # Área de staging (model, rotas)
│   │
│   ├── services/
│   │   ├── spotify_client.py  # Todas as chamadas à API + cache + retry
│   │   ├── csv_service.py     # Geração de CSV
│   │   └── text_parser.py     # Parser de texto para músicas
│   │
│   ├── templates/          # Templates Jinja2
│   └── static/             # CSS e JS
│
└── flask_session/          # Sessões do servidor (gerado em runtime)
```

---

## Dependências principais

| Pacote | Versão | Uso |
|---|---|---|
| Flask | 3.1.3 | Framework web |
| spotipy | 2.26.0 | Cliente da API do Spotify |
| Flask-Session | 0.8.0 | Sessões server-side |
| Flask-SQLAlchemy | 3.1.1 | ORM para staging (SQLite) |
| python-dotenv | 1.2.2 | Leitura do `.env` |
