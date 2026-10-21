import io
import json
import os
import re
import tempfile
import urllib.parse
from fpdf import FPDF
import requests
import streamlit as st
from gtts import gTTS

# =====================================================================
# 🔑 CONFIGURAZIONE FISSA (La tua chiave API interna)
# =====================================================================
DEFAULT_GROQ_API_KEY = (
    "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"
)

# URL protetti contro caratteri invisibili di copia-incolla
URL_MODELS = "".join(
    [c for c in "https://api.groq.com/openai/v1/models" if ord(c) < 128]
)
URL_CHAT = "".join(
    [
        c
        for c in "https://api.groq.com/openai/v1/chat/completions"
        if ord(c) < 128
    ]
)

st.set_page_config(
    page_title="EduSearch — Dashboard Mappe", page_icon="🗺️", layout="wide"
)

# --- LIGHT WEB PRESENTATION ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    .stApp {
        background-color: #FAFAFA;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .dashboard-header {
        background-color: #FFFFFF;
        padding: 32px 40px;
        border-radius: 20px;
        color: #0F172A;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 2px solid #E2E8F0;
    }
    .dashboard-title {
        margin: 0;
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        color: #0F172A;
    }
    .dashboard-subtitle {
        margin: 6px 0 0 0;
        color: #475569;
        font-size: 1.05rem;
        font-weight: 500;
    }
    .badge-pro {
        background: #F1F5F9;
        padding: 10px 18px;
        border-radius: 12px;
        border: 1px solid #CBD5E1;
        font-size: 13px;
        color: #1E293B;
        font-weight: 600;
    }

    div[data-testid="stForm"] {
        background: #FFFFFF;
        border: 2px solid #E2E8F0;
        border-radius: 20px;
        padding: 32px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
    }

    .map-result-banner {
        background: #F1F5F9;
        color: #0F172A;
        padding: 20px 28px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
        border: 2px solid #CBD5E1;
    }

    .web-box-domanda {
        width: 100%;
        max-width: 860px;
        background-color: #FFFFFF;
        border-left: 6px solid #2563EB;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        padding: 18px 24px;
        border-radius: 14px;
        font-weight: 700;
        color: #0F172A;
        font-size: 1.15rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
    }
    .web-box-categoria {
        width: 100%;
        max-width: 800px;
        background-color: #F8FAFC;
        border-left: 5px solid #475569;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        padding: 16px 22px;
        border-radius: 12px;
        font-weight: 600;
        color: #1E293B;
        font-size: 1.05rem;
    }
    .web-box-spiegazione {
        width: 100%;
        max-width: 750px;
        background-color: #FFFFFF;
        border-left: 4px solid #0EA5E9;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        padding: 15px 20px;
        border-radius: 10px;
        text-align: left;
        margin-left: 25px;
        color: #334155;
        font-style: italic;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.01);
    }
    .web-box-dettaglio {
        width: 100%;
        max-width: 710px;
        background-color: #F8FAFC;
        border-left: 3px solid #2563EB;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        padding: 12px 18px 12px 24px;
        border-radius: 8px;
        text-align: left;
        margin-left: 35px;
        color: #1E293B;
        position: relative;
    }
    .web-box-dettaglio::before {
        content: "•";
        color: #2563EB;
        font-size: 20px;
        font-weight: bold;
        position: absolute;
        left: 10px;
        top: 8px;
    }

    .audio-option-card {
        background-color: #FFFFFF;
        border: 2px solid #CBD5E1;
        border-radius: 16px;
        padding: 20px 24px;
        margin-top: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- WEB DASHBOARD HEADER ---
st.markdown(
    """
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">🗺️ EduSearch</h1>
            <p class="dashboard-subtitle">Piattaforma di Studio con Mappe Concettuali Ottimizzate</p>
        </div>
        <div class="badge-pro">
            <span>🔊 Audio & Testo Integrati</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- BARRA LATERALE ---
with st.sidebar:
  st.header("⚙️ Configurazione")
  st.success("🔒 API configurata internamente.")

api_key_input = DEFAULT_GROQ_API_KEY

# Inizializzazione dello stato di sessione persistente
if "testo_risultato" not in st.session_state:
  st.session_state.testo_risultato = None
if "topic_salvato" not in st.session_state:
  st.session_state.topic_salvato = ""
if "orientamento_salvato" not in st.session_state:
  st.session_state.orientamento_salvato = "A4 Verticale"
if "immagini_correlate" not in st.session_state:
  st.session_state.immagini_correlate = []
if "audio_path" not in st.session_state:
  st.session_state.audio_path = None


def trova_modello_attivo(headers):
  try:
    response = requests.get(URL_MODELS, headers=headers)
    if response.status_code == 200:
      data = response.json()
      models = [m["id"] for m in data.get("data", [])]

      modelli_preferiti = [
          "llama-3.3-70b-versatile",
          "llama-3.1-8b-instant",
          "llama3-70b-8192",
          "mixtral-8x7b-32768",
      ]
      for pref in modelli_preferiti:
        if pref in models:
          return pref

      chat_models = []
      for m in models:
        m_lower = m.lower()
        if not any(
            b in m_lower
            for b in [
                "allam",
                "llama-2",
                "llama2",
                "v2",
                "canopylabs",
                "whisper",
                "embed",
                "guard",
                "audio",
                "transcribe",
                "tts",
                "arabic",
            ]
        ):
          chat_models.append(m)

      if chat_models:
        return chat_models[0]
  except Exception:
    pass
  return "llama-3.3-70b-versatile"


def cerca_immagini_attinenti(query):
  try:
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrlimit=3&prop=pageimages&piprop=thumbnail&pithumbsize=400&format=json"
    headers_req = {"User-Agent": "EduSearchApp/1.0"}
    res = requests.get(url, headers=headers_req, timeout=5)
    if res.status_code == 200:
      data = res.json()
      pages = data.get("query", {}).get("pages", {})
      img_urls = []
      for p in pages.values():
        thumb = p.get("thumbnail", {}).get("source")
        if thumb and (thumb.endswith(".jpg") or thumb.endswith(".png")):
          img_urls.append(thumb)
      return img_urls
  except Exception:
    pass
  return []


def genera_audio_mappa(testo, titolo):
  """Sintetizza il testo con un tono naturale e umano per la riproduzione audio."""
  try:
    testo_naturale = (
        f"Ecco la mappa concettuale dedicata a {titolo}.\n\n"
        + testo.replace("TITOLO:", "Argomento principale:")
        .replace("DOMANDA:", "Domanda guida:")
        .replace("SOTTO_CATEGORIA:", "Sezione:")
        .replace("SPIEGAZIONE:", "Spiegazione:")
        .replace("ESEMPIO:", "Esempio pratico:")
        .replace("🎯", "")
        .replace("📌", "")
        .replace("💡", "")
        .replace("🔍", "")
        .replace("**", "")
        .replace("#", "")
    )
    tts = gTTS(text=testo_naturale, lang="it", slow=False)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
      tts.save(tmp_file.name)
      return tmp_file.name
  except Exception:
    return None


class PDFMappa(FPDF):

  def __init__(self, orientation="P", unit="mm", format="A4", titolo=""):
    super().__init__(orientation=orientation, unit=unit, format=format)
    self.titolo_mappa = titolo

  def clean_str(self, txt):
    """Converte e pulisce qualsiasi stringa in formato sicuro latin-1 senza errori."""
    if not txt:
      return ""
    if not isinstance(txt, str):
      txt = str(txt)
    return txt.encode("latin-1", "replace").decode("latin-1")

  def header(self):
    if self.page_no() > 1:
      self.set_font("helvetica", "B", 11)
      self.set_text_color(15, 23, 42)
      titolo_c = self.clean_str(f"MAPPA CONCETTUALE: {self.titolo_mappa.upper()} (Continuazione)")
      self.cell(0, 8, txt=titolo_c, ln=True, align="C")
      self.ln(4)

  def footer(self):
    self.set_y(-12)
    self.set_font("helvetica", "I", 8)
    self.set_text_color(100, 116, 139)
    self.cell(0, 10, txt=f"Pagina {self.page_no()}", align="C")


def genera_pdf(testo, titolo, orientamento="A4 Verticale", immagini=[]):
  ori = "L" if orientamento == "A4 Orizzontale" else "P"
  pdf = PDFMappa(orientation=ori, unit="mm", format="A4", titolo=titolo)
  pdf.add_page()
  pdf.set_auto_page_break(auto=True, margin=15)
  pdf.set_left_margin(15)
  pdf.set_right_margin(15)

  printable_width = 180 if ori == "P" else 267
  titolo_pulito = pdf.clean_str(titolo.upper())

  # Intestazione principale evidente
  pdf.set_font("helvetica", "B", 14)
  pdf.set_text_color(15, 23, 42)
  pdf.set_fill_color(203, 213, 225)
  header_txt = pdf.clean_str(f"MAPPA CONCETTUALE: {titolo_pulito}")
  pdf.cell(printable_width, 12, txt=header_txt, border=1, fill=True, ln=True, align="C")
  pdf.ln(6)

  for linea in testo.split("\n"):
    is_domanda = "DOMANDA:" in linea or "🎯" in linea
    is_sotto = "SOTTO_CATEGORIA:" in linea or "📌" in linea
    is_spiegazione = "SPIEGAZIONE:" in linea or "💡" in linea

    l_clean = (
        linea.replace("TITOLO:", "")
        .replace("DOMANDA:", "")
        .replace("SOTTO_CATEGORIA:", "")
        .replace("SPIEGAZIONE:", "")
        .replace("ESEMPIO:", "")
        .replace("🎯", "")
        .replace("📌", "")
        .replace("💡", "")
        .replace("🔍", "")
        .replace("**", "")
        .replace("#", "")
        .strip()
    )

    l_clean = re.sub(r"\[.*?\]", "", l_clean).strip()

    if not l_clean:
      pdf.ln(3)
      continue

    l_clean_safe = pdf.clean_str(l_clean)

    # Stili PDF con segni evidenti e parametri stringa sicuri
    if is_domanda:
      pdf.set_font("helvetica", "B", 11)
      pdf.set_text_color(15, 23, 42)
      pdf.set_fill_color(191, 219, 254)
      pdf.set_x(15)
      pdf.multi_cell(printable_width, 8, txt=l_clean_safe, border=1, fill=True, align="C")
      pdf.ln(2.5)
    elif is_sotto:
      pdf.set_font("helvetica", "B", 10.5)
      pdf.set_text_color(30, 41, 59)
      pdf.set_fill_color(226, 232, 240)
      pdf.set_x(15)
      pdf.multi_cell(printable_width, 7.5, txt=l_clean_safe, border=1, fill=True, align="C")
      pdf.ln(2.5)
    elif is_spiegazione:
      pdf.set_font("helvetica", "I", 10)
      pdf.set_text_color(51, 65, 85)
      pdf.set_fill_color(255, 255, 255)
      pdf.set_x(22)
      pdf.multi_cell(printable_width - 14, 6.5, txt=l_clean_safe, border=1, fill=True, align="L")
      pdf.ln(2)
    else:
      pdf.set_font("helvetica", "", 10)
      pdf.set_text_color(71, 85, 105)
      pdf.set_fill_color(248, 250, 252)
      pdf.set_x(25)
      item_txt = pdf.clean_str(f"- {l_clean_safe}")
      pdf.multi_cell(printable_width - 20, 6.5, txt=item_txt, border=1, fill=True, align="L")
      pdf.ln(2)

  if immagini:
    pdf.ln(4)
    for img_url in immagini:
      try:
        img_data = requests.get(img_url, timeout=5).content
        img_buffer = io.BytesIO(img_data)
        pdf.image(img_buffer, w=50)
        pdf.ln(4)
      except Exception:
        pass

  # Restituisce i byte in sicurezza
  pdf_output = pdf.output(dest='S')
  if isinstance(pdf_output, str):
    return pdf_output.encode('latin-1')
  return bytes(pdf_output)


# --- INTERFACCIA WEB FORM ---
submit_btn = False

with st.form("form_documento"):
  st.markdown(
      "<h3 style='margin-top: 0; color: #0F172A; font-weight: 700;'>🎯 Nuova"
      " Mappa Concettuale</h3>",
      unsafe_allow_html=True,
  )

  topic = st.text_input(
      "📌 Argomento o Titolo",
      placeholder="Es. Il Verbo, La Cellula, La Rivoluzione Francese, ecc.",
  )

  col1, col2, col3 = st.columns(3)
  with col1:
    profondita = st.selectbox(
        "📊 Livello di Dettaglio / Complessità",
        [
            "Mappa Semplice (Contenuti essenziali)",
            "Mappa Completa (Standard)",
            "Mappa Estesa (Massima completezza e approfondimento)",
        ],
    )
  with col2:
    livello = st.selectbox(
        "🎓 Livello / Destinatario",
        ["Scuola Primaria / Media", "Scuola Superiore", "Universitario"],
    )
  with col3:
    orientamento_pdf = st.selectbox(
        "📐 Orientamento PDF", ["A4 Verticale", "A4 Orizzontale"]
    )

  note = st.text_area(
      "📝 Note o dettagli aggiuntivi (opzionale)",
      placeholder="Eventuali sezioni o focus specifici...",
  )

  submit_btn = st.form_submit_button(
      "🚀 GENERA MAPPA CONCETTUALE", use_container_width=True, type="primary"
  )

if submit_btn:
  if (
      not api_key_input
      or api_key_input == "gsk_..."
      or not api_key_input.startswith("gsk_")
  ):
    st.error(
        "⚠️ Inserisci la tua chiave API di Groq valida nella variabile"
        " DEFAULT_GROQ_API_KEY in cima al file app.py!"
    )
  elif not topic:
    st.error("⚠️ L'argomento non può essere vuoto!")
  else:
    with st.spinner("⏳ Generazione immediata della mappa concettuale in corso..."):
      headers = {
          "Authorization": f"Bearer {api_key_input}",
          "Content-Type": "application/json",
      }

      modello_scelto = trova_modello_attivo(headers)

      if "Semplice" in profondita:
        istruzioni_profondita = (
            "Genera una mappa essenziale, concisa e facilissima da comprendere,"
            " focalizzandoti solo sui concetti base senza appesantire con troppi"
            " dettagli."
        )
      elif "Estesa" in profondita:
        istruzioni_profondita = (
            "Genera una mappa ESTESA e MOLTO COMPLETA. Inserisci ampie"
            " spiegazioni teoriche, dettagli approfonditi, tutte le"
            " sotto-categorie pertinenti ed esempi esaustivi per ogni sezione."
        )
      else:
        istruzioni_profondita = (
            "Genera una mappa completa e ben bilanciata tra concetti chiave,"
            " spiegazioni e sotto-categorie."
        )

      prompt = (
          f"{istruzioni_profondita}\n"
          f"Argomento: {topic}.\n"
          f"Livello scolastico: {livello}.\n"
          f"{(f'Note: {note}' if note else '')}\n\n"
          f"REGOLE TASSATIVE DI FORMATTAZIONE E QUALITÀ LINGUISTICA:\n"
          f"1. GRAMMATICA E SINTASSI IMPECCABILI: Usa esclusivamente un italiano formale, corretto e rigoroso.\n"
          f"2. EVIDENZIAZIONE PAROLE CHIAVE: Inserisci sempre le parole chiave e i concetti fondamentali racchiusi in **grassetto** all'interno delle spiegazioni e degli esempi per facilitare la lettura visiva e la memorizzazione.\n"
          f"3. FORMATO TASSATIVO A BLOCCHI GEOMETRICI (Usa queste etichette esatte a inizio riga):\n"
          f"TITOLO: [ Nome dell'Argomento Principale ]\n"
          f"DOMANDA: 🎯 [ Domanda guida o snodo principale ]\n"
          f"SOTTO_CATEGORIA: 📌 [ Categoria o sotto-sezione ]\n"
          f"SPIEGAZIONE: 💡 [ Definizione teorica o paragrafo esplicativo rigoroso ]\n"
          f"ESEMPIO: 🔍 [ Esempi pratici e punti chiave corretti ]\n\n"
          f"Rispetta rigorosamente il livello di dettaglio richiesto ({profondita})."
      )

      payload = {
          "model": modello_scelto,
          "messages": [{"role": "user", "content": prompt}],
      }

      try:
        response = requests.post(URL_CHAT, headers=headers, json=payload)
        data = response.json()

        if response.status_code == 200 and "choices" in data:
          st.session_state.testo_risultato = data["choices"][0]["message"][
              "content"
          ]
          st.session_state.topic_salvato = topic
          st.session_state.orientamento_salvato = orientamento_pdf
          st.session_state.immagini_correlate = cerca_immagini_attinenti(topic)
          st.session_state.audio_path = None  # Reset audio per la nuova mappa
        else:
          st.error("❌ Errore restituito dall'API:")
          st.json(data)

      except Exception as e:
        st.error(f"❌ Errore di connessione o esecuzione: {e}")

# --- WEB PRESENTATION OF RESULTS ---
if st.session_state.testo_risultato:
  st.success("✨ Mappa concettuale generata con successo!")
  st.markdown("---")

  st.markdown(
      f"""
      <div class="map-result-banner">
          <h2 style='margin: 0; font-size: 1.7rem; font-weight: 800; letter-spacing: -0.025em;'>
              🧠 MAPPA CONCETTUALE: {st.session_state.topic_salvato.upper()}
          </h2>
      </div>
      """,
      unsafe_allow_html=True,
  )

  linee_mappa = st.session_state.testo_risultato.split("\n")
  html_blocks = [
      '<div style="display: flex; flex-direction: column; gap: 14px;'
      ' align-items: center; padding: 15px 0;">'
  ]

  for linea in linee_mappa:
    l_clean = (
        linea.replace("TITOLO:", "")
        .replace("DOMANDA:", "🎯")
        .replace("SOTTO_CATEGORIA:", "📌")
        .replace("SPIEGAZIONE:", "💡")
        .replace("ESEMPIO:", "🔍")
        .replace("#", "")
        .strip()
    )
    if not l_clean:
      continue

    if "🎯" in l_clean:
      block = f'<div class="web-box-domanda">{l_clean}</div>'
    elif "📌" in l_clean:
      block = f'<div class="web-box-categoria">{l_clean}</div>'
    elif "💡" in l_clean:
      block = f'<div class="web-box-spiegazione">{l_clean}</div>'
    else:
      block = f'<div class="web-box-dettaglio">{l_clean}</div>'

    html_blocks.append(block)

  html_blocks.append("</div>")
  st.markdown("".join(html_blocks), unsafe_allow_html=True)

  st.markdown("---")

  # --- OPZIONE AUDIO SU RICHIESTA CON PULSANTE DI DOWNLOAD ---
  st.markdown(
      """
      <div class="audio-option-card">
          <h4 style="margin: 0 0 8px 0; color: #0F172A; font-weight: 700;">🎧 Desideri ascoltare o scaricare la sintesi vocale di questa mappa?</h4>
          <p style="margin: 0; color: #475569; font-size: 14px;">Ascolta l'audio con una voce naturale o scaricalo direttamente sul tuo dispositivo.</p>
      </div>
      """,
      unsafe_allow_html=True,
  )

  col_aud1, col_aud2 = st.columns([2, 3])
  with col_aud1:
    if st.button("🔊 Genera sintesi vocale", use_container_width=True):
      with st.spinner("🎙️ Generazione dell'audio in corso..."):
        st.session_state.audio_path = genera_audio_mappa(
            st.session_state.testo_risultato, st.session_state.topic_salvato
        )

  if st.session_state.audio_path and os.path.exists(
      st.session_state.audio_path
  ):
    st.audio(st.session_state.audio_path, format="audio/mp3")
    
    audio_filename = f"audio_mappa_{st.session_state.topic_salvato.replace(' ', '_').lower()}.mp3"
    with open(st.session_state.audio_path, "rb") as f:
      st.download_button(
          label="📥 Scarica file audio (.MP3)",
          data=f,
          file_name=audio_filename,
          mime="audio/mpeg",
          use_container_width=True,
      )

  if st.session_state.immagini_correlate:
    st.markdown("---")
    st.markdown(
        "<h3 style='color: #0F172A; font-weight: 700;'>🖼️ Risorse Visive"
        " Correlate</h3>",
        unsafe_allow_html=True,
    )
    cols_img = st.columns(len(st.session_state.immagini_correlate))
    for idx, img_url in enumerate(st.session_state.immagini_correlate):
      with cols_img[idx]:
        st.image(img_url, use_container_width=True)

  st.markdown("---")
  st.subheader("📥 Esportazione Documento PDF")

  base_name = f"mappa_{st.session_state.topic_salvato.replace(' ', '_').lower()}"

  try:
    pdf_bytes = genera_pdf(
        st.session_state.testo_risultato,
        st.session_state.topic_salvato,
        st.session_state.orientamento_salvato,
        st.session_state.immagini_correlate,
    )
    st.download_button(
        label=f"📄 Scarica .PDF ({st.session_state.orientamento_salvato})",
        data=pdf_bytes,
        file_name=f"{base_name}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
  except Exception as e:
    st.error(f"Errore durante la creazione del PDF: {e}")

# --- PIÈ DI PAGINA ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #64748B; font-size: 13px;'>©"
    " EduSearch — Tutti i diritti riservati. Progettato e sviluppato da Luigi"
    " Contessa.</p>",
    unsafe_allow_html=True,
)
