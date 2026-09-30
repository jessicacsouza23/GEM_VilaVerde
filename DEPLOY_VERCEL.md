# Publicação do aplicativo no Vercel

O Streamlit continua independente. Não exclua nem altere `app.py` para publicar
esta pasta.

## Configuração única

1. No Vercel, importe o mesmo repositório Git do GEM.
2. Em **Root Directory**, selecione `gem-vila-verde`.
3. Em **Environment Variables**, cadastre para Production e Preview:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
4. Clique em **Deploy**.

Depois disso, todo push para o Git publica uma versão nova do aplicativo. O
Vercel fornece um endereço HTTPS; nele, o botão **Instalar aplicativo** ficará
disponível em aparelhos compatíveis.

## Importante

- Use a URL e a chave pública `anon` do Supabase.
- Nunca cadastre `SUPABASE_SERVICE_ROLE_KEY` no Vercel nem no navegador.
- As migrations do Supabase são uma configuração separada, executada uma única
  vez no SQL Editor ou por uma futura automação de deploy.
