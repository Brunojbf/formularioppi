import os
from flask import Flask, request, render_template, redirect, flash, send_file, session, url_for, get_flashed_messages, request, make_response, jsonify
from supabase import create_client, Client
from collections import defaultdict
import uuid
import json
from weasyprint import HTML
import io
import win32com.client
from functools import wraps
import secrets
import random
import string
import json
from datetime import datetime
import traceback
from urllib.parse import urlparse, parse_qs

# Carregar configuração do Supabase
with open("supabase_config.json") as f:
    config = json.load(f)

SUPABASE_URL = config["SUPABASE_URL"]
SUPABASE_KEY = config["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = 'segredo'

# Usuário e senha fixos para login
USUARIO_FIXO = "admin"
SENHA_FIXA = "senha123"


def gerar_token_5_chars():
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(5))

# Decorator para proteger rotas que exigem login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            flash("Você precisa estar logado para acessar essa página.", "warning")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function

def fornecedor_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('duns') or not session.get('token'):
            flash("Você precisa estar logado para acessar essa página.", "warning")
            return redirect(url_for('loginforn'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def home():
    return render_template("home.html")

from flask import session

@app.route('/cadastro_fornecedor', methods=['GET', 'POST'])
def cadastro_fornecedor():
    if request.method == 'POST':
        # Pega o token enviado pelo formulário, não gera outro!
        token = request.form.get('token')

        data = {
            "nome": request.form['nome'],
            "endereco": request.form['endereco'],
            "cidade": request.form['cidade'],
            "duns": request.form['duns'],
            "pais": request.form['pais'],
            "emailforn": request.form['emailforn'],
            "token": token
        }

        try:
            supabase.table("fornecedores").insert(data).execute()
            flash(f"Fornecedor cadastrado com sucesso! Token: {token}", "success")
        except Exception as e:
            flash(f"Erro ao cadastrar fornecedor: {e}", "danger")

        # Redireciona para GET (gera novo token para novo cadastro)
        return redirect(url_for("fornecedores"))

    # GET: gera token para mostrar no formulário
    token = gerar_token_5_chars()
    return render_template('cadastro_fornecedor.html', token=token)

from datetime import datetime

@app.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        # Bloco 1
        pn = request.form.get("pn")
        descricao = request.form.get("descricao")
        plataforma = request.form.get("plataforma")
        carro = request.form.get("carro")
        planta = request.form.get("planta")
        codigo = request.form.get("codigo")

        # Bloco 2
        fornecedor = request.form.get("fornecedor")
        endereco = request.form.get("endereco")
        cidade = request.form.get("cidade")
        duns = request.form.get("duns")
        responsavel = request.form.get("responsavel")
        email = request.form.get("email")
        celular = request.form.get("celular")

        # Bloco 3 - imagem
        imagem = request.files.get("imagem")

        # Bloco 4 - aprovação
        rep_fornecedor = request.form.get("rep_fornecedor")
        aprov_fornecedor = request.form.get("aprov_fornecedor")
        rep_containers = request.form.get("rep_containers")
        aprov_containers = request.form.get("aprov_containers")

        # Captura data e hora atual para data_aprov_fornecedor
        data_aprov_fornecedor = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        url_imagem = None
        if imagem and imagem.filename != '':
            imagem.seek(0, os.SEEK_END)
            tamanho_bytes = imagem.tell()
            imagem.seek(0)  # volta o cursor pro início

            tamanho_mb = tamanho_bytes / (1024 * 1024)
            if tamanho_mb > 1:
                flash("A imagem excede o limite de 1 MB permitido para upload.", "danger")
                return redirect(url_for("form"))

            ext = imagem.filename.rsplit('.', 1)[-1]
            nome_arquivo = f"{uuid.uuid4()}.{ext}"
            storage_path = f"propostas/{nome_arquivo}"

            try:
                supabase.storage.from_("uploads").upload(storage_path, imagem.read())
                url_imagem = f"{SUPABASE_URL}/storage/v1/object/public/uploads/{storage_path}"
            except Exception as e:
                flash(f"Erro ao fazer upload da imagem: {e}", "danger")
                return redirect(url_for("form"))

        data = {
            "pn": pn,
            "descricao": descricao,
            "plataforma": plataforma,
            "carro": carro,
            "planta": planta,
            "codigo": codigo,
            "fornecedor": fornecedor,
            "endereco": endereco,
            "cidade": cidade,
            "duns": duns,
            "responsavel": responsavel,
            "email": email,
            "celular": celular,
            "imagem_url": url_imagem,
            "rep_fornecedor": rep_fornecedor,
            "aprov_fornecedor": aprov_fornecedor,
            "rep_containers": rep_containers,
            "aprov_containers": aprov_containers,
            "data_aprov_fornecedor": data_aprov_fornecedor  # aqui adiciona a data/hora atual
        }

        try:
            supabase.table("formulario_propostas").insert(data).execute()

            email_recipients = ["bruno.j.ferrari@gm.com"]
            subject = "📋 New PPI Submitted"
            send_email_notificacao(email_recipients, subject, pn, fornecedor, planta, carro)

            flash("Proposta enviada com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao enviar proposta: {e}", "danger")

        return redirect(url_for("form"))

    return render_template("form.html")



@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("usuario")
    password = request.form.get("senha")

    if username == USUARIO_FIXO and password == SENHA_FIXA:
        session["user"] = username
        flash("Login efetuado com sucesso!", "success")
    else:
        flash("Usuário ou senha inválidos.", "danger")

    return redirect(url_for("registros"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("home"))

@app.route('/download')
def download():
    return render_template('download.html')

import uuid

@app.route('/editar/<registro_id>', methods=['GET', 'POST'])
def editar_formulario(registro_id):
    print(f"Editar registro id: {registro_id}")

    if request.method == 'POST':
        # Pega dados do formulário
        pn = request.form.get("pn")
        descricao = request.form.get("descricao")
        plataforma = request.form.get("plataforma")
        carro = request.form.get("carro")
        planta = request.form.get("planta")
        codigo = request.form.get("codigo")

        fornecedor = request.form.get("fornecedor")
        endereco = request.form.get("endereco")
        cidade = request.form.get("cidade")
        duns = request.form.get("duns")
        responsavel = request.form.get("responsavel")
        email = request.form.get("email")
        celular = request.form.get("celular")

        rep_fornecedor = request.form.get("rep_fornecedor")
        aprov_fornecedor = request.form.get("aprov_fornecedor")
        rep_containers = request.form.get("rep_containers")
        aprov_containers = request.form.get("aprov_containers")
        notificar_tabela = request.form.get("notificar_tabela") == "sim"

        # Captura data e hora atual para data_aprov_fornecedor
        data_aprov_containers = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        imagem = request.files.get("imagem")

        # Buscar registro atual para obter URL da imagem anterior
        response_atual = supabase.table("formulario_propostas").select("*").eq("id", registro_id).execute()
        if not response_atual.data or len(response_atual.data) == 0:
            flash("Registro não encontrado para edição.", "danger")
            return redirect(url_for("pendentes"))
        registro_atual = response_atual.data[0]

        url_imagem = registro_atual.get("imagem_url")

        # Upload de nova imagem se enviada
        if imagem and imagem.filename != '':
            ext = imagem.filename.rsplit('.', 1)[-1]
            nome_arquivo = f"{uuid.uuid4()}.{ext}"
            storage_path = f"propostas/{nome_arquivo}"
            supabase.storage.from_("uploads").upload(storage_path, imagem.read())
            url_imagem = f"{SUPABASE_URL}/storage/v1/object/public/uploads/{storage_path}"

        data_update = {
            "pn": pn,
            "descricao": descricao,
            "plataforma": plataforma,
            "carro": carro,
            "planta": planta,
            "codigo": codigo,
            "fornecedor": fornecedor,
            "endereco": endereco,
            "cidade": cidade,
            "duns": duns,
            "responsavel": responsavel,
            "email": email,
            "celular": celular,
            "imagem_url": url_imagem,
            "rep_fornecedor": rep_fornecedor,
            "aprov_fornecedor": aprov_fornecedor,
            "rep_containers": rep_containers,
            "aprov_containers": aprov_containers,
            "data_aprov_containers": data_aprov_containers  # aqui adiciona a data/hora atual
        }

        print(f"Dados para update: {data_update}")

        response = supabase.table("formulario_propostas").update(data_update).eq("id", registro_id).execute()
        print("Resposta completa do update:", response)

        if response.data:
            # Primeiro envio: aprovação
            try:
                print("Valor de aprov_containers:", aprov_containers)

                if aprov_containers in ["aprovado", "reprovado"]:
                    email_recipients = [email]
                    send_email_aprovacao(
                        email_recipients,
                        pn=pn,
                        fornecedor=fornecedor,
                        aprov_containers=aprov_containers
                    )
                    flash("Registro atualizado e e-mail de aprovação enviado com sucesso!", "success")
                else:
                    flash("Registro atualizado. Aguardando aprovação, e-mail de aprovação não enviado.", "info")

            except Exception as e:
                print("Erro ao enviar e-mail de aprovação:", str(e))
                flash("Registro atualizado, mas houve um erro ao enviar o e-mail de aprovação.", "warning")

            # Segundo envio: notificar tabela MGO
            if notificar_tabela:
                try:
                    send_email_mgo(
                        destinatario=["bruno.j.ferrari@gm.com"],
                        pn=pn,
                        fornecedor=fornecedor,
                        planta=planta,
                        duns=duns
                    )
                    flash("E-mail de atualização MGO enviado com sucesso!", "success")
                except Exception as e:
                    print("Erro ao enviar e-mail MGO:", str(e))
                    flash("Houve um erro ao enviar o e-mail de atualização MGO.", "warning")

        else:
            flash("Erro ao atualizar registro. Verifique o ID e os dados enviados.", "danger")

        # Em qualquer dos casos acima, redireciona
        return redirect(url_for("pendentes"))

    else:
        # Requisição GET - buscar dados e exibir formulário para edição
        response = supabase.table("formulario_propostas").select("*").eq("id", registro_id).execute()
        if response.data and len(response.data) > 0:
            registro = response.data[0]
            return render_template("editar_formulario.html", registro=registro)
        else:
            flash("Registro não encontrado.", "danger")
            return redirect(url_for("pendentes"))


@app.route('/editar_formulario_forn/<registro_id>', methods=['GET', 'POST'])
@fornecedor_login_required
def editar_formulario_forn(registro_id):
    duns_session = session.get('duns')
    token_session = session.get('token')

    if not duns_session or not token_session:
        flash("Sua sessão expirou. Faça login novamente.", "warning")
        return redirect(url_for("loginforn"))

    if request.method == 'POST':
        # Captura os campos enviados pelo formulário
        pn = request.form.get("pn")
        descricao = request.form.get("descricao")
        plataforma = request.form.get("plataforma")
        carro = request.form.get("carro")
        planta = request.form.get("planta")
        codigo = request.form.get("codigo")

        fornecedor = request.form.get("fornecedor")
        endereco = request.form.get("endereco")
        cidade = request.form.get("cidade")
        duns = duns_session  # Sempre usa o DUNS da sessão

        responsavel = request.form.get("responsavel")
        email = request.form.get("email")
        celular = request.form.get("celular")

        rep_fornecedor = request.form.get("rep_fornecedor")
        aprov_fornecedor = request.form.get("aprov_fornecedor")
        rep_containers = request.form.get("rep_containers")
        aprov_containers = request.form.get("aprov_containers")
        notificar_tabela = request.form.get("notificar_tabela") == "sim"

        # Captura data e hora atual para data_aprov_fornecedor
        data_aprov_fornecedor = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        imagem = request.files.get("imagem")

        try:
            # Buscar o registro atual e validar o DUNS
            response_atual = supabase.table("formulario_propostas").select("*").eq("id", registro_id).execute()

            if not response_atual.data:
                flash("Registro não encontrado para edição.", "danger")
                return redirect(url_for("registrosforn"))

            registro_atual = response_atual.data[0]

            if registro_atual.get("duns") != duns_session:
                flash("Você não tem permissão para editar este registro.", "danger")
                return redirect(url_for("registrosforn"))

            url_imagem = registro_atual.get("imagem_url")

            # Se houver nova imagem, faz upload
            if imagem and imagem.filename != '':
                ext = imagem.filename.rsplit('.', 1)[-1]
                nome_arquivo = f"{uuid.uuid4()}.{ext}"
                storage_path = f"propostas/{nome_arquivo}"

                supabase.storage.from_("uploads").upload(storage_path, imagem.read())
                url_imagem = f"{SUPABASE_URL}/storage/v1/object/public/uploads/{storage_path}"

            # Monta o dicionário para update
            data_update = {
                "pn": pn,
                "descricao": descricao,
                "plataforma": plataforma,
                "carro": carro,
                "planta": planta,
                "codigo": codigo,
                "fornecedor": fornecedor,
                "endereco": endereco,
                "cidade": cidade,
                "duns": duns,
                "responsavel": responsavel,
                "email": email,
                "celular": celular,
                "imagem_url": url_imagem,
                "rep_fornecedor": rep_fornecedor,
                "aprov_fornecedor": aprov_fornecedor,
                "rep_containers": rep_containers,
                "aprov_containers": aprov_containers,
                "data_aprov_fornecedor": data_aprov_fornecedor  # aqui adiciona a data/hora atual
            }

            # Faz o update no Supabase
            response = supabase.table("formulario_propostas").update(data_update).eq("id", registro_id).execute()

            if response.data:
                # Envia e-mail de aprovação containers, se necessário
                if aprov_containers in ["aguardando aprovacao"]:
                    try:
                        email_recipients = ["bruno.j.ferrari@gm.com"]
                        subject = "📋 New PPI Submitted"
                        send_email_notificacao(email_recipients, subject, pn, fornecedor, planta, carro)

                        flash("Proposta enviada com sucesso!", "success")
                    except Exception as e:
                        print(f"Erro ao enviar proposta: {e}")
                        flash("Registro atualizado. Erro ao enviar o e-mail da proposta.", "warning")
                else:
                    flash("Registro atualizado com sucesso.", "info")

                # Envia e-mail MGO, se solicitado
                if notificar_tabela:
                    try:
                        send_email_mgo(
                            destinatario=["bruno.j.ferrari@gm.com"],
                            pn=pn,
                            fornecedor=fornecedor,
                            planta=planta,
                            duns=duns
                        )
                        flash("E-mail de atualização MGO enviado com sucesso!", "success")
                    except Exception as e:
                        print(f"Erro ao enviar e-mail MGO: {e}")
                        flash("Erro ao enviar e-mail MGO.", "warning")

                # Redireciona após sucesso
                return redirect(url_for("registrosforn"))

            else:
                flash("Erro ao atualizar o registro.", "danger")
                return redirect(url_for("registrosforn"))

        except Exception as e:
            print(f"Erro ao atualizar: {e}")
            flash("Erro interno ao processar a atualização.", "danger")
            return redirect(url_for("registrosforn"))

    else:
        # Método GET: carregar os dados atuais
        try:
            response = supabase.table("formulario_propostas").select("*").eq("id", registro_id).execute()

            if response.data:
                registro = response.data[0]

                if registro.get("duns") != duns_session:
                    flash("Você não tem permissão para acessar este registro.", "danger")
                    return redirect(url_for("registrosforn"))

                return render_template("editar_formulario_forn.html", registro=registro)

            else:
                flash("Registro não encontrado.", "danger")
                return redirect(url_for("registrosforn"))

        except Exception as e:
            print(f"Erro ao carregar registro: {e}")
            flash("Erro ao carregar os dados do registro.", "danger")
            return redirect(url_for("registrosforn"))



@app.route("/registros")
@login_required
def registros():
    pn_filter = request.args.get("pn", "").strip()
    fornecedor_filter = request.args.get("fornecedor", "").strip()
    duns_filter = request.args.get("duns", "").strip()

    # Filtra registros onde aprov_containers = "aprovado"
    query = supabase.table("formulario_propostas").select("*").eq("aprov_containers", "aprovado")

    if pn_filter:
        query = query.ilike("pn", f"%{pn_filter}%")
    if fornecedor_filter:
        query = query.ilike("fornecedor", f"%{fornecedor_filter}%")
    if duns_filter:
        query = query.ilike("duns", f"%{duns_filter}%")

    try:
        response = query.execute()
        registros = response.data
    except Exception as e:
        registros = []
        flash(f"Erro ao carregar registros: {e}", "danger")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("tabela_registros.html", registros=registros)

    return render_template(
        "registros.html",
        registros=registros,
        pn_filter=pn_filter,
        fornecedor_filter=fornecedor_filter,
        duns_filter=duns_filter
    )


@app.route('/downloads')
def downloads():
    return render_template('downloads.html')

@app.route('/registrosforn')
@fornecedor_login_required
def registrosforn():
    duns = session.get('duns')

    # Opcional: validar token no backend para garantir sessão válida (se necessário)

    # Buscar todos os registros do fornecedor logado
    try:
        response = supabase.table("formulario_propostas").select("*").eq("duns", duns).execute()
        registros = response.data if response.data else []
    except Exception as e:
        print(f"Erro ao buscar registros: {e}")
        flash("Erro ao carregar registros.", "danger")
        registros = []

    return render_template("registrosforn.html", registros=registros)





@app.route("/loginforn", methods=["GET", "POST"])
def loginforn():
    if request.method == "POST":
        duns = request.form.get("duns", "").strip()
        token = request.form.get("token", "").strip()

        if not duns or not token:
            flash("Por favor, preencha o DUNS e o Token.", "warning")
            return render_template("loginforn.html")

        try:
            # Validação no Supabase: Confirma se existe o fornecedor com esse DUNS + Token
            fornecedor_resp = supabase.table("fornecedores")\
                .select("*")\
                .eq("duns", duns)\
                .eq("token", token)\
                .execute()

            fornecedores = fornecedor_resp.data

            if not fornecedores:
                flash("DUNS ou Token inválidos. Tente novamente.", "danger")
                return render_template("loginforn.html")

            # ✅ Login bem-sucedido: Salvar na sessão
            session["duns"] = duns
            session["token"] = token

            flash("Login realizado com sucesso!", "success")

            # ✅ Redireciona diretamente para a página de registros filtrados pelo DUNS
            return redirect(url_for("registrosforn"))

        except Exception as e:
            flash(f"Erro ao validar login: {e}", "danger")
            return render_template("loginforn.html")

    # Se for GET → Exibe o formulário de login
    return render_template("loginforn.html")

@app.route('/logout_forn')
def logout_forn():
    # Remove dados do fornecedor da sessão
    session.pop('duns', None)
    session.pop('token', None)
    flash('Logout do fornecedor realizado com sucesso.', 'success')
    return redirect(url_for('home'))  # ou 'home' se preferir


@app.route("/pendentes")
@login_required
def pendentes():
    pn_filter = request.args.get("pn", "").strip()
    fornecedor_filter = request.args.get("fornecedor", "").strip()

    query = supabase.table("formulario_propostas").select("*").eq("aprov_containers", "aguardando aprovacao")

    if pn_filter:
        query = query.ilike("pn", f"%{pn_filter}%")
    if fornecedor_filter:
        query = query.ilike("fornecedor", f"%{fornecedor_filter}%")

    try:
        response = query.execute()
        registros = response.data
    except Exception as e:
        registros = []
        flash(f"Erro ao carregar registros: {e}", "danger")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("tabela_registros.html", registros=registros)

    return render_template("pendentes.html", registros=registros, pn_filter=pn_filter, fornecedor_filter=fornecedor_filter)

@app.route("/gerar_pdf/<registro_id>")

def gerar_pdf(registro_id):
    response = supabase.table("formulario_propostas").select("*").eq("id", registro_id).single().execute()
    registro = response.data

    if not registro:
        flash("Registro não encontrado.", "warning")
        return redirect(url_for("registros"))

    html = render_template("pdf_template.html", registro=registro)
    pdf_io = io.BytesIO()
    HTML(string=html).write_pdf(pdf_io)
    pdf_io.seek(0)

    return send_file(pdf_io, download_name="proposta.pdf", as_attachment=True)

def send_email_notificacao(email_recipients, subject, pn, fornecedor, planta, carro):
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = ";".join(email_recipients)
        mail.Subject = subject

        html_body = f"""
        <html>
        <body>
            <div style="font-family:Segoe UI, sans-serif;">
                <h2 style="color:#0078d7;">📋 New PPI Submitted</h2>
                <p>A New Packaging Proposal Information (PPI) has been submitted and is awaiting approval:</p>
                <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
                    <tr><th>PN</th><td>{pn}</td></tr>
                    <tr><th>Supplier</th><td>{fornecedor}</td></tr>
                    <tr><th>Plant</th><td>{planta}</td></tr>
                    <tr><th>Carline</th><td>{carro}</td></tr>
                </table>
                <p>Check the system for more information.</p>
                <p>Best regards!</p>
            </div>
        </body>
        </html>
        """

        mail.HTMLBody = html_body
        mail.Send()
        print("✅ E-mail enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

def send_email_aprovacao(email_recipients, pn, fornecedor, aprov_containers):
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = ";".join(email_recipients)

        if aprov_containers == "aprovado":
            status_text = "✅ PPI Approved"
            body_msg = "The PPI sent is <strong>aprovada</strong>."
        elif aprov_containers == "reprovado":
            status_text = "❌ PPI Not Approved"
            body_msg = "The PPI sent is <strong>reprovada</strong>."
        else:
            status_text = "🕒 Awaiting Approval"
            body_msg = "The PPI sent is <strong>aguardando aprovação</strong>."

        mail.Subject = f"{status_text} - PN {pn}"

        html_body = f"""
        <html>
        <body style="font-family:Segoe UI, sans-serif;">
            <h2>{status_text}</h2>
            <p>Hello,</p>
            <p>{body_msg}</p>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
                <tr><th>PN</th><td>{pn}</td></tr>
                <tr><th>Supplier</th><td>{fornecedor}</td></tr>
                <tr><th>Status</th><td>{aprov_containers.title()}</td></tr>
            </table>
            <p>Check the system for more information.</p>
            <p>Best regards!</p>
        </body>
        </html>
        """
        mail.HTMLBody = html_body
        mail.Send()
        print("📧 E-mail de aprovação enviado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail de aprovação: {e}")
       
@app.route('/fornecedores')
def fornecedores():
    # Pega todos os fornecedores cadastrados
    response = supabase.table("fornecedores").select("*").execute()
    fornecedores = response.data if response.data else []
    
    return render_template('fornecedores.html', fornecedores=fornecedores)

@app.route('/editar_fornecedor/<registro_id>', methods=['GET', 'POST'])
def editar_fornecedor(registro_id):
    # Buscar dados do fornecedor no Supabase
    response = supabase.table('fornecedores').select('*').eq('id', registro_id).single().execute()
    fornecedor = response.data

    if not fornecedor:
        flash("Fornecedor não encontrado.", "error")
        return redirect(url_for('fornecedores'))

    if request.method == 'POST':
        # Pega os dados do formulário
        nome = request.form.get('nome')
        endereco = request.form.get('endereco')
        cidade = request.form.get('cidade')
        pais = request.form.get('pais')
        duns = request.form.get('duns')
        token = request.form.get('token')

        # Atualiza os dados no Supabase
        update_response = supabase.table('fornecedores').update({
            'nome': nome,
            'endereco': endereco,
            'cidade': cidade,
            'pais': pais,
            'duns': duns,
            'token': token
        }).eq('id', registro_id).execute()

        if update_response and update_response.data:
            flash("Fornecedor atualizado com sucesso!", "success")
            return redirect(url_for('fornecedores'))
        else:
            flash("Erro ao atualizar fornecedor.", "error")


    return render_template('editar_fornecedor.html', fornecedor=fornecedor)


@app.route('/solicitar', methods=['GET', 'POST'])
@login_required
def solicitar():
    if request.method == 'POST':
        dados_json = request.form.get('dados_excel', '[]')
        linhas = json.loads(dados_json)

        # Filtra linhas que têm pelo menos 6 colunas e todos os campos preenchidos
        linhas_validas = [linha for linha in linhas if len(linha) >= 6 and all(c.strip() for c in linha[:6])]
        if not linhas_validas:
            flash("Preencha pelo menos uma linha válida e um e-mail para envio.", "warning")
            return render_template('solicitar.html')

        emails_unicos = sorted(set(linha[5].strip() for linha in linhas_validas))
        pns = [linha[1].strip() for linha in linhas_validas]  # coluna 1 é PN

        try:
            # Cria a solicitação e captura a data
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            solicitacao_resp = supabase.table('solicitacoes').insert({
                'data_solicitacao': data_atual,
                'emails': ';'.join(emails_unicos),
                'status': 'enviada',
                'pns': pns
            }).execute()

            if not solicitacao_resp.data or len(solicitacao_resp.data) == 0:
                raise Exception("Falha ao criar a solicitação no banco")

            solicitacao_id = solicitacao_resp.data[0]['id']
            data_solicitacao = solicitacao_resp.data[0]['data_solicitacao']

            # Insere cada linha na tabela formulario_propostas vinculando solicitacao_id e data
            for linha in linhas_validas:
                planta, pn, descricao, duns, fornecedor, email = linha[:6]

                supabase.table('formulario_propostas').insert({
                    'email': email,
                    'pn': pn,
                    'descricao': descricao,
                    'plataforma': '',
                    'carro': '',
                    'planta': planta,
                    'codigo': '',
                    'fornecedor': fornecedor,
                    'endereco': '',
                    'cidade': '',
                    'duns': duns,
                    'responsavel': '',
                    'celular': '',
                    'rep_fornecedor': '',
                    'aprov_fornecedor': '',
                    'rep_containers': '',
                    'aprov_containers': 'aguardando proposta',
                    'imagem_url': None,
                    'solicitacao_id': solicitacao_id,
                    'data_solicitacao': data_solicitacao,
                    'data_aprov_fornecedor': None,
                    'data_aprov_containers': None
                }).execute()

            # Envia e-mails agrupados
            send_email_solicitacao(emails_unicos, linhas_validas)

            flash("Solicitação enviada e registrada com sucesso!", "success")

        except Exception as e:
            print("⛔ ERRO DETALHADO:")
            traceback.print_exc()
            flash(f"Erro ao processar solicitação: {repr(e)}", "error")

    return render_template('solicitar.html')






@app.route('/buscar_email', methods=['POST'])
def buscar_email():
    data = request.json or {}
    duns = data.get("duns", "").strip()

    if not duns:
        return jsonify({"email": ""})

    try:
        # Busca o email na tabela fornecedores pelo DUNS, limitando 1 resultado
        result = supabase.table("fornecedores").select("emailforn").eq("duns", duns).limit(1).execute()
        if result.data and len(result.data) > 0:
            return jsonify({"email": result.data[0].get("emailforn", "") or ""})
        else:
            return jsonify({"email": ""})
    except Exception as e:
        # Log do erro pode ser adicionado aqui se quiser
        return jsonify({"email": ""})

@app.route("/solicitacoes_em_aberto")
def solicitacoes_em_aberto():
    response = supabase.table("formulario_propostas").select("*").eq("aprov_containers", "aguardando proposta").execute()
    registros_abertos = response.data if response.data else []
    return render_template("solicitacoes_em_aberto.html", registros=registros_abertos)


def send_email_solicitacao(email_recipients, linhas_solicitadas):
    try:
        # Garante que email_recipients é uma lista
        if isinstance(email_recipients, str):
            email_recipients = [email_recipients]

        # Agrupa linhas por e-mail
        grupos_por_email = {}
        for linha in linhas_solicitadas:
            # Verifica se tem pelo menos 6 colunas e campos não vazios
            if len(linha) < 6 or any(not str(campo).strip() for campo in linha[:6]):
                continue
            planta, pn, descricao, duns, fornecedor, email = linha[:6]
            email = email.lower()
            grupos_por_email.setdefault(email, []).append((planta, pn, descricao, duns, fornecedor))

        outlook = win32com.client.Dispatch("Outlook.Application")

        # Envia um email para cada destinatário com suas linhas
        for email, linhas in grupos_por_email.items():
            mail = outlook.CreateItem(0)
            mail.To = email
            mail.Subject = "📋 Packaging Proposal Information (PPI) Request"

            linhas_html = ""
            for planta, pn, descricao, duns, fornecedor in linhas:
                linhas_html += f"""
                <tr>
                    <td>{planta}</td>
                    <td>{pn}</td>
                    <td>{descricao}</td>
                    <td>{duns}</td>
                    <td>{fornecedor}</td>
                </tr>
                """

            html_body = f"""
            <html>
            <body style="font-family:Segoe UI, sans-serif;">
                <h2>📋 PPI Request</h2>
                <p>Hello,</p>
                <p>We are contacting you because we need the PPI (Packaging Proposal Information) for the item(s) below:</p>
                <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                            <th>Plant</th>
                            <th>PN</th>
                            <th>Description</th>
                            <th>DUNS</th>
                            <th>Supplier</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_html}
                    </tbody>
                </table>
                <p>Please evaluate and get back to us as soon as possible.</p>
                <p>Best regards!</p>
            </body>
            </html>
            """

            mail.HTMLBody = html_body
            mail.Send()
            print(f"📧 E-mail enviado para {email} com {len(linhas)} item(s).")

    except Exception as e:
        print(f"❌ Erro ao enviar e-mail de solicitação: {e}")
        import traceback
        traceback.print_exc()


        
def send_email_mgo(destinatario, pn, fornecedor, planta, duns):
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = ";".join(destinatario)
        mail.Subject = "📋 Solicitação de Atualização de Cadastro no MGO"

        html_body = f"""
        <html>
        <body>
            <div style="font-family:Segoe UI, sans-serif;">
                <h2 style="color:#0078d7;">Solicitação de Atualização no MGO</h2>
                <p>Olá,</p>
                <p>Solicitamos que atualize o cadastro no sistema MGO referente à seguinte proposta:</p>
                <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
                    <tr><th>PN</th><td>{pn}</td></tr>
                    <tr><th>Fornecedor</th><td>{fornecedor}</td></tr>
                    <tr><th>Planta</th><td>{planta}</td></tr>
                    <tr><th>DUNS</th><td>{duns}</td></tr>
                </table>
                <p>Obrigado!</p>
            </div>
        </body>
        </html>
        """

        mail.HTMLBody = html_body
        mail.Send()
        print("✅ E-mail MGO enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail MGO: {e}")

if __name__ == "__main__":
    app.run(debug=True)
