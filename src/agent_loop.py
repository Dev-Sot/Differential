"""
Bucle ReAct (Reasoning + Acting) para MEDI-IA.
El LLM razona, decide que tool usar, observa el resultado, y repite
hasta producir una respuesta final.

Patron: Thought -> Action -> Input -> Observation -> ... -> Final Answer
"""

import re
import os
from src.llm import chat
from src.tools import execute_tool, tools_description, TOOLS
from src.memory import get_history, add_turn, set_system

MAX_ITERATIONS = 6  # maximo de ciclos Thought-Action-Observation
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def _load_system_prompt() -> str:
    path = os.path.join(PROMPTS_DIR, "system.txt")
    with open(path, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(tools_description=tools_description())


def _parse_action(text: str) -> tuple[str | None, str | None]:
    """Extrae Action y Input del texto generado por el LLM."""
    action_match = re.search(r"Action:\s*(\w+)", text, re.IGNORECASE)
    input_match = re.search(r"Input:\s*(.+?)(?=\nThought|\nAction|\nObservation|\nFinal|$)",
                             text, re.IGNORECASE | re.DOTALL)
    action = action_match.group(1).strip() if action_match else None
    inp = input_match.group(1).strip() if input_match else None
    return action, inp


def _extract_final_answer(text: str) -> str | None:
    """Extrae la respuesta final si el LLM la produjo."""
    match = re.search(r"Final Answer:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def _extract_urgency_from_response(text: str) -> str:
    """Infiere nivel de urgencia de la respuesta final."""
    text_lower = text.lower()
    if "emergencia" in text_lower:
        return "emergencia"
    if "grave" in text_lower:
        return "grave"
    if "leve" in text_lower:
        return "leve"
    return "moderada"


def run_react(session_id: str, user_message: str) -> dict:
    """
    Ejecuta el bucle ReAct completo para un mensaje del usuario.
    Retorna diccionario con respuesta estructurada.
    """
    # Inicializar sesion con system prompt
    system_prompt = _load_system_prompt()
    set_system(session_id, system_prompt)

    # Agregar mensaje del usuario al historial
    add_turn(session_id, "user", user_message)

    trajectory = []   # registro de pasos para mostrar en UI
    observations = [] # contexto acumulado de las tools

    llm_response = ""
    final_answer = None

    for iteration in range(MAX_ITERATIONS):
        # Construir contexto acumulado para que el LLM vea las observaciones anteriores
        accumulated = ""
        if observations:
            accumulated = "\n\n".join(
                f"Observation {i+1}: {obs}" for i, obs in enumerate(observations)
            )

        # Preparar mensajes para el LLM
        history = get_history(session_id)

        # Si hay observaciones previas, añadirlas como contexto en el ultimo mensaje
        if accumulated and iteration > 0:
            messages = history[:-1] + [{
                "role": "user",
                "content": (
                    f"{history[-1]['content']}\n\n"
                    f"Contexto recopilado hasta ahora:\n{accumulated}\n\n"
                    f"Continua con el razonamiento o da la respuesta final."
                )
            }]
        else:
            messages = history

        # Llamar al LLM
        try:
            llm_response = chat(messages, max_tokens=800, temperature=0.2)
        except Exception as e:
            final_answer = f"Error al contactar el modelo de lenguaje: {e}"
            break

        # Revisar si ya tiene respuesta final
        final_answer = _extract_final_answer(llm_response)
        if final_answer:
            trajectory.append({"type": "final", "content": llm_response})
            break

        # Parsear accion
        action, action_input = _parse_action(llm_response)

        if not action:
            # El LLM no siguio el formato — tratar respuesta como final
            final_answer = llm_response
            trajectory.append({"type": "final", "content": llm_response})
            break

        # Registrar el thought del LLM
        thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction|$)", llm_response,
                                   re.IGNORECASE | re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else llm_response

        trajectory.append({
            "type": "thought",
            "content": thought,
            "action": action,
            "input": action_input or "",
        })

        # Ejecutar la tool
        observation = execute_tool(action, action_input or "")
        observations.append(f"[{action}({action_input})]\n{observation}")

        trajectory.append({
            "type": "observation",
            "tool": action,
            "content": observation[:500],
        })

    # Si agoto iteraciones sin respuesta final
    if not final_answer:
        if observations:
            # Pedir respuesta final con todo el contexto
            context = "\n\n".join(observations)
            messages = get_history(session_id) + [{
                "role": "user",
                "content": (
                    f"Con base en toda la informacion recopilada:\n{context}\n\n"
                    f"Da ahora tu respuesta final estructurada sobre los sintomas: {user_message}"
                )
            }]
            try:
                final_answer = chat(messages, max_tokens=1000, temperature=0.2)
            except Exception:
                final_answer = "No pude generar una respuesta. Por favor consulta con un medico."
        else:
            final_answer = (
                "No encontre informacion suficiente en los libros medicos para estos sintomas. "
                "Esto no reemplaza la consulta medica profesional."
            )

    # Guardar respuesta del asistente en memoria
    add_turn(session_id, "assistant", final_answer)

    urgency = _extract_urgency_from_response(final_answer)
    tools_used = list({step["action"] for step in trajectory if step["type"] == "thought" and "action" in step})
    sources = list({
        line.split("|")[0].replace("[", "").strip()
        for obs in observations
        for line in obs.split("\n")
        if "|" in line and ("Harrison" in line or "Oxford" in line or "Symptom" in line or "Drug" in line)
    })

    return {
        "respuesta": final_answer,
        "urgencia": urgency,
        "gravedad": urgency,
        "trajectory": trajectory,
        "tools_used": tools_used,
        "fuentes": sources,
        "iteraciones": iteration + 1,
        "modo": f"ReAct Agent (Qwen2.5-7B) — {len(tools_used)} tools usadas",
    }
