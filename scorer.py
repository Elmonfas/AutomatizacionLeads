"""Heuristic scoring — no external API needed."""

from scraper import BusinessLead


def score_lead(lead: BusinessLead, freelancer_name: str, city: str) -> BusinessLead:
    score = 1
    reasons = []

    if not lead.has_website:
        score = 10
        reasons.append("sin web")
    else:
        mobile = lead.pagespeed_mobile
        desktop = lead.pagespeed_desktop
        ssl = lead.has_ssl
        old = lead.web_looks_old

        if mobile is not None and mobile < 30:
            score += 4
            reasons.append(f"web muy lenta en móvil ({mobile}/100)")
        elif mobile is not None and mobile < 50:
            score += 3
            reasons.append(f"web lenta en móvil ({mobile}/100)")
        elif mobile is not None and mobile < 65:
            score += 2
            reasons.append(f"web mejorable en móvil ({mobile}/100)")

        if not ssl:
            score += 2
            reasons.append("sin SSL (HTTP)")

        if old:
            score += 2
            reasons.append("tecnología web antigua detectada")

        if lead.is_mobile_friendly is False:
            score += 1
            reasons.append("no es mobile-friendly")

        score = min(score, 9)  # 10 reservado para sin web

    lead.urgency_score = score

    if not reasons:
        reasons.append("web en buen estado")
    lead.problem_summary = reasons[0].capitalize()

    # WhatsApp message
    name = lead.name
    if not lead.has_website:
        lead.whatsapp_message = (
            f"Hola, soy {freelancer_name}, diseñador web en {city}. "
            f"He visto que {name} no tiene página web y creo que podríais ganar muchos clientes con una. "
            f"¿Tienes 5 minutos para que te cuente cómo lo haríamos?"
        )
    elif lead.pagespeed_mobile is not None and lead.pagespeed_mobile < 50:
        lead.whatsapp_message = (
            f"Hola, soy {freelancer_name}, diseñador web en {city}. "
            f"He analizado la web de {name} y carga muy lento en móvil ({lead.pagespeed_mobile}/100), "
            f"lo que hace que la mayoría de visitas se vayan sin comprar. ¿Te puedo explicar cómo lo arreglamos?"
        )
    elif not lead.has_ssl:
        lead.whatsapp_message = (
            f"Hola, soy {freelancer_name}, diseñador web en {city}. "
            f"La web de {name} no tiene HTTPS y los navegadores la marcan como 'no segura', "
            f"lo que espanta a los clientes. Es fácil de solucionar, ¿hablamos?"
        )
    else:
        lead.whatsapp_message = (
            f"Hola, soy {freelancer_name}, diseñador web en {city}. "
            f"He revisado la web de {name} y creo que hay margen de mejora en rendimiento y diseño. "
            f"¿Te interesa que te prepare un pequeño análisis gratuito?"
        )

    return lead


def score_all(leads: list[BusinessLead], freelancer_name: str, city: str) -> list[BusinessLead]:
    print(f"  [scorer] Scoring {len(leads)} leads (heurístico local)...")
    results = [score_lead(lead, freelancer_name, city) for lead in leads]
    return results
