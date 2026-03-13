# 20260214_151200_setup_tereziadmin_panel

## Data: 2026-02-14 15:12:00

## Descrição
Configuração e deploy do admin-panel em produção, disponível em /tereziadmin/.

## Alterações Realizadas

### 1. Build do Admin Panel
- Instaladas dependências npm
- Build de produção executado com base path /tereziadmin/
- Arquivos gerados em /root/chat-bot-pref/admin-panel/dist/

### 2. Configuração do Vite (vite.config.ts)
- Adicionado `base: '/tereziadmin/'` para que assets sejam carregados corretamente

### 3. Deploy em /var/www/tereziadmin/
- Arquivos copiados para /var/www/tereziadmin/
- Permissões ajustadas para www-data:www-data
- Nginx consegue acessar sem problemas de permissão

### 4. Configuração do Nginx (/etc/nginx/sites-available/nexobasis.com.br)
```nginx
# Admin Panel (React SPA) - serve static files
location ^~ /tereziadmin {
    alias /var/www/tereziadmin/;
    try_files $uri $uri/ =404;

    # Handle React Router - serve index.html for non-file routes
    location ^~ /tereziadmin/ {
        try_files $uri $uri/ /tereziadmin/index.html;
    }

    # Cache static assets
    location ~* ^/tereziadmin/.*\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
}
```

## Acesso
- URL: https://nexobasis.com.br/tereziadmin/
- Tipo: React SPA (Single Page Application)
- API Proxy: /tereziapi/ (já configurado anteriormente)

## Estrutura de Arquivos
```
/var/www/tereziadmin/
├── index.html          # Página principal
├── vite.svg            # Favicon
└── assets/
    ├── index-CEi1yUuM.js    # Bundle JS
    ├── index-Bw6ck-X_.css   # Bundle CSS
    └── ...
```

## Comandos para Rebuild (quando necessário)
```bash
cd /root/chat-bot-pref/admin-panel
npm run build

# Copiar para o diretório web
rm -rf /var/www/tereziadmin/*
cp -r /root/chat-bot-pref/admin-panel/dist/* /var/www/tereziadmin/
chown -R www-data:www-data /var/www/tereziadmin

# Recarregar nginx
nginx -t && systemctl reload nginx
```

## Notas Importantes
- O admin panel é um SPA React, então todas as rotas devem servir index.html
- Assets estáticos têm cache de 1 ano para melhor performance
- Headers de segurança aplicados (X-Frame-Options, X-XSS-Protection, X-Content-Type-Options)
- Não conflita com /tereziapi/ ou /grafana/ (usa ^~ para prioridade)
