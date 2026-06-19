"""HVO team member roster.

Maps display name → (calendar_email, slack_email).
Calendar emails use @apollomail.io; Slack/login emails use @apollo.io.
Source: Slack canvas F08SHSMGAA0 (HVO Team Resources), verified June 2026.

To update: check the Slack canvas above for roster changes and edit the MEMBERS list below.
"""

from __future__ import annotations

# (display_name, calendar_email, slack_email)
_MEMBERS: list[tuple[str, str, str]] = [
    ("Alejandro Aguilar", "alejandro.aguilar@apollomail.io", "alejandro.aguilar@apollo.io"),
    ("Alexis Castro", "alex.castro@apollomail.io", "alex.castro@apollo.io"),
    ("Barush Cruz", "barush.cruz@apollomail.io", "barush.cruz@apollo.io"),
    ("Juliana Bonilla", "maria.bonilla@apollomail.io", "maria.bonilla@apollo.io"),
    ("Oscar Lorenzoni", "oscar.lorenzoni@apollomail.io", "oscar.lorenzoni@apollo.io"),
    ("Perla Salazar", "perla.salazar@apollomail.io", "perla.salazar@apollo.io"),
    ("Sergio Vega", "sergio.vega@apollomail.io", "sergio.vega@apollo.io"),
    ("Diego Tamayo", "diego.guzman@apollomail.io", "diego.guzman@apollo.io"),
    ("Eduardo Estrada", "eduardo.maldonado@apollomail.io", "eduardo.maldonado@apollo.io"),
    ("Jorge Manuel", "jorge.gutierrez@apollomail.io", "jorge.gutierrez@apollo.io"),
    ("Josue Neftali", "josue.reyes@apollomail.io", "josue.reyes@apollo.io"),
    ("Andrea Gonzalez", "andrea.gonzalez@apollomail.io", "andrea.gonzalez@apollo.io"),
    ("Rodrigo Ivan", "rodrigo.gaxiola@apollomail.io", "rodrigo.gaxiola@apollo.io"),
    ("Luis Diaz", "luis.diaz@apollomail.io", "luis.diaz@apollo.io"),
    ("Ana Ballesteros", "ana.ballesteros@apollomail.io", "ana.b@apollo.io"),
    ("Ana Mejia", "ana.mejia@apollomail.io", "ana.mejia@apollo.io"),
    ("Marifer Arguedas", "maria.arguedas@apollomail.io", "maria.arguedas@apollo.io"),
    ("Enrique Sampedro", "enrique.sampedro@apollomail.io", "enrique.sampedro@apollo.io"),
    ("Anaid Sansinena", "anaid.sansinena@apollomail.io", "anaid.sansinena@apollo.io"),
    ("Alex Arriaga", "alejandro.arriaga@apollomail.io", "alejandro.arriaga@apollo.io"),
    ("Kellyn Escobar", "kellyn.escobar@apollomail.io", "kellyn.escobar@apollo.io"),
    ("Sasha Suarez", "sasha.suarez@apollomail.io", "sasha.suarez@apollo.io"),
    ("Abril Macias", "abril.lopez@apollomail.io", "abril.lopez@apollo.io"),
    ("Alex Nunez", "ivan.nunezdelapena@apollomail.io", "ivan.nunezdelapena@apollo.io"),
    ("Michel Flores", "michel.flores@apollomail.io", "michel.flores@apollo.io"),
    ("Xoch Sabourin", "xoch.sabourin@apollomail.io", "xoch.sabourin@apollo.io"),
    ("Arlette Estrada", "arlette.estrada@apollomail.io", "arlette.estrada@apollo.io"),
    ("Paloma Tellez", "paloma.tellez@apollomail.io", "paloma.tellez@apollo.io"),
    ("Juan Nieto", "juan.nieto@apollomail.io", "juan.nieto@apollo.io"),
    ("Tamara Moreno", "tamara.moreno@apollomail.io", "tamara.moreno@apollo.io"),
    ("Alan Jimenez", "alan.jimenez@apollomail.io", "alan.jimenez@apollo.io"),
    ("Alice Antunez", "alicia.antunez@apollomail.io", "alicia.antunez@apollo.io"),
    ("Luisana Caraballo", "luisana.caraballo@apollomail.io", "luisana.caraballo@apollo.io"),
    ("Mike Gaytan", "miguel.gaytan@apollomail.io", "miguel.gaytan@apollo.io"),
    ("Natalia Ortega", "natalia.ortega@apollomail.io", "natalia.ortega@apollo.io"),
    ("Rodrigo Phillips", "rodrigo.phillips@apollomail.io", "rodrigo.phillips@apollo.io"),
    ("Laura Rivera", "laura.rivera@apollomail.io", "laura.rivera@apollo.io"),
    ("Elias Marin", "elias.marin@apollomail.io", "elias.marin@apollo.io"),
    ("Monica Cisneros", "monica.cisneros@apollomail.io", "monica.cisneros@apollo.io"),
    ("Gabriela Anaya", "gabriela.anaya@apollomail.io", "gabriela.anaya@apollo.io"),
    ("Sara Mendez", "sara.mendez@apollomail.io", "sara.mendez@apollo.io"),
    ("Dani Garcia", "rafael.garcia@apollomail.io", "rafael.garcia@apollo.io"),
    ("Irving Alvarez", "irving.alvarez@apollomail.io", "irving.alvarez@apollo.io"),
]

# Keyed lookup structures built once at import
_BY_NAME: dict[str, tuple[str, str]] = {
    name.lower(): (cal, slack) for name, cal, slack in _MEMBERS
}
_BY_CALENDAR_EMAIL: dict[str, tuple[str, str]] = {
    cal.lower(): (name, slack) for name, cal, slack in _MEMBERS
}
_ALL_CALENDAR_EMAILS: list[str] = [cal for _, cal, _ in _MEMBERS]


def all_members() -> list[tuple[str, str, str]]:
    """Return list of (display_name, calendar_email, slack_email)."""
    return list(_MEMBERS)


def all_calendar_emails() -> list[str]:
    """Return all @apollomail.io calendar emails."""
    return list(_ALL_CALENDAR_EMAILS)


def find_by_name(name: str) -> tuple[str, str] | None:
    """Return (calendar_email, slack_email) for a display name (case-insensitive).

    Supports partial match on first or last name.
    Returns None if no unique match found.
    """
    key = name.lower().strip()
    if key in _BY_NAME:
        return _BY_NAME[key]
    # Try partial match
    matches = [(k, v) for k, v in _BY_NAME.items() if key in k]
    if len(matches) == 1:
        return matches[0][1]
    return None


def display_name_for(calendar_email: str) -> str | None:
    """Return the display name for a given calendar email."""
    result = _BY_CALENDAR_EMAIL.get(calendar_email.lower())
    if result:
        return result[0]
    return None
