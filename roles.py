import random

ROLES = ["Mafioso", "Doctor", "Detective", "Ciudadano"]

def asignar_roles(jugadores):
    """
    Asigna los roles de manera aleatoria a los jugadores.
    
    - 1 Mafioso
    - 1 Doctor
    - 1 Detective
    - El resto son Ciudadanos
    """
    print(f"[DEBUG] Jugadores para asignar roles: {jugadores}")  # Depuración

    if len(jugadores) < 4:
        raise ValueError("Se necesitan al menos 4 jugadores para asignar roles.")

    roles_asignados = {}

    # Asignar los roles únicos primero
    roles_disponibles = ["Mafioso", "Doctor", "Detective"]
    random.shuffle(roles_disponibles)

    for jugador in jugadores[:3]:  # Los primeros 3 jugadores reciben roles especiales
        roles_asignados[jugador] = roles_disponibles.pop()

    # El resto de jugadores son Ciudadanos
    for jugador in jugadores[3:]:
        roles_asignados[jugador] = "Ciudadano"

    print(f"[DEBUG] Roles asignados: {roles_asignados}")  # Depuración
    return roles_asignados
