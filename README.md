# Ritmo — agente de una plataforma de streaming de música

Proyecto de demostración para el video de **Amazon Bedrock AgentCore**: cómo llevar un agente de IA de tu laptop a producción.

Ritmo es el asistente de una plataforma de streaming de música. Responde dudas de la cuenta del usuario: su plan, cuántas horas ha escuchado, cuándo se le renueva. El recorrido del video va de un agente que corre en local a uno desplegado, con memoria, observable, y que funciona con más de un framework.

## La decisión de diseño que hila todo

El agente **nunca toca la base de datos directamente**. No tiene el connection string, no arma consultas, no tiene credenciales de la base.

En su lugar, el agente llama a una herramienta (`consultar_cuenta`), y esa herramienta le pregunta a un servicio interno (`servicio_datos.py`) que es el único que habla con los datos. El agente solo ve el contrato de la herramienta: qué le pide y qué recibe.

Por qué:

- Un modelo generando consultas contra tu base de producción a partir de texto de usuario es una superficie de ataque, no una funcionalidad.
- El agente corre aislado en un entorno gestionado. Darle credenciales de base rompe ese aislamiento.
- La herramienta es el contrato, no la base. Por eso el mismo agente sirve para Strands o LangGraph sin cambios, y por eso escala a AgentCore Gateway cuando el acceso a datos crece.

## Arquitectura

![Diagrama de arquitectura de Ritmo](docs/arquitectura.svg)

El usuario habla con el agente (Strands o LangGraph) que corre en AgentCore Runtime. El agente razona con un modelo de Amazon Bedrock y, cuando necesita datos de la cuenta, llama a la herramienta `consultar_cuenta`. Esa herramienta es el único camino hacia `servicio_datos.py`, que a su vez es la única capa que toca los datos. El acceso directo del agente a la base está bloqueado por diseño.

## Estructura

| Archivo | Rol |
|---|---|
| `servicio_datos.py` | La única capa que habla con los datos. El agente nunca la importa; solo la herramienta la llama. |
| `agente_local.py` | El agente de Strands **puro**, sin una sola línea de AgentCore. Corre en tu laptop con un loop de chat. Es el "antes" del video. |
| `agente.py` | El **mismo** agente que `agente_local.py`, más las cuatro líneas de AgentCore. Idéntico por dentro; solo se le agrega la puerta de entrada para producción. Se mantiene limpio (sin memoria) para que la comparación lado a lado sea exacta. |
| `agente_memoria.py` | El mismo `agente.py` con AgentCore Memory (corto plazo) añadida. Ritmo recuerda el hilo de la conversación dentro de la sesión. |
| `agente_langgraph.py` | La misma idea con LangGraph. Mismo entrypoint, mismo deploy, misma herramienta. Solo cambia cómo se construye el agente. |
| `crear_memoria.py` | Script de una sola vez para crear el recurso de AgentCore Memory (corto plazo) y obtener su ID. Espera a que quede activo antes de imprimirlo. |
| `setup.sh` | Prepara el entorno: crea el venv e instala las dependencias. |
| `requirements.txt` | Dependencias del agente de Strands. |
| `requirements-langgraph.txt` | Dependencias de la variante de LangGraph. |

Las dos versiones del agente (`agente_local.py` y `agente.py`) tienen por dentro el mismo modelo, las mismas instrucciones y la misma herramienta. La única diferencia son las cuatro líneas de AgentCore. Compararlas lado a lado es el punto del video.

## Preparar el entorno

Necesitas Python 3.10+ y credenciales de AWS con acceso a Bedrock. El proyecto usa el modelo **Amazon Nova Lite** (`us.amazon.nova-lite-v1:0`); asegúrate de tenerlo habilitado en tu región (Bedrock → Model access).

```bash
./setup.sh              # solo el agente de Strands
./setup.sh --langgraph  # además, las dependencias de LangGraph

source .venv/bin/activate

# Credenciales de AWS (nunca en el código). Usa el perfil y la región que correspondan:
export AWS_PROFILE=tu-perfil
export AWS_REGION=us-east-2
```

> El modelo y la región deben coincidir: Nova Lite tiene que estar disponible en la región que uses. Cada terminal nueva necesita `export AWS_PROFILE` de nuevo, o el SDK tomará el perfil `default`.

## Correr el agente local (sin AgentCore)

```bash
python agente_local.py
```

Escribe una pregunta como "¿Cuántas horas he escuchado este mes? soy u-1042" y verás en la consola la llamada a la herramienta antes de la respuesta. Escribe `salir` para terminar. Este agente solo vive mientras la terminal esté abierta.

El usuario de prueba es `u-1042` (plan Premium, 47 horas este mes, renueva el 1 de octubre). Está definido en `servicio_datos.py`.

## Correr el agente con AgentCore (local, antes de desplegar)

```bash
python agente.py
```

Levanta el servidor de AgentCore en el puerto 8080. En otra terminal:

