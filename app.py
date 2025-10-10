import os
from flask import Flask, request, render_template, redirect, flash, send_file, session, url_for, get_flashed_messages, request, make_response, jsonify
from supabase import create_client, Client
from collections import defaultdict
import uuid
import json
from weasyprint import HTML
import io
if os.name == 'nt':  # só importa no Windows
    import win32com.client
from functools import wraps
import secrets
import random
import string
import json
from datetime import datetime
import traceback
from urllib.parse import urlparse, parse_qs
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

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

EMAIL_USER="brunojb_ferrari@hotmail.com"

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
@fornecedor_login_required
def form():
    duns_sessao = session.get("duns")

    # Busca dados do fornecedor
    fornecedor_data = None
    try:
        result = supabase.table("fornecedores").select(
            "nome", "endereco", "cidade", "pais", "duns", "emailforn"
        ).eq("duns", duns_sessao).single().execute()

        if result.data:
            fornecedor_data = result.data
        else:
            flash("Não foi possível encontrar os dados do fornecedor.", "danger")
            return redirect(url_for("logout_forn"))
    except Exception as e:
        flash(f"Erro ao buscar dados do fornecedor: {e}", "danger")
        return redirect(url_for("logout_forn"))

    if request.method == "POST":
        # --- BLOCO 1 ---
        pn = request.form.get("pn")
        descricao = request.form.get("descricao")
        plataforma = request.form.get("plataforma")
        carline = request.form.get("carline")
        planta = request.form.get("planta")
        codigo_planta = request.form.get("codigo_planta")
        cisco = request.form.get("cisco")

        # --- BLOCO 2 ---
        fornecedor = fornecedor_data["nome"]
        endereco = fornecedor_data["endereco"]
        cidade = fornecedor_data["cidade"]
        pais = fornecedor_data["pais"]
        duns = fornecedor_data["duns"]
        email = request.form.get("email")
        responsavel = request.form.get("responsavel")

        # --- BLOCO 3 ---
        aplicavel = request.form.get("aplicavel")
        classe_material = request.form.get("classe_material")
        homologacao = request.form.get("homologacao")
        codigo_onu = request.form.get("codigo_onu")
        etiqueta_identificacao = request.form.get("etiqueta_identificacao")
        etiqueta_risco = request.form.get("etiqueta_risco")
        etiqueta_manuseio = request.form.get("etiqueta_manuseio")

        # --- BLOCO 4 ---
        def parse_float(valor):
            try:
                return float(valor) if valor else None
            except:
                return None

        tipo_primaria = request.form.get("tipo_primaria")
        material_primaria = request.form.get("material_primaria")
        codigo_embalagem_primaria = request.form.get("codigo_embalagem_primaria")
        comprimento_primaria = parse_float(request.form.get("comprimento_primaria"))
        largura_primaria = parse_float(request.form.get("largura_primaria"))
        altura_primaria = parse_float(request.form.get("altura_primaria"))
        standard_pack_primaria = request.form.get("standard_pack_primaria")
        tara_primaria = parse_float(request.form.get("tara_primaria"))
        peso_unitario_primaria = parse_float(request.form.get("peso_unitario_primaria"))
        peso_total_primaria = parse_float(request.form.get("peso_total_primaria"))
        altura_nao_ocupada_primaria = parse_float(request.form.get("altura_nao_ocupada_primaria"))
        ocupacao_primaria = parse_float(request.form.get("ocupacao_primaria"))
        motivo_primaria = request.form.get("motivo_primaria")

        foto_peca_primaria = request.files.get("foto_peca_primaria")
        foto_embalagem_peca_primaria = request.files.get("foto_embalagem_peca_primaria")

        # --- BLOCO 5: Insumos ---
        materiais = request.form.getlist("material[]")
        comprimentos_insumo = request.form.getlist("comprimento_insumo[]")
        larguras_insumo = request.form.getlist("largura_insumo[]")
        espessuras_insumo = request.form.getlist("espessura_insumo[]")
        pesos_unitarios_insumo = request.form.getlist("pesounitario_insumo[]")
        imagens_insumo = request.files.getlist("imagem[]")

        lista_insumos = []
        for i in range(len(materiais)):
            insumo_data = {
                "material": materiais[i],
                "comprimento": parse_float(comprimentos_insumo[i]),
                "largura": parse_float(larguras_insumo[i]),
                "espessura": parse_float(espessuras_insumo[i]),
                "peso_unitario": parse_float(pesos_unitarios_insumo[i]),
                "imagem_url": None
            }

            if imagens_insumo[i] and imagens_insumo[i].filename != '':
                ext = imagens_insumo[i].filename.rsplit('.', 1)[-1]
                nome_arquivo = f"{uuid.uuid4()}.{ext}"
                storage_path = f"insumos/{nome_arquivo}"
                try:
                    supabase.storage.from_("uploads").upload(storage_path, imagens_insumo[i].read())
                    insumo_data["imagem_url"] = f"{SUPABASE_URL}/storage/v1/object/public/uploads/{storage_path}"
                except Exception as e:
                    flash(f"Erro ao fazer upload da imagem do insumo: {e}", "danger")
                    return redirect(url_for("form"))

            lista_insumos.append(insumo_data)

         # --- BLOCO 6: Embalagem Secundária ---
        aplicavel_secundaria = request.form.get("aplicavel_secundaria")
        caixas_camadas_secundaria = request.form.get("caixas_camadas_secundaria")
        camadas_pallet_secundaria = request.form.get("camadas_pallet_secundaria")
        pecas_pallet_secundaria = request.form.get("pecas_pallet_secundaria")
        comprimento_pallet_secundaria = request.form.get("comprimento_pallet_secundaria")
        largura_pallet_secundaria = request.form.get("largura_pallet_secundaria")
        altura_pallet_secundaria = request.form.get("altura_pallet_secundaria")
        peso_pallet_secundaria = request.form.get("peso_pallet_secundaria")
        material_pallet_secundaria = request.form.get("material_pallet_secundaria")
        comprimento_total_secundaria = request.form.get("comprimento_total_secundaria")
        largura_total_secundaria = request.form.get("largura_total_secundaria")
        altura_total_secundaria = request.form.get("altura_total_secundaria")
        peso_total_secundaria = request.form.get("peso_total_secundaria")
        foto_secundaria = request.files.get("foto_secundaria")

        # --- BLOCO 7: Empilhamento ---
        empilhamento_estatico = request.form.get("empilhamento_estatico")
        empilhamento_dinamico = request.form.get("empilhamento_dinamico")

        # --- BLOCO 8: Embalagem Alternativa Descartável ---
        # Primária descartável
        comprimento_primaria_descartavel = request.form.get("comprimento_primaria_descartavel")
        largura_primaria_descartavel = request.form.get("largura_primaria_descartavel")
        altura_primaria_descartavel = request.form.get("altura_primaria_descartavel")
        peso_primaria_descartavel = request.form.get("peso_primaria_descartavel")
        pecas_caixa_primaria_descartavel = request.form.get("pecas_caixa_primaria_descartavel")
        # Secundária descartável
        comprimento_secundaria_descartavel = request.form.get("comprimento_secundaria_descartavel")
        largura_secundaria_descartavel = request.form.get("largura_secundaria_descartavel")
        altura_secundaria_descartavel = request.form.get("altura_secundaria_descartavel")
        peso_secundaria_descartavel = request.form.get("peso_secundaria_descartavel")
        pecas_pallet_descartavel = request.form.get("pecas_pallet_descartavel")
        foto_descartavel = request.files.get("foto_descartavel")

        # --- BLOCO 9: Observações ---
        comentario8 = request.form.get("comentario8")

        # --- BLOCO 10: Aprovação ---
        rep_fornecedor = request.form.get("rep_fornecedor")
        aprov_fornecedor = request.form.get("aprov_fornecedor")
        rep_containers = request.form.get("rep_containers")
        aprov_containers = request.form.get("aprov_containers") or "aguardando aprovacao"
        data_aprov_fornecedor = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        def upload_imagem(arquivo, pasta):
            if arquivo and arquivo.filename != '':
                ext = arquivo.filename.rsplit('.', 1)[-1]
                nome_arquivo = f"{uuid.uuid4()}.{ext}"
                storage_path = f"{pasta}/{nome_arquivo}"
                try:
                    supabase.storage.from_("uploads").upload(storage_path, arquivo.read())
                    return f"{SUPABASE_URL}/storage/v1/object/public/uploads/{storage_path}"
                except Exception as e:
                    flash(f"Erro ao fazer upload da imagem: {e}", "danger")
                    return None
            return None

        url_foto_peca_primaria = upload_imagem(foto_peca_primaria, "propostas")
        url_foto_embalagem_primaria = upload_imagem(foto_embalagem_peca_primaria, "propostas")
        url_foto_secundaria = upload_imagem(foto_secundaria, "propostas")
        url_foto_descartavel = upload_imagem(foto_descartavel, "propostas")

        # -------------------- NOVA LÓGICA: EXCLUIR PNs EXISTENTES --------------------
        try:
            lista_pns = [p.strip() for p in pn.split(",") if p.strip()]

            # Ignora o primeiro PN (considera do segundo em diante)
            for pn_item in lista_pns[1:]:
                registros_existentes = supabase.table("formulario_propostas")\
                    .select("id, pn, aprov_containers")\
                    .eq("pn", pn_item)\
                    .eq("aprov_containers", "aguardando proposta")\
                    .execute()

                if registros_existentes.data:
                    for r in registros_existentes.data:
                        delete_result = supabase.table("formulario_propostas")\
                            .delete()\
                            .eq("id", r["id"])\
                            .execute()

                        print(f"🗑️ Exclusão executada para ID {r['id']} (PN {r['pn']}). Retorno Supabase:", delete_result)
        except Exception as e:
            print(f"❌ Erro ao excluir PNs existentes: {e}")
            flash("Erro ao processar exclusão de PNs existentes.", "danger")


        # Monta dados para envio ao Supabase
        data = {
            # Bloco 1
            "pn": pn,
            "descricao": descricao,
            "plataforma": plataforma,
            "carline": carline,
            "planta": planta,
            "codigo_planta": codigo_planta,
            "cisco": cisco,
            # Bloco 2
            "fornecedor": fornecedor,
            "endereco": endereco,
            "cidade": cidade,
            "pais": pais,
            "duns": duns,
            "responsavel": responsavel,
            "email": email,
            # Bloco 3
            "aplicavel": aplicavel,
            "classe_material": classe_material,
            "homologacao": homologacao,
            "codigo_onu": codigo_onu,
            "etiqueta_identificacao": etiqueta_identificacao,
            "etiqueta_risco": etiqueta_risco,
            "etiqueta_manuseio": etiqueta_manuseio,
            # Bloco 4
            "tipo_primaria": tipo_primaria,
            "material_primaria": material_primaria,
            "codigo_embalagem_primaria": codigo_embalagem_primaria,
            "comprimento_primaria": comprimento_primaria,
            "largura_primaria": largura_primaria,
            "altura_primaria": altura_primaria,
            "standard_pack_primaria": standard_pack_primaria,
            "tara_primaria": tara_primaria,
            "peso_unitario_primaria": peso_unitario_primaria,
            "peso_total_primaria": peso_total_primaria,
            "altura_nao_ocupada_primaria": altura_nao_ocupada_primaria,
            "ocupacao_primaria": ocupacao_primaria,
            "motivo_primaria": motivo_primaria,
            "foto_peca_primaria_url": url_foto_peca_primaria,
            "foto_embalagem_peca_primaria_url": url_foto_embalagem_primaria,
            # Bloco 5
            "insumos": lista_insumos,  # jsonb
            # Bloco 6
            "aplicavel_secundaria": aplicavel_secundaria,
            "caixas_camadas_secundaria": caixas_camadas_secundaria,
            "camadas_pallet_secundaria": camadas_pallet_secundaria,
            "pecas_pallet_secundaria": pecas_pallet_secundaria,
            "comprimento_pallet_secundaria": comprimento_pallet_secundaria,
            "largura_pallet_secundaria": largura_pallet_secundaria,
            "altura_pallet_secundaria": altura_pallet_secundaria,
            "peso_pallet_secundaria": peso_pallet_secundaria,
            "material_pallet_secundaria": material_pallet_secundaria,
            "comprimento_total_secundaria": comprimento_total_secundaria,
            "largura_total_secundaria": largura_total_secundaria,
            "altura_total_secundaria": altura_total_secundaria,
            "peso_total_secundaria": peso_total_secundaria,
            "foto_secundaria_url": url_foto_secundaria,
            # Bloco 7
            "empilhamento_estatico": empilhamento_estatico,
            "empilhamento_dinamico": empilhamento_dinamico,
            # Bloco 8
            "comprimento_primaria_descartavel": comprimento_primaria_descartavel,
            "largura_primaria_descartavel": largura_primaria_descartavel,
            "altura_primaria_descartavel": altura_primaria_descartavel,
            "peso_primaria_descartavel": peso_primaria_descartavel,
            "pecas_caixa_primaria_descartavel": pecas_caixa_primaria_descartavel,
            "comprimento_secundaria_descartavel": comprimento_secundaria_descartavel,
            "largura_secundaria_descartavel": largura_secundaria_descartavel,
            "altura_secundaria_descartavel": altura_secundaria_descartavel,
            "peso_secundaria_descartavel": peso_secundaria_descartavel,
            "pecas_pallet_descartavel": pecas_pallet_descartavel,
            "foto_descartavel_url": url_foto_descartavel,
            # Bloco 8
            "comentario8": comentario8,
            # Bloco 9
            "rep_fornecedor": rep_fornecedor,
            "aprov_fornecedor": aprov_fornecedor,
            "rep_containers": rep_containers,
            "aprov_containers": aprov_containers,
            "data_aprov_fornecedor": data_aprov_fornecedor
        }

        try:
            supabase.table("formulario_propostas").insert(data).execute()

            email_recipients = ["brunojb_ferrari@hotmail.com"]
            subject = "📋 New PPI Submitted - GMB"
            send_email_notificacao(email_recipients, subject, pn, fornecedor, planta, carline)

            flash("Proposta enviada com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao enviar proposta: {e}", "danger")

        return redirect(url_for("form"))

    return render_template("form.html", fornecedor_data=fornecedor_data)




