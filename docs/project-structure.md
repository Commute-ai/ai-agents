```commute-ai-agents/
├── .github/
│   └── workflows/
│       ├── ci.yml                      # Existing
│       └── sync-subtask-week.yml       # Existing
│
├── app/                                # Existing application code
│   ├── __init__.py
│   ├── main.py                         # Existing
│   ├── config.py                       # Enhanced with template config
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── routes.py               # Enhanced
│   │       └── endpoints/
│   │           ├── health.py           # Existing
│   │           └── agents.py           # NEW: Agent endpoints
│   │
│   ├── agents/                         # NEW: AI Agents system
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py
│   │   │   └── route_agent.py
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── template_manager.py     # Data assets manager
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── requests.py
│   │       └── responses.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── logger.py                   # Existing
│
├── data/                               # NEW: Data assets (outside app/)
│   └── prompts/                        # Template storage
│       ├── system/                     # System prompts
│       │   ├── base_agent.j2
│       │   ├── route_analysis.j2
│       │   └── recommendation.j2
│       ├── user/                       # User prompt templates
│       │   ├── route_request.j2
│       │   └── feedback_request.j2
│       ├── partials/                   # Reusable components
│       │   ├── weather_section.j2
│       │   ├── traffic_section.j2
│       │   └── user_profile.j2
│       └── macros/                     # Jinja2 macros
│           ├── formatting.j2
│           └── calculations.j2
│
├── tests/                              # Existing
│   ├── __init__.py
│   ├── unit/
│   │   └── agents/                     # NEW: Agent tests
│   │       └── test_template_manager.py
│   └── integration/
│       └── test_agent_flow.py          # NEW: End-to-end tests
│
├── .env.example                        # NEW: Template environment vars
├── .gitignore                          # Enhanced
├── Makefile                           # Existing
├── pyproject.toml                     # Enhanced with jinja2
├── README.md                          # Existing
└── shell.nix                          # Existing
```
