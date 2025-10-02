# Login Web API

Autenticação de usuários via API REST usando **FastAPI**, **PostgreSQL**, **SQLAlchemy** e **JWT**.

---

## **Funcionalidades**

- Cadastro de novos usuários (`/register`)
- Login de usuários com retorno de JWT (`/login`)
- Senhas seguras com hash (`bcrypt`)
- Pronto para integração com frontend
- Dockerfile para fácil deploy
- Estrutura limpa e pronta para expansão

---

## **Pré-requisitos**

- Python 3.11+
- Docker (opcional, recomendado para deploy)
- Banco de dados PostgreSQL rodando

---

## **Configuração das variáveis de ambiente**

Defina as variáveis diretamente no sistema ou no Docker:

- `DATABASE_URL`  
  Exemplo:  
  `postgresql://usuario:senha@host:5432/nome_do_banco`
- `SECRET_KEY`  
  Uma string secreta forte para os tokens JWT
- `ACCESS_TOKEN_EXPIRE_MINUTES`  
  (opcional, padrão: 30)

---

## **Rodando com Docker**

```bash
docker build -t login-api .
docker run -d   --name login-api   -p 8000:8000   -e DATABASE_URL=postgresql://usuario:senha@host:5432/nome_do_banco   -e SECRET_KEY=sua_secret_key   login-api
```

---

## **Testando a API**

Acesse a documentação automática no navegador:  
[http://localhost:8000/docs](http://localhost:8000/docs)

### **Endpoints principais**

- `POST /register`  
  Cadastra um novo usuário  
  ```json
  {
    "username": "seu_usuario",
    "password": "sua_senha"
  }
  ```
- `POST /login`  
  Faz login e retorna o JWT  
  ```json
  {
    "username": "seu_usuario",
    "password": "sua_senha"
  }
  ```

---

## **Frontend de exemplo**

Inclua o arquivo `index.html` no repositório para testar login e autenticação de forma simples.

---

## **Personalização**

- Para ambientes de produção, ajuste o CORS e variáveis sensíveis!
- Expanda a API criando mais rotas e modelos conforme a necessidade.

---

## **Licença**

[MIT](LICENSE)

---

Desenvolvido por [Seu Nome] — Health Safety 🚀