@app.route("/get_embalagens")
def get_embalagens():
    tipo = request.args.get("tipo")
    material = request.args.get("material")
    codigo = request.args.get("codigo")  # opcional

    query = supabase.table("embalagens").select(
        "codigo, comprimento_ext, largura_ext, altura_ext, tara"
    ).eq("tipo", tipo).eq("material", material)

    if codigo:
        query = query.eq("codigo", codigo)

    response = query.execute()
    return jsonify(response.data)

from flask import jsonify

@app.route('/get_altura/<codigo>')
def get_altura(codigo):
    result = supabase.table('embalagens').select('altura_int').eq('codigo', codigo).single().execute()

    # result.data pode ser None ou {}
    if not result.data or 'altura_int' not in result.data:
        return jsonify({"error": "Registro não encontrado"}), 404

    return jsonify({"altura_int": result.data['altura_int']})

from flask import jsonify

@app.route("/api/embalagens/<codigo>", methods=["GET"])
def get_embalagem(codigo):
    try:
        result = supabase.table("embalagens").select("size").eq("codigo", codigo).execute()
        if result.data:
            return jsonify(result.data[0])
        else:
            return jsonify({"error": "Embalagem não encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_pns_fornecedor")
def get_pns_fornecedor():
    # Recupera o DUNS da sessão
    duns = session.get("duns")
    if not duns:
        return jsonify({"error": "Nenhum DUNS encontrado na sessão"}), 400

    # Agora filtrando corretamente pela coluna "duns"
    result = supabase.table("formulario_propostas") \
        .select("id, pn") \
        .eq("duns", duns) \
        .execute()

    if not result.data:
        return jsonify([])

    return jsonify(result.data)


@app.route("/get_dados_pn/<pn_id>")  # sem "int:"
def get_dados_pn(pn_id):
    result = supabase.table("formulario_propostas").select("*").eq("id", pn_id).execute()
    if not result.data:
        return jsonify({})
    return jsonify(result.data[0])




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
@fornecedor_login_required
def download():
    return render_template('download.html')

import uuid

@app.route('/editar/<registro_id>', methods=['GET', 'POST'])
def editar_formulario(registro_id):
    print(f"Editar registro id: {registro_id}")

    # Função para converter valores para float
    def parse_float(valor):
        try:
            return float(valor) if valor else None
        except:
            return None

    # Função para upload de imagens
    def upload_imagem(arquivo, pasta):
        if arquivo and arquivo.filename != '':
            ext = arquivo.filename.rsplit('.', 1)[-1]
            nome_arquivo = f"{uuid.uuid4()}.{ext}"
            storage_path = f"{pasta}/{nome_arquivo}"
            try:
                supabase.storage.from_("uploads").upload(storage_path, arquivo.read())
                return f"{SUPABASE_URL}/storage/v1/object/public/uploads/{storage_path}"
            except Exception as e:
                flash(f"Erro ao fazer upload da imagem: {e}", "danger")
                return None
        return None

    # Busca registro atual
    response_atual = supabase.table("formulario_propostas").select("*").eq("id", registro_id).execute()
    if not response_atual.data or len(response_atual.data) == 0:
        flash("Registro não encontrado para edição.", "danger")
        return redirect(url_for("pendentes"))
    registro_atual = response_atual.data[0]

    if request.method == 'POST':
        # --- BLOCO 1 ---
        pn = request.form.get("pn")
        descricao = request.form.get("descricao")
        plataforma = request.form.get("plataforma")
        carline = request.form.get("carline")
        planta = request.form.get("planta")
        codigo_planta = request.form.get("codigo_planta")
        cisco = request.form.get("cisco")

        # --- BLOCO 2 ---
        fornecedor = request.form.get("fornecedor")
        endereco = request.form.get("endereco")
        cidade = request.form.get("cidade")
        pais = request.form.get("pais")
        duns = request.form.get("duns")
        responsavel = request.form.get("responsavel")
        email = request.form.get("email")

        # --- BLOCO 3 ---
        aplicavel = request.form.get("aplicavel")
        classe_material = request.form.get("classe_material")
        homologacao = request.form.get("homologacao")
        codigo_onu = request.form.get("codigo_onu")
        etiqueta_identificacao = request.form.get("etiqueta_identificacao")
        etiqueta_risco = request.form.get("etiqueta_risco")
        etiqueta_manuseio = request.form.get("etiqueta_manuseio")

        # --- BLOCO 4 ---
        tipo_primaria = request.form.get("tipo_primaria")
        material_primaria = request.form.get("material_primaria")
        codigo_embalagem_primaria = request.form.get("codigo_embalagem_primaria")
        comprimento_primaria = parse_float(request.form.get("comprimento_primaria"))
        largura_primaria = parse_float(request.form.get("largura_primaria"))
        altura_primaria = parse_float(request.form.get("altura_primaria"))
        standard_pack_primaria = request.form.get("standard_pack_primaria")
        tara_primaria = parse_float(request.form.get("tara_primaria"))
        peso_unitario_primaria = parse_float(request.form.get("peso_unitario_primaria"))
        peso_total_primaria = parse_float(request.form.get("peso_total_primaria"))
        altura_nao_ocupada_primaria = parse_float(request.form.get("altura_nao_ocupada_primaria"))
        ocupacao_primaria = parse_float(request.form.get("ocupacao_primaria"))
        motivo_primaria = request.form.get("motivo_primaria")

        foto_peca_primaria = request.files.get("foto_peca_primaria")
        foto_embalagem_peca_primaria = request.files.get("foto_embalagem_peca_primaria")

        # --- BLOCO 5: Insumos ---
        materiais = request.form.getlist("material[]")
        comprimentos_insumo = request.form.getlist("comprimento_insumo[]")
        larguras_insumo = request.form.getlist("largura_insumo[]")
        espessuras_insumo = request.form.getlist("espessura_insumo[]")
        pesos_unitarios_insumo = request.form.getlist("pesounitario_insumo[]")
        imagens_insumo = request.files.getlist("imagem[]")

        lista_insumos = []
        for i in range(len(materiais)):
            insumo_data = {
                "material": materiais[i],
                "comprimento": parse_float(comprimentos_insumo[i]),
                "largura": parse_float(larguras_insumo[i]),
                "espessura": parse_float(espessuras_insumo[i]),
                "peso_unitario": parse_float(pesos_unitarios_insumo[i]),
                "imagem_url": None
            }
            if imagens_insumo[i] and imagens_insumo[i].filename != '':
                insumo_data["imagem_url"] = upload_imagem(imagens_insumo[i], "insumos")
            lista_insumos.append(insumo_data)

        # --- BLOCO 6: Embalagem Secundária ---
        aplicavel_secundaria = request.form.get("aplicavel_secundaria")
        caixas_camadas_secundaria = request.form.get("caixas_camadas_secundaria")
        camadas_pallet_secundaria = request.form.get("camadas_pallet_secundaria")
        pecas_pallet_secundaria = request.form.get("pecas_pallet_secundaria")
        comprimento_pallet_secundaria = request.form.get("comprimento_pallet_secundaria")
        largura_pallet_secundaria = request.form.get("largura_pallet_secundaria")
        altura_pallet_secundaria = request.form.get("altura_pallet_secundaria")
        peso_pallet_secundaria = request.form.get("peso_pallet_secundaria")
        material_pallet_secundaria = request.form.get("material_pallet_secundaria")
        comprimento_total_secundaria = request.form.get("comprimento_total_secundaria")
        largura_total_secundaria = request.form.get("largura_total_secundaria")
        altura_total_secundaria = request.form.get("altura_total_secundaria")
        peso_total_secundaria = request.form.get("peso_total_secundaria")
        foto_secundaria = request.files.get("foto_secundaria")

        # --- BLOCO 7: Empilhamento ---
        empilhamento_estatico = request.form.get("empilhamento_estatico")
        empilhamento_dinamico = request.form.get("empilhamento_dinamico")

        # --- BLOCO 8: Embalagem Alternativa Descartável ---
        comprimento_primaria_descartavel = request.form.get("comprimento_primaria_descartavel")
        largura_primaria_descartavel = request.form.get("largura_primaria_descartavel")
        altura_primaria_descartavel = request.form.get("altura_primaria_descartavel")
        peso_primaria_descartavel = request.form.get("peso_primaria_descartavel")
        pecas_caixa_primaria_descartavel = request.form.get("pecas_caixa_primaria_descartavel")
        comprimento_secundaria_descartavel = request.form.get("comprimento_secundaria_descartavel")
        largura_secundaria_descartavel = request.form.get("largura_secundaria_descartavel")
        altura_secundaria_descartavel = request.form.get("altura_secundaria_descartavel")
        peso_secundaria_descartavel = request.form.get("peso_secundaria_descartavel")
        pecas_pallet_descartavel = request.form.get("pecas_pallet_descartavel")
        foto_descartavel = request.files.get("foto_descartavel")

        # --- BLOCO 9: Observações ---
        comentario8 = request.form.get("comentario8")

        # --- BLOCO 10: Aprovação ---
        rep_fornecedor = request.form.get("rep_fornecedor")
        aprov_fornecedor = request.form.get("aprov_fornecedor")
        rep_containers = request.form.get("rep_containers")
        aprov_containers = request.form.get("aprov_containers")
        data_aprov_fornecedor = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_aprov_containers = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Uploads das fotos principais
        url_foto_primaria = upload_imagem(foto_peca_primaria, "propostas") or registro_atual.get("foto_peca_primaria_url")
        url_foto_embalagem_primaria = upload_imagem(foto_embalagem_peca_primaria, "propostas") or registro_atual.get("foto_embalagem_peca_primaria_url")
        url_foto_secundaria = upload_imagem(foto_secundaria, "propostas") or registro_atual.get("foto_secundaria_url")
        url_foto_descartavel = upload_imagem(foto_descartavel, "propostas") or registro_atual.get("foto_descartavel_url")

        # Monta dados de update
        data_update = {
                        # Bloco 1
            "pn": pn,
            "descricao": descricao,
            "plataforma": plataforma,
            "carline": carline,
            "planta": planta,
            "codigo_planta": codigo_planta,
            "cisco": cisco,
            # Bloco 2
            "fornecedor": fornecedor,
            "endereco": endereco,
            "cidade": cidade,
            "pais": pais,
            "duns": duns,
            "responsavel": responsavel,
            "email": email,
            # Bloco 3
            "aplicavel": aplicavel,
            "classe_material": classe_material,
            "homologacao": homologacao,
            "codigo_onu": codigo_onu,
            "etiqueta_identificacao": etiqueta_identificacao,
            "etiqueta_risco": etiqueta_risco,
            "etiqueta_manuseio": etiqueta_manuseio,
            # Bloco 4
            "tipo_primaria": tipo_primaria,
            "material_primaria": material_primaria,
            "codigo_embalagem_primaria": codigo_embalagem_primaria,
            "comprimento_primaria": comprimento_primaria,
            "largura_primaria": largura_primaria,
            "altura_primaria": altura_primaria,
            "standard_pack_primaria": standard_pack_primaria,
            "tara_primaria": tara_primaria,
            "peso_unitario_primaria": peso_unitario_primaria,
            "peso_total_primaria": peso_total_primaria,
            "altura_nao_ocupada_primaria": altura_nao_ocupada_primaria,
            "ocupacao_primaria": ocupacao_primaria,
            "motivo_primaria": motivo_primaria,
            "foto_peca_primaria_url": url_foto_primaria,
            "foto_embalagem_peca_primaria_url": url_foto_embalagem_primaria,
            # Bloco 5
            "insumos": lista_insumos,  # jsonb
            # Bloco 6
            "aplicavel_secundaria": aplicavel_secundaria,
            "caixas_camadas_secundaria": caixas_camadas_secundaria,
            "camadas_pallet_secundaria": camadas_pallet_secundaria,
            "pecas_pallet_secundaria": pecas_pallet_secundaria,
            "comprimento_pallet_secundaria": comprimento_pallet_secundaria,
            "largura_pallet_secundaria": largura_pallet_secundaria,
            "altura_pallet_secundaria": altura_pallet_secundaria,
            "peso_pallet_secundaria": peso_pallet_secundaria,
            "material_pallet_secundaria": material_pallet_secundaria,
            "comprimento_total_secundaria": comprimento_total_secundaria,
            "largura_total_secundaria": largura_total_secundaria,
            "altura_total_secundaria": altura_total_secundaria,
            "peso_total_secundaria": peso_total_secundaria,
            "foto_secundaria_url": url_foto_secundaria,
            # Bloco 7
            "empilhamento_estatico": empilhamento_estatico,
            "empilhamento_dinamico": empilhamento_dinamico,
            # Bloco 8
            "comprimento_primaria_descartavel": comprimento_primaria_descartavel,
            "largura_primaria_descartavel": largura_primaria_descartavel,
            "altura_primaria_descartavel": altura_primaria_descartavel,
            "peso_primaria_descartavel": peso_primaria_descartavel,
            "pecas_caixa_primaria_descartavel": pecas_caixa_primaria_descartavel,
            "comprimento_secundaria_descartavel": comprimento_secundaria_descartavel,
            "largura_secundaria_descartavel": largura_secundaria_descartavel,
            "altura_secundaria_descartavel": altura_secundaria_descartavel,
            "peso_secundaria_descartavel": peso_secundaria_descartavel,
            "pecas_pallet_descartavel": pecas_pallet_descartavel,
            "foto_descartavel_url": url_foto_descartavel,
            # Bloco 8
            "comentario8": comentario8,
            # Bloco 9
            "rep_fornecedor": rep_fornecedor,
            "aprov_fornecedor": aprov_fornecedor,
            "rep_containers": rep_containers,
            "aprov_containers": aprov_containers,
            "data_aprov_fornecedor": data_aprov_fornecedor,
            "data_aprov_containers": data_aprov_containers
        }

        # Atualiza no Supabase
        response = supabase.table("formulario_propostas").update(data_update).eq("id", registro_id).execute()
        print("Resposta completa do update:", response)

        # Envio de e-mails
        try:
            if aprov_containers in ["aprovado", "reprovado"]:
                send_email_aprovacao(email_recipients=email, pn=pn, fornecedor=fornecedor, aprov_containers=aprov_containers)
                flash("Registro atualizado e e-mail de aprovação enviado com sucesso!", "success")
        except Exception as e:
            print("Erro ao enviar e-mail de aprovação:", str(e))
            flash("Registro atualizado, mas houve um erro ao enviar o e-mail de aprovação.", "warning")

        return redirect(url_for("pendentes"))

    else:
        # Requisição GET - buscar dados e exibir formulário
        registro = registro_atual
        insumos = registro.get("insumos") or []
        return render_template("editar_formulario.html", registro=registro, insumos=insumos)




# ---------------- Funções auxiliares ----------------
def parse_float(valor):
    try:
        return float(valor)
    except (ValueError, TypeError):
        return 0.0

def upload_imagem(arquivo, pasta):
    if arquivo and arquivo.filename != '':
        nome_arquivo = f"{uuid.uuid4()}.{arquivo.filename.rsplit('.', 1)[-1]}"
        storage_path = f"{pasta}/{nome_arquivo}"
        try:
            supabase.storage.from_("uploads").upload(storage_path, arquivo.read())
            return f"{SUPABASE_URL}/storage/v1/object/public/uploads/{storage_path}"
        except Exception as e:
            print(f"Erro ao enviar arquivo {arquivo.filename}: {e}")
            return None
    return None

# ---------------- Rota principal ----------------
@app.route('/editar_formulario_forn/<registro_id>', methods=['GET', 'POST'])
@fornecedor_login_required
def editar_formulario_forn(registro_id):
    duns_session = session.get('duns')
    token_session = session.get('token')

    if not duns_session or not token_session:
        flash("Sua sessão expirou. Faça login novamente.", "warning")
        return redirect(url_for("loginforn"))

    try:
        # Buscar o registro atual e validar o DUNS
        response_atual = supabase.table("formulario_propostas").select("*").eq("id", registro_id).execute()
        if not response_atual.data:
            flash("Registro não encontrado.", "danger")
            return redirect(url_for("registrosforn"))

        registro_atual = response_atual.data[0]

        if registro_atual.get("duns") != duns_session:
            flash("Você não tem permissão para acessar este registro.", "danger")
            return redirect(url_for("registrosforn"))

    except Exception as e:
        print(f"Erro ao carregar registro: {e}")
        flash("Erro ao carregar os dados do registro.", "danger")
        return redirect(url_for("registrosforn"))

    if request.method == 'POST':
        # --- BLOCO 1 ---
        pn = request.form.get("pn")
        descricao = request.form.get("descricao")
        plataforma = request.form.get("plataforma")
        carline = request.form.get("carline")
        planta = request.form.get("planta")
        codigo_planta = request.form.get("codigo_planta")
        cisco = request.form.get("cisco")

        # --- BLOCO 2 ---
        fornecedor = request.form.get("fornecedor")
        endereco = request.form.get("endereco")
        cidade = request.form.get("cidade")
        pais = request.form.get("pais")
        duns = duns_session
        responsavel = request.form.get("responsavel")
        email = request.form.get("email")

        # --- BLOCO 3 ---
        aplicavel = request.form.get("aplicavel")
        classe_material = request.form.get("classe_material")
        homologacao = request.form.get("homologacao")
        codigo_onu = request.form.get("codigo_onu")
        etiqueta_identificacao = request.form.get("etiqueta_identificacao")
        etiqueta_risco = request.form.get("etiqueta_risco")
        etiqueta_manuseio = request.form.get("etiqueta_manuseio")

        # --- BLOCO 4 ---
        tipo_primaria = request.form.get("tipo_primaria")
        material_primaria = request.form.get("material_primaria")
        codigo_embalagem_primaria = request.form.get("codigo_embalagem_primaria")
        comprimento_primaria = parse_float(request.form.get("comprimento_primaria"))
        largura_primaria = parse_float(request.form.get("largura_primaria"))
        altura_primaria = parse_float(request.form.get("altura_primaria"))
        standard_pack_primaria = request.form.get("standard_pack_primaria")
        tara_primaria = parse_float(request.form.get("tara_primaria"))
        peso_unitario_primaria = parse_float(request.form.get("peso_unitario_primaria"))
        peso_total_primaria = parse_float(request.form.get("peso_total_primaria"))
        altura_nao_ocupada_primaria = parse_float(request.form.get("altura_nao_ocupada_primaria"))
        ocupacao_primaria = parse_float(request.form.get("ocupacao_primaria"))
        motivo_primaria = request.form.get("motivo_primaria")
        foto_peca_primaria = request.files.get("foto_peca_primaria")
        foto_embalagem_peca_primaria = request.files.get("foto_embalagem_peca_primaria")

        # --- BLOCO 5: Insumos ---
        materiais = request.form.getlist("material[]")
        comprimentos_insumo = request.form.getlist("comprimento_insumo[]")
        larguras_insumo = request.form.getlist("largura_insumo[]")
        espessuras_insumo = request.form.getlist("espessura_insumo[]")
        pesos_unitarios_insumo = request.form.getlist("pesounitario_insumo[]")
        imagens_insumo = request.files.getlist("imagem[]")

        lista_insumos = []
        for i in range(len(materiais)):
            insumo_data = {
                "material": materiais[i],
                "comprimento": parse_float(comprimentos_insumo[i]),
                "largura": parse_float(larguras_insumo[i]),
                "espessura": parse_float(espessuras_insumo[i]),
                "peso_unitario": parse_float(pesos_unitarios_insumo[i]),
                "imagem_url": upload_imagem(imagens_insumo[i], "insumos") if imagens_insumo[i] and imagens_insumo[i].filename != '' else None
            }
            lista_insumos.append(insumo_data)

        # --- BLOCO 6: Embalagem Secundária ---
        aplicavel_secundaria = request.form.get("aplicavel_secundaria")
        caixas_camadas_secundaria = request.form.get("caixas_camadas_secundaria")
        camadas_pallet_secundaria = request.form.get("camadas_pallet_secundaria")
        pecas_pallet_secundaria = request.form.get("pecas_pallet_secundaria")
        comprimento_pallet_secundaria = request.form.get("comprimento_pallet_secundaria")
        largura_pallet_secundaria = request.form.get("largura_pallet_secundaria")
        altura_pallet_secundaria = request.form.get("altura_pallet_secundaria")
        peso_pallet_secundaria = request.form.get("peso_pallet_secundaria")
        material_pallet_secundaria = request.form.get("material_pallet_secundaria")
        comprimento_total_secundaria = request.form.get("comprimento_total_secundaria")
        largura_total_secundaria = request.form.get("largura_total_secundaria")
        altura_total_secundaria = request.form.get("altura_total_secundaria")
        peso_total_secundaria = request.form.get("peso_total_secundaria")
        foto_secundaria = request.files.get("foto_secundaria")

        # --- BLOCO 7: Empilhamento ---
        empilhamento_estatico = request.form.get("empilhamento_estatico")
        empilhamento_dinamico = request.form.get("empilhamento_dinamico")

        # --- BLOCO 8: Embalagem Alternativa Descartável ---
        comprimento_primaria_descartavel = request.form.get("comprimento_primaria_descartavel")
        largura_primaria_descartavel = request.form.get("largura_primaria_descartavel")
        altura_primaria_descartavel = request.form.get("altura_primaria_descartavel")
        peso_primaria_descartavel = request.form.get("peso_primaria_descartavel")
        pecas_caixa_primaria_descartavel = request.form.get("pecas_caixa_primaria_descartavel")
        comprimento_secundaria_descartavel = request.form.get("comprimento_secundaria_descartavel")
        largura_secundaria_descartavel = request.form.get("largura_secundaria_descartavel")
        altura_secundaria_descartavel = request.form.get("altura_secundaria_descartavel")
        peso_secundaria_descartavel = request.form.get("peso_secundaria_descartavel")
        pecas_pallet_descartavel = request.form.get("pecas_pallet_descartavel")
        foto_descartavel = request.files.get("foto_descartavel")

        # --- BLOCO 9: Observações ---
        comentario8 = request.form.get("comentario8")

        # --- BLOCO 10: Aprovação ---
        rep_fornecedor = request.form.get("rep_fornecedor")
        aprov_fornecedor = request.form.get("aprov_fornecedor")
        rep_containers = request.form.get("rep_containers")
        aprov_containers = request.form.get("aprov_containers")
        data_aprov_fornecedor = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_aprov_containers = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Uploads das fotos principais
        url_foto_primaria = upload_imagem(foto_peca_primaria, "propostas") or registro_atual.get("foto_peca_primaria_url")
        url_foto_embalagem_primaria = upload_imagem(foto_embalagem_peca_primaria, "propostas") or registro_atual.get("foto_embalagem_peca_primaria_url")
        url_foto_secundaria = upload_imagem(foto_secundaria, "propostas") or registro_atual.get("foto_secundaria_url")
        url_foto_descartavel = upload_imagem(foto_descartavel, "propostas") or registro_atual.get("foto_descartavel_url")
        
# -------------------- NOVA LÓGICA: EXCLUIR PNs EXISTENTES --------------------
        try:
            lista_pns = [p.strip() for p in pn.split(",") if p.strip()]

            # Ignora o primeiro PN (considera do segundo em diante)
            for pn_item in lista_pns[1:]:
                    # Busca registros pelo PN (a partir do 2º PN incluso)
                    registros_existentes = supabase.table("formulario_propostas")\
                        .select("id, pn, aprov_containers")\
                        .eq("pn", pn_item)\
                        .eq("aprov_containers", "aguardando proposta")\
                        .neq("id", registro_id)\
                        .execute()

                    if registros_existentes.data:
                        for r in registros_existentes.data:
                            delete_result = supabase.table("formulario_propostas")\
                                .delete()\
                                .eq("id", r["id"])\
                                .execute()

                            print(f"🗑️ Exclusão executada para ID {r['id']} (PN {r['pn']}). Retorno Supabase:", delete_result)
        except Exception as e:
            print(f"❌ Erro ao excluir PNs existentes: {e}")
            flash("Erro ao processar exclusão de PNs existentes.", "danger")

        # -------------------- UPDATE DO REGISTRO ATUAL --------------------
        data_update = {
                                # Bloco 1
            "pn": pn,
            "descricao": descricao,
            "plataforma": plataforma,
            "carline": carline,
            "planta": planta,
            "codigo_planta": codigo_planta,
            "cisco": cisco,
            # Bloco 2
            "fornecedor": fornecedor,
            "endereco": endereco,
            "cidade": cidade,
            "pais": pais,
            "duns": duns,
            "responsavel": responsavel,
            "email": email,
            # Bloco 3
            "aplicavel": aplicavel,
            "classe_material": classe_material,
            "homologacao": homologacao,
            "codigo_onu": codigo_onu,
            "etiqueta_identificacao": etiqueta_identificacao,
            "etiqueta_risco": etiqueta_risco,
            "etiqueta_manuseio": etiqueta_manuseio,
            # Bloco 4
            "tipo_primaria": tipo_primaria,
            "material_primaria": material_primaria,
            "codigo_embalagem_primaria": codigo_embalagem_primaria,
            "comprimento_primaria": comprimento_primaria,
            "largura_primaria": largura_primaria,
            "altura_primaria": altura_primaria,
            "standard_pack_primaria": standard_pack_primaria,
            "tara_primaria": tara_primaria,
            "peso_unitario_primaria": peso_unitario_primaria,
            "peso_total_primaria": peso_total_primaria,
            "altura_nao_ocupada_primaria": altura_nao_ocupada_primaria,
            "ocupacao_primaria": ocupacao_primaria,
            "motivo_primaria": motivo_primaria,
            "foto_peca_primaria_url": url_foto_primaria,
            "foto_embalagem_peca_primaria_url": url_foto_embalagem_primaria,
            # Bloco 5
            "insumos": lista_insumos,  # jsonb
            # Bloco 6
            "aplicavel_secundaria": aplicavel_secundaria,
            "caixas_camadas_secundaria": caixas_camadas_secundaria,
            "camadas_pallet_secundaria": camadas_pallet_secundaria,
            "pecas_pallet_secundaria": pecas_pallet_secundaria,
            "comprimento_pallet_secundaria": comprimento_pallet_secundaria,
            "largura_pallet_secundaria": largura_pallet_secundaria,
            "altura_pallet_secundaria": altura_pallet_secundaria,
            "peso_pallet_secundaria": peso_pallet_secundaria,
            "material_pallet_secundaria": material_pallet_secundaria,
            "comprimento_total_secundaria": comprimento_total_secundaria,
            "largura_total_secundaria": largura_total_secundaria,
            "altura_total_secundaria": altura_total_secundaria,
            "peso_total_secundaria": peso_total_secundaria,
            "foto_secundaria_url": url_foto_secundaria,
            # Bloco 7
            "empilhamento_estatico": empilhamento_estatico,
            "empilhamento_dinamico": empilhamento_dinamico,
            # Bloco 8
            "comprimento_primaria_descartavel": comprimento_primaria_descartavel,
            "largura_primaria_descartavel": largura_primaria_descartavel,
            "altura_primaria_descartavel": altura_primaria_descartavel,
            "peso_primaria_descartavel": peso_primaria_descartavel,
            "pecas_caixa_primaria_descartavel": pecas_caixa_primaria_descartavel,
            "comprimento_secundaria_descartavel": comprimento_secundaria_descartavel,
            "largura_secundaria_descartavel": largura_secundaria_descartavel,
            "altura_secundaria_descartavel": altura_secundaria_descartavel,
            "peso_secundaria_descartavel": peso_secundaria_descartavel,
            "pecas_pallet_descartavel": pecas_pallet_descartavel,
            "foto_descartavel_url": url_foto_descartavel,
            # Bloco 8
            "comentario8": comentario8,
            # Bloco 9
            "rep_fornecedor": rep_fornecedor,
            "aprov_fornecedor": aprov_fornecedor,
            "rep_containers": rep_containers,
            "aprov_containers": aprov_containers,
            "data_aprov_fornecedor": data_aprov_fornecedor,
            "data_aprov_containers": data_aprov_containers
        }

        # Faz o update no Supabase
        try:
            response = supabase.table("formulario_propostas").update(data_update).eq("id", registro_id).execute()

            if response.data:
                if aprov_containers == "aguardando aprovacao":
                    try:
                        email_recipients = ["brunojb_ferrari@hotmail.com"]
                        subject = "📋 New PPI Submitted"
                        send_email_notificacao(email_recipients, subject, pn, fornecedor, planta, carline)
                        flash("Proposta enviada com sucesso!", "success")
                    except Exception as e:
                        print(f"Erro ao enviar proposta: {e}")
                        flash("Registro atualizado. Erro ao enviar o e-mail da proposta.", "warning")
                else:
                    flash("Registro atualizado com sucesso.", "info")

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
        return render_template("editar_formulario_forn.html", registro=registro_atual)





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

@app.route("/embalagens", methods=["GET", "POST"])
def embalagens():
    if request.method == "POST":
        # Captura dados do formulário
        codigo = request.form.get("codigo")
        tipo = request.form.get("tipo")
        material = request.form.get("material")
        size = request.form.get("size")
        comprimento_ext = request.form.get("comprimento_ext")
        largura_ext = request.form.get("largura_ext")
        altura_ext = request.form.get("altura_ext")
        comprimento_int = request.form.get("comprimento_int")
        largura_int = request.form.get("largura_int")
        altura_int = request.form.get("altura_int")
        tara = request.form.get("tara")

        try:
            # Monta dados para inserir
            data = {
                "codigo": codigo,
                "tipo": tipo,
                "material": material,
                "size": size,
                "comprimento_ext": float(comprimento_ext) if comprimento_ext else None,
                "largura_ext": float(largura_ext) if largura_ext else None,
                "altura_ext": float(altura_ext) if altura_ext else None,
                "comprimento_int": float(comprimento_int) if comprimento_int else None,
                "largura_int": float(largura_int) if largura_int else None,
                "altura_int": float(altura_int) if altura_int else None,
                "tara": float(tara) if tara else None,
                "data_cadastro": datetime.now(),
            }

            supabase.table("embalagens").insert(data).execute()
            flash("Embalagem cadastrada com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao cadastrar embalagem: {e}", "danger")

        return redirect(url_for("embalagens"))

    # GET → consulta todas as embalagens
    try:
        result = supabase.table("embalagens").select("*").execute()
        embalagens_list = result.data if result.data else []
    except Exception as e:
        flash(f"Erro ao buscar embalagens: {e}", "danger")
        embalagens_list = []

    return render_template("embalagens.html", embalagens=embalagens_list)

@app.route("/embalagens/cadastrar", methods=["GET", "POST"])
def cadastrar_embalagem():
    if request.method == "POST":
        codigo = request.form.get("codigo")
        tipo = request.form.get("tipo")
        material = request.form.get("material")
        size = request.form.get("size")
        comprimento_ext = request.form.get("comprimento_ext")
        largura_ext = request.form.get("largura_ext")
        altura_ext = request.form.get("altura_ext")
        comprimento_int = request.form.get("comprimento_int")
        largura_int = request.form.get("largura_int")
        altura_int = request.form.get("altura_int")
        tara = request.form.get("tara")
        data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "codigo": codigo,
            "tipo": tipo,
            "material": material,
            "size": size,
            "comprimento_ext": comprimento_ext,
            "largura_ext": largura_ext,
            "altura_ext": altura_ext,
            "comprimento_int": comprimento_int,
            "largura_int": largura_int,
            "altura_int": altura_int,
            "tara": tara,
            "data_cadastro": data_cadastro,
        }

        try:
            supabase.table("embalagens").insert(data).execute()
            flash("Embalagem cadastrada com sucesso!", "success")
            return redirect(url_for("embalagens"))
        except Exception as e:
            flash(f"Erro ao cadastrar embalagem: {e}", "danger")

    return render_template("cadastro_embalagem.html")

