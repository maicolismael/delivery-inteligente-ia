# delivery-inteligente-ia
Proyecto de Inteligencia Artificial: agente de delivery inteligente con Q-Learning para optimizar rutas, reducir distancia y priorizar entregas.

git checkout main
git pull origin main
git merge develop
git push origin main

# 🚚 Sistema de Despacho Inteligente

Sistema desarrollado en Python que simula un entorno de despacho inteligente utilizando un agente basado en Q-Learning para optimizar rutas de entrega.

El proyecto incluye:

- Simulación de pedidos
- Métricas de desempeño
- Agente Q-Learning
- Interfaz gráfica en CustomTkinter
- Visualización de resultados y métricas

---

# 📁 Estructura del proyecto

```bash
delivery-inteligente-ia/
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── entorno.py
│   ├── agente.py
│   ├── recompensas.py
│   ├── qlearning.py
│   └── metricas.py
│
├── ui/
│   └── app.py
│
├── data/
│   └── pedidos_simulados.json
│
├── docs/
│   └── informe.md
│
├── resultados/
│   └── .gitkeep
│
├── requirements.txt
├── README.md
└── .gitignore