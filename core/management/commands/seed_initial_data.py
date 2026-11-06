from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Profile, SiteConfiguration
from training.models import TrainingCategory, TrainingService


# Fuente: información proporcionada por el titular en la solicitud del proyecto.
# Son áreas ofrecidas, no registros de cursos impartidos. No se infieren horas,
# clientes, fechas, proyectos, documentos ni estadísticas.
SERVICES = [
    ("inteligencia-artificial", "Inteligencia artificial generativa", "ai", "Aplicaciones de IA generativa y herramientas actuales para el trabajo y el aprendizaje."),
    ("excel-productividad", "Excel y herramientas de productividad", "chart", "Formación en Excel básico, intermedio y avanzado, con un enfoque práctico y aplicado al trabajo."),
    ("power-bi-datos", "Power BI y análisis de datos", "chart", "Herramientas para organizar, analizar y comunicar información mediante Microsoft Power BI."),
    ("python-programacion", "Python y programación", "code", "Aprendizaje de programación y desarrollo de software mediante teoría, demostraciones y ejercicios."),
    ("desarrollo-web", "Desarrollo web y aplicaciones", "code", "Formación en desarrollo web y aplicaciones full stack, conectando conceptos con su aplicación práctica."),
    ("bases-de-datos", "Bases de datos y SQL", "database", "Fundamentos y uso de bases de datos y SQL para trabajar con información de forma estructurada."),
    ("ciberseguridad", "Ciberseguridad", "shield", "Formación en ciberseguridad y cuidado de la información en entornos tecnológicos."),
    ("sistemas-operativos", "Sistemas operativos y herramientas TI", "desktop", "Capacitación en Linux, Windows y herramientas de tecnologías de la información."),
    ("alfabetizacion-digital", "Alfabetización digital", "desktop", "Uso de herramientas digitales, Windows, internet y correo electrónico para desenvolverse en el trabajo."),
    ("diseno-curricular", "Diseño curricular y docencia virtual", "book", "Diseño de experiencias de aprendizaje y formación virtual con orientación a la aplicación laboral."),
]


class Command(BaseCommand):
    help = "Carga el perfil y las áreas de capacitación documentadas, sin sobrescribir ediciones. No crea usuarios ni cursos ficticios."

    @transaction.atomic
    def handle(self, *args, **options):
        Profile.objects.get_or_create(pk=1, defaults={
            "full_name": "Gastón Nicolás Salgado Jara",
            "professional_title": "Ingeniero en Informática",
            "headline": "Tecnología que se aprende. Conocimiento que se aplica.",
            "introduction": "Docente, relator tecnológico y desarrollador de software. Formación práctica para personas, equipos y organizaciones en Chile.",
            "biography_technology": "Ingeniero en informática con más de 15 años de trayectoria en tecnologías de la información. Mi experiencia abarca desarrollo de software, análisis de sistemas y administración tecnológica para organizaciones de distintos sectores productivos.",
            "biography_teaching": "He desarrollado mi trayectoria docente en formación técnica, educación superior y capacitación laboral, como docente, relator y facilitador. Mi foco es transmitir conocimientos tecnológicos con metodologías prácticas, aprendizaje aplicado y herramientas actuales.",
            "teaching_methodology": "Combino teoría, demostraciones, ejercicios prácticos y aplicación laboral. El objetivo es conectar cada conocimiento con situaciones y necesidades concretas del trabajo.",
            "location": "Talca, Región del Maule, Chile",
            "coverage": "Relatorías presenciales en Chile y capacitaciones online",
            "email": "gastonsalgadoj@gmail.com",
            "whatsapp": "+56 9 3069 8473",
            "linkedin_url": "https://www.linkedin.com/in/gast%C3%B3n-nicol%C3%A1s-salgado-jara-93042b52/",
            "is_published": True,
        })
        SiteConfiguration.objects.get_or_create(pk=1, defaults={
            "site_name": "Gastón Salgado",
            "seo_title": "Gastón Salgado · Docencia TI y capacitación tecnológica en Chile",
            "seo_description": "Gastón Nicolás Salgado Jara, ingeniero en informática, docente y relator en Talca. Capacitación en inteligencia artificial, Excel, Power BI y programación.",
        })
        for position, (slug, name, icon, summary) in enumerate(SERVICES, start=1):
            category, _ = TrainingCategory.objects.get_or_create(slug=slug, defaults={"name": name, "description": summary, "position": position, "is_published": True})
            TrainingService.objects.get_or_create(slug=slug, defaults={"name": name, "category": category, "summary": summary, "icon": icon, "position": position, "is_published": True})
        self.stdout.write(self.style.SUCCESS("Datos iniciales disponibles. Se conservaron los registros y las ediciones existentes."))