@app.route('/editar_embalagem/<registro_id>', methods=['GET', 'POST'])
def editar_embalagem(registro_id):
    # Buscar dados da embalagem no Supabase
    response = supabase.table('embalagens').select('*').eq('id', registro_id).single().execute()
    embalagem = response.data

    if not embalagem:
        flash("Embalagem não encontrada.", "error")
        return redirect(url_for('embalagens'))  # Substitua pela rota que lista as embalagens

    if request.method == 'POST':
        # Pega os dados do formulário
        codigo = request.form.get("codigo")
        tipo = request.form.get("tipo")
        material = request.form.get("material")
        size = request.form.get("size")
        comprimento_ext = request.form.get("comprimento_ext")
        largura_ext = request.form.get("largura_ext")
        altura_ext = request.form.get("altura_ext")
        comprimento_int = request.form.get("comprimento_int")
        largura_int = request.form.get("largura_int")
        altura_int = request.form.get("altura_int")
        tara = request.form.get("tara")

        # Atualiza os dados no Supabase
        try:
            supabase.table("embalagens").update({
                "codigo": codigo,
                "tipo": tipo,
                "material": material,
                "size": size,
                "comprimento_ext": comprimento_ext,
                "largura_ext": largura_ext,
                "altura_ext": altura_ext,
                "comprimento_int": comprimento_int,
                "largura_int": largura_int,
                "altura_int": altura_int,
                "tara": tara
            }).eq("id", registro_id).execute()

            flash("Embalagem atualizada com sucesso!", "success")
            return redirect(url_for("embalagens"))  # Substitua pela rota que lista as embalagens
        except Exception as e:
            flash(f"Erro ao atualizar embalagem: {e}", "danger")

    return render_template("editar_embalagem.html", embalagem=embalagem)




