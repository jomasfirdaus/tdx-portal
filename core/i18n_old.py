"""
Lightweight static-string translation store for TDC.

Why not Django's built-in gettext i18n? This project keeps almost all real
content (Profile, News, Programs, Team, Gallery captions...) in the database
with one column per language, edited through the custom dashboard. What's
left over is a small, stable set of UI strings (menu items, buttons, form
labels). A plain Python dictionary is easier to audit, needs no `gettext`
system dependency or `.mo` compilation step, and is trivial for non-technical
staff to extend later.
"""

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ("en", "tet", "pt")

STRINGS = {
    "nav.home":        {"en": "Home",           "tet": "Uma",              "pt": "Início"},
    "nav.profile":     {"en": "Profile",        "tet": "Perfil",           "pt": "Perfil"},
    "nav.vision_mission": {"en": "Vision & Mission", "tet": "Vizaun & Misaun", "pt": "Visão e Missão"},
    "nav.programs":    {"en": "Programs",       "tet": "Programa",         "pt": "Programas"},
    "nav.structure":   {"en": "Team & Structure","tet": "Ekipa & Estrutura","pt": "Equipa e Estrutura"},
    "nav.news":        {"en": "News",           "tet": "Notísia",          "pt": "Notícias"},
    "nav.gallery":     {"en": "Gallery",        "tet": "Galeria",          "pt": "Galeria"},
    "nav.contact":     {"en": "Contact",        "tet": "Kontaktu",         "pt": "Contacto"},
    "nav.staff_login": {"en": "Staff Login",    "tet": "Tama Ekipa",       "pt": "Acesso da Equipa"},

    "home.hero_eyebrow": {"en": "Timor Diagnostics Center", "tet": "Timor Diagnostics Center", "pt": "Timor Diagnostics Center"},
    "home.cta_programs": {"en": "Explore our programs", "tet": "Haree ami-nia programa", "pt": "Explore os nossos programas"},
    "home.cta_contact":  {"en": "Get in touch", "tet": "Kontaktu ami", "pt": "Fale connosco"},
    "home.about_title":  {"en": "Who we are", "tet": "Ami se", "pt": "Quem somos"},
    "home.stats_title":  {"en": "TDC at a glance", "tet": "TDC iha vista badak", "pt": "TDC em números"},
    "home.services_title": {"en": "Services & Expertise", "tet": "Servisu & Kompeténsia", "pt": "Serviços e Especialidade"},
    "home.programs_title": {"en": "Featured Programs", "tet": "Programa Sira Destaka", "pt": "Programas em Destaque"},
    "home.news_title":    {"en": "Latest News", "tet": "Notísia Foun", "pt": "Últimas Notícias"},
    "home.view_all":      {"en": "View all", "tet": "Haree hotu", "pt": "Ver tudo"},
    "home.read_more":     {"en": "Read more", "tet": "Lee tan", "pt": "Ler mais"},

    "profile.title": {"en": "Our Profile", "tet": "Ami-nia Perfil", "pt": "O Nosso Perfil"},
    "profile.governance_title": {"en": "Governance & Leadership", "tet": "Governasaun & Lidaransa", "pt": "Governação e Liderança"},
    "profile.org_structure_title": {"en": "Organizational Structure", "tet": "Estrutura Organizasaun", "pt": "Estrutura Organizacional"},

    "vm.vision_label": {"en": "Vision", "tet": "Vizaun", "pt": "Visão"},
    "vm.mission_label": {"en": "Mission", "tet": "Misaun", "pt": "Missão"},
    "vm.values_title": {"en": "Core Values", "tet": "Valór Sira", "pt": "Valores Fundamentais"},

    "programs.title": {"en": "Programs & Activities", "tet": "Programa & Atividade", "pt": "Programas e Atividades"},
    "programs.status.ongoing": {"en": "Ongoing", "tet": "La'o hela", "pt": "Em curso"},
    "programs.status.completed": {"en": "Completed", "tet": "Remata ona", "pt": "Concluído"},
    "programs.status.planned": {"en": "Planned", "tet": "Planeadu", "pt": "Planeado"},
    "programs.empty": {"en": "No programs published yet.", "tet": "Seidauk iha programa.", "pt": "Ainda não há programas publicados."},

    "structure.title": {"en": "Team & Structure", "tet": "Ekipa & Estrutura", "pt": "Equipa e Estrutura"},
    "structure.board": {"en": "Board Members", "tet": "Membru Konsellu", "pt": "Membros do Conselho"},
    "structure.leadership": {"en": "Leadership", "tet": "Lidaransa", "pt": "Liderança"},
    "structure.units": {"en": "Operational Units", "tet": "Unidade Operasional", "pt": "Unidades Operacionais"},

    "news.title": {"en": "News & Updates", "tet": "Notísia & Atualizasaun", "pt": "Notícias e Atualizações"},
    "news.empty": {"en": "No news published yet.", "tet": "Seidauk iha notísia.", "pt": "Ainda não há notícias publicadas."},
    "news.published_on": {"en": "Published on", "tet": "Publika iha", "pt": "Publicado em"},

    "gallery.title": {"en": "Photo Gallery", "tet": "Galeria Foto", "pt": "Galeria de Fotos"},
    "gallery.empty": {"en": "No albums published yet.", "tet": "Seidauk iha album.", "pt": "Ainda não há álbuns publicados."},
    "gallery.photos_count": {"en": "photos", "tet": "foto", "pt": "fotos"},

    "contact.title": {"en": "Contact Us", "tet": "Kontaktu Ami", "pt": "Contacte-nos"},
    "contact.form_title": {"en": "Send us a message", "tet": "Haruka mensajen ba ami", "pt": "Envie-nos uma mensagem"},
    "contact.field_name": {"en": "Full name", "tet": "Naran kompletu", "pt": "Nome completo"},
    "contact.field_email": {"en": "Email address", "tet": "Email", "pt": "Endereço de email"},
    "contact.field_phone": {"en": "Phone (optional)", "tet": "Telefone (opsional)", "pt": "Telefone (opcional)"},
    "contact.field_subject": {"en": "Subject", "tet": "Asuntu", "pt": "Assunto"},
    "contact.field_message": {"en": "Message", "tet": "Mensajen", "pt": "Mensagem"},
    "contact.submit": {"en": "Send message", "tet": "Haruka mensajen", "pt": "Enviar mensagem"},
    "contact.success": {"en": "Thank you — your message has been sent. We'll respond soon.", "tet": "Obrigadu — ami simu ona ita-nia mensajen. Ami sei responde lalais.", "pt": "Obrigado — a sua mensagem foi enviada. Responderemos em breve."},
    "contact.office": {"en": "Office", "tet": "Eskritóriu", "pt": "Escritório"},
    "contact.phone": {"en": "Phone", "tet": "Telefone", "pt": "Telefone"},
    "contact.email": {"en": "Email", "tet": "Email", "pt": "Email"},

    # Contact-form validation & throttle messages (previously hardcoded English).
    "contact.err_required": {"en": "This field is required.", "tet": "Kampu ida-ne'e presiza prienxe.", "pt": "Este campo é obrigatório."},
    "contact.err_invalid_email": {"en": "Enter a valid email address.", "tet": "Hakerek email ida ne'ebé loos.", "pt": "Introduza um endereço de email válido."},
    "contact.err_spam": {"en": "Spam detected.", "tet": "Deteta spam.", "pt": "Spam detetado."},
    "contact.err_too_fast": {"en": "Please take a moment to fill in the form.", "tet": "Favór ida, uza tempu uitoan atu prienxe formuláriu.", "pt": "Por favor, dedique um momento a preencher o formulário."},
    "contact.err_message_short": {"en": "Please write a slightly longer message so we can help you.", "tet": "Favór ida, hakerek mensajen naruk uitoan atu ami bele ajuda ita.", "pt": "Por favor, escreva uma mensagem um pouco mais longa para que possamos ajudar."},
    "contact.err_throttled": {"en": "You're sending messages too quickly. Please try again later.", "tet": "Ita haruka mensajen lalais liu. Favór ida, koko fali depois.", "pt": "Está a enviar mensagens demasiado depressa. Tente novamente mais tarde."},

    # Location / map module (homepage + contact page).
    "location.title": {"en": "Find Us", "tet": "Hetan Ami", "pt": "Encontre-nos"},
    "location.subtitle": {"en": "Visit our office", "tet": "Vizita ami-nia eskritóriu", "pt": "Visite o nosso escritório"},
    "location.address": {"en": "Address", "tet": "Enderesu", "pt": "Endereço"},
    "location.hours": {"en": "Opening Hours", "tet": "Oras Loke", "pt": "Horário de Funcionamento"},
    "location.get_directions": {"en": "Get Directions", "tet": "Hetan Direksaun", "pt": "Obter Direções"},
    "location.view_map": {"en": "View on map", "tet": "Haree iha mapa", "pt": "Ver no mapa"},

    "footer.rights": {"en": "All rights reserved.", "tet": "Direitu hotu rezerva.", "pt": "Todos os direitos reservados."},
    "footer.quicklinks": {"en": "Quick Links", "tet": "Ligasaun Lalais", "pt": "Links Rápidos"},
    "footer.follow": {"en": "Follow us", "tet": "Tuir ami", "pt": "Siga-nos"},

    "common.skip_to_content": {"en": "Skip to content", "tet": "Salta ba konteúdu", "pt": "Saltar para o conteúdo"},
    "errors.404_message": {"en": "The page you're looking for doesn't exist or has moved.", "tet": "Pájina ne'ebé ita buka la eziste ka muda ona fatin.", "pt": "A página que procura não existe ou foi movida."},
    "errors.500_message": {"en": "Something went wrong on our side. Please try again shortly.", "tet": "Iha problema iha ami-nia parte. Favór ida, koko fali lakleur.", "pt": "Ocorreu um erro do nosso lado. Tente novamente em breve."},
    "errors.back_home": {"en": "Back to homepage", "tet": "Fila ba pájina prinsipál", "pt": "Voltar à página inicial"},

    "common.learn_more": {"en": "Learn more", "tet": "Hatene tan", "pt": "Saiba mais"},
    "common.back": {"en": "Back", "tet": "Fila", "pt": "Voltar"},
    "common.search": {"en": "Search", "tet": "Buka", "pt": "Pesquisar"},
    "common.share": {"en": "Share", "tet": "Fahe", "pt": "Partilhar"},
}


def t(key, lang):
    """Return the translated string for `key`, falling back to English."""
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get(DEFAULT_LANGUAGE) or key
