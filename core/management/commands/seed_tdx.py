"""
Seeds the database with TDx's real organizational content (profile, vision,
mission, service areas, core values, and organizational structure) drawn
from the reference profile document supplied by TDx.

Intentionally NOT seeded: Team members, Programs, News, and Gallery — the
source document does not name specific staff, so real names/photos are left
for TDx staff to add through the dashboard rather than invented here.

Run with: python manage.py seed_tdx
Safe to re-run: uses update_or_create / get_or_create throughout.
"""
import os

from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import CoreValue, Location, PageHeader, ServiceArea, SiteProfile, Statistic
from structure.models import Department


class Command(BaseCommand):
    help = "Seed TDx profile, vision/mission, services, values, statistics and org structure."

    def handle(self, *args, **options):
        self.seed_profile()
        self.seed_services()
        self.seed_values()
        self.seed_statistics()
        self.seed_structure()
        self.seed_location()
        self.seed_page_headers()
        self.stdout.write(self.style.SUCCESS("TDx seed data loaded. Review and refine wording via the dashboard, especially the Tetum/Portuguese columns."))

    def seed_profile(self):
        profile, _ = SiteProfile.objects.update_or_create(
            pk=1,
            defaults=dict(
                org_name="Timor Diagnostics (TDx)",
                short_name="TDx",
                tagline_en="Accurate, timely, and accessible diagnostics for every community in Timor-Leste.",
                tagline_tet="Diagnóstiku ne'ebé loos, iha tempu, no fasil atu asesu ba komunidade hotu iha Timor-Leste.",
                tagline_pt="Diagnósticos precisos, atempados e acessíveis para todas as comunidades de Timor-Leste.",

                about_en=(
                    "Timor Diagnostics (TDx) is a locally driven private initiative established to deliver "
                    "laboratory testing and a wide range of diagnostic services, including consultancy, home "
                    "care, and technical support. TDx provides accurate, timely, and accessible diagnostic "
                    "services that strengthen Timor-Leste's health system while establishing itself as the "
                    "country's leading private provider of high-quality diagnostics."
                ),
                about_tet=(
                    "Timor Diagnostics (TDx) mak inisiativa privadu ida ne'ebé rai-laran-nian, harii atu fó "
                    "servisu testu laboratóriu no serbisu diagnóstiku oioin, inklui konsultória, kuidadu-uma, "
                    "no apoiu téknika. TDx fó servisu diagnóstiku ne'ebé loos, iha tempu, no fasil atu asesu, "
                    "hodi hametin sistema saúde Timor-Leste nian no sai fornesedór privadu ne'ebé lidera iha "
                    "diagnóstiku kualidade-aas."
                ),
                about_pt=(
                    "A Timor Diagnostics (TDx) é uma iniciativa privada de raiz local, criada para prestar "
                    "testes laboratoriais e uma vasta gama de serviços de diagnóstico, incluindo consultoria, "
                    "cuidados domiciliários e apoio técnico. A TDx presta serviços de diagnóstico precisos, "
                    "atempados e acessíveis, fortalecendo o sistema de saúde de Timor-Leste e afirmando-se "
                    "como o principal prestador privado de diagnósticos de alta qualidade no país."
                ),

                about_secondary_en=(
                    "By complementing public sector laboratories and extending services to communities, TDx "
                    "ensures reliable, patient-centered outcomes while setting the benchmark for private "
                    "healthcare excellence. By bridging gaps in public health infrastructure, TDx ensures "
                    "communities, institutions, and partners have access to accurate, timely, and reliable "
                    "diagnostics."
                ),
                about_secondary_tet=(
                    "Ho komplementa laboratóriu setór públiku no hasa'e servisu ba komunidade sira, TDx "
                    "garante rezultadu ne'ebé fiável no foka ba pasiente, hodi sai referénsia ba servisu "
                    "saúde privadu ne'ebé di'ak. Ho taka fila fatin mamuk iha infraestrutura saúde públika, "
                    "TDx garante komunidade, instituisaun, no parseiru sira bele asesu ba diagnóstiku ne'ebé "
                    "loos, iha tempu, no fiável."
                ),
                about_secondary_pt=(
                    "Ao complementar os laboratórios do setor público e alargar os serviços às comunidades, "
                    "a TDx garante resultados fiáveis e centrados no paciente, ao mesmo tempo que estabelece "
                    "o padrão de excelência para os cuidados de saúde privados. Ao colmatar lacunas na "
                    "infraestrutura de saúde pública, a TDx assegura que comunidades, instituições e parceiros "
                    "tenham acesso a diagnósticos precisos, atempados e fiáveis."
                ),

                vision_en=(
                    "To be the leading private diagnostic and consultancy hub in Timor-Leste, bridging public "
                    "and private efforts for resilient healthcare."
                ),
                vision_tet=(
                    "Atu sai sentru diagnóstiku no konsultória privadu ne'ebé lidera iha Timor-Leste, taka "
                    "fila esforsu públiku no privadu ba sistema saúde ne'ebé forte."
                ),
                vision_pt=(
                    "Ser o principal centro privado de diagnóstico e consultoria em Timor-Leste, unindo os "
                    "esforços públicos e privados para uma saúde resiliente."
                ),

                mission_en=(
                    "Deliver accurate, timely, and accessible diagnostic services for all, ensuring "
                    "inclusiveness by reaching every community, institution, and patient across Timor-Leste."
                ),
                mission_tet=(
                    "Fó servisu diagnóstiku ne'ebé loos, iha tempu, no fasil atu asesu ba ema hotu, garante "
                    "inkluzaun ho to'o komunidade, instituisaun, no pasiente hotu iha Timor-Leste tomak."
                ),
                mission_pt=(
                    "Prestar serviços de diagnóstico precisos, atempados e acessíveis para todos, garantindo "
                    "a inclusão ao alcançar todas as comunidades, instituições e pacientes em Timor-Leste."
                ),

                phone_primary="+670 000 0000",
                email_primary="info@tdx.tl",
                address_en="Dili, Timor-Leste",
                address_tet="Dili, Timor-Leste",
                address_pt="Díli, Timor-Leste",
            ),
        )
        self.stdout.write(f"Site profile: {profile}")

    def seed_location(self):
        location, _ = Location.objects.update_or_create(
            name_en="TDx Head Office",
            defaults=dict(
                name_tet="Eskritóriu Sentrál TDx",
                name_pt="Sede da TDx",
                address_en="Dili, Timor-Leste",
                address_tet="Dili, Timor-Leste",
                address_pt="Díli, Timor-Leste",
                latitude="-8.556856",
                longitude="125.560314",
                phone="+670 000 0000",
                email="info@tdx.tl",
                opening_hours_en="Mon\u2013Fri: 08:00\u201317:00\nSat: 08:00\u201312:00\nSun: Closed",
                opening_hours_tet="Seg\u2013Sex: 08:00\u201317:00\nSab: 08:00\u201312:00\nDom: Taka",
                opening_hours_pt="Seg\u2013Sex: 08:00\u201317:00\nS\u00e1b: 08:00\u201312:00\nDom: Fechado",
                is_primary=True,
                order=0,
                is_active=True,
            ),
        )
        self.stdout.write(f"Location: {location} (update the coordinates/address via Dashboard \u2192 Locations)")

        home_collection, _ = Location.objects.update_or_create(
            name_en="Home Collection",
            defaults=dict(
                name_tet="Kolleta iha Uma",
                name_pt="Recolha ao Domic\u00edlio",
                phone="+670 000 0000",
                email="info@tdx.tl",
                is_primary=False,
                show_on_map=False,
                order=1,
                is_active=True,
            ),
        )
        self.stdout.write(f"Location: {home_collection} (selectable when booking, hidden from the map)")

    def seed_page_headers(self):
        # Matches the approved TDC header design out of the box (seal
        # watermark, purple->green decorative panel, theme-colored title) —
        # staff can still fine-tune each page via Dashboard -> Page Headers.
        DEFAULTS = dict(
            overlay_opacity=40, text_color="", height="md", show_breadcrumb=True, is_active=True,
            motto_en="Saúde diak, ba moris diak", motto_tet="Saúde diak, ba moris diak", motto_pt="Saúde diak, ba moris diak",
            tagline_en="Good health for a good life", tagline_tet="Good health for a good life", tagline_pt="Good health for a good life",
        )
        pages = [
            dict(page_key="profile", title_en="Our Profile", title_tet="Ami-nia Perfil", title_pt="O Nosso Perfil"),
            dict(page_key="vision_mission", title_en="Vision & Mission", title_tet="Vizaun & Misaun", title_pt="Visão e Missão"),
            dict(page_key="programs", title_en="Programs & Activities", title_tet="Programa & Atividade", title_pt="Programas e Atividades"),
            dict(page_key="structure", title_en="Team & Structure", title_tet="Ekipa & Estrutura", title_pt="Equipa e Estrutura"),
            dict(page_key="news", title_en="News & Updates", title_tet="Notísia & Atualizasaun", title_pt="Notícias e Atualizações"),
            dict(page_key="gallery", title_en="Photo Gallery", title_tet="Galeria Foto", title_pt="Galeria de Fotos"),
            dict(page_key="contact", title_en="Contact Us", title_tet="Kontaktu Ami", title_pt="Contacte-nos"),
            dict(page_key="appointments", title_en="Book an Appointment", title_tet="Book Appointment", title_pt="Marcar Consulta"),
        ]
        for page in pages:
            page_key = page.pop("page_key")
            PageHeader.objects.update_or_create(page_key=page_key, defaults={**DEFAULTS, **page})

        # Home renders through the same {% page_header %} component
        # (variant="home") as every other page — see templates/public/home.html.
        # title_en is "<primary> | <accent>", split by the variant="home"
        # rendering into the two-tone stacked brand title from the approved
        # design (docs/design/home.png); everything else (motto, tagline,
        # decorative art) is identical to every other page's header.
        home, _ = PageHeader.objects.update_or_create(
            page_key="home",
            defaults=dict(
                title_en="TIMOR | DIAGNOSTIC CENTER",
                title_tet="TIMOR | DIAGNOSTIC CENTER",
                title_pt="TIMOR | DIAGNOSTIC CENTER",
                motto_en="Saúde diak, ba moris diak", motto_tet="Saúde diak, ba moris diak", motto_pt="Saúde diak, ba moris diak",
                tagline_en="Good health for a good life", tagline_tet="Good health for a good life", tagline_pt="Good health for a good life",
                overlay_opacity=40, text_color="",
            ),
        )
        # Seeds the decorative panel's default image only if nothing has
        # been uploaded yet (never overwrites a staff-chosen image on
        # re-run) — reproduces today's CSS/SVG fallback look exactly, so
        # Home's approved appearance holds while background_image becomes
        # a real, dashboard-editable field instead of a hardcoded asset.
        if not home.background_image:
            asset_path = os.path.join(os.path.dirname(__file__), "seed_assets", "page_header_default_bg.png")
            with open(asset_path, "rb") as f:
                home.background_image.save("page_header_default_bg.png", File(f), save=True)

        self.stdout.write("Page headers: 9 pages seeded with their current look (customize via Dashboard → Page Headers)")

    def seed_services(self):
        rows = [
            dict(
                name_en="Clinical Diagnostics", name_tet="Diagnóstiku Klíniku", name_pt="Diagnóstico Clínico",
                function_en="Hematology, biochemistry, microbiology, serology, and molecular testing.",
                function_tet="Hematolojia, biokímika, mikrobiolojia, serolojia, no testu molekulár.",
                function_pt="Hematologia, bioquímica, microbiologia, serologia e testes moleculares.",
                value_en="Provides accurate results for patient care; builds credibility and forms the foundation of diagnostic operations.",
                value_tet="Fó rezultadu loos ba kuidadu pasiente; harii kredibilidade no sai baze ba operasaun diagnóstiku.",
                value_pt="Fornece resultados precisos para os cuidados ao paciente; constrói credibilidade e é a base das operações de diagnóstico.",
                icon="microscope", order=1,
            ),
            dict(
                name_en="Public Health Surveillance", name_tet="Vijilánsia Saúde Públika", name_pt="Vigilância de Saúde Pública",
                function_en="Outbreak monitoring and public health response support.",
                function_tet="Monitor surtu no apoiu ba resposta saúde públika.",
                function_pt="Monitorização de surtos e apoio à resposta de saúde pública.",
                value_en="Positions TDx as a partner in national disease control and emergency preparedness.",
                value_tet="Halo TDx sai parseiru ba kontrola moras nasionál no prontidaun emerjénsia.",
                value_pt="Posiciona a TDx como parceira no controlo nacional de doenças e na preparação para emergências.",
                icon="shield", order=2,
            ),
            dict(
                name_en="Laboratory Consultancy", name_tet="Konsultória Laboratóriu", name_pt="Consultoria Laboratorial",
                function_en="Workflow design, accreditation support, and digital integration (HMIS–LIMS–mSupply).",
                function_tet="Dezeñu fluxu servisu, apoiu akreditasaun, no integrasaun dijitál (HMIS–LIMS–mSupply).",
                function_pt="Desenho de fluxos de trabalho, apoio à acreditação e integração digital (HMIS–LIMS–mSupply).",
                value_en="Expands influence beyond service delivery; generates revenue through advisory and capacity-building contracts.",
                value_tet="Hasa'e influénsia liu husi entrega servisu; jera rendimentu husi kontratu konsultória no kapasitasaun.",
                value_pt="Amplia a influência para além da prestação de serviços; gera receita através de contratos de consultoria e capacitação.",
                icon="clipboard", order=3,
            ),
            dict(
                name_en="Capacity Building", name_tet="Kapasitasaun", name_pt="Capacitação",
                function_en="Training for laboratory technicians, scientists, and phlebotomists.",
                function_tet="Formasaun ba téknicu laboratóriu, sientista, no flebotomista.",
                function_pt="Formação de técnicos de laboratório, cientistas e flebotomistas.",
                value_en="Strengthens national human resources for health and ensures long-term sustainability.",
                value_tet="Hametin rekursu umanu nasionál ba saúde no garante sustentabilidade bá oin.",
                value_pt="Reforça os recursos humanos nacionais para a saúde e garante sustentabilidade a longo prazo.",
                icon="graduation", order=4,
            ),
            dict(
                name_en="Procurement Support", name_tet="Apoiu Aprovizionamentu", name_pt="Apoio à Aquisição",
                function_en="Technical specifications, vendor negotiations, and reagent continuity.",
                function_tet="Espesifikasaun téknika, negosiasaun ho fornesedór, no kontinuidade reajente.",
                function_pt="Especificações técnicas, negociação com fornecedores e continuidade de reagentes.",
                value_en="Guarantees quality and cost-effective supply chain management; enhances donor confidence.",
                value_tet="Garante kualidade no jestaun kadeia fornesimentu ne'ebé eficás; hasa'e konfiansa doadór.",
                value_pt="Garante qualidade e uma gestão da cadeia de abastecimento eficiente; reforça a confiança dos doadores.",
                icon="truck", order=5,
            ),
            dict(
                name_en="Wellbeing Programs", name_tet="Programa Bem-Estar", name_pt="Programas de Bem-Estar",
                function_en="Staff health, home care, and resilience building for the wider community.",
                function_tet="Saúde funsionáriu, kuidadu-uma, no harii rezilénsia ba komunidade.",
                function_pt="Saúde dos colaboradores, cuidados domiciliários e desenvolvimento de resiliência comunitária.",
                value_en="Improves workforce morale and productivity; demonstrates holistic care values.",
                value_tet="Hasa'e morál no produtividade ekipa; hatudu valór kuidadu ne'ebé kompletu.",
                value_pt="Melhora o moral e a produtividade da equipa; demonstra valores de cuidado holístico.",
                icon="heart", order=6,
            ),
        ]
        for row in rows:
            ServiceArea.objects.update_or_create(name_en=row["name_en"], defaults=row)
        self.stdout.write(f"Service areas: {len(rows)}")

    def seed_values(self):
        rows = [
            dict(
                name_en="Clinical Excellence", name_tet="Ezelénsia Klíniku", name_pt="Excelência Clínica",
                description_en="Medical doctors and laboratory professionals on our Board uphold rigorous clinical standards in every test we run.",
                description_tet="Doutór médiku no profisionál laboratóriu iha ami-nia Konsellu mantein padraun klíniku ne'ebé rigorozu iha testu hotu-hotu.",
                description_pt="Médicos e profissionais de laboratório no nosso Conselho mantêm padrões clínicos rigorosos em cada teste realizado.",
                icon="stethoscope", order=1,
            ),
            dict(
                name_en="Community Trust", name_tet="Konfiansa Komunidade", name_pt="Confiança da Comunidade",
                description_en="Church representatives on our Board reinforce ethical oversight and social responsibility toward every patient.",
                description_tet="Reprezentante igreja iha ami-nia Konsellu hametin superviza étika no responsabilidade sosiál ba pasiente hotu-hotu.",
                description_pt="Representantes da igreja no nosso Conselho reforçam a supervisão ética e a responsabilidade social para com cada paciente.",
                icon="hands", order=2,
            ),
            dict(
                name_en="Evidence & Innovation", name_tet="Evidénsia & Inovasaun", name_pt="Evidência e Inovação",
                description_en="Academics on our Board bring evidence-based approaches, research integration, and training frameworks.",
                description_tet="Akadémiku iha ami-nia Konsellu lori metodolojia bazeia-evidénsia, integrasaun peskiza, no kuadru formasaun.",
                description_pt="Académicos no nosso Conselho trazem abordagens baseadas em evidências, integração de investigação e quadros de formação.",
                icon="lightbulb", order=3,
            ),
            dict(
                name_en="Accountability & Transparency", name_tet="Responsabilidade & Transparénsia", name_pt="Responsabilidade e Transparência",
                description_en="Our Board provides strategic oversight, ensures compliance, and gives donors and partners confidence through transparent governance.",
                description_tet="Ami-nia Konsellu fó superviza estratéjiku, garante kumprimentu, no fó konfiansa ba doadór no parseiru liu husi governasaun transparente.",
                description_pt="O nosso Conselho assegura supervisão estratégica, garante conformidade e dá confiança a doadores e parceiros através de uma governação transparente.",
                icon="scale", order=4,
            ),
        ]
        for row in rows:
            CoreValue.objects.update_or_create(name_en=row["name_en"], defaults=row)
        self.stdout.write(f"Core values: {len(rows)}")

    def seed_statistics(self):
        rows = [
            dict(label_en="Technical Core Units", label_tet="Unidade Téknika Sentrál", label_pt="Unidades Técnicas Centrais", value="3", icon="layers", order=1),
            dict(label_en="Service Areas", label_tet="Área Servisu", label_pt="Áreas de Serviço", value="6", icon="grid", order=2),
            dict(label_en="Governance Pillars", label_tet="Pilar Governasaun", label_pt="Pilares de Governação", value="4", icon="columns", order=3),
            dict(label_en="Community-Centered", label_tet="Foka ba Komunidade", label_pt="Centrado na Comunidade", value="100%", icon="heart", order=4),
        ]
        for row in rows:
            Statistic.objects.update_or_create(label_en=row["label_en"], defaults=row)
        self.stdout.write(f"Statistics: {len(rows)}")

    def seed_structure(self):
        board, _ = Department.objects.update_or_create(
            name_en="Board", defaults=dict(
                name_en="Board", name_tet="Konsellu", name_pt="Conselho",
                description_en="The strategic oversight body, ensuring accountability, transparency, and alignment with national health priorities. Intentionally multidisciplinary — medical doctors, academics, church representatives, and medical laboratory professionals.",
                description_tet="Órgaun superviza estratéjiku, garante responsabilidade, transparénsia, no alinhamentu ho prioridade saúde nasionál. Multidisiplinár — doutór médiku, akadémiku, reprezentante igreja, no profisionál laboratóriu médiku.",
                description_pt="O órgão de supervisão estratégica, garantindo responsabilidade, transparência e alinhamento com as prioridades nacionais de saúde. Intencionalmente multidisciplinar — médicos, académicos, representantes da igreja e profissionais de laboratório médico.",
                category="governance", icon="users", order=1, parent=None,
            )
        )
        md, _ = Department.objects.update_or_create(
            name_en="Managing Director", defaults=dict(
                name_en="Managing Director", name_tet="Diretór Jerál", name_pt="Diretor Geral",
                description_en="The executive leader responsible for day-to-day operations and execution of Board strategy, overseeing Finance, Logistics & Admin, and the Technical Core.",
                description_tet="Lider ezekutivu ne'ebé responsábel ba operasaun loron-loron no ezekuta estratéjia Konsellu, superviza Finansa, Lojístika & Admin, no Núkleu Téknika.",
                description_pt="O líder executivo responsável pelas operações do dia a dia e pela execução da estratégia do Conselho, supervisionando as Finanças, a Logística & Administração e o Núcleo Técnico.",
                category="executive", icon="briefcase", order=2, parent=board,
            )
        )
        finance, _ = Department.objects.update_or_create(
            name_en="Finance Unit", defaults=dict(
                name_en="Finance Unit", name_tet="Unidade Finansa", name_pt="Unidade Financeira",
                description_en="Budgeting & accounting, financial planning, and marketing — the engine of sustainability and growth.",
                description_tet="Orsamentu & kontabilidade, planeamentu finanseiru, no marketing — matan ba sustentabilidade no kresimentu.",
                description_pt="Orçamento e contabilidade, planeamento financeiro e marketing — o motor da sustentabilidade e do crescimento.",
                category="unit", icon="wallet", order=3, parent=md,
            )
        )
        logistics, _ = Department.objects.update_or_create(
            name_en="Logistic & Admin Unit", defaults=dict(
                name_en="Logistic & Admin Unit", name_tet="Unidade Lojístika & Admin", name_pt="Unidade de Logística e Administração",
                description_en="Supply chain management, human resources, administrative support, and media & communications.",
                description_tet="Jestaun kadeia fornesimentu, rekursu umanu, apoiu administrativu, no média & komunikasaun.",
                description_pt="Gestão da cadeia de abastecimento, recursos humanos, apoio administrativo e comunicação.",
                category="unit", icon="settings", order=4, parent=md,
            )
        )
        technical, _ = Department.objects.update_or_create(
            name_en="Technical Core", defaults=dict(
                name_en="Technical Core", name_tet="Núkleu Téknika", name_pt="Núcleo Técnico",
                description_en="Integrates laboratory excellence, mobile phlebotomy, and holistic wellbeing care — the operational backbone of TDx.",
                description_tet="Integra ezelénsia laboratóriu, flebotomia móvel, no kuidadu bem-estar kompletu — sentru operasionál TDx nian.",
                description_pt="Integra a excelência laboratorial, a flebotomia móvel e os cuidados de bem-estar holísticos — a espinha dorsal operacional da TDx.",
                category="unit", icon="cpu", order=5, parent=md,
            )
        )
        sub_units = [
            dict(name_en="Testing Unit", name_tet="Unidade Testu", name_pt="Unidade de Testes",
                 description_en="Laboratory diagnostics, public health testing, and outbreak surveillance.",
                 description_tet="Diagnóstiku laboratóriu, testu saúde públika, no vijilánsia surtu.",
                 description_pt="Diagnóstico laboratorial, testes de saúde pública e vigilância de surtos.",
                 icon="flask", order=1),
            dict(name_en="Phlebotomy Unit", name_tet="Unidade Flebotomia", name_pt="Unidade de Flebotomia",
                 description_en="In-facility, home, and on-site sample collection with cold-chain integrity.",
                 description_tet="Kolesaun amostra iha fasilidade, uma, no fatin, ho kadeia frius ne'ebé mantein.",
                 description_pt="Recolha de amostras nas instalações, ao domicílio e no local, com integridade da cadeia de frio.",
                 icon="syringe", order=2),
            dict(name_en="Wellbeing & Care Unit", name_tet="Unidade Bem-Estar & Kuidadu", name_pt="Unidade de Bem-Estar e Cuidados",
                 description_en="Occupational health, psychosocial support, and community home-care outreach.",
                 description_tet="Saúde okupasionál, apoiu psikososiál, no alkansu kuidadu-uma ba komunidade.",
                 description_pt="Saúde ocupacional, apoio psicossocial e cuidados domiciliários comunitários.",
                 icon="heart-pulse", order=3),
        ]
        for row in sub_units:
            row["category"] = "unit"
            row["parent"] = technical
            Department.objects.update_or_create(name_en=row["name_en"], defaults=row)

        self.stdout.write("Organizational structure: Board → Managing Director → 3 units (+3 technical sub-units)")