def send_email_notificacao(email_recipients, subject, pn, fornecedor, codigo_planta, carline):
    try:
        html_body = f"""
        <html>
        <body>
            <div style="font-family:Segoe UI, sans-serif;">
                <h2 style="color:#0078d7;">📋 New PPI Submitted</h2>
                <p>A New Packaging Proposal Information (PPI) has been submitted and is awaiting approval:</p>
                <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
                    <tr><th>PN</th><td>{pn}</td></tr>
                    <tr><th>Supplier</th><td>{fornecedor}</td></tr>
                    <tr><th>Plant</th><td>{codigo_planta}</td></tr>
                    <tr><th>Carline</th><td>{carline}</td></tr>
                </table>
                <p>Check the system for more information.</p>
                <p>Best regards!</p>
            </div>
        </body>
        </html>
        """

        if isinstance(email_recipients, str):
            email_recipients = [email_recipients]

        message = Mail(
            from_email='brunojb_ferrari@hotmail.com',  # Seu e-mail verificado no SendGrid (ou autorizado)
            to_emails=email_recipients,
            subject=subject,
            html_content=html_body
        )

        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)

        if response.status_code == 202:
            print("✅ E-mail enviado com sucesso!")
        else:
            print(f"⚠️ Código de resposta: {response.status_code}\n{response.body}")

    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

