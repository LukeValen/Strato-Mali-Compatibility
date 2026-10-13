# Compatibilidade Strato Mali

Site estático para relatórios da comunidade sobre jogos no Strato Mali. O catálogo inicial contém apenas nomes e Title IDs; **não há estrelas ou status presumidos**. Cada nota publicada vem de um GitHub Issue aberto e revisado.

## Fluxo de publicação

1. Usuário abre **Enviar avaliação** e preenche o formulário em `.github/ISSUE_TEMPLATE/compatibility-report.yml`. É necessário entrar no GitHub. O relato fica público no Issue, mas ainda não entra no site.
2. Mantenedor confere Title ID, descrição e contexto de GPU/driver/versão. Somente depois adiciona a etiqueta `compatibility-approved` ao Issue. Crie essa etiqueta uma vez na interface de Labels do repositório.
3. O workflow `.github/workflows/pages.yml` executa em mudanças nos Issues, no push, manualmente e uma vez ao dia. Ele coleta Issues abertos com essa etiqueta, valida os campos, gera `data/reviews.json` em `dist/` e publica pelo GitHub Pages.
4. Remover a etiqueta ou fechar o Issue retira a avaliação do site na próxima publicação. Uma versão anterior permanece até que o novo deploy termine.

As avaliações podem divergir conforme a GPU. O filtro por GPU calcula a média apenas para os relatos daquele modelo; os detalhes incluem versão e driver. O selo de status do cartão é o relato mais recente no filtro, enquanto as notas são a média dos relatos exibidos. Relatos não são testes independentes da equipe.

## Configurar GitHub Pages

No repositório público: **Settings → Pages → Build and deployment → Source: GitHub Actions**. Em **Actions**, execute manualmente `Publish compatibility list` na branch `main` se o push inicial ocorreu antes de ativar Pages. O endereço aparecerá no resultado do deploy. GitHub Pages e Actions em repositório público estão sujeitos aos limites do plano gratuito.

## Desenvolvimento e uso no app

Execute `python3 -m unittest discover -s tests` e sirva a raiz localmente com `python3 -m http.server 8000`. A página lê `data/games.json` e `data/reviews.json`; o workflow substitui apenas a cópia publicada de `reviews.json`. O app pode consumir a mesma URL `data/reviews.json`, com cache local, identificação por Title ID e filtro por GPU, sem enviar dados do aparelho ao GitHub e sem chamar a API de Issues por instalação.

Dados de Issues são exibidos como texto (`textContent`) e os links passam por validação de origem. Nunca envie ROMs, chaves ou informações pessoais no formulário público.