```bash
curl -X POST http://localhost:8080/invocations \
     -H "Content-Type: application/json" \
     -d '{"prompt": "¿Qué plan tengo? soy u-1042"}'
```

## Desplegar a AgentCore

```bash
pip install bedrock-agentcore-starter-toolkit

agentcore configure --entrypoint agente.py
agentcore deploy
agentcore invoke '{"prompt": "¿Qué plan tengo? soy u-1042"}'
```

`configure` prepara el agente, `deploy` lo publica en AgentCore Runtime y devuelve el ARN, `invoke` lo llama ya desplegado.

> Nota: en versiones recientes del starter toolkit el comando de publicación es `agentcore deploy` (antes se llamaba `agentcore launch`, que sigue como alias). La primera invocación tras un deploy tarda más por el arranque en frío.

## Memoria (Parte 4 del video)

La memoria vive en su propio archivo, `agente_memoria.py`, para no cargar `agente.py` (que es el de la comparación y el deploy). Usamos **memoria de corto plazo**: AgentCore guarda los turnos de la conversación y los trae de vuelta en cada respuesta, así Ritmo recuerda lo que ya se dijeron dentro de la sesión.

Primero crea el recurso de memoria una vez (tarda ~1-2 min en quedar activo, créalo antes de grabar):

```bash
python crear_memoria.py
# copia el ID que imprime
export RITMO_MEMORY_ID=<el-id>
```

Con `RITMO_MEMORY_ID` en el entorno, corre el agente con memoria (levanta el servidor de AgentCore en el puerto 8080):

```bash
python agente_memoria.py
```

En otra terminal, prueba que recuerda dentro de la conversación:

```bash
# Turno 1: le cuentas un gusto
curl -s -X POST http://localhost:8080/invocations \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Me gusta la salsa para hacer ejercicio"}'

# Turno 2: le preguntas por él y lo recuerda
curl -s -X POST http://localhost:8080/invocations \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Según lo que te conté, ¿qué escucho cuando hago ejercicio?"}'
```

Ojo: la memoria de la conversación es distinta de los datos de la cuenta (que viven en `servicio_datos.py`). Uno es quién es el usuario, el otro es qué se han dicho. (AgentCore también ofrece memoria de largo plazo entre sesiones vía estrategias; aquí usamos corto plazo para mantener la demo simple.)

## La misma idea con LangGraph (Parte 6 del video)

`agente_langgraph.py` es el mismo Ritmo construido con LangGraph en vez de Strands. El entrypoint, el deploy y la forma de invocarlo son idénticos; solo cambia cómo se arma el agente por dentro. El deploy es el mismo:

```bash
agentcore configure --entrypoint agente_langgraph.py --requirements-file requirements-langgraph.txt
agentcore deploy
agentcore invoke '{"prompt": "¿Qué plan tengo? soy u-1042"}'
```

> Detalle importante del deploy de LangGraph: en modo `direct_code_deploy` el toolkit empaqueta las dependencias del `requirements.txt` de la raíz (el de Strands), aunque le pases `--requirements-file`. Si el runtime falla con `ModuleNotFoundError: No module named 'langchain'`, coloca las dependencias de LangGraph como `requirements.txt` de la raíz para ese deploy (respalda el de Strands antes y restáuralo después), borra el caché `.bedrock_agentcore/<agente>/dependencies.*` y vuelve a hacer `deploy`.

## Solución de problemas

- **`LoginRefreshRequired` / `Your session has expired`**: tu sesión de AWS caducó. Reautentica (`aws login --profile <perfil>`) y vuelve a exportar `AWS_PROFILE`.
- **Credenciales de la cuenta equivocada**: si el agente falla con credenciales aunque hiciste login, revisa que `AWS_PROFILE` esté exportado en esa terminal. Sin él, el SDK usa el perfil `default`.
- **`address already in use` en el puerto 8080**: quedó un `python agente.py` o `python agente_memoria.py` corriendo. Ciérralo con `Ctrl+C` o libera el puerto antes de arrancar otro.
- **`ModuleNotFoundError: No module named 'langchain'` al invocar el deploy de LangGraph**: ver la nota de la sección de LangGraph (hay que empaquetar el `requirements` correcto).
- **El modelo responde con bloques `<thinking>`**: Nova a veces incluye su razonamiento. `agente_memoria.py` ya lo filtra en la respuesta; si lo ves en otro agente, ajusta el manejo de la salida.
- **`Memory status is not active`**: el recurso de memoria aún se está creando. `crear_memoria.py` ya espera a que quede activo; si lo creaste por otra vía, espera ~1-2 min.

## Nota de seguridad

Las credenciales de AWS van por variables de entorno, nunca en el código ni en el repo. El `.gitignore` ya excluye `.env`, llaves y artefactos del deploy. Después de grabar, limpia los recursos de AWS (runtime, repositorio de ECR, rol de IAM, recurso de memoria) para no dejar nada facturando.
