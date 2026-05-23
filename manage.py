"""
CLI de administracion para MEDI-IA.

Uso:
    python manage.py sessions              # listar sesiones con stats
    python manage.py cleanup --days 30     # eliminar sesiones inactivas
    python manage.py clear <session_id>    # eliminar una sesion concreta
"""

import sys
import argparse
from src.memory import cleanup_old_sessions, session_stats, clear_session


def cmd_sessions(_args):
    stats = session_stats()
    if not stats:
        print("No hay sesiones guardadas.")
        return
    print(f"{'SESSION ID':<40} {'TURNS':>5}  {'LAST SEEN'}")
    print("-" * 70)
    for s in stats:
        last = s["last_seen"] or "desconocido"
        print(f"{s['session']:<40} {s['turns']:>5}  {last}")
    print(f"\nTotal: {len(stats)} sesion(es)")


def cmd_cleanup(args):
    days = args.days
    eliminated = cleanup_old_sessions(days=days)
    if eliminated == 0:
        print(f"No hay sesiones inactivas por mas de {days} dias.")
    else:
        print(f"Eliminadas {eliminated} sesion(es) inactivas por mas de {days} dias.")


def cmd_clear(args):
    sid = args.session_id
    clear_session(sid)
    print(f"Sesion '{sid}' eliminada.")


def main():
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description="Administracion de sesiones de MEDI-IA",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("sessions", help="Listar todas las sesiones con estadisticas")

    p_cleanup = sub.add_parser("cleanup", help="Eliminar sesiones inactivas")
    p_cleanup.add_argument(
        "--days", type=int, default=30,
        help="Dias de inactividad para considerar una sesion obsoleta (default: 30)",
    )

    p_clear = sub.add_parser("clear", help="Eliminar una sesion especifica")
    p_clear.add_argument("session_id", help="ID de la sesion a eliminar")

    args = parser.parse_args()
    {"sessions": cmd_sessions, "cleanup": cmd_cleanup, "clear": cmd_clear}[args.command](args)


if __name__ == "__main__":
    main()