def send_email_aprovacao(email_recipients, pn, fornecedor, aprov_containers):
    try:
        # Define texto do status e mensagem conforme o valor de aprov_containers
        if aprov_containers == "aprovado":
            status_text = "✅ PPI Approved"
            body_msg = "The PPI sent is <strong>aprovada</strong>."
        elif aprov_containers == "reprovado":
            status_text = "❌ PPI Not Approved"
            body_msg = "The PPI sent is <strong>reprovada</strong>."
        else:
            status_text = "🕒 Awaiting Approval"
            body_msg = "The PPI sent is <strong>aguardando aprovação</strong>."

        # Monta o corpo HTML
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

        # Garante que email_recipients é lista
        if isinstance(email_recipients, str):
            email_recipients = [email_recipients]

        # Cria o objeto Mail do SendGrid
        message = Mail(
            from_email='brunojb_ferrari@hotmail.com',  # seu e-mail autorizado no SendGrid
            to_emails=email_recipients,
            subject=f"{status_text} - PN {pn}",
            html_content=html_body
        )

        # Pega a chave da variável de ambiente
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)

        if response.status_code == 202:
            print("📧 E-mail de aprovação enviado com sucesso.")
        else:
            print(f"⚠️ Código de resposta: {response.status_code}\n{response.body}")

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
        try:
            linhas = json.loads(dados_json)
        except Exception as e:
            flash("Erro ao ler os dados da tabela.", "error")
            return render_template('solicitar.html')

        # Filtra linhas válidas (mínimo 6 campos preenchidos)
        linhas_validas = [linha for linha in linhas if len(linha) >= 6 and all(c.strip() for c in linha[:6])]
        if not linhas_validas:
            flash("Preencha pelo menos uma linha válida com e-mail.", "warning")
            return render_template('solicitar.html')

        # Dicionário de plantas e códigos
        plantas = {
            "GM São Caetano do Sul": { "codigos": { "B1": "72671", "B2": "72507", "4E": "72667" } },
            "GM São José dos Campos": { "codigos": { "C1": "72677", "C2": "72669", "4J": "72668" } },
            "GM Gravataí": { "codigos": { "G1": "72475", "KK": "72474" } },
            "GM Joinville": { "codigos": { "HB": "72476" } },
            "GM Mogi das Cruzes": { "codigos": { "4M": "72477" } }
        }

        try:
            # Cria a solicitação principal
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            emails_unicos = sorted(set(linha[5].strip() for linha in linhas_validas if linha[5].strip()))
            pns = [linha[1].strip() for linha in linhas_validas]

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

            # Inserção de cada linha válida
            for linha in linhas_validas:
                codigo_planta = linha[0].strip()
                pn = linha[1].strip()
                descricao = linha[2].strip()
                duns = linha[3].strip()
                fornecedor = linha[4].strip()
                email = linha[5].strip()

                # Busca dados do fornecedor pelo DUNS na tabela 'fornecedores'
                fornecedor_resp = supabase.table('fornecedores').select('*').eq('duns', duns).execute()
                if fornecedor_resp.data and len(fornecedor_resp.data) > 0:
                    fornecedor_info = fornecedor_resp.data[0]
                    endereco = fornecedor_info.get('endereco', '-')
                    cidade = fornecedor_info.get('cidade', '-')
                    pais = fornecedor_info.get('pais', '-')
                    fornecedor = fornecedor_info.get('nome', fornecedor)
                    email = fornecedor_info.get('email', email)
                else:
                    endereco = cidade = pais = "-"
                
                # Determina planta e cisco pelo codigo_planta
                planta = cisco = "-"
                for p, info in plantas.items():
                    if codigo_planta in info["codigos"]:
                        planta = p
                        cisco = info["codigos"][codigo_planta]
                        break

                # Inserção no Supabase
                supabase.table('formulario_propostas').insert({
                    'codigo_planta': codigo_planta,
                    'planta': planta,
                    'cisco': cisco,
                    'endereco': endereco,
                    'cidade': cidade,
                    'pais': pais,
                    'pn': pn,
                    'descricao': descricao,
                    'duns': duns,
                    'fornecedor': fornecedor,
                    'email': email,
                    'plataforma': '',
                    'carline': '',
                    'responsavel': '',
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
            if emails_unicos:
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
        return jsonify({"email": "", "nome": ""})

    try:
        result = (
            supabase.table("fornecedores")
            .select("emailforn, nome")
            .eq("duns", duns)
            .limit(1)
            .execute()
        )

        if result.data and len(result.data) > 0:
            fornecedor = result.data[0]
            return jsonify({
                "email": fornecedor.get("emailforn", "") or "",
                "nome": fornecedor.get("nome", "") or "",
                "endereco": fornecedor.get("endereco", "") or "",
                "cidade": fornecedor.get("cidade", "") or "",
                "pais": fornecedor.get("pais", "") or ""
            })
        else:
            return jsonify({"email": "", "nome": ""})
    except Exception as e:
        return jsonify({"email": "", "nome": ""})



@app.route("/solicitacoes_em_aberto")
def solicitacoes_em_aberto():
    response = supabase.table("formulario_propostas").select("*").eq("aprov_containers", "aguardando proposta").execute()
    registros_abertos = response.data if response.data else []
    return render_template("solicitacoes_em_aberto.html", registros=registros_abertos)


def send_email_solicitacao(email_recipients, linhas_solicitadas):
    try:
        # Se for string, transforma em lista
        if isinstance(email_recipients, str):
            email_recipients = [email_recipients]

        # Agrupa linhas por e-mail (ignorando email_recipients porque na função original não é usado diretamente)
        grupos_por_email = {}
        for linha in linhas_solicitadas:
            if len(linha) < 6 or any(not str(campo).strip() for campo in linha[:6]):
                continue
            planta, pn, descricao, duns, fornecedor, email = linha[:6]
            email = email.lower()
            grupos_por_email.setdefault(email, []).append((planta, pn, descricao, duns, fornecedor))

        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

        for email, linhas in grupos_por_email.items():
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

            message = Mail(
                from_email='brunojb_ferrari@hotmail.com',  # seu e-mail autorizado no SendGrid
                to_emails=email,
                subject="📋 Packaging Proposal Information (PPI) Request",
                html_content=html_body
            )

            response = sg.send(message)
            if response.status_code == 202:
                print(f"📧 E-mail enviado para {email} com {len(linhas)} item(s).")
            else:
                print(f"⚠️ Falha ao enviar para {email}. Código: {response.status_code}")

    except Exception as e:
        print(f"❌ Erro ao enviar e-mail de solicitação: {e}")
        import traceback
        traceback.print_exc()

@app.route("/reenviar_solicitacao/<solicitacao_id>")
@login_required
def reenviar_solicitacao(solicitacao_id):
    try:
        # 1️⃣ Buscar a solicitação principal
        solicitacao_resp = supabase.table('solicitacoes').select('*').eq('id', solicitacao_id).execute()
        if not solicitacao_resp.data or len(solicitacao_resp.data) == 0:
            flash("Solicitação não encontrada.", "error")
            return redirect(url_for("solicitar"))

        solicitacao = solicitacao_resp.data[0]

        # 2️⃣ Buscar todas as linhas associadas na tabela formulario_propostas
        linhas_resp = supabase.table('formulario_propostas').select('*').eq('solicitacao_id', solicitacao_id).execute()
        if not linhas_resp.data or len(linhas_resp.data) == 0:
            flash("Nenhuma linha encontrada para esta solicitação.", "error")
            return redirect(url_for("solicitar"))

        linhas = []
        emails_unicos = set()

        # 3️⃣ Montar linhas no mesmo formato que send_email_solicitacao espera
        for registro in linhas_resp.data:
            planta = registro.get('planta', '')
            pn = registro.get('pn', '')
            descricao = registro.get('descricao', '')
            duns = registro.get('duns', '')
            fornecedor = registro.get('fornecedor', '')
            email = registro.get('email', '')

            linhas.append([planta, pn, descricao, duns, fornecedor, email])
            if email:
                emails_unicos.add(email.strip())

        # 4️⃣ Enviar e-mails
        if emails_unicos:
            send_email_solicitacao(list(emails_unicos), linhas)

        flash("Solicitação reenviada com sucesso!", "success")

    except Exception as e:
        print(f"❌ Erro ao reenviar solicitação: {e}")
        import traceback
        traceback.print_exc()
        flash("Erro ao reenviar solicitação.", "error")

    return redirect(url_for("solicitacoes_em_aberto"))




        
def send_email_mgo(destinatario, pn, fornecedor, planta, duns):
    try:
        # Monta o corpo HTML
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

        # Garante que destinatario é lista
        if isinstance(destinatario, str):
            destinatario = [destinatario]

        # Cria o objeto Mail do SendGrid
        message = Mail(
            from_email='brunojb_ferrari@hotmail.com',  # seu e-mail autorizado no SendGrid
            to_emails=destinatario,
            subject="📋 Solicitação de Atualização de Cadastro no MGO",
            html_content=html_body
        )

        # Pega a chave da variável de ambiente
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)

        if response.status_code == 202:
            print("✅ E-mail MGO enviado com sucesso!")
        else:
            print(f"⚠️ Código de resposta: {response.status_code}\n{response.body}")

    except Exception as e:
        print(f"❌ Erro ao enviar e-mail MGO: {e}")

if __name__ == "__main__":
    app.run(debug=True)
